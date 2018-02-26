"""
Convert SBML model to ODE system which can be integrated with scipy.
"""
import os
import numpy as np
from scipy.integrate import odeint
from matplotlib import pyplot as plt
try:
    import libsbml
except ImportError:
    import tesbml as libsbml

import re
from pprint import pprint
from sbmlutils.converters.mathml import evaluableMathML
from collections import defaultdict


# TODO: jinja2 template for python code generation
# TODO: fix dependency order with reactions (general dependency order)

# TODO: separate in required y and yc (calculated y)
# TODO: helper functions for y calculation and data frame
# TODO: proper calculation of initial conditions (initial assignments & assignment rules)
# TODO: R export


# TODO: does not handle ConversionFactors, FunctionDefinitions nor Events



class SBML2ODE(object):
    """ SBML 2 ode converter.

    Writes out python or R ODE files which can be used with standard
    integrators like scipy odeint or R odeint.
    """

    def __init__(self, doc):
        """

        :param doc: SBMLdocument
        """
        self.doc = doc  # type: libsbml.SBMLDocument


        self.x0 = {}  # initial conditions
        self.dxids = {}  # state variables x
        self.pids = {}  # parameters p
        self.yids = {}  # assigned variables
        self.rids = {}  # reactions
        self.yids_ordered = None

        self._create_odes()

    @classmethod
    def from_file(cls, sbml_file):
        doc = libsbml.readSBMLFromFile(sbml_file)  # type: libsbml.SBMLDocument
        return cls(doc)


    def _create_odes(self):

        """ Creates information of ODE system from SBMLDocument.

        :return:
        """
        model = self.doc.getModel()  # type: libsbml.Model
        # --------------
        # parameters
        # --------------
        # 1. constant parameters (real parameters of the system)
        for parameter in model.getListOfParameters():  # type: libsbml.Parameter
            pid = parameter.getId()
            if parameter.getConstant():
                value = parameter.getValue()
            else:
                value = ''
            self.pids[pid] = value

        # --------------
        # species
        # --------------
        for species in model.getListOfSpecies():  # type: libsbml.Species
            sid = species.getId()
            self.dxids[sid] = ''
            # initial condition
            value = None
            compartment = model.getCompartment(species.getCompartment())  # type: libsbml.Compartment
            if species.isSetInitialAmount():
                value = species.getInitialAmount()
                if not species.getHasOnlySubstanceUnits():
                    # FIXME: handle the initial assignments/assignment rules for compartment volumes
                    value = value / compartment.getSize()

            elif species.isSetInitialConcentration():
                value = species.getInitialConcentration()
                if species.getHasOnlySubstanceUnits():
                    # FIXME: handle the initial assignments/assignment rules for compartment volumes
                    value = value * compartment.getSize()

            self.x0[sid] = value

        # --------------
        # rules
        # --------------
        for rule in model.getListOfRules():  # type: libsbml.Rule
            type_code = rule.getTypeCode()
            # --------------
            # rate rules
            # --------------
            if type_code == libsbml.SBML_RATE_RULE:
                # directly converted to odes (create additional state variables)
                rate_rule = rule  # type: libsbml.AssignmentRule
                variable = rate_rule.getVariable()

                # store rule
                astnode = rate_rule.getMath()
                self.dxids[variable] = astnode

                # dxids[variable] = evaluableMathML(astnode)

                # could be species or parameter
                if variable in self.pids:
                    del self.pids[variable]
                    parameter = model.getParameter(variable)
                    self.x0[variable] = parameter.getValue()

            # --------------
            # assignment rules
            # --------------
            elif type_code == libsbml.SBML_ASSIGNMENT_RULE:
                as_rule = rule  # type: libsbml.RateRule
                variable = as_rule.getVariable()
                astnode = as_rule.getMath()
                self.yids[variable] = astnode
                # yids[variable] = evaluableMathML(astnode)
                if variable in self.dxids:
                    del self.dxids[variable]
                if variable in self.pids:
                    del self.pids[variable]

        # Process the kinetic laws of reactions
        for reaction in model.getListOfReactions():  # type: libsbml.Reaction
            rid = reaction.getId()
            if reaction.isSetKineticLaw():
                klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
                astnode = klaw.getMath()
            self.rids[rid] = astnode

            for reactant in reaction.getListOfReactants():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=reactant, sign="-")
            for product in reaction.getListOfProducts():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=product, sign="+")

        # check which math depends on other math (build tree of dependencies)
        filtered_ids = set(list(self.pids.keys()) + list(self.dxids.keys()) + list(self.rids.keys()))
        self.yids_ordered = self._ordered_yids(model, filtered_ids)

        # replacement dictionaries:
        pids_idx = {}
        for k, key in enumerate(sorted(self.pids.keys())):
            pids_idx[key] = k
        yids_idx = {}
        for k, key in enumerate(self.yids_ordered):
            yids_idx[key] = k
        dxids_idx = {}
        for k, key in enumerate(sorted(self.dxids.keys())):
            dxids_idx[key] = k

        pprint(pids_idx)

        for d in [self.yids, self.rids, self.dxids]:
            # replace p and x, y
            for key in d:
                astnode = d[key]
                if not isinstance(astnode, libsbml.ASTNode):
                    continue

                if True:
                    # replace parameters
                    for key_rep, index in pids_idx.items():
                        ast_rep = libsbml.parseL3Formula('p__{}__'.format(index))
                        astnode.replaceArgument(key_rep, ast_rep)
                    # replace states
                    for key_rep, index in dxids_idx.items():
                        ast_rep = libsbml.parseL3Formula('x__{}__'.format(index))
                        astnode.replaceArgument(key_rep, ast_rep)
                    # replace y (use ordery yids for lookup)
                    for key_rep, index in yids_idx.items():
                        ast_rep = libsbml.parseL3Formula('y__{}__'.format(index))
                        astnode.replaceArgument(key_rep, ast_rep)

                formula = evaluableMathML(astnode)
                if True:
                    formula = re.sub("p__", "p[", formula)
                    formula = re.sub("x__", "x[", formula)
                    formula = re.sub("y__", "y[", formula)
                    formula = re.sub("__", "]", formula)

                d[key] = formula

    def _add_reaction_formula(self, model, rid, species_ref, sign):
        """ Adds part of reaction formula to ODEs for species.

        :param rid:
        :param species_ref:
        :param sign:
        :return:
        """
        stoichiometry = species_ref.getStoichiometry()
        sid = species_ref.getSpecies()
        species = model.getSpecies(sid)
        vid = species.getCompartment()

        # stoichiometry prefix
        if abs(stoichiometry - 1.0) < 1E-10:
            stoichiometry = ''
        else:
            stoichiometry = '{}*'.format(stoichiometry)

        # check if only substance units
        if species.getHasOnlySubstanceUnits():
            self.dxids[sid] += ' {} {}{}'.format(sign, stoichiometry, rid)
        else:
            self.dxids[sid] += ' {} {}{}/{}'.format(sign, stoichiometry, rid, vid)

    def _ordered_yids(self, model, filtered_ids):
        """ Get the order of the vids from the assignment rules.

        :param model:
        :param filtered_ids
        :return:
        """
        g = defaultdict(set)

        def add_dependency_edges(g, astnode):
            """ Add the dependency edges to the graph.

            :param g:
            :param astnode:
            :return:
            """
            # variable --depends_on--> v2
            for k in range(astnode.getNumChildren()):
                child = astnode.getChild(k)  # type: libsbml.ASTNode
                if child.getType() == libsbml.AST_NAME:

                    # add to dependency graph if id is not a defined parameter or state variable
                    sid = child.getName()
                    if sid not in filtered_ids:
                        g[variable].add(sid)

                # recursive adding of children
                add_dependency_edges(g, child)

        # create dependency graph
        for rule in model.getListOfRules():  # type: libsbml.Rule
            # assignment rules
            type_code = rule.getTypeCode()
            if type_code == libsbml.SBML_ASSIGNMENT_RULE:
                as_rule = rule  # type: libsbml.AssignmentRule
                variable = as_rule.getVariable()
                g[variable] = set()

                # traverse astnode to find the dependencies (add to graph)
                astnode = as_rule.getMath()  # type: libsbml.ASTNode
                add_dependency_edges(g, astnode)

        def create_ordered_variables(g, yids=None):
            if yids is None:
                yids = []

            yids_remove = []
            for yid in sorted(g.keys()):
                yid_deps = g[yid]

                # add yids with no dependencies
                if len(yid_deps) == 0:
                    yids_remove.append(yid)

            # add nodes with no dependencies to list
            yids = yids + list(yids_remove)  # hard copy to store

            for yid in yids_remove:
                # remove the yid from nodes
                del g[yid]
                # remove the yid from dependency graph
                for s in g.values():
                    if yid in s:
                        s.remove(yid)

            # still nodes in dependency graph (recursive removal)
            print(len(yids))
            print(len(g))
            if len(g) > 0:
                yids = create_ordered_variables(g, yids=yids)
            return yids

        # create order from dependency graph
        yids = create_ordered_variables(g)
        return yids


    def to_python(self, py_file):
        """ Write ODEs to python.

        :param py_file:
        :return:
        """
        # TODO: provide functions for calculating the full solution (as DataFrame)
        with open(py_file, "w") as f:
            # -------------------
            # imports
            # -------------------
            f.write('"""\n')
            f.write("{}\n".format(model_id))
            f.write('"""\n')
            f.write("import numpy as np\n")
            f.write("\n\n")

            # -------------------
            # ids
            # -------------------
            f.write("xids = [")
            for key in sorted(self.dxids.keys()):
                f.write('"{}", '.format(key))
            f.write("]\n")

            f.write("pids = [")
            for key in sorted(self.pids.keys()):
                f.write('"{}", '.format(key))
            f.write("]\n")

            f.write("yids = [")
            for key in self.yids_ordered:
                f.write('"{}", '.format(key))
            f.write("]\n\n")

            # -------------------
            # initial conditions
            # -------------------
            f.write("x0 = [\n")
            for k, key in enumerate(sorted(self.x0.keys())):
                f.write('    {},\t\t# {} [{}]\n'.format(self.x0[key], key, k))
            f.write("]\n\n")

            # -------------------
            # parameters
            # -------------------
            for vid, d in [('p', self.pids)]:
                f.write("{} = [\n".format(vid))
                for k, key in enumerate(sorted(d.keys())):
                    f.write('    {},\t\t# {} [{}]\n'.format(d[key], key, k))
                f.write("]\n\n")

            # -------------------
            # odes
            # -------------------

            f.write("def f_dxdt(x, t, p):\n")
            f.write('    """ ODE system """\n')

            # y
            f.write("    y = np.zeros(shape=({}, 1))\n".format(len(self.yids)))
            for k, key in enumerate(self.yids_ordered):
                f.write('    y[{}] = {},\t\t# {} [{}]\n'.format(k, self.yids[key], key, k))
            f.write("\n\n")

            # r
            f.write("    # reactions\n")
            for key in sorted(self.rids.keys()):
                f.write('    {} = {}\n'.format(key, self.rids[key]))
            f.write("\n\n")

            f.write("    return [\n")
            for k, key in enumerate(sorted(self.dxids.keys())):
                f.write('        {},\t\t# {} [{}]\n'.format(self.dxids[key], key, k))
            f.write("    ]\n\n")


#####################################################################################

if __name__ == "__main__":

    # convert xpp to sbml
    model_id = "limax_pkpd_38"
    in_dir = './scipyode_example'
    out_dir = './scipyode_example/results'
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))
    py_file = os.path.join(in_dir, "{}.py".format(model_id))

    sbml2ode = SBML2ODE.from_file(sbml_file=sbml_file)
    sbml2ode.to_python(py_file=py_file)
