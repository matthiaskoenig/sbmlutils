# Flux balance constraints

The SBML [fbc](https://sbml.org/documents/specifications/level-3/version-1/fbc/) package turns a reaction network into a constraint based model: every reaction gets a lower and an upper flux bound, an objective says what to optimize, and gene products link reactions to the genes which encode them.

`sbmlutils` supports fbc version 2 and version 3.

## Flux bounds

Bounds are parameters, referenced by their id on the reaction:

```python
from sbmlutils.factory import Model, Package, Parameter, Reaction, Units, UnitDefinition


class U(Units):
    """Units of the model."""

    hr = UnitDefinition("hr")
    mmole = UnitDefinition("mmole")
    mmole_per_hr = UnitDefinition("mmole_per_hr", "mmole/hr")


model = Model(sid="fbc_example", packages=[Package.FBC_V3], units=U)

model.parameters = [
    Parameter("zero", 0.0, U.mmole_per_hr, constant=True, sboTerm="SBO:0000612"),
    Parameter(
        "ub_inf", float("inf"), U.mmole_per_hr, constant=True, sboTerm="SBO:0000612"
    ),
    Parameter(
        "lb_inf", -float("inf"), U.mmole_per_hr, constant=True, sboTerm="SBO:0000612"
    ),
]

model.reactions = [
    Reaction(
        sid="v1",
        equation="9.46 Glcxt + 12.92 O2 => X []",
        lowerFluxBound="zero",
        upperFluxBound="ub_inf",
    ),
]
```

`add_default_flux_bounds` adds the bounds to a model which has none, which is what a model needs before cobrapy will read it:

```python
from sbmlutils.fbc.fbc import add_default_flux_bounds

add_default_flux_bounds(doc, lower=-1000.0, upper=1000.0)
```

## Exchange reactions

An exchange reaction is the boundary of the model: it lets a species enter or leave the system. `ExchangeReaction` creates it from the species id, with the `EX_` prefix the field expects:

```python
from sbmlutils.factory import ExchangeReaction

model.reactions.extend(
    [
        ExchangeReaction(
            species_id="Glcxt", lowerFluxBound="lb_glc", upperFluxBound="zero"
        ),
        ExchangeReaction(
            species_id="X", lowerFluxBound="lb_inf", upperFluxBound="ub_inf"
        ),
    ]
)
```

## Objective

The objective says which combination of fluxes is optimized and in which direction:

```python
from sbmlutils.factory import Objective

model.objectives = [
    Objective(
        sid="biomass_max",
        objectiveType="maximize",
        active=True,
        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0},
    )
]
```

`fluxObjectives` maps a reaction id to its coefficient. Several objectives can be defined, exactly one is `active`.

## Gene products

Gene products and the association of a reaction with them record which genes carry a reaction:

```python
from sbmlutils.factory import GeneProduct, Reaction

model.gene_products = [
    GeneProduct("g_b3670", label="b3670", name="b3670"),
    GeneProduct("g_b3671", label="b3671", name="b3671"),
]

Reaction(
    sid="v1",
    equation="A => B",
    geneProductAssociation="g_b3670 AND g_b3671",
)
```

The association is a boolean expression over the gene product ids, with `AND` and `OR`.

## Chemical formula and charge

The formula and the charge of a species are fbc attributes and are set in the model definition or from an [annotation file](annotations.md#from-a-spreadsheet):

```python
from sbmlutils.factory import Species

Species(
    sid="glc",
    compartment="cell",
    initialConcentration=0.0,
    chemicalFormula="C6H12O6",
    charge=0,
)
```

`sbmlutils.fbc.cobra.check_mass_balance` reports the reactions which are not balanced.

## User defined constraints (fbc v3)

fbc version 3 adds constraints over several fluxes at once:

```python
from sbmlutils.factory import Parameter, UserDefinedConstraint

model.parameters += [
    Parameter("uc1", 5.0),  # the bound of the constraint
    Parameter("coef_plus_one", 1.0),  # the coefficients of the components
    Parameter("coef_minus_one", -1.0),
]

model.user_defined_constraints = [
    UserDefinedConstraint(
        lowerBound="uc1",
        upperBound="uc1",
        components={"RGLX": "coef_plus_one", "RXLG": "coef_minus_one"},
        variableType="linear",
    ),
]
```

The bounds and the coefficients are references to parameters, not numbers: fbc version 3 declares them as `SIdRef`, so the constraint above reads as `uc1 <= 1.0 * RGLX - 1.0 * RXLG <= uc1`.

## cobrapy

[cobrapy](https://cobrapy.readthedocs.io) does the flux balance analysis. It is not a dependency of `sbmlutils`; install it with the `cobra` extra:

```bash
pip install sbmlutils[cobra]
```

```python
from sbmlutils.fbc.cobra import cobra_reaction_info, read_cobra_model

model = read_cobra_model("fbc_model.xml")
solution = model.optimize()
print(solution.objective_value)

df = cobra_reaction_info(model)  # bounds and objective coefficients as a DataFrame
```

The complete examples are in `examples/fbc/`: `fbc_v2.py`, `fbc_v3.py`, `fbc_mass_charge.py` and `fbc_userdefinedconstraints.py`.
