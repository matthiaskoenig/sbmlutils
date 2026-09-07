# Validation

libsbml validates a document against the SBML specification and reports what it finds as a list of errors. `sbmlutils` runs those checks, groups the results and prints a report which says what is wrong and where.

## Validating a file

```python
from sbmlutils.io import validate_sbml

results = validate_sbml("model.xml")
print(results.error_count, results.warning_count, results.all_count)
print(results.is_valid())
```

`validate_sbml` accepts a path, an SBML string or an `SBMLDocument` and returns a `ValidationResult` with the errors and warnings and a count of each severity. `validate_doc` does the same for a document which is already read.

## Consistency checks

Which checks run is configured with `ValidationOptions`:

```python
from sbmlutils.validation import ValidationOptions

options = ValidationOptions(
    general_consistency=True,  # the SBML language constructs
    identifier_consistency=True,  # the identifiers used in the model
    units_consistency=True,  # the units of every quantity and formula
    mathml_consistency=True,  # the syntax of the MathML
    sbo_consistency=True,  # the SBO terms
    overdetermined_model=True,  # whether the model is overdetermined
    modeling_practice=True,  # style recommendations
    internal_consistency=True,  # the model as consistent XML
    log_errors=True,  # log what was found
)
```

Every check is on by default. The unit check is the expensive and the interesting one: it recomputes the units of every formula and reports where they do not add up. A model which is still being written is validated faster with `ValidationOptions(units_consistency=False)`.

`modeling_practice` reports style recommendations (an unset unit, a parameter which is never used) rather than errors, so it is the first one to turn off when the report gets noisy.

## While the model is created

`create_model` validates what it writes:

```python
from sbmlutils.factory import ValidationOptions, create_model

create_model(
    model=model,
    filepath="model.xml",
    validate=True,
    validation_options=ValidationOptions(units_consistency=False),
)
```

Validation reports, it does not block: the file is written either way, and the result tells you what to fix. `validate=False` skips the check.

## The report

The report of a validation lists the counts per category and then every message with its severity, its category, the line it is on and the explanation from the specification:

```
──────────────────────────────── Validate SBML ─────────────────────────────────
model.xml
valid                    : FALSE
validation error(s)      : 1
validation warnings(s)   : 0
    general              : True
    identifier           : True
    mathml               : True
    overdetermined       : True
    sbo                  : True
    units                : True
check time (s)           : 0.012
────────────────────────────────────────────────────────────────────────────────
```

The messages go through the logging of the package, so an application decides where they end up, see [Installation](installation.md#logging).

## Checking a libsbml call

`check` is the helper the package itself uses around libsbml calls, which return a status code instead of raising:

```python
from sbmlutils.validation import check

check(species.setId("glc"), "set id on species")
```

It returns `True` when the call succeeded and logs what failed otherwise.
