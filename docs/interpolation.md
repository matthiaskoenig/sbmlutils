# Interpolation

A model often has to follow measured data: a plasma concentration over time, a dose response curve, an input which was recorded rather than computed. `sbmlutils.data.interpolation` turns a table of data points into assignment rules which evaluate an interpolation of the data, so the data drives a simulation like any other quantity. The rules make a model of their own, drive the quantities of an existing model in place, drive it through a comp model which leaves the original untouched, or go into a model definition of the factory.

## From a data frame

```python
import pandas as pd

from sbmlutils.data.interpolation import INTERPOLATION_LINEAR, Interpolation

data = pd.DataFrame(
    {
        "time": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [0.0, 2.0, 1.0, 1.5, 2.5, 3.5],
        "z": [10.0, 5.0, 2.5, 1.25, 0.6, 0.3],
    }
)

interpolation = Interpolation(data=data, method=INTERPOLATION_LINEAR)
interpolation.write_sbml_to_file("interpolation.xml")
```

The first column is x, every other column is interpolated against it. x named `time` is the simulation time, any other name is the quantity of that id in the model the interpolation runs in. Each column becomes a parameter with an assignment rule which evaluates the interpolation, so simulating the model at time `t` gives the interpolated `y` and `z`. The model is SBML Level 3 Version 2, and every interpolated parameter has a port (and x too, when it is not the time), so the model can be used as a submodel. `write_sbml_to_string()` returns the SBML instead of writing a file.

## From a file

`from_csv` and `from_tsv` read the data from a file, with x in the first column:

```python
data.to_csv("data.csv", index=False)
interpolation = Interpolation.from_csv("data.csv", method="linear")

data.to_csv("data.tsv", sep="\t", index=False)
interpolation = Interpolation.from_tsv("data.tsv", method="cubic spline")
```

## The methods

The methods are the members of the `InterpolationMethod` string enum of `sbmlutils.data.interpolation`, also available as the module constants below. A plain string like `"linear"` is accepted too, an unknown method raises a `ValueError`:

| method | value | what it does |
| --- | --- | --- |
| `INTERPOLATION_CONSTANT` | `"constant"` | the value of the previous data point, a step function |
| `INTERPOLATION_LINEAR` | `"linear"` | a straight line between two data points |
| `INTERPOLATION_CUBIC_SPLINE` | `"cubic spline"` | a natural cubic spline through all data points |

All three go exactly through the data points; they differ in what happens between them. Outside the data every method holds the first value before it and the last value after it. The formulas are piecewise expressions over x, so the model is valid SBML which any simulator evaluates. The numbers of the data are held exactly in the formula; the MathML libsbml writes keeps 15 significant digits of them.

The data is checked when the `Interpolation` is created, and data which cannot be interpolated raises a `ValueError` which names the column: fewer than 2 columns, a column name which is not a string (read the data with its header) or which repeats, a first column whose name is not an SBML id, a column which is not numeric, a missing or an infinite value, a value of x which repeats, and fewer than 2 data points (3 for the cubic spline). Data whose first column is not ascending is sorted, with a warning.

## Simulating an interpolation

```python
import roadrunner

r = roadrunner.RoadRunner("interpolation.xml")
s = r.simulate(0, 5, 51, selections=["time", "y", "z"])
```

## Driving a model in place

The model of glucose uptake of `examples/interpolation/driving.py` has the plasma glucose `glc_ext` as a species:

```python
from pathlib import Path

from sbmlutils.factory import (
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.validation import ValidationOptions

model = Model(
    "uptake",
    compartments=[Compartment("plasma", 1.0), Compartment("liver", 0.5)],
    species=[
        Species("glc_ext", initialConcentration=5.0, compartment="plasma"),
        Species("glc", initialConcentration=5.0, compartment="liver"),
    ],
    parameters=[Parameter("Vmax", 2.0), Parameter("Km", 5.0), Parameter("k_use", 0.2)],
    reactions=[
        Reaction("GLCIM", "glc_ext -> glc", formula="Vmax * glc_ext / (Km + glc_ext)"),
        Reaction("GLCUSE", "glc -> ", formula="k_use * glc"),
    ],
)
create_model(
    model,
    filepath=Path("uptake.xml"),
    validation_options=ValidationOptions(units_consistency=False),
)
```

`drive` makes the measured plasma glucose drive it. A column drives the element of its own id:

```python
glucose = pd.DataFrame(
    {
        "time": [0.0, 10.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0],
        "glc_ext": [5.0, 5.3, 7.4, 9.1, 8.7, 7.8, 6.4, 5.7],
    }
)
interpolation = Interpolation(glucose, method="linear")
doc = interpolation.drive("uptake.xml", filepath=Path("uptake_driven.xml"))

r = roadrunner.RoadRunner("uptake_driven.xml")
s = r.simulate(0, 120, 121, selections=["time", "[glc_ext]", "[glc]"])
```

