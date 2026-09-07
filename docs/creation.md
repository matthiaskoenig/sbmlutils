# Model creation

A model is a python object. `Model` holds the elements of the model — compartments, species, parameters, reactions, rules, events — and `create_model` turns that definition into an SBML file.

## The model definition

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


class U(Units):
    """Units of the model."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    l = UnitDefinition("l", "liter")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")


model = Model(
    sid="glycolysis",
    name="minimal glycolysis model",
    notes="""
    # Minimal glycolysis model
    Glucose is taken up and phosphorylated.
    """,
    units=U,
    model_units=ModelUnits(
        time=U.min, extent=U.mmole, substance=U.mmole, volume=U.l
    ),
    compartments=[
        Compartment("cell", value=1.0, unit=U.l, name="cell", constant=True),
    ],
    species=[
        Species("glc", initialConcentration=5.0, compartment="cell", substanceUnit=U.mmole),
        Species("g6p", initialConcentration=0.0, compartment="cell", substanceUnit=U.mmole),
    ],
    parameters=[
        Parameter("Vmax", 1.0, U.mmole_per_min),
        Parameter("Km", 0.1, U.mM),
    ],
    reactions=[
        Reaction(
            "GK",
            name="glucokinase",
            equation="glc -> g6p",
            formula=("Vmax * glc / (Km + glc)", U.mmole_per_min),
        ),
    ],
)

result = create_model(model=model, filepath=Path("glycolysis.xml"))
```

`create_model` returns a `FactoryResult` with the `sbml_path` it wrote and the created `Model`. It validates the model by default, see [Validation](validation.md).

The elements can be passed to the constructor or assigned afterwards, which is useful when they are built programmatically:

```python
model.species += [
    Species(f"s{k}", initialConcentration=0.0, compartment="cell", substanceUnit=U.mmole)
    for k in range(10)
]
```

`objects=[...]` accepts elements of any kind in one list; they are sorted into the right collection by their type.

## The elements

| element | what it is |
| --- | --- |
| `Compartment` | a compartment, `value` is its size |
| `Species` | a species, given as `initialConcentration` or `initialAmount` |
| `Parameter` | a parameter, `value` is a number or a formula |
| `Reaction` | a reaction, with an `equation` and a rate `formula` |
| `InitialAssignment` | the initial value of a symbol as a formula |
| `AssignmentRule`, `RateRule`, `AlgebraicRule` | the rules of the model |
| `Event` | a discrete event with a trigger and assignments |
| `Function` | a function definition |
| `Constraint` | a constraint on the state of the model |
| `Objective`, `FluxObjective`, `GeneProduct` | the [fbc](fbc.md) elements |
| `Submodel`, `Port`, `ReplacedElement`, `ReplacedBy`, `Deletion` | the [comp](comp.md) elements |
| `Uncertainty`, `UncertParameter`, `UncertSpan` | the [distrib](distrib.md) elements |

Every element is an `Sbase` and accepts the attributes every SBML element has: `sid`, `name`, `metaId`, `sboTerm`, `notes`, `annotations`, `port`, `uncertainties` and `keyValuePairs`.

## Reactions

The stoichiometry of a reaction is written as an equation string, which is parsed by `sbmlutils.reaction_equation`:

```python
Reaction("R1", equation="2 glc + atp -> g6p + adp")   # stoichiometries
Reaction("R2", equation="glc <-> g6p")                # reversible, `->` is irreversible
Reaction("R3", equation="glc -> g6p [enzyme]")        # modifiers in brackets
Reaction("R4", equation="fS glc -> g6p")              # variable stoichiometry
Reaction("R5", equation="=> cit")                     # no reactants
Reaction("R6", equation="acoa =>")                    # no products
```

The rate is given as `formula`, either as a plain string or as a `(formula, unit)` tuple, which is what makes the [unit check](units.md#unit-consistency) meaningful. The full grammar of the equations is documented in `sbmlutils.reaction_equation`.

## Packages

SBML packages are activated on the model and their elements are then available:

```python
from sbmlutils.factory import Model, Package

model = Model(sid="example", packages=[Package.COMP_V1, Package.FBC_V3, Package.DISTRIB_V1])
```

| package | guide |
| --- | --- |
| `Package.COMP_V1` | [Model composition](comp.md) |
| `Package.FBC_V2`, `Package.FBC_V3` | [Flux balance constraints](fbc.md) |
| `Package.DISTRIB_V1` | [Distributions and uncertainties](distrib.md) |

The layout package needs no entry in `packages`: assigning `model.layouts` with the objects of `sbmlutils.layout` activates it.

## Several models at once

`create_model` accepts an iterable of models, which are merged into one before the file is written. This keeps a large model in several files:

```python
from examples import compartments, reactions, species

create_model(model=[compartments.model, species.model, reactions.model], filepath="model.xml")
```

The later model wins where the definitions overlap, which is how a base model is parameterized for a specific case.

## Examples

The [`examples/`](https://github.com/matthiaskoenig/sbmlutils/tree/develop/examples) directory of the repository holds a runnable model for every concept: species in amounts and concentrations, reactions with units, assignments and rules, events, annotations, notes, and complete models from a small demo to a whole body physiological model. They are run as modules from the root of the repository:

```bash
python -m examples.species
python -m examples.tutorial.minimal_model
```
