# Flux Balance Constraints (fbc)

The fbc package adds bounds, objectives and other constraints to a reaction network. In a flux balance analysis, a solver finds steady-state reaction fluxes that satisfy the constraints and optimize the active objective.

## Define a constrained pathway

The `feed` reaction supplies `A` at up to 10 mmol per hour. The `convert` reaction turns `A` into `B` at up to 6 mmol per hour, and `drain` removes `B`. Steady state requires the three fluxes to be equal, so maximizing `drain` gives 6 mmol per hour. All bounds are nonnegative and are represented as constant parameters.

```python
from pathlib import Path

from sbmlutils.factory import (
    Compartment,
    Model,
    ModelUnits,
    Objective,
    Package,
    Parameter,
    Reaction,
    Species,
    UnitDefinition,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml


class U(Units):
    """Units for flux bounds."""

    hour = UnitDefinition("hour", "hour")
    mmole = UnitDefinition("mmole", "mmole")
    mmol_per_hour = UnitDefinition("mmol_per_hour", "mmole/hour")


model = Model(
    sid="constrained_pathway",
    packages=[Package.FBC_V2],
    units=U,
    model_units=ModelUnits(
        time=U.hour, extent=U.mmole, substance=U.mmole, volume=U.litre
    ),
    strict=True,
    compartments=[Compartment("cell", value=1.0, unit=U.litre)],
    species=[
        Species("A", compartment="cell", initialAmount=0.0),
        Species("B", compartment="cell", initialAmount=0.0),
    ],
    parameters=[
        Parameter("zero", value=0.0, unit=U.mmol_per_hour),
        Parameter("feed_cap", value=10.0, unit=U.mmol_per_hour),
        Parameter("conversion_cap", value=6.0, unit=U.mmol_per_hour),
    ],
    reactions=[
        Reaction(
            "feed", equation="-> A", lowerFluxBound="zero", upperFluxBound="feed_cap"
        ),
        Reaction(
            "convert",
            equation="A -> B",
            lowerFluxBound="zero",
            upperFluxBound="conversion_cap",
        ),
        Reaction(
            "drain", equation="B ->", lowerFluxBound="zero", upperFluxBound="feed_cap"
        ),
    ],
    objectives=[
        Objective(
            sid="maximize_drain",
            objectiveType="maximize",
            active=True,
            fluxObjectives={"drain": 1.0},
        )
    ],
)
result = create_model(model, Path("constrained_pathway.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
objective = sbml_model.getPlugin("fbc").getActiveObjective()
assert objective.getFluxObjective(0).getReaction() == "drain"
bound_id = sbml_model.getReaction("convert").getPlugin("fbc").getUpperFluxBound()
assert sbml_model.getParameter(bound_id).getValue() == 6.0
```

The factory writes the constraints and objective to SBML. Solving the optimization problem requires an FBA-capable tool. This example uses fbc version 2, which supports linear objectives. Use fbc version 3 for features such as user-defined constraints.

See [Flux balance constraints](../fbc.md) for gene product associations, exchange reactions and package versions.
