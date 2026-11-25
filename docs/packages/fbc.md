# Flux Balance Constraints (fbc)

The fbc package adds flux bounds, objectives, gene product associations and other constraint-based modeling constructs to an SBML reaction network. A flux balance analysis finds steady-state fluxes that satisfy the bounds and constraints and optimize the active objective.

## Bound reaction and exchange fluxes

This model takes up L-lactate, converts it to D-lactate and exports the D-lactate. An `ExchangeReaction` consumes one unit of the species in the written reaction, so negative flux denotes uptake and positive flux denotes export. The L-lactate exchange allows uptake up to 10 mmol per hour, the conversion allows forward flux up to 6 mmol per hour, and the D-lactate exchange allows export up to 10 mmol per hour.

Run the examples on this page in order. The first block creates the pathway and defines the helper used to write, validate and reload its later versions.

```python
from pathlib import Path

import libsbml

from sbmlutils.factory import (
    Compartment,
    ExchangeReaction,
    Model,
    ModelUnits,
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
    """Units for the pathway fluxes and their bounds."""

    hour = UnitDefinition("hour", "hour")
    mmole = UnitDefinition("mmole", "mmole")
    mmol_per_hour = UnitDefinition("mmol_per_hour", "mmole/hour")


def write_fbc(model: Model, filename: str) -> libsbml.SBMLDocument:
    """Write and validate a flux model, then reload it."""
    result = create_model(model, Path(filename), sbml_version=2, raise_on_error=True)
    return read_sbml(result.sbml_path)


convert = Reaction(
    "convert",
    equation="L_lactate -> D_lactate",
    lowerFluxBound="zero",
    upperFluxBound="conversion_cap",
)
model = Model(
    "lactate_pathway",
    packages=[Package.FBC_V2],
    units=U,
    model_units=ModelUnits(
        time=U.hour, extent=U.mmole, substance=U.mmole, volume=U.litre
    ),
    strict=True,
    compartments=[Compartment("cell", value=1.0, unit=U.litre)],
    species=[
        Species("L_lactate", compartment="cell", initialAmount=0.0),
        Species("D_lactate", compartment="cell", initialAmount=0.0),
    ],
    parameters=[
        Parameter("zero", value=0.0, unit=U.mmol_per_hour),
        Parameter("uptake_limit", value=-10.0, unit=U.mmol_per_hour),
        Parameter("conversion_cap", value=6.0, unit=U.mmol_per_hour),
        Parameter("export_cap", value=10.0, unit=U.mmol_per_hour),
    ],
    reactions=[
        ExchangeReaction(
            "L_lactate", lowerFluxBound="uptake_limit", upperFluxBound="zero"
        ),
        convert,
        ExchangeReaction(
            "D_lactate",
            reversible=False,
            lowerFluxBound="zero",
            upperFluxBound="export_cap",
        ),
    ],
)
doc = write_fbc(model, "lactate_bounds.xml")
sbml_model = doc.getModel()
assert sbml_model.getPlugin("fbc").getStrict()
uptake = sbml_model.getReaction("EX_L_lactate")
assert uptake.getReactant(0).getSpecies() == "L_lactate"
assert uptake.getNumProducts() == 0
lower_id = uptake.getPlugin("fbc").getLowerFluxBound()
assert sbml_model.getParameter(lower_id).getValue() == -10.0
assert uptake.getPlugin("fbc").getUpperFluxBound() == "zero"
conversion = sbml_model.getReaction("convert").getPlugin("fbc")
upper_id = conversion.getUpperFluxBound()
assert sbml_model.getParameter(upper_id).getValue() == 6.0
assert sbml_model.getParameter(upper_id).getUnits() == "mmol_per_hour"
```

Each bound stores the ID of a parameter. With `strict=True`, give every reaction both bounds and use constant parameters with explicit values. This pathway leaves its two species subject to steady-state balance, so uptake, conversion and export have the same flux magnitude.

## Set objective coefficients and select the active objective

