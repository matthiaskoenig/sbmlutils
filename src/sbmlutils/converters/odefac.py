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
- Piecewise functions (supported in python)
- Dynamical changing compartments
- Species with AssignmentRules

The math of the python code is translated on the libsbml AST (`python_math`), so
that every construct of the L3 infix syntax becomes the corresponding python.

Every name, unit and other free text is written through the `single_line` filter,
which removes all line breaks, so that the text of a model can never leave the
comment it is written into and become code. The ids written into code are checked
to be SIds (`ValueError` otherwise), which libsbml does not guarantee: it reads a
document with an invalid id and only reports an error.
"""

from __future__ import annotations

import keyword
import logging
import math
import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

import jinja2
import libsbml

# template location (for language templates)
from sbmlutils import RESOURCES_DIR
from sbmlutils.converters.mathml import evaluableMathML
from sbmlutils.io import read_sbml
from sbmlutils.report.units import udef_to_string

logger = logging.getLogger(__name__)
TEMPLATE_DIR = RESOURCES_DIR / "converters"


def single_line(value: object) -> str:
    r"""Make text safe inside a single-line comment of every target language.

    Every line break (`\n`, `\r`, the unicode line and paragraph separators) and
    every other control character is replaced by a space, so that the text ends
    where the line ends.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the text on a single line
    """
    return "".join(
        " " if unicodedata.category(char) in {"Cc", "Zl", "Zp"} else char
        for char in str(value)
    )


_TEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "%": r"\%",
    "~": r"\textasciitilde{}",
}


def tex_text(value: object) -> str:
    r"""Make text safe inside a latex `\text{}` on a single line.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the text on a single line with the latex special characters escaped
    """
    return "".join(_TEX_SPECIAL.get(char, char) for char in single_line(value))


def check_sid(sid: str) -> str:
    """Check that an id which is written into code is an SId.

    libsbml reads a document whose ids are not SIds and only reports an error, so
    an id can hold any text, e.g. a line of code.

    Args:
        sid: id to check

    Returns:
        the id

    Raises:
        ValueError: if the id is not an SId
    """
    if not libsbml.SyntaxChecker.isValidSBMLSId(sid):
        raise ValueError(f"The id {sid!r} is not an SId and cannot be written as code.")
    return sid


def _check_math_sids(astnode: libsbml.ASTNode) -> None:
    """Check that every identifier in the math is an SId.

    Raises:
        ValueError: if an identifier is not an SId
    """
    if astnode.getType() in {libsbml.AST_NAME, libsbml.AST_FUNCTION}:
        check_sid(astnode.getName())
    for k in range(astnode.getNumChildren()):
        _check_math_sids(astnode.getChild(k))


# functions which are the same numpy function in python
_PYTHON_FUNCTIONS: dict[int, str] = {
    libsbml.AST_FUNCTION_ABS: "np.abs",
    libsbml.AST_FUNCTION_ARCCOS: "np.arccos",
    libsbml.AST_FUNCTION_ARCCOSH: "np.arccosh",
    libsbml.AST_FUNCTION_ARCSIN: "np.arcsin",
    libsbml.AST_FUNCTION_ARCSINH: "np.arcsinh",
    libsbml.AST_FUNCTION_ARCTAN: "np.arctan",
    libsbml.AST_FUNCTION_ARCTANH: "np.arctanh",
    libsbml.AST_FUNCTION_CEILING: "np.ceil",
    libsbml.AST_FUNCTION_COS: "np.cos",
    libsbml.AST_FUNCTION_COSH: "np.cosh",
    libsbml.AST_FUNCTION_EXP: "np.exp",
    libsbml.AST_FUNCTION_FLOOR: "np.floor",
    libsbml.AST_FUNCTION_LN: "np.log",
    libsbml.AST_FUNCTION_SIN: "np.sin",
    libsbml.AST_FUNCTION_SINH: "np.sinh",
    libsbml.AST_FUNCTION_TAN: "np.tan",
    libsbml.AST_FUNCTION_TANH: "np.tanh",
}

# functions which are the reciprocal of a numpy function, sec(x) = 1/cos(x)
_PYTHON_RECIPROCALS: dict[int, str] = {
    libsbml.AST_FUNCTION_SEC: "np.cos",
    libsbml.AST_FUNCTION_CSC: "np.sin",
    libsbml.AST_FUNCTION_COT: "np.tan",
    libsbml.AST_FUNCTION_SECH: "np.cosh",
    libsbml.AST_FUNCTION_CSCH: "np.sinh",
    libsbml.AST_FUNCTION_COTH: "np.tanh",
}

# functions which are a numpy function of the reciprocal, arcsec(x) = arccos(1/x)
_PYTHON_OF_RECIPROCALS: dict[int, str] = {
    libsbml.AST_FUNCTION_ARCSEC: "np.arccos",
    libsbml.AST_FUNCTION_ARCCSC: "np.arcsin",
    libsbml.AST_FUNCTION_ARCCOT: "np.arctan",
    libsbml.AST_FUNCTION_ARCSECH: "np.arccosh",
    libsbml.AST_FUNCTION_ARCCSCH: "np.arcsinh",
    libsbml.AST_FUNCTION_ARCCOTH: "np.arctanh",
}

_PYTHON_RELATIONALS: dict[int, str] = {
    libsbml.AST_RELATIONAL_EQ: "==",
    libsbml.AST_RELATIONAL_NEQ: "!=",
    libsbml.AST_RELATIONAL_GT: ">",
    libsbml.AST_RELATIONAL_GEQ: ">=",
    libsbml.AST_RELATIONAL_LT: "<",
    libsbml.AST_RELATIONAL_LEQ: "<=",
}


def _python_number(value: float) -> str:
    """Python literal of a float, `inf` and `nan` included."""
    if math.isnan(value):
        return "np.nan"
    if math.isinf(value):
        return "np.inf" if value > 0 else "-np.inf"
    return repr(float(value))


def python_value(value: object) -> str:
    """Python literal of an initial value or a parameter value.

    Args:
        value: a number, `None` for an unset value or the math of an initial
            assignment, which the python code does not support

    Returns:
        the python literal, `np.nan` for a value which is not a number
    """
    if isinstance(value, bool | int | float):
        return _python_number(float(value))
    return "np.nan"


def python_math(astnode: libsbml.ASTNode, symbols: Mapping[str, str]) -> str:
    """Translate math into a python expression.

    The expression uses `numpy` as `np` and `math`, the time is `t`. Every
    identifier is written as its entry in `symbols`, an identifier without an
    entry is never written.

    Args:
        astnode: the math
        symbols: python expression of each identifier, e.g. `{"k1": "p[0]"}`

    Returns:
        the python expression

    Raises:
        NotImplementedError: for an identifier without an entry in `symbols`
            (e.g. a local parameter) and for a construct the python code does
            not support (function definitions, `delay`, `rateOf`, csymbol
            functions)
    """
    return _python_math(astnode, symbols)[0]


# precedence of the python expressions, an operand is put in parentheses if its
# precedence is lower than its place requires
_CONDITIONAL = 1
_NOT = 3
_COMPARISON = 4
_XOR = 5
_SUM = 6
_PRODUCT = 7
_UNARY = 8
_POWER = 9
_ATOM = 10


def _python_math(
    astnode: libsbml.ASTNode, symbols: Mapping[str, str], condition: bool = False
) -> tuple[str, int]:
    """Translate math into a python expression.

    Args:
        astnode: the math
        symbols: python expression of each identifier
        condition: the expression is used as a condition, not as a number

    Returns:
        the python expression and its precedence
    """
    ast_type = astnode.getType()
    children: list[libsbml.ASTNode] = [
        astnode.getChild(k) for k in range(astnode.getNumChildren())
    ]

    def operand(
        child: libsbml.ASTNode, precedence: int, condition: bool = False
    ) -> str:
        """Python expression of a child, in parentheses below the precedence."""
        code, child_precedence = _python_math(child, symbols, condition)
        return code if child_precedence >= precedence else f"({code})"

    def argument(child: libsbml.ASTNode, condition: bool = False) -> str:
        """Python expression of a child as the argument of a call."""
        return _python_math(child, symbols, condition)[0]

    def operation(op: str, precedence: int) -> tuple[str, int]:
        """Left associative operation on all children."""
        first, *others = children
        code = op.join(
            [operand(first, precedence)]
            + [operand(child, precedence + 1) for child in others]
        )
        return code, precedence

    # numbers and constants
    if ast_type == libsbml.AST_INTEGER:
        integer: int = astnode.getInteger()
        return str(integer), _ATOM if integer >= 0 else _UNARY
    if ast_type in {libsbml.AST_REAL, libsbml.AST_REAL_E, libsbml.AST_NAME_AVOGADRO}:
        real: float = astnode.getReal()
        return _python_number(real), _UNARY if real < 0 else _ATOM
    if ast_type == libsbml.AST_RATIONAL:
        return f"{astnode.getNumerator()} / {astnode.getDenominator()}", _PRODUCT
    constants = {
        libsbml.AST_CONSTANT_E: "np.e",
        libsbml.AST_CONSTANT_PI: "np.pi",
        libsbml.AST_CONSTANT_TRUE: "True",
        libsbml.AST_CONSTANT_FALSE: "False",
        libsbml.AST_NAME_TIME: "t",
    }
    if ast_type in constants:
        return constants[ast_type], _ATOM

    # identifiers
    if ast_type == libsbml.AST_NAME:
        sid = astnode.getName()
        if sid not in symbols:
            raise NotImplementedError(
                f"The identifier {sid!r} is no parameter, compartment, species or "
                f"assigned variable of the model (e.g. a local parameter) and is "
                f"not supported by the python code."
            )
        return symbols[sid], _ATOM

    # arithmetic
    if ast_type in {libsbml.AST_PLUS, libsbml.AST_TIMES}:
        if not children:
            return ("0" if ast_type == libsbml.AST_PLUS else "1"), _ATOM
        if len(children) == 1:
            return _python_math(children[0], symbols)
        if ast_type == libsbml.AST_PLUS:
            return operation(" + ", _SUM)
        return operation(" * ", _PRODUCT)
    if ast_type == libsbml.AST_MINUS:
        if len(children) == 1:
            return f"-{operand(children[0], _POWER)}", _UNARY
        return operation(" - ", _SUM)
    if ast_type == libsbml.AST_DIVIDE:
        return operation(" / ", _PRODUCT)
    if ast_type in {libsbml.AST_POWER, libsbml.AST_FUNCTION_POWER}:
        # right associative and binding tighter than a unary minus on its left
        base, exponent = children
        return f"{operand(base, _ATOM)} ** {operand(exponent, _UNARY)}", _POWER

    # functions
    if ast_type in _PYTHON_FUNCTIONS:
        return f"{_PYTHON_FUNCTIONS[ast_type]}({argument(children[0])})", _ATOM
    if ast_type in _PYTHON_RECIPROCALS:
        f = _PYTHON_RECIPROCALS[ast_type]
        return f"1.0 / {f}({argument(children[0])})", _PRODUCT
    if ast_type in _PYTHON_OF_RECIPROCALS:
        f = _PYTHON_OF_RECIPROCALS[ast_type]
        return f"{f}(1.0 / {operand(children[0], _PRODUCT + 1)})", _ATOM
    if ast_type == libsbml.AST_FUNCTION_LOG:
        # the base is the first child, 10 if it is missing
        if len(children) == 1:
            return f"np.log10({argument(children[0])})", _ATOM
        base, value = children
        return f"np.log({argument(value)}) / np.log({argument(base)})", _PRODUCT
    if ast_type == libsbml.AST_FUNCTION_ROOT:
        # the degree is the first child, 2 if it is missing
        if len(children) == 1:
            return f"np.sqrt({argument(children[0])})", _ATOM
        degree, value = children
        return (
            f"{operand(value, _ATOM)} ** (1.0 / {operand(degree, _PRODUCT + 1)})",
            _POWER,
        )
    if ast_type == libsbml.AST_FUNCTION_FACTORIAL:
        return f"math.gamma({argument(children[0])} + 1)", _ATOM
    if ast_type == libsbml.AST_FUNCTION_REM:
        # the remainder has the sign of the dividend
        return f"np.fmod({argument(children[0])}, {argument(children[1])})", _ATOM
    if ast_type == libsbml.AST_FUNCTION_QUOTIENT:
        # the integer part of the quotient, truncated towards zero
        dividend, divisor = children
        quotient = f"{operand(dividend, _PRODUCT)} / {operand(divisor, _PRODUCT + 1)}"
        return f"np.trunc({quotient})", _ATOM
    if ast_type in {libsbml.AST_FUNCTION_MAX, libsbml.AST_FUNCTION_MIN}:
        name = "max" if ast_type == libsbml.AST_FUNCTION_MAX else "min"
        return f"{name}({', '.join(argument(c) for c in children)})", _ATOM

    # logic and relations, a python bool: a numpy bool is no number, the sum of
    # two numpy bools is their logical or
    if ast_type in {libsbml.AST_LOGICAL_AND, libsbml.AST_LOGICAL_OR}:
        if not children:
            return str(ast_type == libsbml.AST_LOGICAL_AND), _ATOM
        op = " and " if ast_type == libsbml.AST_LOGICAL_AND else " or "
        code = op.join(operand(c, _NOT, condition=True) for c in children)
        return f"bool({code})", _ATOM
    if ast_type == libsbml.AST_LOGICAL_NOT:
        return f"not {operand(children[0], _NOT, condition=True)}", _NOT
    if ast_type == libsbml.AST_LOGICAL_XOR:
        if not children:
            return "False", _ATOM
        code = " ^ ".join(f"bool({argument(c, condition=True)})" for c in children)
        return code, _XOR
    if ast_type == libsbml.AST_LOGICAL_IMPLIES:
        premise, conclusion = children
        code = (
            f"not {operand(premise, _NOT, condition=True)}"
            f" or {operand(conclusion, _NOT, condition=True)}"
        )
        return f"bool({code})", _ATOM
    if ast_type in _PYTHON_RELATIONALS:
        # python chains relations as MathML does: a < b < c is a < b and b < c
        op = f" {_PYTHON_RELATIONALS[ast_type]} "
        code = op.join(operand(c, _COMPARISON + 1) for c in children)
        return (code, _COMPARISON) if condition else (f"bool({code})", _ATOM)

    # piecewise(value1, condition1, value2, condition2, ..., otherwise), as a
    # conditional expression, which evaluates only the branch which applies
    if ast_type == libsbml.AST_FUNCTION_PIECEWISE:
        # the otherwise, undefined (nan) if it is missing
        code = operand(children[-1], _CONDITIONAL) if len(children) % 2 else "np.nan"
        for k in range(len(children) // 2 * 2 - 2, -1, -2):
            value = operand(children[k], _CONDITIONAL + 1)
            test = operand(children[k + 1], _CONDITIONAL + 1, condition=True)
            code = f"{value} if {test} else {code}"
        return code, _CONDITIONAL

    formula = libsbml.formulaToL3String(astnode)
    raise NotImplementedError(
        f"The math '{formula}' is not supported by the python code "
        f"(libsbml ASTNode type {ast_type})."
    )


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

        self.names: dict[str, str] = {}
        self.model_units: dict[str, str | None] = {}
        self.units: dict[str, str | None] = {}

        # --- fixed model entities ---
        # p: constants (parameters, compartments, species)
        # x: initial values (state variables)

        # assignments
        # p=: assignment rules (species, parameters, compartments)
        # x0=: initial values

        # kinetics dx/dt
        # x: state variables (species, parameters, compartments)

        self.x0: dict = {}  # initial amounts/concentrations
        self.dx: dict = {}
        self.dx_ast: dict = {}  # state variables x (odes)

        self.x_compartments: dict = {}  # compartments of species
        self.x_: set = set()  # species state variables as concentrations

        self.p: dict = {}  # parameters p (constants)

        self.y_ast: dict = {}  # assigned variables
        self.yids_ordered: list[str]  # yids in order of math dependencies

        # create name dictionary
        sbase: libsbml.SBase
        for sbase in doc.getListOfAllElements():
            sid = sbase.getId()
            if sid and sbase.isSetName():
                self.names[sid] = sbase.getName()

        # create odes
        self._create_odes()

    def info(self) -> None:
        """Log the information on the ODE system at debug level."""
        logger.debug(
            "ODE system: model_units=%s, x0=%s, dx=%s, dx_ast=%s, p=%s, y_ast=%s, "
            "yids_ordered=%s",
            self.model_units,
            self.x0,
            self.dx,
            self.dx_ast,
            self.p,
            self.y_ast,
            self.yids_ordered,
        )

    @classmethod
    def from_file(cls, sbml_file: Path) -> SBML2ODE:
        """Create converter from SBML file.

        Args:
            sbml_file: path of the SBML file

        Returns:
            the converter of the model of the file

        Raises:
            ValueError: if the file cannot be read, see `read_sbml`
        """
        doc: libsbml.SBMLDocument = read_sbml(sbml_file)
        return cls(doc)

    def _create_odes(self) -> None:
        """Create information of ODE system from SBMLDocument."""
        model: libsbml.Model = self.doc.getModel()

        # --------------
        # model units
        # --------------
        self.model_units["time"] = udef_to_string(
            model.getTimeUnits(), model=model, format="str"
        )
        self.model_units["substance"] = udef_to_string(
            model.getSubstanceUnits(), model=model, format="str"
        )
        self.model_units["length"] = udef_to_string(
            model.getLengthUnits(), model=model, format="str"
        )
        self.model_units["area"] = udef_to_string(
            model.getAreaUnits(), model=model, format="str"
        )
        self.model_units["volume"] = udef_to_string(
            model.getVolumeUnits(), model=model, format="str"
        )
        self.model_units["extent"] = udef_to_string(
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
            self.units[pid] = udef_to_string(
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
            self.units[cid] = udef_to_string(
                compartment.getUnits(), model=model, format="str"
            )

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
            ustr = udef_to_string(species.getUnits(), model=model, format="str")
            if not species.getHasOnlySubstanceUnits():
                compartment = model.getCompartment(species.getCompartment())
                ustr = f"{ustr}/{udef_to_string(compartment.getUnits(), model=model, format='str')}"
            self.units[sid] = ustr

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
                        self.units[variable] = udef_to_string(
                            parameter.getUnits(), model=model, format="str"
                        )
                    compartment = model.getCompartment(variable)
                    if compartment:
                        self.x0[variable] = compartment.getSize()
                        self.units[variable] = udef_to_string(
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

                # assignment rule variables are no odes, move to y
                if variable in self.x0:
                    del self.x_compartments[variable]
                    del self.x0[variable]
                    del self.dx_ast[variable]

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
            self.units[rid] = f"{self.model_units['extent']}/{self.model_units['time']}"

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

        # cleanup species with no reactions
        # remove_variables = {k for k, astnode in self.dx_ast.items() if not astnode}
        # for variable in remove_variables:
        #     del self.x_compartments[variable]
        #     del self.x0[variable]
        #     del self.dx_ast[variable]

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
        y: dict[str, libsbml.ASTNode | str], filtered_ids: set[str]
    ) -> dict[str, set]:
        """Create dependency graph from given dictionary.

        :param y: { variable: astnode } dictionary
        :param filtered_ids: ids which are defined elsewhere and not part of dependency tree
        :return:
        """

        def add_dependency_edges(
            g: dict[str, set], variable: str, astnode: libsbml.ASTNode | str
        ) -> None:
            """Add the dependency edges to the graph."""
            if isinstance(astnode, str):
                # already a formula, it carries no dependency information
                return

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
        g: dict[str, set] = defaultdict(set)
        for variable, astnode in y.items():
            g[variable] = set()
            add_dependency_edges(g, variable=variable, astnode=astnode)

        return g

    def _ordered_yids(self) -> list[str]:
        """Get the order of the yids from the assignment rules."""
        filtered_ids: set[str] = set(list(self.p.keys()) + list(self.dx_ast.keys()))
        g: dict[str, set] = SBML2ODE.dependency_graph(self.y_ast, filtered_ids)
        # only the assigned variables are ordered; an id which is none of them
        # (e.g. a local parameter) can never be removed from the graph
        yids_all = set(self.y_ast)
        g = {yid: deps & yids_all for yid, deps in g.items()}

        def create_ordered_variables(
            g: dict[str, set], yids: list[str] | None = None
        ) -> list[str]:
            if yids is None:
                yids = []

            yids_remove = []
            for yid in sorted(g.keys()):
                yid_deps = g[yid]

                # add yids with no dependencies
                if len(yid_deps) == 0:
                    yids_remove.append(yid)

            if not yids_remove:
                raise ValueError(
                    f"The assignments of {sorted(g)} depend on each other in a cycle."
                )

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
        return create_ordered_variables(g)

    def to_python(self, py_file: Path | None = None) -> str:
        """Write ODEs to python."""
        for sid, value in self.x0.items():
            if isinstance(value, libsbml.ASTNode):
                logger.warning(
                    "The initial assignment of '%s' is not supported by the python "
                    "code and is ignored.",
                    sid,
                )
        content = self._render_template(
            template_file="odefac_template.pytemp",
            index_offset=0,
            replace_symbols=True,
            python=True,
        )
        if py_file:
            with open(py_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def to_tex(self, tex_file: Path | None = None) -> str:
        """Write ODEs to tex/latex."""
        content = self._render_template(
            template_file="odefac_template.tex",
            index_offset=0,
            replace_symbols=False,
            code=False,
        )
        if tex_file:
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def to_R(self, r_file: Path | None = None) -> str:
        """Write ODEs to R."""
        content = self._render_template(
            template_file="odefac_template.R",
            index_offset=1,
            replace_symbols=True,
        )
        if r_file:
            with open(r_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def to_julia(self, jl_file: Path | None = None) -> str:
        """Write ODEs to julia.

        Generated files can be used as an input for DifferentialEquations.jl
        https://docs.sciml.ai/DiffEqDocs/stable/

        """
        content = self._render_template(
            template_file="odefac_template.jl",
            index_offset=1,
            replace_symbols=True,
        )
        if jl_file:
            with open(jl_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def to_markdown(self, md_file: Path | None = None) -> str:
        """Write ODEs to markdown."""
        content = self._render_template(
            template_file="odefac_template.md",
            index_offset=0,
            replace_symbols=False,
            code=False,
            check_math=False,
        )
        if md_file:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def to_custom_template(
        self, template_file: Path, output_file: Path | None = None
    ) -> str:
        """Write ODEs to custom template."""
        content = self._render_template(
            template_file=template_file.name,
            index_offset=0,
            replace_symbols=False,
            template_dir=template_file.parent,
        )
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def _render_template(
        self,
        template_file: str = "odefac_template.pytemp",
        index_offset: int = 0,
        replace_symbols: bool = True,
        template_dir: Path | None = None,
        python: bool = False,
        code: bool = True,
        check_math: bool = True,
    ) -> str:
        """Render given language template.

        The templates write every name, unit and other free text through the
        `single_line` filter (`tex_text` in latex), the python template writes
        values through `python_value`.

        Args:
            template_file: name of the template in the template directory
            index_offset: index of the first element of the vectors, 0 or 1
            replace_symbols: write the parameters and the states as elements of
                the vectors `p` and `x`
            template_dir: directory of the template, the packaged templates if
                not given
            python: translate the math into python (`python_math`)
            code: the output is code, so every id written into it must be an SId
            check_math: every identifier in the math must be an SId, the math
                is written unescaped (latex)

        Returns:
            the rendered template

        Raises:
            ValueError: if the output is code and an id in it is not an SId, or
                an identifier in the math is not an SId and the math is checked
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
        env.filters["single_line"] = single_line
        env.filters["tex_text"] = tex_text
        env.filters["python_value"] = python_value
        template = env.get_template(template_file)

        if code:
            self._check_code_sids()

        # indices for replacements
        (pids_idx, _yids_idx, dxids_idx) = self._indices(index_offset=index_offset)

        # names of the assigned variables in python and the python of all ids
        py_names = self._python_names()
        py_symbols: dict[str, str] = {
            **{pid: f"p[{index}]" for pid, index in pids_idx.items()},
            **{xid: f"x[{index}]" for xid, index in dxids_idx.items()},
            **py_names,
        }

        # create formulas
        def to_formula(
            ast_dict: dict[str, libsbml.ASTNode | str],
            replace_symbols: bool = True,
        ) -> dict[str, libsbml.ASTNode | str | float]:
            """Replace all symbols in given astnode dictionary.

            :param replace_symbols:
            :param ast_dict:
            :return:
            """
            d: dict[str, libsbml.ASTNode | str | float] = {}

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

                    if check_math:
                        _check_math_sids(astnode)

                    if python and replace_symbols:
                        d[key] = python_math(astnode, py_symbols)
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
        y_sym = to_formula(self.y_ast, replace_symbols=False)
        dx_sym = to_formula(self.dx_ast, replace_symbols=False)

        def flat_formulas() -> tuple[dict, dict]:
            """Create a flat formula by full replacement.

            Uses the order of the dependencies.
            """
            # deepcopy the ast dicts for replacements
            y_flat = {}
            for yid in self.yids_ordered:
                astnode = self.y_ast[yid]
                y_flat[yid] = astnode.deepCopy()

            # deepcopy
            dx_flat = {}
            for xid, astnode in self.dx_ast.items():
                if astnode is not None:
                    dx_flat[xid] = astnode.deepCopy()
                else:
                    logger.warning("No ASTNode for '%s'", xid)

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
            "model_units": self.model_units,
            "units": self.units,
            "names": self.names,
            "xids": sorted(self.dx_ast.keys()),
            "pids": sorted(self.p.keys()),
            "yids": self.yids_ordered,
            "py_names": py_names,
            # 'rids': sorted(self.r.keys()),
            "x0": self.x0,
            "x_compartments": self.x_compartments,
            "p": self.p,
            "y": y,
            "dx": dx,
            "y_sym": y_sym,
            "dx_sym": dx_sym,
            "y_flat": y_flat,
            "dx_flat": dx_flat,
        }
        return str(template.render(c))

    def _check_code_sids(self) -> None:
        """Check that every id which is written into code is an SId.

        Raises:
            ValueError: if an id is not an SId
        """
        model: libsbml.Model = self.doc.getModel()
        if model.isSetId():
            check_sid(model.getId())
        for sid in [*self.dx_ast, *self.p, *self.y_ast, *self.x_compartments.values()]:
            check_sid(sid)

    # names the python code uses besides the assigned variables
    _PYTHON_RESERVED = frozenset(
        [*keyword.kwlist, "x", "t", "p", "y", "np", "pd", "math", "bool", "max", "min"]
    )

    def _python_names(self) -> dict[str, str]:
        """Python names of the assigned variables, which are local variables.

        An id which is a python keyword or a name the code uses itself gets
        underscores appended until it is unique, e.g. `lambda_` or `p_`.

        Returns:
            python name of each assigned variable
        """
        taken = set(self.y_ast) | self._PYTHON_RESERVED
        names: dict[str, str] = {}
        for yid in self.yids_ordered:
            name = yid
            if yid in self._PYTHON_RESERVED:
                while name in taken:
                    name = f"{name}_"
                taken.add(name)
            names[yid] = name
        return names

    def _indices(
        self, index_offset: int = 0
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Get indices of pids, yids and dxids."""
        # replacement dictionaries:
        pids_idx: dict[str, int] = {}
        for k, key in enumerate(sorted(self.p.keys())):
            pids_idx[key] = k + index_offset
        yids_idx: dict[str, int] = {}
        for k, key in enumerate(self.yids_ordered):
            yids_idx[key] = k + index_offset
        dxids_idx: dict[str, int] = {}
        for k, key in enumerate(sorted(self.dx_ast.keys())):
            dxids_idx[key] = k + index_offset

        return pids_idx, yids_idx, dxids_idx
