# SBML Core

SBML Level 3 Core defines the structure of a model, including compartments, species, reactions, parameters, rules and events. Packages extend this structure. A kinetic model with well-mixed compartments can usually be represented using Core alone.

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

`hasOnlySubstanceUnits=True` gives the species identifier amount semantics in formulas. For a concentration-based rate law, define the initial concentrations and account for compartment volume when converting a concentration rate into a reaction rate.

See [Model creation](../creation.md) for rules, events and factory options, and [Units](../units.md) for model defaults and formula units.
