# Flux balance constraints

The SBML [fbc](https://sbml.org/documents/specifications/level-3/version-1/fbc/) package turns a reaction network into a constraint based model: every reaction gets a lower and an upper flux bound, an objective says what to optimize, and gene products link reactions to the genes which encode them.

`sbmlutils` supports fbc version 2 and version 3 ([Olivier *et al.* 2026](references.md#sbml-packages)).

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

## Strict models

`fbc:strict` on the model promises that the model is a proper constraint based model: every reaction has both bounds, the bounds are constant parameters with a value, and every species reference is constant. `Model.strict` sets it:

```python
from sbmlutils.factory import Model, Package

model = Model(sid="strict_model", packages=[Package.FBC_V3], strict=True)
```

A model which states `strict` declares fbc for it, with `packages=` or without: the attribute lives on the fbc plugin of the model, so a model which says anything about strictness needs the package. An unset `strict` says nothing and is written as `false` wherever fbc is declared, which is the weakest claim and always valid. fbc version 1 has no such attribute, so a document read from fbc version 1 comes back as `fbc:strict="false"` rather than claiming a strictness its source never stated.

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

A flux objective which states no `variableType` takes the `linear` of the objective, which is the fbc version 3 default. It is written as `fbc:variableType` in an fbc version 3 document and not at all in an fbc version 2 one, which has no such attribute and whose flux objectives are linear by definition; a `quadratic` flux objective cannot be expressed in fbc version 2 and is reported.

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

The charge is written as the fbc version of the document spells it: an integer in fbc version 2, a double in fbc version 3. A charge which is not a whole number therefore needs `Package.FBC_V3`; in an fbc version 2 document it is reported and left unset rather than rounded to a charge the model never stated.

`sbmlutils.fbc.cobra.check_mass_balance` reports the reactions which are not balanced.

## Key value pairs (fbc v3)

fbc version 3 lets every element carry a list of key-value pairs, a structured annotation of keys, values and the URI which defines the meaning of a key:

```python
from sbmlutils.factory import KeyValuePair, Parameter

Parameter(
    "p1",
    value=1.0,
    keyValuePairs=[
        KeyValuePair(
            key="source",
            value="literature",
            uri="https://identifiers.org/pubmed:10659856",
        )
    ],
)
```

A reactant, product or modifier takes them too, through the `keyValuePairs` of its `EquationPart`. The pairs are only written into a document which declares fbc version 3: in an fbc version 2 document, or in one without fbc, libsbml has no place for them, so nothing is written and the loss is reported once for the document, with how many pairs on how many elements, an example and what to declare. libsbml writes the `id` and the `name` of a pair into any document but reads them back only from an SBML Level 3 Version 2 one, so write L3V2 for a pair whose id has to survive being read again.

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

The bounds and the coefficients are references to parameters, not numbers: fbc version 3 declares them as `SIdRef`, so the constraint above reads as `uc1 <= 1.0 * RGLX - 1.0 * RXLG <= uc1`. A constraint is written into a document which declares fbc version 3 and is reported for one which does not, like a key-value pair and with the same report.

## What round trips

`sbml_to_model` reads the fbc content of a document, so an fbc model can be read, changed in python and written back, see [Reading and writing](io.md#the-packages):

| Construct | After a round trip |
| --- | --- |
| `fbc:strict` of the model | preserved, as `Model.strict` |
| flux bounds of a reaction | preserved, the bound parameters and their values |
| objectives and flux objectives | preserved, with the type, the coefficients and which objective is the active one |
| gene products | preserved, with label, associated species and their own metadata |
| the gene product association of a reaction | the boolean expression is preserved, the metadata of its nodes is not |
| charge and chemical formula of a species | preserved |
| user defined constraints and their components | preserved |
| key value pairs | preserved, except on a reactant or a product |

What the round trip does not keep:

- **The metadata of the nodes of a gene product association.** `Reaction.geneProductAssociation` is the association as an infix string over the gene product ids, which has no place for an id, a name, a metaid or an SBO term on an `and`, an `or` or a `geneProductRef` node. Such metadata is lost, and there is no way around it today; the logical rule itself is not lost. libsbml also writes a nested group of the same operator back without the inner parentheses, `((a and b) and c)` as `(a and b and c)`, which is the same rule.
- **The key value pairs of a reactant or a product.** They are written into the document, but libsbml 5.21.2 does not read the `<fbc:listOfKeyValuePairs>` of a `<speciesReference>` back, so they are gone for every reader, this one included. The pairs of a modifier are read back normally.
- **`fbc:strict` on a model definition.** libsbml 5.21.2 writes the attribute twice on a `<comp:modelDefinition>`, which leaves a file no reader can open, so it is not written there and the loss is reported once per document.
- **The strictness of an fbc version 1 model**, which such a document does not state, see above. A model which really is strict gets it back with `model.strict = True` after reading, and validating what is written then says whether the claim holds.

The verification uses the 34 fbc cases of the [SBML test suite](https://github.com/sbmlteam/sbml-test-suite) and the fbc files of the repository. The test-suite cases are uniform and contain no gene products, associations, user defined constraints or key value pairs; those come from `e_coli_core`, `Recon3D` and the example files under `resources/examples/`.

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
