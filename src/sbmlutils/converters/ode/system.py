"""Analysis of an SBML model into its system of ordinary differential equations.

`OdeSystem.from_sbml` resolves the semantics of SBML core once, as roadrunner
implements them, so that a format only prints what the system holds:

- **States** are the species which are neither constant nor boundary nor assigned
  and take part in a reaction, and every compartment, species, parameter and species
  reference with a rate rule. Every other quantity is constant or assigned; a
  quantity an event changes is constant between the events (`Quantity.constant` is
  the flag of SBML, `Quantity.role` the role in the system).
- **Species** are held as roadrunner holds them, in amount if `hasOnlySubstanceUnits`,
  else in concentration; the reaction terms of a species in concentration are
  divided by its compartment. A rate rule applies to the species as written.
- **A species in concentration in a variable compartment** (a rate rule, an
  assignment rule or an event changes the size) without a rule of its own is held as
  its amount `n_<id>` (`OdeSystem.amounts`, made unique against the ids of the
  model), the quantity SBML conserves when the size changes, and its concentration
  is the assignment `S = n_S / V` of origin `concentration`. The amount is a state
  if the species is a state, else a constant (roadrunner keeps the amount of a
  boundary or constant species when the size changes). An event which assigns
  the concentration assigns the amount `n_S = S_new * V` with the size before the
  event; an event which changes the size of the compartment of a species in
  concentration with a rate rule rescales it, `S = S * V / V_new`.
- **Conversion factors**: the conversion factor of a species, else of the model,
  multiplies the reaction terms of the species.
- **Stoichiometry** is a number, or the id of the species reference if a rule, an
  initial assignment or an event sets it; a species reference with an id is a
  quantity of the system.
- **Local parameters** are renamed to `<reaction id>_<id>`, made unique, and are
  constant parameters of the system.
- **`rateOf(x)`** is replaced by the right hand side of `x` for a state, by `0` for a
  constant, by `d(n/V)/dt` for a concentration held as amount; the rate of another
  assigned variable is unsupported.
- **Assignments** (assignment rules, concentrations and reaction rates) are ordered
  by their dependencies, ties in the order of the document; a cycle is an error.
- **Initial values** at t=0 (`OdeSystem.initial`) are every state, every constant set
  by an initial assignment or converted between amount and concentration, every
  assigned variable and the reaction rates these depend on, in one order of their
  dependencies, so that an initial assignment of a rule and a rule of an initial
  assignment are both right.
- **Events** keep their trigger as written and get its continuous root function
  (`events.trigger_root`, of the trigger with its function definitions expanded);
  an event without an id is `event<index>`, one without a trigger never fires.
- **Defaults** as roadrunner holds them: a compartment without a size has the size
  1, a stoichiometry which is not set is 1, a reaction without a kinetic law has the
  rate 0; a rule, initial assignment, event assignment or function definition
  without math is ignored (L3V2).
- **Unsupported** constructs are collected as `(construct, element id)`: algebraic
  rules, `delay`, fast reactions, distrib functions, an event assignment to a
  constant, a trigger without a continuous root function, the rate of an assigned
  variable. A comp model is flattened first, an L1 or L2 model read as L3V2.

Every math of the system is a deep copy owned by the system, so the document can be
freed. The dataclasses which hold math compare by identity (`eq=False`), a libsbml
math has no value equality.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from functools import cached_property
from pathlib import Path
from typing import Literal

import libsbml

from sbmlutils.comp.flatten import flatten_sbml_doc
from sbmlutils.converters.ode.dependencies import names, order
from sbmlutils.converters.ode.events import trigger_root
from sbmlutils.io.sbml import read_sbml
from sbmlutils.report.units import udef_to_string

__all__ = [
    "Assignment",
    "Event",
    "EventAssignment",
    "FunctionDefinition",
    "ModelInfo",
    "Ode",
    "OdeSystem",
    "Participant",
    "Quantity",
    "Reaction",
    "Symbol",
]


Kind = Literal[
    "compartment",
    "species",
    "parameter",
    "reaction",
    "species_reference",
    "function",
    "event",
]
Role = Literal["constant", "state", "assigned"]
Origin = Literal[
    "assignment_rule",
    "initial_assignment",
    "reaction",
    "initial_value",
    "concentration",
]


@dataclass(frozen=True)
class Symbol:
    """An element with an id: its name, unit, SBO term and kind."""

    sid: str
    name: str | None
    unit: str | None
    sbo: str | None
    kind: Kind


@dataclass(frozen=True)
class Quantity:
    """A compartment, species, parameter, species reference or amount of a species.

    Attributes:
        symbol: the symbol
        value: the value of the document in the representation of the quantity, `None`
            if it is not set or needs a conversion, which `OdeSystem.initial` holds
        constant: the constant flag of SBML
        role: the role in the system
        compartment: the compartment of a species or an amount
        amount: a species in amount (`hasOnlySubstanceUnits`)
        boundary: the boundary condition of a species
        conversion_factor: the conversion factor of a species, else of the model
        amount_of: the species of an amount, see `OdeSystem.amounts`
    """

    symbol: Symbol
    value: float | None
    constant: bool
    role: Role
    compartment: str | None = None
    amount: bool | None = None
    boundary: bool | None = None
    conversion_factor: str | None = None
    amount_of: str | None = None


@dataclass(frozen=True, eq=False)
class FunctionDefinition:
    """A function definition, called by the math."""

    symbol: Symbol
    arguments: tuple[str, ...]
    body: libsbml.ASTNode


@dataclass(frozen=True, eq=False)
class Assignment:
    """The value of a variable from its math: a rule, a rate, an initial value."""

    variable: str
    math: libsbml.ASTNode
    origin: Origin


@dataclass(frozen=True)
class Participant:
    """A reactant or product with its stoichiometry, a number or a species reference."""

    species: str
    stoichiometry: float | str


@dataclass(frozen=True, eq=False)
class Reaction:
    """A reaction; the rate refers to the renamed local parameters."""

    symbol: Symbol
    reactants: tuple[Participant, ...]
    products: tuple[Participant, ...]
    modifiers: tuple[str, ...]
    reversible: bool
    rate: libsbml.ASTNode
    local_parameters: tuple[str, ...]


@dataclass(frozen=True, eq=False)
class Ode:
    """The ordinary differential equation of a state.

    Attributes:
        variable: the state
        rhs: the complete right hand side
        origin: the reactions or the rate rule of the state
        reaction_terms: the sum of stoichiometry, conversion factor and rate of each
            reaction of a species, before the division by the volume
        volume: the compartment the reaction terms are divided by
        amount_of: the species whose amount the state is
    """

    variable: str
    rhs: libsbml.ASTNode
    origin: Literal["reactions", "rate_rule"]
    reaction_terms: libsbml.ASTNode | None = None
    volume: str | None = None
    amount_of: str | None = None


@dataclass(frozen=True, eq=False)
class EventAssignment:
    """The new value of a variable when an event is executed."""

    variable: str
    math: libsbml.ASTNode


@dataclass(frozen=True, eq=False)
class Event:
    """An event; `root` is the root function of the trigger, `None` if it has none."""

    symbol: Symbol
    trigger: libsbml.ASTNode
    root: libsbml.ASTNode | None
    initial_value: bool
    persistent: bool
    delay: libsbml.ASTNode | None
    priority: libsbml.ASTNode | None
    use_values_from_trigger_time: bool
    assignments: tuple[EventAssignment, ...]


@dataclass(frozen=True)
class ModelInfo:
    """The model: id, name, SBML level and version, notes as plain text, units."""

    sid: str | None
    name: str | None
    level: int
    version: int
    notes: str | None
    units: Mapping[str, str | None]
    source: str | None


@dataclass(frozen=True, eq=False)
class OdeSystem:
    """The ODE system of an SBML model, see the module for the semantics."""

    info: ModelInfo
    compartments: tuple[Quantity, ...]
    species: tuple[Quantity, ...]
    amounts: tuple[Quantity, ...]
    parameters: tuple[Quantity, ...]
    species_references: tuple[Quantity, ...]
    functions: tuple[FunctionDefinition, ...]
    assignments: tuple[Assignment, ...]
    initial: tuple[Assignment, ...]
    reactions: tuple[Reaction, ...]
    odes: tuple[Ode, ...]
    events: tuple[Event, ...]
    unsupported: tuple[tuple[str, str], ...]

    @classmethod
    def from_sbml(cls, source: Path | str | libsbml.SBMLDocument) -> OdeSystem:
        """Analyse an SBML model.

        Args:
            source: path, SBML string or document, which is not changed

        Returns:
            the ODE system

        Raises:
            ValueError: if the source cannot be read or the model is not well
                defined, e.g. its assignments depend on each other in a cycle
        """
        doc, file_name, level = _document(source)
        return _Analysis(doc, file_name, level).system()

    @property
    def states(self) -> tuple[str, ...]:
        """The ids of the states, in the order of the odes."""
        return tuple(ode.variable for ode in self.odes)

    @property
    def constants(self) -> tuple[str, ...]:
        """The ids of the constants, in the order of `quantities`."""
        return tuple(q.symbol.sid for q in self.quantities if q.role == "constant")

    @property
    def assigned(self) -> tuple[str, ...]:
        """The assigned variables in dependency order, then the reactions."""
        rules = [a.variable for a in self.assignments if a.origin != "reaction"]
        rates = [a.variable for a in self.assignments if a.origin == "reaction"]
        return (*rules, *rates)

    def quantity(self, sid: str) -> Quantity:
        """The quantity of an id, `KeyError` if it is none."""
        return self._quantities[sid]

    def symbol(self, sid: str) -> Symbol:
        """The symbol of an id, `KeyError` if it is none."""
        return self._symbols[sid]

    @property
    def quantities(self) -> tuple[Quantity, ...]:
        """The compartments, species, amounts, parameters and species references."""
        return (
            *self.compartments,
            *self.species,
            *self.amounts,
            *self.parameters,
            *self.species_references,
        )

    @cached_property
    def _quantities(self) -> dict[str, Quantity]:
        """The quantities by their id."""
        return {q.symbol.sid: q for q in self.quantities}

    @cached_property
    def _symbols(self) -> dict[str, Symbol]:
        """The symbols by their id."""
        symbols = {sid: q.symbol for sid, q in self._quantities.items()}
        for element in (*self.reactions, *self.functions, *self.events):
            symbols[element.symbol.sid] = element.symbol
        return symbols


# --- reading --------------------------------------------------------------------------


def _document(
    source: Path | str | libsbml.SBMLDocument,
) -> tuple[libsbml.SBMLDocument, str | None, tuple[int, int]]:
    """The document of a source, flattened and in L3.

    A document which is passed is copied before it is changed.

    Returns:
        the document, the name of the file it was read from and the level and
        version it was written in
    """
    if isinstance(source, libsbml.SBMLDocument):
        doc, file_name, owned = source, None, False
    else:
        doc, owned = read_sbml(source), True
        is_sbml = isinstance(source, str) and "<sbml" in source
        file_name = None if is_sbml else Path(source).name
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError("The SBML document has no model.")
    level = (doc.getLevel(), doc.getVersion())
    comp: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if comp is not None and comp.getNumSubmodels() > 0:
        doc = flatten_sbml_doc(doc if owned else doc.clone())
        owned = True
    if doc.getLevel() < 3:
        # L3 holds every construct of L1 and L2, a stoichiometry math becomes a
        # species reference with an assignment rule
        doc = doc if owned else doc.clone()
        if not doc.setLevelAndVersion(3, 2, False):
            raise ValueError(
                f"The L{level[0]}V{level[1]} document cannot be read as L3V2."
            )
    return doc, file_name, level


def _plain_text(notes: libsbml.XMLNode) -> str:
    """The text of XHTML notes, one line per line of text."""
    texts: list[str] = []
    stack = [notes]
    while stack:
        node = stack.pop()
        if node.isText():
            texts.append(node.getCharacters())
        stack.extend(node.getChild(k) for k in reversed(range(node.getNumChildren())))
    lines = (line.strip() for line in "".join(texts).splitlines())
    return "\n".join(line for line in lines if line)


# --- building math --------------------------------------------------------------------


def _node(ast_type: int, *children: libsbml.ASTNode) -> libsbml.ASTNode:
    """A node of the math with the given children, which it takes ownership of."""
    node = libsbml.ASTNode(ast_type)
    for child in children:
        node.addChild(child)
    return node


def _name(sid: str) -> libsbml.ASTNode:
    """The name of an id."""
    node = libsbml.ASTNode(libsbml.AST_NAME)
    node.setName(sid)
    return node


def _number(value: float | None) -> libsbml.ASTNode:
    """A real number, `NaN` for a value which is not set."""
    node = libsbml.ASTNode(libsbml.AST_REAL)
    node.setValue(math.nan if value is None else float(value))
    return node


def _product(factors: list[libsbml.ASTNode]) -> libsbml.ASTNode:
    """The product of the factors, the factor itself if it is the only one."""
    return factors[0] if len(factors) == 1 else _node(libsbml.AST_TIMES, *factors)


def _sum(terms: list[libsbml.ASTNode]) -> libsbml.ASTNode:
    """The sum of the terms, the term itself if it is the only one."""
    return terms[0] if len(terms) == 1 else _node(libsbml.AST_PLUS, *terms)


def _walk(ast: libsbml.ASTNode) -> Iterable[libsbml.ASTNode]:
    """Every node of the math."""
    stack = [ast]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.getChild(k) for k in range(node.getNumChildren()))


def _rename(ast: libsbml.ASTNode, renamed: Mapping[str, str]) -> None:
    """Rename the names of the math in place."""
    for node in _walk(ast):
        if node.getType() == libsbml.AST_NAME and node.getName() in renamed:
            node.setName(renamed[node.getName()])


# the types of the distrib functions, e.g. `normal(mean, sd)`
_DISTRIB = range(
    libsbml.AST_DISTRIB_FUNCTION_NORMAL, libsbml.AST_DISTRIB_FUNCTION_RAYLEIGH + 1
)


def _term(
    sign: int, stoichiometry: float | str, factor: str | None, rid: str
) -> libsbml.ASTNode:
    """The term of a reaction in the ode of a species, `-2 * f * J` for a reactant."""
    factors = []
    negated = sign < 0
    if isinstance(stoichiometry, str):
        factors.append(_name(stoichiometry))
    elif stoichiometry != 1.0:
        factors.append(_number(sign * stoichiometry))
        negated = False
    if factor:
        factors.append(_name(factor))
    factors.append(_name(rid))
    term = _product(factors)
    return _node(libsbml.AST_MINUS, term) if negated else term


def _ordered(assignments: list[Assignment]) -> tuple[Assignment, ...]:
    """The assignments in the order of their dependencies."""
    by_variable = {a.variable: a for a in assignments}
    items = [(a.variable, a.math) for a in assignments]
    return tuple(by_variable[sid] for sid in order(items))


# --- the analysis ---------------------------------------------------------------------


class _Analysis:
    """The analysis of one model, which builds its `OdeSystem`.

    The math of the document is read once into copies (`_math`), every math the
    system holds is a copy with each rateOf resolved (`_resolve`).
    """

    def __init__(
        self, doc: libsbml.SBMLDocument, file_name: str | None, level: tuple[int, int]
    ) -> None:
        """Read the rules of the model and the ids it takes.

        Args:
            doc: the document, flattened and in L3
            file_name: the name of the file the document was read from
            level: the level and version the document was written in
        """
        # the document owns the model, it is kept alive while the model is read
        self.doc = doc
        self.model: libsbml.Model = doc.getModel()
        self.file_name = file_name
        self.level = level
        self.unsupported: list[tuple[str, str]] = []
        self.taken: set[str] = {
            element.getIdAttribute() for element in self.model.getListOfAllElements()
        } | {self.model.getId()}
        self.rate_rules: dict[str, libsbml.ASTNode] = {}
        self.assignment_rules: dict[str, libsbml.ASTNode] = {}
        self.initial_assignments: dict[str, libsbml.ASTNode] = {}
        self.event_variables: set[str] = {
            assignment.getVariable()
            for event in self.model.getListOfEvents()
            for assignment in event.getListOfEventAssignments()
        }
        self._read_rules()
        # the quantities and reactions by id, the amount of each species held as
        # amount, the conversion factor of each species, the right hand side of
        # each state as read and with its rateOf resolved
        self.quantities: dict[str, Quantity] = {}
        self.reaction_ids: set[str] = set()
        self.amounts: dict[str, str] = {}
        self.factors: dict[str, str] = {}
        self.rhs: dict[str, libsbml.ASTNode] = {}
        self.resolved: dict[str, libsbml.ASTNode] = {}

    # --- helpers ------------------------------------------------------------------

    def _unique(self, base: str) -> str:
        """An id which the model does not take, `base`, else `base_1`, `base_2`, ..."""
        sid, k = base, 0
        while sid in self.taken:
            k += 1
            sid = f"{base}_{k}"
        self.taken.add(sid)
        return sid

    def _unit(self, uid: str) -> str | None:
        """The unit of a unit id, `None` if it is not set."""
        return udef_to_string(uid, model=self.model, format="str") if uid else None

    def _symbol(
        self, element: libsbml.SBase, kind: Kind, unit: str | None, sid: str = ""
    ) -> Symbol:
        """The symbol of an element, under the given id if it is renamed."""
        return Symbol(
            sid=sid or element.getId(),
            name=element.getName() if element.isSetName() else None,
            unit=unit,
            sbo=element.getSBOTermID() if element.isSetSBOTerm() else None,
            kind=kind,
        )

    def _math(self, element: str, ast: libsbml.ASTNode) -> libsbml.ASTNode:
        """A copy of the math of an element, its unsupported constructs collected."""
        for node in _walk(ast):
            if node.getType() == libsbml.AST_FUNCTION_DELAY:
                self._unsupported("delay", element)
            elif node.getType() in _DISTRIB:
                self._unsupported("distrib function", element)
        return ast.deepCopy()

    def _unsupported(self, construct: str, element: str) -> None:
        """Collect an unsupported construct once."""
        if (construct, element) not in self.unsupported:
            self.unsupported.append((construct, element))

    def _read_rules(self) -> None:
        """Read the rules and the initial assignments by their variable."""
        rule: libsbml.Rule
        for k, rule in enumerate(self.model.getListOfRules()):
            if rule.isAlgebraic():
                label = rule.getIdAttribute() or rule.getMetaId() or f"rule{k}"
                self._unsupported("algebraic rule", label)
                continue
            variable = rule.getVariable()
            if variable in self.rate_rules or variable in self.assignment_rules:
                raise ValueError(f"The variable '{variable}' has more than one rule.")
            # a rule without math is ignored (L3V2)
            if rule.isSetMath():
                rules = self.rate_rules if rule.isRate() else self.assignment_rules
                rules[variable] = self._math(variable, rule.getMath())
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            symbol = assignment.getSymbol()
            if symbol in self.assignment_rules or symbol in self.initial_assignments:
                raise ValueError(
                    f"The variable '{symbol}' has an initial assignment and an "
                    f"assignment rule or a second initial assignment."
                )
            # an initial assignment without math is ignored (L3V2)
            if assignment.isSetMath():
                math = self._math(symbol, assignment.getMath())
                self.initial_assignments[symbol] = math

    def _role(self, sid: str) -> Role:
        """The role of a quantity by its rules."""
        if sid in self.rate_rules:
            return "state"
        return "assigned" if sid in self.assignment_rules else "constant"

    def _quantity(
        self,
        element: libsbml.Compartment | libsbml.Parameter | libsbml.SpeciesReference,
        kind: Kind,
        unit: str | None,
        value: float | None,
    ) -> Quantity:
        """The quantity of a compartment, parameter or species reference."""
        return Quantity(
            symbol=self._symbol(element, kind, unit),
            value=value,
            constant=element.getConstant(),
            role=self._role(element.getId()),
        )

    # --- the system ---------------------------------------------------------------

    def system(self) -> OdeSystem:
        """Analyse the model into its ODE system."""
        functions = self._read_functions()
        reactions, local_parameters, references = self._read_reactions()
        compartments = [
            self._quantity(
                c,
                "compartment",
                self._compartment_unit(c),
                # a compartment without a size has the size 1, as roadrunner holds
                # it, e.g. a compartment of 0 dimensions
                c.getSize() if c.isSetSize() else 1.0,
            )
            for c in self.model.getListOfCompartments()
        ]
        species, amounts = self._read_species(reactions)
        parameters = [
            self._quantity(
                p,
                "parameter",
                self._unit(p.getUnits()),
                p.getValue() if p.isSetValue() else None,
            )
            for p in self.model.getListOfParameters()
        ]
        parameters.extend(local_parameters)
        quantities = [*compartments, *species, *amounts, *parameters, *references]
        self.quantities = {q.symbol.sid: q for q in quantities}
        self.reaction_ids = {r.symbol.sid for r in reactions}
        odes = self._build_odes(quantities, reactions)
        odes = [
            replace(ode, rhs=self._resolved_rate(ode.variable, ode.variable))
            for ode in odes
        ]
        reactions = [
            replace(r, rate=self._resolve(r.rate, r.symbol.sid)) for r in reactions
        ]
        return OdeSystem(
            info=self._read_info(),
            compartments=tuple(compartments),
            species=tuple(species),
            amounts=tuple(amounts),
            parameters=tuple(parameters),
            species_references=tuple(references),
            functions=tuple(functions),
            assignments=self._build_assignments(amounts, reactions),
            initial=self._build_initial(quantities, reactions),
            reactions=tuple(reactions),
            odes=tuple(odes),
            events=tuple(self._read_events()),
            unsupported=tuple(self.unsupported),
        )

    # --- the elements -------------------------------------------------------------

    def _read_info(self) -> ModelInfo:
        """The information of the model."""
        model = self.model
        units = {
            "time": model.getTimeUnits(),
            "substance": model.getSubstanceUnits(),
            "extent": model.getExtentUnits(),
            "volume": model.getVolumeUnits(),
            "area": model.getAreaUnits(),
            "length": model.getLengthUnits(),
        }
        return ModelInfo(
            sid=model.getId() if model.isSetId() else None,
            name=model.getName() if model.isSetName() else None,
            level=self.level[0],
            version=self.level[1],
            notes=_plain_text(model.getNotes()) if model.isSetNotes() else None,
            units={key: self._unit(uid) for key, uid in units.items()},
            source=self.file_name,
        )

    def _read_functions(self) -> list[FunctionDefinition]:
        """The function definitions, which stay functions called by the math."""
        functions = []
        function: libsbml.FunctionDefinition
        for function in self.model.getListOfFunctionDefinitions():
            fid = function.getId()
            body: libsbml.ASTNode | None = function.getBody()
            # a function definition without math is ignored (L3V2)
            if body is None:
                continue
            body = self._math(fid, body)
            if any(n.getType() == libsbml.AST_FUNCTION_RATE_OF for n in _walk(body)):
                self._unsupported("rateOf in a function definition", fid)
            arguments = tuple(
                function.getArgument(k).getName()
                for k in range(function.getNumArguments())
            )
            symbol = self._symbol(function, "function", None)
            functions.append(FunctionDefinition(symbol, arguments, body))
        return functions

    def _read_reactions(self) -> tuple[list[Reaction], list[Quantity], list[Quantity]]:
        """The reactions, their renamed local parameters and species references."""
        extent = self._unit(self.model.getExtentUnits())
        time = self._unit(self.model.getTimeUnits())
        unit = f"{extent}/{time}" if extent and time else None
        reactions: list[Reaction] = []
        local_parameters: list[Quantity] = []
        references: list[Quantity] = []
        reaction: libsbml.Reaction
        for reaction in self.model.getListOfReactions():
            rid = reaction.getId()
            if reaction.isSetFast() and reaction.getFast():
                self._unsupported("fast reaction", rid)
            law: libsbml.KineticLaw | None = reaction.getKineticLaw()
            renamed: dict[str, str] = {}
            parameter: libsbml.LocalParameter
            for parameter in [] if law is None else law.getListOfLocalParameters():
                sid = self._unique(f"{rid}_{parameter.getId()}")
                renamed[parameter.getId()] = sid
                symbol = self._symbol(
                    parameter, "parameter", self._unit(parameter.getUnits()), sid
                )
                value = parameter.getValue() if parameter.isSetValue() else None
                local_parameters.append(Quantity(symbol, value, True, "constant"))
            if law is not None and law.isSetMath():
                rate = self._math(rid, law.getMath())
                _rename(rate, renamed)
            else:
                # a reaction without a kinetic law has no flux, as roadrunner holds it
                rate = _number(0.0)
            sides: list[list[Participant]] = [[], []]
            for side, listed in enumerate(
                (reaction.getListOfReactants(), reaction.getListOfProducts())
            ):
                ref: libsbml.SpeciesReference
                for ref in listed:
                    sides[side].append(self._participant(ref))
                    if ref.isSetId():
                        # an unset stoichiometry is 1, as roadrunner holds it
                        value = (
                            ref.getStoichiometry() if ref.isSetStoichiometry() else 1.0
                        )
                        references.append(
                            self._quantity(ref, "species_reference", None, value)
                        )
            reactions.append(
                Reaction(
                    symbol=self._symbol(reaction, "reaction", unit),
                    reactants=tuple(sides[0]),
                    products=tuple(sides[1]),
                    modifiers=tuple(
                        m.getSpecies() for m in reaction.getListOfModifiers()
                    ),
                    reversible=reaction.getReversible(),
                    rate=rate,
                    local_parameters=tuple(renamed.values()),
                )
            )
        return reactions, local_parameters, references

    def _participant(self, ref: libsbml.SpeciesReference) -> Participant:
        """The species of a species reference and its stoichiometry."""
        sid = ref.getId()
        changed = (
            self.rate_rules,
            self.assignment_rules,
            self.initial_assignments,
            self.event_variables,
        )
        if ref.isSetId() and any(sid in ids for ids in changed):
            return Participant(ref.getSpecies(), sid)
        value = ref.getStoichiometry() if ref.isSetStoichiometry() else 1.0
        return Participant(ref.getSpecies(), value)

    def _compartment_unit(self, compartment: libsbml.Compartment) -> str | None:
        """The unit of a compartment, else the unit of the model of its dimensions."""
        if compartment.isSetUnits():
            return self._unit(compartment.getUnits())
        default = {
            3.0: self.model.getVolumeUnits,
            2.0: self.model.getAreaUnits,
            1.0: self.model.getLengthUnits,
        }.get(compartment.getSpatialDimensionsAsDouble())
        return self._unit(default()) if default else None

    def _species_unit(self, species: libsbml.Species) -> tuple[str | None, str | None]:
        """The unit of the substance of a species and the unit of the species."""
        substance = self._unit(
            species.getSubstanceUnits() or self.model.getSubstanceUnits()
        )
        if species.getHasOnlySubstanceUnits():
            return substance, substance
        compartment = self.model.getCompartment(species.getCompartment())
        volume = self._compartment_unit(compartment) if compartment else None
        if not substance or not volume:
            return substance, None
        return substance, f"{substance}/{volume if volume.isalnum() else f'({volume})'}"

    def _read_species(
        self, reactions: list[Reaction]
    ) -> tuple[list[Quantity], list[Quantity]]:
        """The species and the amounts of the species held as amount."""
        reacting = {p.species for r in reactions for p in (*r.reactants, *r.products)}
        species_list: list[Quantity] = []
        amounts: list[Quantity] = []
        species: libsbml.Species
        for species in self.model.getListOfSpecies():
            sid, cid = species.getId(), species.getCompartment()
            in_amount = species.getHasOnlySubstanceUnits()
            boundary, constant = species.getBoundaryCondition(), species.getConstant()
            substance, unit = self._species_unit(species)
            factor = species.getConversionFactor() or self.model.getConversionFactor()
            if factor:
                self.factors[sid] = factor
            value = None
            if species.isSetInitialAmount() and in_amount:
                value = species.getInitialAmount()
            elif species.isSetInitialConcentration() and not in_amount:
                value = species.getInitialConcentration()
            role: Role = (
                "state"
                if sid in reacting and not boundary and not constant
                else "constant"
            )
            variable_size = self._role(cid) != "constant" or cid in self.event_variables
            if sid in self.assignment_rules or sid in self.rate_rules:
                role = self._role(sid)
            elif not in_amount and variable_size:
                # held as amount, the concentration is assigned
                aid = self._unique(f"n_{sid}")
                self.amounts[sid] = aid
                amounts.append(
                    Quantity(
                        symbol=Symbol(
                            aid,
                            f"amount of {species.getName() or sid}",
                            substance,
                            None,
                            "species",
                        ),
                        value=(
                            species.getInitialAmount()
                            if species.isSetInitialAmount()
                            else None
                        ),
                        constant=constant,
                        role=role,
                        compartment=cid,
                        amount=True,
                        boundary=boundary,
                        conversion_factor=factor or None,
                        amount_of=sid,
                    )
                )
                role = "assigned"
            species_list.append(
                Quantity(
                    symbol=self._symbol(species, "species", unit),
                    value=value,
                    constant=constant,
                    role=role,
                    compartment=cid,
                    amount=in_amount,
                    boundary=boundary,
                    conversion_factor=factor or None,
                )
            )
        return species_list, amounts

    # --- the odes -----------------------------------------------------------------

    def _build_odes(
        self, quantities: list[Quantity], reactions: list[Reaction]
    ) -> list[Ode]:
        """The odes of the states, their right hand sides with rateOf not resolved."""
        terms: dict[str, list[libsbml.ASTNode]] = {}
        for reaction in reactions:
            rid = reaction.symbol.sid
            for sign, side in ((-1, reaction.reactants), (1, reaction.products)):
                for p in side:
                    term = _term(
                        sign, p.stoichiometry, self.factors.get(p.species), rid
                    )
                    terms.setdefault(p.species, []).append(term)
        odes = []
        for quantity in quantities:
            sid = quantity.symbol.sid
            if quantity.role != "state":
                continue
            if sid in self.rate_rules:
                ode = Ode(sid, self.rate_rules[sid], "rate_rule")
            elif quantity.amount:
                reaction_terms = _sum(terms[quantity.amount_of or sid])
                rhs = reaction_terms.deepCopy()
                ode = Ode(
                    sid, rhs, "reactions", reaction_terms, None, quantity.amount_of
                )
            else:
                reaction_terms = _sum(terms[sid])
                cid = str(quantity.compartment)
                rhs = _node(libsbml.AST_DIVIDE, reaction_terms.deepCopy(), _name(cid))
                ode = Ode(sid, rhs, "reactions", reaction_terms, cid)
            self.rhs[sid] = ode.rhs
            odes.append(ode)
        return odes

    def _resolved_rate(
        self, sid: str, element: str, stack: frozenset[str] = frozenset()
    ) -> libsbml.ASTNode:
        """A copy of the right hand side of a state with every rateOf resolved."""
        if sid not in self.resolved:
            if sid in stack:
                raise ValueError(
                    f"The rates of {sorted(stack)} depend on each other in a cycle."
                )
            self.resolved[sid] = self._resolve(self.rhs[sid], element, stack | {sid})
        return self.resolved[sid].deepCopy()

    def _rate_of(
        self, sid: str, element: str, stack: frozenset[str]
    ) -> libsbml.ASTNode | None:
        """The rate of change of an id, `None` if it is unsupported."""
        if sid in self.rhs:
            return self._resolved_rate(sid, element, stack)
        if sid in self.amounts:
            # the concentration of an amount: d(n/V)/dt = (dn/dt - S dV/dt) / V
            aid, cid = self.amounts[sid], str(self.quantities[sid].compartment)
            if cid in self.assignment_rules:
                self._unsupported("rateOf of an assigned variable", element)
                return None
            rate = self._resolved_rate(aid, element, stack) if aid in self.rhs else None
            if cid in self.rhs:
                size_rate = self._resolved_rate(cid, element, stack)
                dilution = _node(libsbml.AST_TIMES, _name(sid), size_rate)
                operands = [dilution] if rate is None else [rate, dilution]
                rate = _node(libsbml.AST_MINUS, *operands)
            if rate is None:
                return _number(0.0)
            return _node(libsbml.AST_DIVIDE, rate, _name(cid))
        quantity = self.quantities.get(sid)
        if quantity is None and sid not in self.reaction_ids:
            raise ValueError(
                f"The rateOf in '{element}' refers to the unknown id '{sid}'."
            )
        if quantity is not None and quantity.role == "constant":
            return _number(0.0)
        self._unsupported("rateOf of an assigned variable", element)
        return None

    def _resolve(
        self, ast: libsbml.ASTNode, element: str, stack: frozenset[str] = frozenset()
    ) -> libsbml.ASTNode:
        """A copy of the math with every supported rateOf replaced by the rate."""
        copy = ast.deepCopy()
        if copy.getType() == libsbml.AST_FUNCTION_RATE_OF:
            return self._replacement(copy, element, stack) or copy
        nodes = [copy]
        while nodes:
            node = nodes.pop()
            for k in range(node.getNumChildren()):
                child = node.getChild(k)
                rate = None
                if child.getType() == libsbml.AST_FUNCTION_RATE_OF:
                    rate = self._replacement(child, element, stack)
                if rate is None:
                    nodes.append(child)
                else:
                    # the node takes ownership of the rate and deletes the rateOf
                    node.replaceChild(k, rate, True)
        return copy

    def _replacement(
        self, rate_of: libsbml.ASTNode, element: str, stack: frozenset[str]
    ) -> libsbml.ASTNode | None:
        """The rate of change of the argument of a rateOf, `None` if unsupported."""
        argument = rate_of.getChild(0) if rate_of.getNumChildren() == 1 else None
        if argument is None or argument.getType() != libsbml.AST_NAME:
            self._unsupported("rateOf of an expression", element)
            return None
        return self._rate_of(argument.getName(), element, stack)

    # --- assignments and initial values -------------------------------------------

    def _build_assignments(
        self, amounts: list[Quantity], reactions: list[Reaction]
    ) -> tuple[Assignment, ...]:
        """The concentrations, assignment rules and reaction rates in dependency order."""
        assignments = [
            Assignment(str(q.amount_of), self._concentration(q), "concentration")
            for q in amounts
        ]
        assignments.extend(
            Assignment(sid, self._resolve(ast, sid), "assignment_rule")
            for sid, ast in self.assignment_rules.items()
        )
        assignments.extend(
            Assignment(r.symbol.sid, r.rate.deepCopy(), "reaction") for r in reactions
        )
        return _ordered(assignments)

    @staticmethod
    def _concentration(amount: Quantity) -> libsbml.ASTNode:
        """The concentration of the species of an amount, `n / V`."""
        cid = str(amount.compartment)
        return _node(libsbml.AST_DIVIDE, _name(amount.symbol.sid), _name(cid))

    def _initial_of(self, quantity: Quantity) -> Assignment | None:
        """The initial value of a quantity if it is computed at t=0."""
        sid, cid = quantity.symbol.sid, str(quantity.compartment)
        if sid in self.assignment_rules:
            math = self._resolve(self.assignment_rules[sid], sid)
            return Assignment(sid, math, "assignment_rule")
        if sid in self.initial_assignments:
            math = self._resolve(self.initial_assignments[sid], sid)
            return Assignment(sid, math, "initial_assignment")
        species: libsbml.Species | None = self.model.getSpecies(sid)
        if quantity.amount_of is not None:
            # the initial amount, else the amount of the initial concentration
            if quantity.value is None or quantity.amount_of in self.initial_assignments:
                math = _node(libsbml.AST_TIMES, _name(quantity.amount_of), _name(cid))
                return Assignment(sid, math, "initial_value")
        elif sid in self.amounts:
            if species is not None and species.isSetInitialAmount():
                return Assignment(
                    sid,
                    self._concentration(self.quantities[self.amounts[sid]]),
                    "concentration",
                )
            return Assignment(sid, _number(quantity.value), "initial_value")
        elif species is not None:
            # converted with the initial size of the compartment
            if species.isSetInitialAmount() and not quantity.amount:
                value = _number(species.getInitialAmount())
                math = _node(libsbml.AST_DIVIDE, value, _name(cid))
                return Assignment(sid, math, "initial_value")
            if species.isSetInitialConcentration() and quantity.amount:
                value = _number(species.getInitialConcentration())
                math = _node(libsbml.AST_TIMES, value, _name(cid))
                return Assignment(sid, math, "initial_value")
        if quantity.role == "state":
            return Assignment(sid, _number(quantity.value), "initial_value")
        return None

    def _build_initial(
        self, quantities: list[Quantity], reactions: list[Reaction]
    ) -> tuple[Assignment, ...]:
        """The initial values at t=0 in dependency order, with the rates they need."""
        initial = [a for q in quantities if (a := self._initial_of(q)) is not None]
        referenced = set().union(*(names(a.math) for a in initial))
        needed: set[str] = set()
        while True:
            # the rates the initial values need, and the rates these need
            new = [r for r in reactions if r.symbol.sid in referenced - needed]
            if not new:
                break
            for reaction in new:
                needed.add(reaction.symbol.sid)
                referenced |= names(reaction.rate)
        initial.extend(
            Assignment(r.symbol.sid, r.rate.deepCopy(), "reaction")
            for r in reactions
            if r.symbol.sid in needed
        )
        return _ordered(initial)

    # --- events -------------------------------------------------------------------

    def _read_events(self) -> list[Event]:
        """The events, their assignments to the representation of the states."""
        events = []
        event: libsbml.Event
        for k, event in enumerate(self.model.getListOfEvents()):
            eid = event.getId() if event.isSetId() else self._unique(f"event{k}")
            trigger_element: libsbml.Trigger | None = event.getTrigger()
            if trigger_element is not None and trigger_element.isSetMath():
                trigger = self._resolve(self._math(eid, trigger_element.getMath()), eid)
            else:
                # an event without a trigger never fires (L3V2)
                trigger = libsbml.ASTNode(libsbml.AST_CONSTANT_FALSE)
            # the root of a call of a function definition is the root of its body
            expanded = trigger.deepCopy()
            libsbml.SBMLTransforms.replaceFD(
                expanded, self.model.getListOfFunctionDefinitions()
            )
            try:
                root: libsbml.ASTNode | None = trigger_root(expanded)
            except NotImplementedError:
                self._unsupported("event trigger", eid)
                root = None
            events.append(
                Event(
                    symbol=self._symbol(event, "event", None, eid),
                    trigger=trigger,
                    root=root,
                    initial_value=(
                        trigger_element is None or trigger_element.getInitialValue()
                    ),
                    persistent=(
                        trigger_element is None or trigger_element.getPersistent()
                    ),
                    delay=self._optional_math(eid, event.getDelay()),
                    priority=self._optional_math(eid, event.getPriority()),
                    use_values_from_trigger_time=event.getUseValuesFromTriggerTime(),
                    assignments=self._event_assignments(eid, event),
                )
            )
        return events

    def _optional_math(
        self, element: str, sbase: libsbml.Delay | libsbml.Priority | None
    ) -> libsbml.ASTNode | None:
        """The math of a delay or a priority, `None` if it is not set."""
        if sbase is None or not sbase.isSetMath():
            return None
        return self._resolve(self._math(element, sbase.getMath()), element)

    def _event_assignments(
        self, eid: str, event: libsbml.Event
    ) -> tuple[EventAssignment, ...]:
        """The assignments of an event to the states and constants of the system.

        The concentration of a species held as amount is assigned as amount with the
        size before the event (test case 01779). A species in concentration with a
        rate rule is rescaled when the event changes the size of its compartment,
        its amount stays (test case 01506).
        """
        assigned: dict[str, libsbml.ASTNode] = {}
        assignment: libsbml.EventAssignment
        for assignment in event.getListOfEventAssignments():
            variable = assignment.getVariable()
            quantity = self.quantities.get(variable)
            if quantity is None:
                raise ValueError(
                    f"The event '{eid}' assigns '{variable}', which is no quantity."
                )
            if not assignment.isSetMath():
                continue
            if quantity.constant:
                self._unsupported("event assignment to a constant", eid)
            elif quantity.role == "assigned" and variable not in self.amounts:
                self._unsupported("event assignment to an assigned variable", eid)
            else:
                math = self._math(eid, assignment.getMath())
                assigned[variable] = self._resolve(math, eid)
        result = []
        for variable, math in assigned.items():
            if variable in self.amounts:
                cid = _name(str(self.quantities[variable].compartment))
                math = _node(libsbml.AST_TIMES, math.deepCopy(), cid)
                variable = self.amounts[variable]
            result.append(EventAssignment(variable, math))
        for quantity in self.quantities.values():
            sid, cid = quantity.symbol.sid, str(quantity.compartment)
            rescaled = (
                quantity.symbol.kind == "species"
                and sid in self.rate_rules
                and not quantity.amount
                and cid in assigned
            )
            if rescaled:
                value = assigned[sid].deepCopy() if sid in assigned else _name(sid)
                product = _node(libsbml.AST_TIMES, value, _name(cid))
                math = _node(libsbml.AST_DIVIDE, product, assigned[cid].deepCopy())
                result = [a for a in result if a.variable != sid]
                result.append(EventAssignment(sid, math))
        return tuple(result)