The production objective rewards D-lactate secretion and applies a smaller cost to L-lactate uptake. Since uptake is expressed as a negative flux, its positive coefficient reduces the objective value. A second, inactive objective lets a tool select a different optimization target later.

```python
from sbmlutils.factory import Objective

model.objectives = [
    Objective(
        "production",
        objectiveType="maximize",
        active=True,
        fluxObjectives={"EX_D_lactate": 1.0, "EX_L_lactate": 0.1},
    ),
    Objective(
        "minimize_conversion",
        objectiveType="minimize",
        active=False,
        fluxObjectives={"convert": 1.0},
    ),
]
doc = write_fbc(model, "lactate_objectives.xml")
fbc = doc.getModel().getPlugin("fbc")
assert fbc.getNumObjectives() == 2
assert fbc.getActiveObjectiveId() == "production"
objective = fbc.getActiveObjective()
assert objective.getType() == "maximize"
assert {
    term.getReaction(): term.getCoefficient()
    for term in objective.getListOfFluxObjectives()
} == {"EX_D_lactate": 1.0, "EX_L_lactate": 0.1}
assert fbc.getObjective("minimize_conversion").getType() == "minimize"
```

The keys in `fluxObjectives` are reaction IDs and the values are their coefficients. The example writes the objective for use in a separate flux analysis tool.

## Associate a reaction with gene products

In this illustrative rule, the conversion can use either a two-subunit enzyme, which requires both its gene products, or an alternative enzyme. Declare the gene products on the model and use their SBML IDs in the boolean expression.

```python
from sbmlutils.factory import GeneProduct

model.gene_products = [
    GeneProduct("g_subunit_a", label="subunit A"),
    GeneProduct("g_subunit_b", label="subunit B"),
    GeneProduct("g_alternative", label="alternative enzyme"),
]
convert.geneProductAssociation = "(g_subunit_a AND g_subunit_b) OR g_alternative"
doc = write_fbc(model, "lactate_genes.xml")
sbml_model = doc.getModel()
fbc = sbml_model.getPlugin("fbc")
assert fbc.getGeneProduct("g_subunit_a").getLabel() == "subunit A"
reaction_fbc = sbml_model.getReaction("convert").getPlugin("fbc")
association = reaction_fbc.getGeneProductAssociation().getAssociation()
assert isinstance(association, libsbml.FbcOr)
subunits = association.getAssociation(0)
assert isinstance(subunits, libsbml.FbcAnd)
assert {ref.getGeneProduct() for ref in subunits.getListOfAssociations()} == {
    "g_subunit_a",
    "g_subunit_b",
}
assert association.getAssociation(1).getGeneProduct() == "g_alternative"
```

## Record chemical formula and charge

L-lactate and D-lactate are stereoisomers of the lactate anion. They have the same elemental composition and a charge of -1. Set these attributes on their `Species` definitions so a tool can check mass and charge balance.

```python
for species in model.species:
    species.chemicalFormula = "C3H5O3"
    species.charge = -1

doc = write_fbc(model, "lactate_chemistry.xml")
sbml_model = doc.getModel()
for sid in ("L_lactate", "D_lactate"):
    species_fbc = sbml_model.getSpecies(sid).getPlugin("fbc")
    assert species_fbc.getChemicalFormula() == "C3H5O3"
    assert species_fbc.getCharge() == -1
```

## Constrain a combination of fluxes in fbc version 3

Suppose the combined magnitude of the import and export is limited to 8 mmol per hour. Because the two exchanges have opposite signs, the bound applies to `v(EX_D_lactate) - v(EX_L_lactate)`. The lower and upper bounds refer to model parameters in flux units, while each linear coefficient refers to a dimensionless parameter. Both exchange fluxes have the same magnitude at steady state, so the additional constraint limits conversion to 4 mmol per hour.

