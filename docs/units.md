# Units

Every quantity in a model has a unit, and SBML requires those units to be declared as `UnitDefinition` elements built from base unit kinds, exponents, scales and multipliers. Writing them out by hand is tedious and easy to get wrong.

`sbmlutils` lets you write a unit as the string you would say out loud — `mmole/min/l` — and parses it with [pint](https://pint.readthedocs.io) into the SBML representation.

## Defining units

Units are collected in a class which subclasses `Units`. Every attribute is a `UnitDefinition` with an id and, unless the id is already a unit expression, the expression it stands for:

```python
from sbmlutils.factory import UnitDefinition, Units


class U(Units):
    """Units of the model."""

    min = UnitDefinition("min")
    s = UnitDefinition("s", "second")
    mmole = UnitDefinition("mmole")
    l = UnitDefinition("l", "liter")
    mM = UnitDefinition("mM", "mmole/liter")
    per_min = UnitDefinition("per_min", "1/min")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    mmole_per_min_l = UnitDefinition("mmole_per_min_l", "mmole/min/l")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
```

The id of a unit definition must be a valid SBML identifier and must **not** be the name of an SBML base unit kind. `UnitDefinition("litre")` is invalid for that reason; give the definition another id and put the base unit in the expression, e.g. `UnitDefinition("l", "liter")`.

The class is passed to the model as `units=U` and its definitions are written into the SBML model.

## The units of the model

The model level units say what a quantity without an explicit unit means. They are set with `ModelUnits`:

```python
from sbmlutils.factory import Model, ModelUnits

model = Model(
    sid="example",
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.meter,
        area=U.m2,
        volume=U.l,
    ),
)
```

## Units on elements

Every element carries the unit of its value:

```python
from sbmlutils.factory import Compartment, Parameter, Reaction, Species

Compartment("cell", value=1.0, unit=U.l)
Parameter("Vmax", value=1.0, unit=U.mmole_per_min)
Species("glc", initialConcentration=5.0, compartment="cell", substanceUnit=U.mmole)
Reaction(
    "R1", equation="glc -> g6p", formula=("Vmax * glc / (Km + glc)", U.mmole_per_min)
)
```

A reaction formula is a `(formula, unit)` tuple: the unit is the unit of the rate, which is what the unit consistency check compares the formula against.

## Unit consistency

`create_model` validates the model and, by default, checks unit consistency:

```python
from sbmlutils.factory import ValidationOptions, create_model

create_model(
    model=model,
    filepath="model.xml",
    validation_options=ValidationOptions(units_consistency=True),
)
```

Unit errors are reported like any other validation problem, see [Validation](validation.md). A model which is not unit consistent is still written; the check reports, it does not block.

## Rendering a unit

`sbmlutils.report.units.udef_to_string` renders a libsbml `UnitDefinition` as a readable string or as latex, which is what the [reports](reports.md) use:

```python
from sbmlutils.report.units import udef_to_string

udef_to_string(udef, format="str")  # 'mmol/min/l'
udef_to_string(udef, format="latex")  # '\\frac{mmol}{min \\cdot l}'
```
