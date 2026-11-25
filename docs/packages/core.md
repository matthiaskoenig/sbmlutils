# core

SBML Level 3 core defines the structure of a model, including compartments, species, reactions, parameters, rules and events. Packages extend this structure. A kinetic model with well-mixed compartments can usually be represented using core alone.

Run the examples in order. The first example defines the units and a base model; later examples copy that model and write separate SBML files. Each file can be read independently.

## Create a first-order conversion

A single reaction converts `A` into `B` in a one-litre compartment. Both species use amounts in moles, so `k * A` gives a reaction rate in moles per second. The reaction's stoichiometry makes the amount of `A` decrease and the amount of `B` increase at that rate.

```python
from pathlib import Path

from sbmlutils.factory import (
    Compartment,
    Model,
    ModelUnits,
    Parameter,
    Reaction,
    Species,
    UnitDefinition,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml


class U(Units):
    """Units used in the conversion model."""

    per_second = UnitDefinition("per_second", "1/second")
    mole_per_second = UnitDefinition("mole_per_second", "mole/second")
    per_mole_second = UnitDefinition("per_mole_second", "1/(mole*second)")


model = Model(
    sid="conversion",
    units=U,
    model_units=ModelUnits(
        time=U.second, extent=U.mole, substance=U.mole, volume=U.litre
    ),
    compartments=[Compartment("cell", value=1.0, unit=U.litre)],
    species=[
        Species("A", compartment="cell", initialAmount=1.0, hasOnlySubstanceUnits=True),
        Species("B", compartment="cell", initialAmount=0.0, hasOnlySubstanceUnits=True),
    ],
    parameters=[Parameter("k", value=0.1, unit=U.per_second)],
    reactions=[Reaction("conversion_rate", equation="A -> B", formula="k * A")],
)
result = create_model(model, Path("conversion.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
reaction = doc.getModel().getReaction("conversion_rate")
assert reaction.getReactant(0).getSpecies() == "A"
assert reaction.getProduct(0).getSpecies() == "B"
```

`hasOnlySubstanceUnits=True` gives the species identifier amount semantics in formulas. With `False`, the identifier denotes concentration, including when `initialAmount` supplies the starting quantity. Either initial-value attribute can initialize a species; the flag determines its meaning in formulas. For a concentration-based rate law, account for compartment volume when converting a concentration rate into a reaction rate.

## Stoichiometry, reversibility and modifiers

The equation `2 A <-> B [E]` defines two reactant units of `A`, one product unit of `B`, and a modifier `E`. A modifier participates in the rate law without being consumed or produced by the reaction. Here `E` scales the forward rate relative to a reference enzyme amount. The reverse term lets the net rate become negative.

```python
from copy import deepcopy

dimer = deepcopy(model)
dimer.sid = "reversible_dimerization"
dimer.species.append(
    Species(
        "E",
        compartment="cell",
        initialAmount=0.05,
        hasOnlySubstanceUnits=True,
        boundaryCondition=True,
    )
)
dimer.parameters = [
    Parameter("kf", value=0.1, unit=U.per_mole_second),
    Parameter("kr", value=0.01, unit=U.per_second),
    Parameter("enzyme_reference", value=0.05, unit=U.mole),
]
dimer.reactions = [
    Reaction(
        "dimerize",
        equation="2 A <-> B [E]",
        formula="kf * A^2 * E / enzyme_reference - kr * B",
    )
]
result = create_model(dimer, Path("dimerization.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
reaction = doc.getModel().getReaction("dimerize")
assert reaction.getReversible()
assert reaction.getReactant(0).getStoichiometry() == 2.0
assert reaction.getModifier(0).getSpecies() == "E"
```

`boundaryCondition=True` excludes `E` from changes caused by reactions. The kinetic law explicitly states its dependence on `E`; a modifier in the equation alone does not add a factor to the formula.

## Function definitions and local parameters

`Function` defines a reusable MathML function. Pass species, compartments and global parameters as lambda arguments. A function can also call another function definition. `LocalParameter` belongs to one kinetic law; here `k_local` is available inside the reaction without becoming a global parameter.

```python
from sbmlutils.factory import Function, KineticLaw, LocalParameter

local_model = deepcopy(model)
local_model.sid = "local_kinetics"
local_model.functions = [Function("first_order", "lambda(s, rate, rate * s)")]
local_model.reactions = [
    Reaction(
        "conversion_rate",
        equation="A -> B",
        formula=KineticLaw(
            math="first_order(A, k_local)",
            local_parameters=[LocalParameter("k_local", value=0.25, unit=U.per_second)],
        ),
    )
]
result = create_model(local_model, Path("local_kinetics.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
kinetics = sbml_model.getReaction("conversion_rate").getKineticLaw()
assert kinetics.getLocalParameter("k_local").getValue() == 0.25
assert sbml_model.getParameter("k_local") is None
assert sbml_model.getParameter("k").getValue() == 0.1
assert sbml_model.getFunctionDefinition("first_order").getMath().isLambda()
```

## Initial assignments

An `InitialAssignment` computes a value during initialization. It overrides the literal initial value on its target and does not keep that target equal to the expression during simulation. Here `B` starts at one quarter of a one-mole pool instead of its literal initial amount of zero.

