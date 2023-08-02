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
- Piecewise functions
- Dynamical changing compartments
- Species with AssignmentRules
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import jinja2
import libsbml
import numpy as np

# template location (for language templates)
from sbmlutils import RESOURCES_DIR
from sbmlutils.console import console
from sbmlutils.converters.mathml import evaluableMathML
from sbmlutils.log import get_logger
from sbmlutils.report.units import udef_to_string


logger = get_logger(__file__)
TEMPLATE_DIR = RESOURCES_DIR / "converters"


class SBML2ODE:
    """SBML to ODE converter.

    Writes out python or R ODE files which can be solved with standard
    integrators like scipy odeint or R desolve.
    """

    def __init__(self, doc: libsbml.SBMLDocument):
        """Init with SBMLDocument.

        :param doc: SBMLDocument
        """
        self.doc: libsbml.SBMLDocument = doc

        self.units: Dict[str, Optional[str]] = {}  # model units
        self.x0: Dict = {}  # initial amounts/concentrations
        self.a_ast: Dict = {}  # initial assignments
        self.dx: Dict = {}
        self.dx_ast: Dict = {}  # state variables x (odes)
        self.x_units: Dict = {}  # state variables x units
        self.x_compartments: Dict = {}  # compartments of species
        self.x_: Set = set()  # species state variables as concentrations
        self.p: Dict = {}  # parameters p (constants)
        self.p_units: Dict = {}  # parameter units
        self.y_ast: Dict = {}  # assigned variables
        self.yids_ordered: List[str]  # yids in order of math dependencies
        self.y_units: Dict = {}  # y units

        self._create_odes()

    def info(self) -> None:
        """Print information on ODE system to console."""
        console.rule(title="ODE System", align="left", style="white")
        console.print(f"{self.units=}")
        console.print(f"{self.x0=}")
        console.print(f"{self.x_units=}")
        console.print(f"{self.a_ast=}")
        console.print(f"{self.dx=}")
        console.print(f"{self.dx_ast=}")
        console.print(f"{self.p=}")
        console.print(f"{self.p_units=}")
        console.print(f"{self.y_ast=}")
        console.print(f"{self.y_units=}")
        console.print(f"{self.yids_ordered=}")

    @classmethod
    def from_file(cls, sbml_file: Path) -> SBML2ODE:
        """Create converter from SBML file."""
        doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_file))
        return cls(doc)

    def _create_odes(self) -> None:
        """Create information of ODE system from SBMLDocument."""
        model: libsbml.Model = self.doc.getModel()

        # --------------
        # model units
        # --------------
        self.units["time"] = udef_to_string(
            model.getTimeUnits(), model=model, format="str"
        )
        self.units["substance"] = udef_to_string(
            model.getSubstanceUnits(), model=model, format="str"
        )
        self.units["length"] = udef_to_string(
            model.getLengthUnits(), model=model, format="str"
        )
        self.units["area"] = udef_to_string(
            model.getAreaUnits(), model=model, format="str"
        )
        self.units["volume"] = udef_to_string(
            model.getVolumeUnits(), model=model, format="str"
        )
        self.units["extent"] = udef_to_string(
            model.getExtentUnits(), model=model, format="str"
        )

        # --------------
        # parameters
        # --------------
        parameter: libsbml.Parameter
        for parameter in model.getListOfParameters():
            pid = parameter.getId()
            value = parameter.getValue()
            self.p[pid] = value
            self.p_units[pid] = udef_to_string(
                parameter.getUnits(), model=model, format="str"
            )

        # --------------
        # compartments
        # --------------
        # constant compartments (parameters of the system)
        compartment: libsbml.Compartment
        for compartment in model.getListOfCompartments():
            cid = compartment.getId()
            value = compartment.getSize()
            self.p[cid] = value
            self.p_units[cid] = udef_to_string(
                compartment.getUnits(), model=model, format="str"
            )

        # --------------
        # species
        # --------------
        species: libsbml.Species
        for species in model.getListOfSpecies():
            sid = species.getId()

            # FIXME: handle species with assignment rules
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
            ustr = udef_to_string(species.getUnits(), model=model, format="str")
            if not species.getHasOnlySubstanceUnits():
                compartment = model.getCompartment(species.getCompartment())
                ustr = f"{ustr}/{udef_to_string(compartment.getUnits(), model=model, format='str')}"
            self.x_units[sid] = ustr

            # compartments
            self.x_compartments[sid] = species.getCompartment()

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
                        self.x_units[variable] = udef_to_string(
                            parameter.getUnits(), model=model, format="str"
                        )
                    compartment = model.getCompartment(variable)
                    if compartment:
                        self.x0[variable] = compartment.getSize()
                        self.x_units[variable] = udef_to_string(
                            compartment.getUnits(), model=model, format="str"
                        )

            # --------------
            # assignment rules
            # --------------
            elif type_code == libsbml.SBML_ASSIGNMENT_RULE:
                as_rule: libsbml.AssignmentRule = rule
                variable = as_rule.getVariable()
                astnode = as_rule.getMath()
                self.y_ast[variable] = astnode

                if variable in self.dx_ast:
                    if variable in self.dx:
                        del self.dx[variable]
                        self.y_units[variable] = self.x_units[variable]
                        del self.x_units[variable]

                if variable in self.p:
                    del self.p[variable]
                    self.y_units[variable] = self.p_units[variable]
                    del self.p_units[variable]

        # Process the kinetic laws of reactions
        reaction: libsbml.Reaction
        for reaction in model.getListOfReactions():
            rid = reaction.getId()
            if reaction.isSetKineticLaw():
                klaw: libsbml.KineticLaw = reaction.getKineticLaw()
                astnode = klaw.getMath()
            self.y_ast[rid] = astnode
            self.y_units[rid] = f"{self.units['extent']}/{self.units['time']}"

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
        stoichiometry: float = species_ref.getStoichiometry()
        sid: str = species_ref.getSpecies()
        species: libsbml.Species = model.getSpecies(sid)
        vid = species.getCompartment()

        # ------------------
        # conversion factor
        # ------------------
        cf: str = ""
        # global conversion factor
        if model.isSetConversionFactor():
            cf = model.getConversionFactor()
        # local conversion factor takes precedence
        if species.isSetConversionFactor():
            cf = species.getConversionFactor()

        if cf != "":
            cf = f"{cf}*"

        # stoichiometry prefix
        if abs(stoichiometry - 1.0) < 1e-10:
            stoichiometry_str = ""
        else:
            stoichiometry_str = f"{stoichiometry}*"

        if not species.getBoundaryCondition():
            if sid not in self.dx_ast:
                self.dx_ast[sid] = ""

            # check if only substance units
            in_amount = species.getHasOnlySubstanceUnits()
            if in_amount:
                self.dx_ast[sid] += f" {sign}{stoichiometry_str}{cf}{rid}"
            else:
                # in concentration, dividing by the volume
                self.dx_ast[sid] += f" {sign}{stoichiometry_str}{cf}{rid}/{vid}"

        # FIXME: handle variable compartments (see SBML specification for details)

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
            # handle terminal nodes
            if astnode.getType() == libsbml.AST_NAME:
                # add to dependency graph if id is not a defined parameter or state variable
                sid = astnode.getName()
                if sid not in filtered_ids:
                    g[variable].add(sid)

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
        """Get the order of the yids from the assignment rules."""
        filtered_ids: Set[str] = set(list(self.p.keys()) + list(self.dx_ast.keys()))
        # console.print(f"{filtered_ids=}")
        # console.print(f"{self.y_ast=}")
        g: Dict[str, Set] = SBML2ODE.dependency_graph(self.y_ast, filtered_ids)
        # console.print(g)

        def create_ordered_variables(
            g: Dict[str, Set], yids: Optional[List[str]] = None
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
                # console.print(g)
                yids = create_ordered_variables(g, yids=yids)
            return yids

        # create order from dependency graph
        yids = create_ordered_variables(g)
        return yids

    def to_python(self, py_file: Path) -> None:
        """Write ODEs to python."""
        content = self._render_template(
            template_file="odefac_template.pytemp",
            index_offset=0,
            replace_symbols=True,
        )
        with open(py_file, "w") as f:
            f.write(content)

    def to_R(self, r_file: Path) -> None:
        """Write ODEs to R."""
        content = self._render_template(
            template_file="odefac_template.R",
            index_offset=1,
            replace_symbols=True,
        )
        with open(r_file, "w") as f:
            f.write(content)

    def to_markdown(self, md_file: Path) -> None:
        """Write ODEs to markdown."""
        content = self._render_template(
            template_file="odefac_template.md",
            index_offset=0,
            replace_symbols=False,
        )
        with open(md_file, "w") as f:
            f.write(content)

    def to_custom_template(self, output_file: Path, template_file: Path) -> None:
        """Write ODEs to custom template."""
        content = self._render_template(
            template_file=template_file.name,
            index_offset=0,
            replace_symbols=False,
            template_dir=template_file.parent,
        )
        with open(output_file, "w") as f:
            f.write(content)

    def _render_template(
        self,
        template_file: str = "odefac_template.pytemp",
        index_offset: int = 0,
        replace_symbols: bool = True,
        template_dir: Optional[Path] = None,
    ) -> str:
        """Render given language template.

        :return: rendered template string.
        """
        if not template_dir:
            template_dir = TEMPLATE_DIR
        # template environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            extensions=[],
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

                if not astnode:
                    # constant rate
                    d[key] = 0
                else:
                    # rate equations
                    if not isinstance(astnode, libsbml.ASTNode):
                        # already a formula
                        d[key] = astnode
                        continue

                    if replace_symbols:
                        astnode = astnode.deepCopy()

                        # replace parameters (p)
                        for key_rep, index in pids_idx.items():
                            ast_rep = libsbml.parseL3Formula(f"p___{index}___")
                            astnode.replaceArgument(key_rep, ast_rep)
                        # replace states (x)
                        for key_rep, index in dxids_idx.items():
                            ast_rep = libsbml.parseL3Formula(f"x___{index}___")
                            astnode.replaceArgument(key_rep, ast_rep)

                    formula = evaluableMathML(astnode)
                    if replace_symbols:
                        formula = re.sub("p___", "p[", formula)
                        formula = re.sub("x___", "x[", formula)
                        formula = re.sub("y___", "y[", formula)
                        formula = re.sub("___", "]", formula)

                    d[key] = formula
            return d

        # replace parameters and states with (p[*], x[*]
        y = to_formula(self.y_ast, replace_symbols=replace_symbols)
        dx = to_formula(self.dx_ast, replace_symbols=replace_symbols)

        # keep symbols (no replacements)
        y_sym = to_formula(self.y_ast, replace_symbols=replace_symbols)
        dx_sym = to_formula(self.dx_ast, replace_symbols=replace_symbols)

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
                if astnode is not None:
                    dx_flat[xid] = astnode.deepCopy()
                else:
                    logger.warning(f"No ASTNode for '{xid}'")

            # replacements y_flat
            for yid in reversed(self.yids_ordered):
                astnode = y_flat[yid]
                for key in reversed(self.yids_ordered):
                    ast_rep = y_flat[key]
                    astnode.replaceArgument(key, ast_rep)

            # replacements dx_flat
            for _x_id, astnode in dx_flat.items():
                if isinstance(astnode, libsbml.ASTNode):
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
            "units": self.units,
            "xids": sorted(self.dx_ast.keys()),
            "pids": sorted(self.p.keys()),
            "yids": self.yids_ordered,
            # 'rids': sorted(self.r.keys()),
            "x0": self.x0,
            "x_units": self.x_units,
            "x_compartments": self.x_compartments,
            "p": self.p,
            "p_units": self.p_units,
            "y": y,
            "y_units": self.y_units,
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
