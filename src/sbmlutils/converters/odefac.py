"""Convert SBML models to ODE systems for various programming languages.

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

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union

import jinja2
import libsbml

# template location (for language templates)
from sbmlutils import RESOURCES_DIR
from sbmlutils.converters.mathml import evaluableMathML


TEMPLATE_DIR = RESOURCES_DIR / "converters"


class SBML2ODE:
    """SBML to ODE converter.

    Writes out python or R ODE files which can be solved with standard
    integrators like scipy odeint or R desolve.
    """

    def __init__(self, doc: libsbml.SBMLDocument):
        """Init with SBMLDocument.

        :param doc: SBMLdocument
        """
        self.doc: libsbml.SBMLDocument = doc

        self.x0: Dict = {}  # initial amounts/concentrations
        self.a_ast: Dict = {}  # initial assignments
        self.dx: Any
        self.dx_ast: Dict = {}  # state variables x (odes)
        self.p: Dict = {}  # parameters p (constants)
        self.y_ast: Dict = {}  # assigned variables
        self.yids_ordered: List[str]  # yids in order of math dependencies

        self._create_odes()

    @classmethod
    def from_file(cls, sbml_file: Path) -> "SBML2ODE":
        """Create converter from SBML file."""
        doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_file))
        return cls(doc)

    def _create_odes(self) -> None:
        """Create information of ODE system from SBMLDocument."""
        model: libsbml.Model = self.doc.getModel()
        # --------------
        # parameters
        # --------------
        # 1. constant parameters (real parameters of the system)
        parameter: libsbml.Parameter
        for parameter in model.getListOfParameters():
            pid = parameter.getId()
            if parameter.getConstant():
                value = parameter.getValue()
            else:
                value = ""
            self.p[pid] = value

        # --------------
        # compartments
        # --------------
        # constant compartments (parameters of the system)
        compartment: libsbml.Compartment
        for compartment in model.getListOfCompartments():
            cid = compartment.getId()
            if compartment.getConstant():
                value = compartment.getSize()
            else:
                value = ""
            self.p[cid] = value

        # --------------
        # species
        # --------------
        species: libsbml.Species
        for species in model.getListOfSpecies():
            sid = species.getId()
            self.dx_ast[sid] = ""
            # initial condition
            value = None
            compartment = model.getCompartment(species.getCompartment())
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

        assignment: libsbml.InitialAssignment
        for assignment in model.getListOfInitialAssignments():
            variable = assignment.getSymbol()
            astnode = assignment.getMath()
            self.x0[variable] = astnode

        # --------------
        # rules
        # --------------
        rule: libsbml.Rule
        for rule in model.getListOfRules():
            type_code = rule.getTypeCode()
            # --------------
            # rate rules
            # --------------
            if type_code == libsbml.SBML_RATE_RULE:
                # directly converted to odes (create additional state variables)
                rate_rule: libsbml.RateRule = rule
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
                as_rule: libsbml.AssignmentRule = rule
                variable = as_rule.getVariable()
                astnode = as_rule.getMath()
                self.y_ast[variable] = astnode
                # yids[variable] = evaluableMathML(astnode)
                if variable in self.dx_ast:
                    del self.dx[variable]
                if variable in self.p:
                    del self.p[variable]

        # Process the kinetic laws of reactions
        reaction: libsbml.Reaction
        for reaction in model.getListOfReactions():
            rid = reaction.getId()
            if reaction.isSetKineticLaw():
                klaw: libsbml.KineticLaw = reaction.getKineticLaw()
                astnode = klaw.getMath()
            self.y_ast[rid] = astnode

            # create astnode for dx_ast
            reactant: libsbml.SpeciesReference
            for reactant in reaction.getListOfReactants():
                self._add_reaction_formula(
                    model, rid=rid, species_ref=reactant, sign="-"
                )
            product: libsbml.SpeciesReference
            for product in reaction.getListOfProducts():
                self._add_reaction_formula(
                    model, rid=rid, species_ref=product, sign="+"
                )

        # create astnodes for the formula strings
        for key, astnode in self.dx_ast.items():
            if not isinstance(astnode, libsbml.ASTNode):
                astnode = libsbml.parseL3FormulaWithModel(astnode, model)
                self.dx_ast[key] = astnode

        # check which math depends on other math (build tree of dependencies)
        self.yids_ordered = self._ordered_yids()

    def _add_reaction_formula(
        self,
        model: libsbml.Model,
        rid: str,
        species_ref: libsbml.SpeciesReference,
        sign: str,
    ) -> None:
        """Add part of reaction formula to ODEs for species."""
        stoichiometry = species_ref.getStoichiometry()
        sid = species_ref.getSpecies()
        species = model.getSpecies(sid)
        vid = species.getCompartment()

        # stoichiometry prefix
        if abs(stoichiometry - 1.0) < 1e-10:
            stoichiometry = ""
        else:
            stoichiometry = f"{stoichiometry}*"

        # check if only substance units
        if species.getHasOnlySubstanceUnits():
            self.dx_ast[sid] += f" {sign}{stoichiometry}{rid}"
        else:
            self.dx_ast[sid] += f" {sign}{stoichiometry}{rid}/{vid}"

    @staticmethod
    def dependency_graph(
        y: Dict[str, Union[libsbml.ASTNode, str]], filtered_ids: Set[str]
    ) -> Dict[str, Set]:
        """Create dependency graph from given dictionary.

        :param y: { variable: astnode } dictionary
        :param filtered_ids: ids which are defined elsewhere and not part of dependency tree
        :return:
        """

        def add_dependency_edges(
            g: Dict[str, Set], variable: str, astnode: libsbml.ASTNode
        ) -> None:
            """Add the dependency edges to the graph."""
            # variable --depends_on--> v2
            for k in range(astnode.getNumChildren()):
                child: libsbml.ASTNode = astnode.getChild(k)
                if child.getType() == libsbml.AST_NAME:

                    # add to dependency graph if id is not a defined parameter or state variable
                    sid = child.getName()
                    if sid not in filtered_ids:
                        g[variable].add(sid)

                # recursive adding of children
                add_dependency_edges(g, variable, child)

        # create math dependency graph
        g: Dict[str, Set] = defaultdict(set)
        for variable, astnode in y.items():
            g[variable] = set()
            add_dependency_edges(g, variable=variable, astnode=astnode)

        return g

    def _ordered_yids(self) -> List[str]:
        """Get the order of the vids from the assignment rules.

        :param model:
        :param filtered_ids
        :return:
        """
        filtered_ids: Set[str] = set(list(self.p.keys()) + list(self.dx_ast.keys()))
        g: Dict[str, Set] = SBML2ODE.dependency_graph(self.y_ast, filtered_ids)
        # pprint(g)

        def create_ordered_variables(
            g: Dict[str, Set], yids: List[str] = None
        ) -> List[str]:
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

    def to_python(self, py_file: Path) -> None:
        """Write ODEs to python."""
        content = self._render_template(
            template_file="odefac_template.pytemp", index_offset=0
        )
        with open(py_file, "w") as f:
            f.write(content)

    def to_R(self, r_file: Path) -> None:
        """Write ODEs to R."""
        content = self._render_template(
            template_file="odefac_template.R", index_offset=1
        )
        with open(r_file, "w") as f:
            f.write(content)

    def _render_template(
        self, template_file: str = "odefac_template.pytemp", index_offset: int = 0
    ) -> str:
        """Render given language template.

        :return: rendered template string.
        """
        # template environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            extensions=["jinja2.ext.autoescape"],
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(template_file)

        # indices for replacements
        (pids_idx, yids_idx, dxids_idx) = self._indices(index_offset=index_offset)

        # create formulas
        def to_formula(
            ast_dict: Dict[str, Union[libsbml.ASTNode, str]],
            replace_symbols: bool = True,
        ) -> Dict[str, Union[libsbml.ASTNode, str]]:
            """Replace all symbols in given astnode dictionary.

            :param replace_symbols:
            :param ast_dict:
            :return:
            """
            d: Dict[str, Union[libsbml.ASTNode, str]] = dict()

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
                        ast_rep = libsbml.parseL3Formula(f"p__{index}__")
                        astnode.replaceArgument(key_rep, ast_rep)
                    # replace states (x)
                    for key_rep, index in dxids_idx.items():
                        ast_rep = libsbml.parseL3Formula(f"x__{index}__")
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

        def flat_formulas() -> Tuple[Dict, Dict]:
            """Create a flat formula by full replacement.

            Uses the order of the dependencies.
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
            for _x_id, astnode in dx_flat.items():
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
            "model": self.doc.getModel(),
            "xids": sorted(self.dx_ast.keys()),
            "pids": sorted(self.p.keys()),
            "yids": self.yids_ordered,
            # 'rids': sorted(self.r.keys()),
            "x0": self.x0,
            "p": self.p,
            "y": y,
            "dx": dx,
            "y_sym": y_sym,
            "dx_sym": dx_sym,
            "y_flat": y_flat,
            "dx_flat": dx_flat,
        }
        return str(template.render(c))

    def _indices(
        self, index_offset: int = 0
    ) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
        """Get indices of pids, yids and dxids."""
        # replacement dictionaries:
        pids_idx: Dict[str, int] = {}
        for k, key in enumerate(sorted(self.p.keys())):
            pids_idx[key] = k + index_offset
        yids_idx: Dict[str, int] = {}
        for k, key in enumerate(self.yids_ordered):
            yids_idx[key] = k + index_offset
        dxids_idx: Dict[str, int] = {}
        for k, key in enumerate(sorted(self.dx_ast.keys())):
            dxids_idx[key] = k + index_offset

        return pids_idx, yids_idx, dxids_idx