```python
from sbmlutils.factory import InitialAssignment

initialized = deepcopy(model)
initialized.sid = "computed_initial_amount"
initialized.parameters += [
    Parameter("starting_pool", value=1.0, unit=U.mole),
    Parameter("fraction", value=0.25, unit=U.dimensionless),
]
initialized.assignments = [InitialAssignment("B", "fraction * starting_pool")]
result = create_model(initialized, Path("initial_assignment.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
assignment = doc.getModel().getInitialAssignmentBySymbol("B")
assert assignment.getSymbol() == "B"
assert doc.getModel().getSpecies("B").getInitialAmount() == 0.0
```

The written SBML retains both the literal value and the overriding initial assignment. A tool which initializes the model evaluates the expression to obtain `0.25` mole.

## Assignment rules and rate rules

An `AssignmentRule` defines a quantity at every time point. A `RateRule` defines its time derivative instead. Their target parameters must have `constant=False`. Do not give one target both kinds of rule, or define a reacting species by an assignment rule at the same time.

```python
from sbmlutils.factory import AssignmentRule, RateRule

ruled = deepcopy(model)
ruled.sid = "rules"
ruled.parameters += [
    Parameter("total", value=None, unit=U.mole, constant=False),
    Parameter("accumulator", value=0.0, unit=U.mole, constant=False),
    Parameter("input_rate", value=0.02, unit=U.mole_per_second),
]
ruled.rules = [AssignmentRule("total", "A + B")]
ruled.rate_rules = [RateRule("accumulator", "input_rate")]
result = create_model(ruled, Path("rules.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
assert sbml_model.getRuleByVariable("total").isAssignment()
assert sbml_model.getRuleByVariable("accumulator").isRate()
assert sbml_model.getParameter("accumulator").getValue() == 0.0
```

`total` follows `A + B`. `accumulator` starts at zero and increases at `0.02` mole per second; its rule is not an instruction to assign `0.02` mole to it.

## Algebraic rules

An `AlgebraicRule` states that its expression equals zero. It has no target variable. A compatible tool solves for variables which are not fixed elsewhere. The example makes `free` variable and states `total - bound - free = 0`, giving a free amount of `0.75` mole. Its supplied initial value is consistent with that equation.

```python
from sbmlutils.factory import AlgebraicRule

balance = Model(
    sid="algebraic_balance",
    units=U,
    model_units=model.model_units,
    parameters=[
        Parameter("total", value=1.0, unit=U.mole),
        Parameter("bound", value=0.25, unit=U.mole),
        Parameter("free", value=0.75, unit=U.mole, constant=False),
    ],
    algebraic_rules=[AlgebraicRule("balance", "total - bound - free", unit=U.mole)],
)
result = create_model(balance, Path("algebraic_balance.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
assert doc.getModel().getRule(0).isAlgebraic()
assert not doc.getModel().getRule(0).isSetVariable()
```

Algebraic rules need solver support. Fixing every variable in the expression or adding another independent definition of the same unknown can overdetermine a model.

## Events: trigger, delay, priority and assignments

An `Event` makes a discrete change when its trigger changes from false to true. This trigger activates at 10 seconds; a two-second delay schedules the change to `k` at 12 seconds. When events are due at the same time, a higher-priority event executes first, and the remaining priorities are reevaluated after each execution.

```python
from sbmlutils.factory import Delay, Event, EventAssignment, Priority, Trigger

switched = deepcopy(model)
switched.sid = "delayed_rate_switch"
switched.parameters = [Parameter("k", value=0.1, unit=U.per_second, constant=False)]
switched.events = [
    Event(
        "switch_rate",
        trigger=Trigger("time >= 10 second", initialValue=False, persistent=True),
        delay=Delay("2 second"),
        priority=Priority("1 dimensionless"),
        assignments=[EventAssignment("k", "0.5 per_second")],
        useValuesFromTriggerTime=False,
    )
]
result = create_model(switched, Path("event.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
event = doc.getModel().getEvent("switch_rate")
assert event.isSetDelay() and event.isSetPriority()
assert not event.getUseValuesFromTriggerTime()
assert event.getEventAssignment(0).getVariable() == "k"
```

`initialValue=False` supplies the trigger's value immediately before time zero. With `persistent=True`, a scheduled event remains scheduled even if the trigger later becomes false. `useValuesFromTriggerTime=False` evaluates assignment expressions when the event executes; `True` captures their values when triggered. All assignments in one event update simultaneously.

## Constraints and messages

A `Constraint` states an assumption about allowed model states. Its formula must be Boolean and its message must be XHTML. This constraint records that the amount of `A` must remain nonnegative.

```python
from sbmlutils.factory import Constraint

constrained = deepcopy(model)
constrained.sid = "nonnegative_amount"
constrained.constraints = [
    Constraint(
        "nonnegative_A",
        math="A >= 0 mole",
        message=(
            '<body xmlns="http://www.w3.org/1999/xhtml">'
            "<p>The amount of A must be nonnegative.</p></body>"
        ),
    )
]
result = create_model(constrained, Path("constraint.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
constraint = doc.getModel().getConstraint(0)
assert constraint.getMath().isRelational()
assert "nonnegative" in constraint.getMessageString()
```

A constraint does not change a rate law or reset a state. Simulation tools can report when its assumption is violated.

See [Model creation](../creation.md) for factory options, [Units](../units.md) for unit definitions, and [Annotations](../annotations.md) and [Notes](../notes.md) for the metadata shared by core and package elements.