```python
from sbmlutils.factory import UserDefinedConstraint, UserDefinedConstraintComponent

model.packages = [Package.FBC_V3]
model.parameters.extend(
    [
        Parameter("exchange_cap", value=8.0, unit=U.mmol_per_hour),
        Parameter("plus_one", value=1.0, unit=U.dimensionless),
        Parameter("minus_one", value=-1.0, unit=U.dimensionless),
    ]
)
model.user_defined_constraints = [
    UserDefinedConstraint(
        sid="exchange_capacity",
        lowerBound="zero",
        upperBound="exchange_cap",
        components=[
            UserDefinedConstraintComponent(
                variable="EX_D_lactate", coefficient="plus_one", variableType="linear"
            ),
            UserDefinedConstraintComponent(
                variable="EX_L_lactate", coefficient="minus_one", variableType="linear"
            ),
        ],
    )
]
doc = write_fbc(model, "lactate_capacity.xml")
sbml_model = doc.getModel()
fbc = sbml_model.getPlugin("fbc")
assert fbc.getPackageVersion() == 3
capacity = fbc.getUserDefinedConstraint(0)
assert capacity.getId() == "exchange_capacity"
assert sbml_model.getParameter(capacity.getLowerBound()).getValue() == 0.0
assert sbml_model.getParameter(capacity.getUpperBound()).getValue() == 8.0
components = capacity.getListOfUserDefinedConstraintComponents()
assert all(
    term.getVariableType() == libsbml.FBC_VARIABLE_TYPE_LINEAR for term in components
)
assert {
    term.getVariable(): sbml_model.getParameter(term.getCoefficient()).getValue()
    for term in components
} == {"EX_D_lactate": 1.0, "EX_L_lactate": -1.0}
```

## Add key-value metadata in fbc version 3

Attach a key-value pair to record metadata about an element. Here the conversion reaction carries an experimental scenario label. The URI can identify the vocabulary or definition of the key.

```python
from sbmlutils.factory import KeyValuePair

scenario_uri = "https://example.org/model-metadata/scenario"
convert.keyValuePairs = [
    KeyValuePair(
        key="scenario",
        value="bench-scale",
        uri=scenario_uri,
        sid="conversion_scenario",
    )
]
doc = write_fbc(model, "lactate_metadata.xml")
conversion_fbc = doc.getModel().getReaction("convert").getPlugin("fbc")
scenario = conversion_fbc.getKeyValuePair(0)
assert scenario.getId() == "conversion_scenario"
assert (scenario.getKey(), scenario.getValue(), scenario.getUri()) == (
    "scenario",
    "bench-scale",
    scenario_uri,
)
```

The example writes SBML Level 3 Version 2 so libSBML also reads back the key-value pair's optional ID.

## Fill missing bounds on an existing document

`add_default_flux_bounds` fills missing bounds in an SBML document that declares fbc. The helper keeps existing references, creates constant parameters for its default lower and upper values, and leaves their units for the caller to set. Here an in-memory draft is missing the upper conversion bound. The default fills that gap while retaining the uptake bound.

```python
from sbmlutils.fbc.fbc import add_default_flux_bounds
from sbmlutils.io import write_sbml
from sbmlutils.validation import validate_doc

draft = read_sbml(Path("lactate_metadata.xml"))
draft_model = draft.getModel()
conversion = draft_model.getReaction("convert").getPlugin("fbc")
conversion.unsetUpperFluxBound()
add_default_flux_bounds(draft, lower=0.0, upper=12.0)
for bound_id in ("lower", "upper"):
    draft_model.getParameter(bound_id).setUnits(U.mmol_per_hour.sid)

path = Path("lactate_default_bounds.xml")
write_sbml(draft, path)
doc = read_sbml(path)
assert validate_doc(doc).error_count == 0
sbml_model = doc.getModel()
conversion = sbml_model.getReaction("convert").getPlugin("fbc")
assert conversion.getLowerFluxBound() == "zero"
upper_id = conversion.getUpperFluxBound()
assert sbml_model.getParameter(upper_id).getValue() == 12.0
assert sbml_model.getReaction("EX_L_lactate").getPlugin("fbc").getLowerFluxBound() == (
    "uptake_limit"
)
```

See [Flux balance constraints](../fbc.md) for package versions and round-trip behavior.