The source is an SBML file, an SBML string or a `libsbml.SBMLDocument`, which is changed and returned; `filepath` writes the driven model in addition, its SBML Level and Version are kept. What `drive` does:

- A parameter or a compartment becomes non constant, a species a non constant boundary species, so it stays a reactant or a product of its reactions. Only these three can be driven.
- The data is in the units of the element it drives, and x in the units of x in the model (the time in the time unit of the model). Nothing is converted.
- The data of a species is its concentration, or its amount if the species has only substance units, as an assignment rule on a species means in SBML.
- An element which the model determines already, by an assignment rule, a rate rule, an algebraic rule or an event assignment, raises a `ValueError`: driving it would replace the mechanism of the model, which `drive` never does silently. An initial assignment of a driven element is removed, with a log message, because SBML forbids it next to an assignment rule.
- A column which is not in the data, two columns driving one element, an element which is not in the model and an x which is not in the model raise a `ValueError`. The checks run before anything changes, so a refused document is unchanged.

`targets` maps a column to the element it drives when the names differ, and x can be any quantity of the model. Here the measured maximal rate drives `Vmax` by the value of `Km`:

```python
dose_response = pd.DataFrame({"Km": [1.0, 5.0, 10.0], "Vmax_data": [1.0, 2.0, 2.5]})
Interpolation(dose_response, method="linear").drive(
    "uptake.xml", targets={"Vmax_data": "Vmax"}, filepath=Path("uptake_vmax.xml")
)
```

## Driving a model through comp

`drive_comp` leaves the original untouched and writes a comp model which drives it:

```python
from sbmlutils.comp import flatten_sbml

interpolation.drive_comp("uptake.xml", filepath=Path("uptake_driven_comp.xml"))
flatten_sbml(Path("uptake_driven_comp.xml"), Path("uptake_driven_flat.xml"))

r = roadrunner.RoadRunner("uptake_driven_flat.xml")
s = r.simulate(0, 120, 121, selections=["time", "[glc_ext]", "[uptake__glc]"])
```

The comp document has the original as the submodel `uptake` of the top model `uptake_driven`, which holds the assignment rules. comp requires an element to be replaced by one of its own class (except a parameter, which anything with a value may replace), so every driven element gets a placeholder of its class in the top model, which replaces it in the original: a parameter for a parameter, a compartment for a compartment, and for a species a species in a compartment which reads the compartment of the original. x other than the time is a parameter of the top model which reads x of the original. A reference into the original goes through its port when it declares one for the element, else by the id.

After flattening the elements of the original are named after the submodel, `uptake__glc`, while the driven elements and x keep their ids, and the flattened model simulates as the model driven in place. The rest behaves as `drive`:

- The original is referenced by an external model definition, relative to the directory of `filepath`, so the two files can be moved together; without `filepath` the reference is absolute. `embed=True` copies the original into the comp document as a model definition instead, which is needed for an SBML string or a document, which have no file to reference. A hierarchical model (one with submodels or model definitions) is referenced, it cannot be embedded.
- The original has to be SBML Level 3, comp is a Level 3 package; `drive` in place supports Level 2 as well.
- The top model takes over the units of the original, so the placeholders have the units of the elements they replace.
- An initial assignment of a driven element cannot be removed without changing the original: if it has a metaid it is deleted in the submodel, otherwise `drive_comp` raises a `ValueError` and `drive` is the way to go.

## In a model definition

`assignment_rules` gives the interpolation as assignment rules of a model definition, which declares the driven elements itself, non constant and with their units:

```python
infusion = pd.DataFrame({"time": [0.0, 30.0, 60.0], "f_data": [0.0, 1.0, 0.0]})
model = Model(
    "infusion",
    parameters=[Parameter("f", 0.0, constant=False)],
)
model.rules = Interpolation(infusion, method="linear").assignment_rules(
    targets={"f_data": "f"}
)
create_model(
    model,
    filepath=Path("infusion.xml"),
    validation_options=ValidationOptions(units_consistency=False),
)
```

## Examples

`examples/interpolation/` has three examples, each writes its figure into the current working directory and opens no window:

```bash
python -m examples.interpolation.interpolation
python -m examples.interpolation.driving
python -m examples.interpolation.pancreas
```

`interpolation` interpolates the same data with all three methods, `driving` drives the uptake model with measured plasma glucose in place and through comp, and `pancreas` drives the ATP/ADP ratio of a model by its glucose with a measured dose response.
