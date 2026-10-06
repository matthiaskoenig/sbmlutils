# Driving models with data: interpolation in place, via comp and in the factory

Issue: [#16](https://github.com/matthiaskoenig/sbmlutils/issues/16), "Update spline fitting, interpolation and corresponding model updates".

## Goal

A model is driven by data when one of its quantities, e.g. an external glucose concentration, follows interpolated measurements instead of a value of its own. `sbmlutils.data.interpolation` today only writes a standalone model which evaluates the interpolation. #16 asks for

1. documentation of the feature with examples,
2. examples which build models from data and couple data to models,
3. usability: it must be simple to (A) modify a model in place and (B) create a comp model which drives the original model.

Success: an existing SBML model (any file, e.g. from BioModels) is driven by a table of data in one call, in place or through a comp model which leaves the original file untouched; a python model definition takes the same interpolation as rules; the guide and two runnable examples show all of it.

## Decisions

- SBML first: the core works on a libsbml document, the factory gets a thin layer on top. Driving through `sbml_to_model` and `create_model` is rejected, the parser does not read everything (its docstring lists what), so it would not be "in place".
- One `Interpolation` object, three outputs (standalone, in place, comp) and the factory rules, all built on one core.
- Outside the range of the data every method holds the first value before it and the last value after it (today linear and cubic spline evaluate to `0.0` there). This is the new default, also for the standalone model.
- The data is in the units of the quantity it drives, and x in the units of x in the model (time in the time unit of the model). Nothing is converted; the created elements take the units of their targets.
- The comp document references the original as an external model definition by default, `embed=True` copies it in.

## The core

`_write_interpolation(model, target, interpolator)` writes one data column as an assignment rule on the element `target` of a `libsbml.Model`. Standalone, in place and comp all go through it; it never creates or removes the target, its caller prepares it.

`Interpolator.formula()` keeps its name and returns the formula as an L3 string, every number written as the `repr` of its float, and `Interpolator.ast()` parses it once into the libsbml AST which the writers use; parsing cannot fail, x and the numbers are the only tokens and x is checked to be an SId. The AST holds every number exactly, the MathML libsbml writes keeps 15 significant digits of it (a limit of libsbml, not of the interpolation).

- constant: `piecewise(y0, x < x1, y1, x < x2, ..., yn)`, the value of the previous data point, `y0` before the data
- linear: `piecewise(y0, x < x0, y0 + m0*(x - x0), x < x1, ..., yn)`, `yn` after the data
- cubic spline: the natural spline per interval, `y0` before and `yn` after the data

The first column is x. `time` is the simulation time (the csymbol), any other name is the id of a quantity of the model the interpolation runs in.

The data is checked when the `Interpolation` is created and a violation raises a `ValueError` (today these are warnings and the model is written anyway):

- at least 2 columns
- at least 2 rows, at least 3 for the cubic spline
- no missing values
- no duplicate x values
- the name of the first column is an SId (it names x in the model)

The other columns are named freely when `targets` maps them to the ids they drive; where a column name is used as an id itself (the standalone model, `targets=None`) a name which is not an SId raises a `ValueError` there.

Data whose first column is not ascending is sorted, with a warning, as today.

## The standalone model

`Interpolation(data, method)`, `from_csv`, `from_tsv`, `write_sbml_to_file` and `write_sbml_to_string` keep their signatures. The model is written through the factory (`Document(model).create_sbml()`), SBML L3V2, every interpolated parameter with a port, so the model can be used as a submodel. The notes name the columns and the method; the notes with the copyright 2016-2020 and the author are removed.

`Interpolator` stays public. `Interpolation.create_interpolators` becomes the property `Interpolation.interpolators`, `Interpolation.add_interpolator_to_model` is removed: it deleted a parameter of the same id without asking.

## (A) In place: `Interpolation.drive`

```python
def drive(
    self,
    source: Path | str | libsbml.SBMLDocument,
    targets: Mapping[str, str] | None = None,
    filepath: Path | None = None,
) -> libsbml.SBMLDocument
```

- `source` is a path, an SBML string or a document. A document is changed in place and returned; a path or a string is read with `read_sbml` and the new document returned. `filepath` writes the result in addition. Level and version of the document are kept, SBML Level 2 and 3 are supported.
- `targets` maps a data column to the id of the element it drives; `None` means every column drives the element of its own id. A column which is not in the data or a target which is not in the model raises a `ValueError`.
- The target is a
  - parameter: set `constant=False`
  - species: set `constant=False` and `boundaryCondition=True`, so that it can stay a reactant or product. The data is its concentration, or its amount if it has only substance units, as an assignment rule on a species means in SBML.
  - compartment: set `constant=False`

  Any other element (a reaction, a species reference, ...) raises a `ValueError`.
- A target which already has an assignment rule, a rate rule, an algebraic rule (by the variable it determines) or an event assignment raises a `ValueError` naming it; the mechanism of the model is never replaced silently. An initial assignment of the target is removed, logged at info level, because SBML forbids it next to an assignment rule.
- x is `time` or the id of an element of the model; a missing x raises a `ValueError`.
- The target keeps its units.
- Only the model of the document is driven, for a hierarchical model the elements of its top model.
- The document is validated with `validate_doc` (reporting, never blocking, as `create_model`).

## (B) Through comp: `Interpolation.drive_comp`

```python
def drive_comp(
    self,
    source: Path | str | libsbml.SBMLDocument,
    targets: Mapping[str, str] | None = None,
    filepath: Path | None = None,
    embed: bool = False,
) -> libsbml.SBMLDocument
```

A new comp document (L3V1, or L3V2 when the original is L3V2) whose top model `<model id>_driven` has the original as the submodel `<model id>` and holds the assignment rules of the interpolation. After flattening the elements of the original are named `<model id>__<id>`, the replaced targets and x keep their ids.

- The original has to be SBML Level 3, comp is a Level 3 package; a Level 2 original raises a `ValueError` which names the conversion to Level 3 (`drive` in place supports Level 2).
- The original is referenced by an `ExternalModelDefinition`, so it is never touched. Its `source` is relative to the directory of `filepath`, so the two files can be moved together, and absolute when nothing is written; the location of the document is set to `filepath`, so the reference resolves for the document in memory as well. A string or a document has no file to reference and raises a `ValueError` unless `embed=True`.
- `embed=True` copies the model of the original into the document as a `ModelDefinition` and enables the packages the original document declares. A model which itself has comp content (submodels or model definitions) cannot be embedded and raises a `ValueError`; it is referenced externally.
- comp requires a replacement to have the SBML class of the element it replaces, except that anything with mathematical meaning may replace a parameter (rule comp-21201). The top model therefore holds a placeholder of the class of every target, which replaces the target of the original (`comp:replacedElement`):
  - parameter target: a parameter
  - species target: a species with the compartment, `hasOnlySubstanceUnits` and the units of the target, `boundaryCondition=True`, `constant=False`; its compartment is a placeholder compartment of the top model which is replaced *by* the compartment of the original (`comp:replacedBy`)
  - compartment target: a compartment with the spatial dimensions and the units of the target

  The assignment rule of the interpolation determines the placeholder.
- x other than `time` is a parameter of the top model which is replaced *by* x of the original, which is allowed for an x of any class.
- A reference to an element of the original goes through its port if the original declares one for it (`comp:portRef`), else by its id (`comp:idRef`).
- The placeholders take the units of their targets. The top model copies the unit definitions they use and the model units of the original (`timeUnits`, `substanceUnits`, `extentUnits`, `volumeUnits`, `areaUnits`, `lengthUnits`), so the replacements and the unit check agree.
- Conflicts as in place. An initial assignment of a target cannot be removed without touching the original: if it has a metaid it is deleted (`comp:deletion` by `comp:metaIdRef`), otherwise a `ValueError` points to `drive`.
- The document is validated; `filepath` writes it.

Flattening the document of `drive_comp` (`sbmlutils.comp.flatten_sbml`) gives the model of `drive`, up to the prefix of the ids of the original; the tests simulate both with roadrunner and compare the trajectories.

## The factory: `Interpolation.assignment_rules`

```python
def assignment_rules(self, targets: Mapping[str, str] | None = None) -> list[AssignmentRule]
```

returns the `AssignmentRule` objects of `sbmlutils.factory` of the interpolation, the formula as the L3 string of the same AST, so a model definition takes them with `model.rules += interpolation.assignment_rules(...)`. The targets are declared in the model definition, non constant and with their units, as the guide shows.

## Documentation

`docs/interpolation.md` is rewritten around the use cases: the standalone model; the methods, with the values held outside the data; driving a model in place; driving it through comp, with the ids after flattening; an interpolation in a model definition; and the contract: the data in the units of the target, a species driven in concentration or in amount as it declares, what is refused and why. Every code block runs against the package. `docs/api/data.interpolation.md` stays `::: sbmlutils.data.interpolation`.

## Examples

- `examples/interpolation/driving.py` (new): a small model of glucose uptake with an external glucose species is driven by a measured time course, in place and through comp; both are simulated with roadrunner and plotted against the data, the figure is written into the working directory.
- `examples/interpolation/pancreas.py` uses the new API; its dependency `atp_adp ~ glc`, where x is a quantity of the model, is the second driving example. Its plot draws every curve once (today twice, solid and dashed).
- `examples/interpolation/interpolation.py` stays the example of the methods.

## Tests

`tests/interpolation/`:

- the formulas of the three methods: through the data points, the values held before and after the data, the spline coefficients
- the data checks
- in place: a parameter, a species with and without only substance units, a compartment; time and a model quantity as x; every conflict; a missing x, column or target; a document changed in place; level 2
- comp: external and embedded; through a port and by id; a species target with its compartment; x a model quantity; an initial assignment with and without metaid; the relative `source`; an embedded hierarchical model refused
- the equivalence of in place and flattened comp, simulated with roadrunner
- the factory rules in a model created with `create_model`
- `examples.interpolation.driving` in `tests/examples/test_example_scripts.py`

## Release notes

In the notes of the next release (0.16.0, the removals are breaking):

- breaking: linear and cubic spline hold the end values outside the data instead of `0.0`; invalid data raises a `ValueError` instead of a warning; `add_interpolator_to_model` is removed and `create_interpolators` is the property `interpolators`; the standalone model is SBML L3V2
- new: `drive`, `drive_comp`, `assignment_rules`; the guide and the examples of driving a model with data (#16)

## Out of scope

- unit conversion of the data (pint)
- driving elements inside model definitions of a hierarchical model
- fitting a spline which does not go through the data points (smoothing)
