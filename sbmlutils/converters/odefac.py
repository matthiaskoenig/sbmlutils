"""
Convert SBML models to ODE systems for various programming languages.
This allows easy integration with existing workflows by rendering respective code templates.

Currently supported code generation:
- python: scipy
- R: desolve
- R: dmod

The following SBML core constructs are currently NOT supported:
- ConversionFactors
- FunctionDefinitions
- InitialAssignments
- Events
"""

# TODO: helper functions for initial conditions (initial assignments & assignment rules)
# TODO: does not handle: ConversionFactors, FunctionDefinitions, InitialAssignments, nor Events
# TODO: add parameter rules, i.e. parameters which are assignments solely based on parameters (reduces complexity of full system).

import os
import re
from collections import defaultdict
import jinja2
from pprint import pprint
import libsbml

from sbmlutils.converters.mathml import evaluableMathML


# template location (for language templates)
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


class SBML2ODE(object):
    """ SBML to ODE converter.

    Writes out python or R ODE files which can be solved with standard
    integrators like scipy odeint or R desolve.
    """
    def __init__(self, doc):
        """ Init with SBMLDocument.

        :param doc: SBMLdocument
        """
        self.doc = doc  # type: libsbml.SBMLDocument

        self.x0 = {}        # initial amounts/concentrations
        self.a_ast = {}     # initial assignments
        self.dx_ast = {}    # state variables x (odes)
        self.p = {}         # parameters p (constants)
        self.y_ast = {}     # assigned variables
        self.yids_ordered = None  # ordered y values in order of math dependencies

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
            self.dx_ast[sid] = ''
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
                self.dx_ast[variable] = astnode

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
                self.y_ast[variable] = astnode
                # yids[variable] = evaluableMathML(astnode)
                if variable in self.dx_ast:
                    del self.dx[variable]
                if variable in self.p:
                    del self.p[variable]

        # Process the kinetic laws of reactions
        for reaction in model.getListOfReactions():  # type: libsbml.Reaction
            rid = reaction.getId()
            if reaction.isSetKineticLaw():
                klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
                astnode = klaw.getMath()
            self.y_ast[rid] = astnode

            # create astnode for dx_ast
            for reactant in reaction.getListOfReactants():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=reactant, sign="-")
            for product in reaction.getListOfProducts():  # type: libsbml.SpeciesReference
                self._add_reaction_formula(model, rid=rid, species_ref=product, sign="+")

        # create astnodes for the formula strings
        for key, astnode in self.dx_ast.items():
            if not isinstance(astnode, libsbml.ASTNode):
                astnode = libsbml.parseL3FormulaWithModel(astnode, model)
                self.dx_ast[key] = astnode

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
            self.dx_ast[sid] += ' {}{}{}'.format(sign, stoichiometry, rid)
        else:
            self.dx_ast[sid] += ' {}{}{}/{}'.format(sign, stoichiometry, rid, vid)

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

        # create math dependency graph
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
        filtered_ids = set(list(self.p.keys()) + list(self.dx_ast.keys()))
        g = SBML2ODE.dependency_graph(self.y_ast, filtered_ids)
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

    def to_python(self, py_file):
        """ Write ODEs to python.

        :param py_file:
        :return:
        """
        content = self._render_template(template="template.py", index_offset=0)
        with open(py_file, "w") as f:
            f.write(content)

    def to_R(self, r_file):
        """ Write ODEs to R.

        :param py_file:
        :return:
        """
        content = self._render_template(template="template.R", index_offset=1)
        with open(r_file, "w") as f:
            f.write(content)

    def _render_template(self, template='template.py', index_offset=0):
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

        # indices for replacements
        (pids_idx, yids_idx, dxids_idx) = self._indices(index_offset=index_offset)

        # create formulas
        def to_formula(ast_dict, replace_symbols=True):
            """ Replaces all symbols in given astnode dictionary.

            :param ast_dict:
            :return:
            """
            d = dict()

            for key in ast_dict:
                astnode = ast_dict[key]
                if not isinstance(astnode, libsbml.ASTNode):
                    # already a formula
                    d[key] = astnode
                    continue

                if replace_symbols:
                    astnode = astnode.deepCopy()

                    # replace parameters (p)
                    for key_rep, index in pids_idx.items():
                        ast_rep = libsbml.parseL3Formula('p__{}__'.format(index))
                        astnode.replaceArgument(key_rep, ast_rep)
                    # replace states (x)
                    for key_rep, index in dxids_idx.items():
                        ast_rep = libsbml.parseL3Formula('x__{}__'.format(index))
                        astnode.replaceArgument(key_rep, ast_rep)

                formula = evaluableMathML(astnode)
                if replace_symbols:
                    formula = re.sub("p__", "p[", formula)
                    formula = re.sub("x__", "x[", formula)
                    formula = re.sub("y__", "y[", formula)
                    formula = re.sub("__", "]", formula)

                d[key] = formula
            return d

        # replace parameters and states with (p[*], x[*]
        y = to_formula(self.y_ast, replace_symbols=True)
        dx = to_formula(self.dx_ast, replace_symbols=True)

        # keep symbols (no replacements)
        y_sym = to_formula(self.y_ast, replace_symbols=False)
        dx_sym = to_formula(self.dx_ast, replace_symbols=False)

        def flat_formulas():
            """ Creates a flat formula by full replacement.
            Uses the order of the dependencies.

            :param ast_dict:
            :return:
            """
            # deepcopy the ast dicts for replacements
            y_flat = dict()
            for yid in self.yids_ordered:
                astnode = self.y_ast[yid]
                y_flat[yid] = astnode.deepCopy()

            # deepcopy
            dx_flat = dict()
            for xid, astnode in self.dx_ast.items():
                dx_flat[xid] = astnode.deepCopy()

            # replacements y_flat
            for yid in reversed(self.yids_ordered):
                astnode = y_flat[yid]
                for key in reversed(self.yids_ordered):
                    ast_rep = y_flat[key]
                    astnode.replaceArgument(key, ast_rep)

            # replacements dx_flat
            for x_id, astnode in dx_flat.items():
                for key in reversed(self.yids_ordered):
                    ast_rep = y_flat[key]
                    astnode.replaceArgument(key, ast_rep)

            return y_flat, dx_flat

        # flatten dx and y, i.e., full replacements of astnode for one line expressions
        y_flat, dx_flat = flat_formulas()
        y_flat = to_formula(y_flat, replace_symbols=False)
        dx_flat = to_formula(dx_flat, replace_symbols=False)

        # context
        c = {
            'model': self.doc.getModel(),
            'xids': sorted(self.dx_ast.keys()),
            'pids': sorted(self.p.keys()),
            'yids': self.yids_ordered,
            # 'rids': sorted(self.r.keys()),

            'x0': self.x0,
            'p': self.p,
            'y': y,
            'dx': dx,
            'y_sym': y_sym,
            'dx_sym': dx_sym,
            'y_flat': y_flat,
            'dx_flat': dx_flat
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
        for k, key in enumerate(sorted(self.dx_ast.keys())):
            dxids_idx[key] = k + index_offset

        return (pids_idx, yids_idx, dxids_idx)


#####################################################################################
if __name__ == "__main__":

    # convert xpp to sbml
    model_id = "limax_pkpd_v50"
    in_dir = './odefac_example'
    out_dir = './odefac_example/results'
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))
    py_file = os.path.join(in_dir, "{}.py".format(model_id))
    r_file = os.path.join(in_dir, "{}.R".format(model_id))

    # create python code
    sbml2ode = SBML2ODE.from_file(sbml_file=sbml_file)
    sbml2ode.to_python(py_file=py_file)

    # create R code
    sbml2ode = SBML2ODE.from_file(sbml_file=sbml_file)
    sbml2ode.to_R(r_file=r_file)
