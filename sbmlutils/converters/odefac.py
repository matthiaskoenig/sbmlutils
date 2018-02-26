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

import jinja2
import re
from pprint import pprint
from sbmlutils.converters.mathml import evaluableMathML
from collections import defaultdict


# TODO: proper calculation of initial conditions (initial assignments & assignment rules)
# TODO: R export

# TODO: separate in required y and yc (calculated y)
# TODO: does not handle ConversionFactors, FunctionDefinitions nor Events

# template location
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


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

        self.x0 = {}    # initial amounts/concentrations
        self.a = {}     # initial assignments
        self.dx = {}    # state variables x (odes)
        self.p = {}     # parameters p (constants)
        self.y = {}     # assigned variables
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
            self.p[pid] = value

        # --------------
        # compartments
        # --------------
        # constant compartments (parameters of the system)
        for compartment in model.getListOfCompartments():  # type: libsbml.Compartment
            cid = compartment.getId()
            if compartment.getConstant():
                value = compartment.getSize()
            else:
                value = ''
            self.p[cid] = value

        # --------------
        # species
        # --------------
        for species in model.getListOfSpecies():  # type: libsbml.Species
            sid = species.getId()
            self.dx[sid] = ''
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

        # --------------------
        # initial assignments
        # --------------------
        # types of objects whose identifiers are permitted as the values of InitialAssignment symbol attributes
        # are Compartment, Species, SpeciesReference and (global) Parameter objects in the model.

        for assignment in model.getListOfInitialAssignments():  # type: libsbml.InitialAssignment
            variable = assignment.getSymbol()
            astnode = assignment.getMath()
            self.x0[variable] = astnode

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
                self.dx[variable] = astnode

                # dxids[variable] = evaluableMathML(astnode)

                # could be species, parameter, or compartment
                if variable in self.p:
                    del self.p[variable]
                    parameter = model.getParameter(variable)
                    if parameter:
                        self.x0[variable] = parameter.getValue()
                    compartment = model.getCompartment(variable)
                    if compartment:
                        self.x0[variable] = compartment.getSize()

            # --------------
            # assignment rules
            # --------------
            elif type_code == libsbml.SBML_ASSIGNMENT_RULE:
                as_rule = rule  # type: libsbml.RateRule
                variable = as_rule.getVariable()
                astnode = as_rule.getMath()
                self.y[variable] = astnode
                # yids[variable] = evaluableMathML(astnode)
                if variable in self.dx:
                    del self.dx[variable]
                if variable in self.p:
                    del self.p[variable]

        # Process the kinetic laws of reactions
        for reaction in model.getListOfReactions():  # type: libsbml.Reaction
            rid = reaction.getId()
            if reaction.isSetKineticLaw():
                klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
                astnode = klaw.getMath()
            self.y[rid] = astnode

            for reactant in reaction.getListOfReactants():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=reactant, sign="-")
            for product in reaction.getListOfProducts():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=product, sign="+")


        # check which math depends on other math (build tree of dependencies)
        self.yids_ordered = self._ordered_yids()


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
            self.dx[sid] += ' {}{}{}'.format(sign, stoichiometry, rid)
        else:
            self.dx[sid] += ' {}{}{}/{}'.format(sign, stoichiometry, rid, vid)

    @staticmethod
    def dependency_graph(y, filtered_ids):
        """ Creates dependency graph from given dictionary.

        :param y: { variable: astnode } dictionary
        :param filtered_ids: ids which are defined elsewhere and not part of dependency tree
        :return:
        """

        def add_dependency_edges(g, variable, astnode):
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
                add_dependency_edges(g, variable, child)


        # create the math dependency graph
        g = defaultdict(set)
        for variable, astnode in y.items():
            g[variable] = set()
            add_dependency_edges(g, variable=variable, astnode=astnode)

        return g

    def _ordered_yids(self):
        """ Get the order of the vids from the assignment rules.

        :param model:
        :param filtered_ids
        :return:
        """
        filtered_ids = set(list(self.p.keys()) + list(self.dx.keys()))
        g = SBML2ODE.dependency_graph(self.y, filtered_ids)
        # pprint(g)

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
            if len(g) > 0:
                yids = create_ordered_variables(g, yids=yids)
            return yids

        # create order from dependency graph
        yids = create_ordered_variables(g)
        return yids

    def _render_template(self, template='template.py'):
        """ Renders given language template.

        :param template:
        :return:
        """
        # template environment
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                                 extensions=['jinja2.ext.autoescape'],
                                 trim_blocks=True,
                                 lstrip_blocks=True)
        template = env.get_template(template)

        # Context
        c = {
            'model': self.doc.getModel(),
            'xids': sorted(self.dx.keys()),
            'pids': sorted(self.p.keys()),
            'yids': self.yids_ordered,
            # 'rids': sorted(self.r.keys()),

            'x0': self.x0,
            'p': self.p,
            'y': self.y,
            'dx': self.dx,
        }
        return template.render(c)


    def _indices(self, index_offset=0):
        # replacement dictionaries:
        pids_idx = {}
        for k, key in enumerate(sorted(self.p.keys())):
            pids_idx[key] = k + index_offset
        yids_idx = {}
        for k, key in enumerate(self.yids_ordered):
            yids_idx[key] = k + index_offset
        dxids_idx = {}
        for k, key in enumerate(sorted(self.dx.keys())):
            dxids_idx[key] = k + index_offset

        return (pids_idx, yids_idx, dxids_idx)

    def to_python(self, py_file):
        """ Write ODEs to python.

        :param py_file:
        :return:
        """
        (pids_idx, yids_idx, dxids_idx) = self._indices(index_offset=0)

        for d in [self.y, self.dx]:
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

                formula = evaluableMathML(astnode)
                if True:
                    formula = re.sub("p__", "p[", formula)
                    formula = re.sub("x__", "x[", formula)
                    formula = re.sub("y__", "y[", formula)
                    formula = re.sub("__", "]", formula)

                d[key] = formula

        content = self._render_template(template="template.py")
        with open(py_file, "w") as f:
            f.write(content)

    def to_R(self, r_file):
        """ Write ODEs to R.

        :param py_file:
        :return:
        """
        (pids_idx, yids_idx, dxids_idx) = self._indices(index_offset=1)

        for d in [self.y, self.dx]:
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

                formula = evaluableMathML(astnode)
                if True:
                    formula = re.sub("p__", "p[", formula)
                    formula = re.sub("x__", "x[", formula)
                    formula = re.sub("y__", "y[", formula)
                    formula = re.sub("__", "]", formula)

                d[key] = formula

        content = self._render_template(template="template.R")
        with open(r_file, "w") as f:
            f.write(content)


#####################################################################################

if __name__ == "__main__":

    # convert xpp to sbml
    model_id = "limax_pkpd_39"
    in_dir = './odefac_example'
    out_dir = './odefac_example/results'
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))
    py_file = os.path.join(in_dir, "{}.py".format(model_id))
    r_file = os.path.join(in_dir, "{}.R".format(model_id))

    sbml2ode = SBML2ODE.from_file(sbml_file=sbml_file)
    sbml2ode.to_python(py_file=py_file)

    sbml2ode = SBML2ODE.from_file(sbml_file=sbml_file)
    sbml2ode.to_R(r_file=r_file)
