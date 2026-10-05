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
  the concentration assigns the amount `n_S = S_new * V` with the size at the
  execution before the event; an event which changes the size of the compartment
  of a species in concentration with a rate rule rescales it, `S = S * V / V_new`
  (`EventAssignment` keeps the value of SBML and this conversion apart, they are
  evaluated at different times). The state of an amount takes the place of its
  species in the order of the states.
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
  1 (its `Quantity.value`), a stoichiometry which is not set is 1, a reaction
  without a kinetic law has the rate 0; a rule, initial assignment, event
  assignment or function definition without math is ignored (L3V2).
- **Constants in `OdeSystem.initial`** are only those set by an initial assignment
  and those whose value is a conversion with another quantity (a species in
  concentration with an initial amount, divided by its compartment, and the
  reverse); every other constant has its value in `Quantity.value`, so that a
  value passed for it is kept.
- **Unsupported** constructs are collected as `(construct, element id)`: algebraic
  rules, `delay`, fast reactions, distrib functions, an event assignment to a
  constant, a trigger without a continuous root function, the rate of an assigned
  variable. A comp model is flattened first, an L1 or L2 model read as L3V2.

Every math of the system is a deep copy owned by the system, so the document can be
freed; a sum is written with the signs of its terms (`astutil.signed_sum`). The
analysis itself is `sbmlutils.converters.ode.analysis`. The dataclasses which hold math compare by identity (`eq=False`), a libsbml
math has no value equality.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Literal

import libsbml

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
        value: the value of the document in the representation of the quantity, the
            default 1 of a compartment without a size; `None` if it is not set or
            needs a conversion, which `OdeSystem.initial` then holds
        constant: the constant flag of SBML
        role: the role in the system
        compartment: the compartment of a species or an amount, `None` for a
            species in amount without a compartment, which L3 requires and
            libsbml reads
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
    """The new value of a variable when an event is executed.

    The new value is `value * scale / new(divisor)`, each part optional:

    - `value` is `math`, evaluated as SBML says: at the trigger time if the event
      uses the values from the trigger time, else at the execution; `1` if `math` is
      `None`;
    - `scale` is evaluated at the execution of the event, with the values before any
      assignment of the event is applied, i.e. after the events executed before it;
    - `new(divisor)` is the new value of the assignment of the same event to the id
      `divisor`, a compartment which is assigned without scale.

    Attributes:
        variable: the variable, the amount of a species held as amount
        math: the value SBML assigns, `None` for a species whose amount stays
        scale: `V` for a concentration assigned as amount `n = S * V` and for a
            rescaled concentration, `S * V` for a concentration whose amount stays
        divisor: the compartment whose new size divides a rescaled concentration,
            `S = S_value * V / V_new`
    """

    variable: str
    math: libsbml.ASTNode | None
    scale: libsbml.ASTNode | None = None
    divisor: str | None = None


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
        # the analysis builds the dataclasses of this module
        from sbmlutils.converters.ode.analysis import analyse

        return analyse(source)

    def render(self, fmt: str, **options: object) -> str:
        """Render the system in a format, see `formats.render`.

        Args:
            fmt: the name of the format, a key of `formats.FORMATS`
            **options: the options of the format

        Returns:
            the code or the document
        """
        # the formats render the dataclasses of this module
        from sbmlutils.converters.ode import formats

        return formats.render(self, fmt, **options)

    def write(
        self, path: Path | str, fmt: str | None = None, **options: object
    ) -> Path:
        """Write the system to a file in the format of its suffix, see `formats.write`.

        Args:
            path: the path of the file
            fmt: the name of the format, by default the format of the suffix
            **options: the options of the format

        Returns:
            the path
        """
        from sbmlutils.converters.ode import formats

        return formats.write(self, path, fmt, **options)

    def render_template(
        self, template: Path | str, fmt: str = "python", **options: object
    ) -> str:
        """Render the system with a template of its own, see `formats.render_template`.

        Args:
            template: the path of the jinja2 template
            fmt: the name of the format whose context the template gets
            **options: the options of the format

        Returns:
            the rendered template
        """
        from sbmlutils.converters.ode import formats

        return formats.render_template(self, template, fmt, **options)

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
        """The assigned variables and reactions, in the order of `assignments`."""
        return tuple(a.variable for a in self.assignments)

    def quantity(self, sid: str) -> Quantity:
        """The quantity of an id, `KeyError` if it is none."""
        return self._quantities[sid]

    def symbol(self, sid: str) -> Symbol:
        """The symbol of an id, `KeyError` if it is none."""
        return self._symbols[sid]

    @property
    def quantities(self) -> tuple[Quantity, ...]:
        """The compartments, species, parameters and species references.

        A species held as amount is followed by its amount.
        """
        amount_of = {amount.amount_of: amount for amount in self.amounts}
        held = (
            quantity
            for species in self.species
            for quantity in (species, amount_of.get(species.symbol.sid))
            if quantity is not None
        )
        return (*self.compartments, *held, *self.parameters, *self.species_references)

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
