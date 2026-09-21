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

## What writing a model reports

Validation judges the document which was written. Writing it reports what libsbml would not take, which no validation of the result can show, because what is not in the file cannot be found in it:

- **A value libsbml refuses** is an error naming the element, the attribute and the value, e.g. a charge which is not a whole number in an fbc version 2 document.
- **An attribute the document has no place for** - one which the SBML level and version, or the version of the package, does not have at all - is one warning per kind of element and attribute, with the count, an example and what to write instead, see [Reading and writing](io.md#round-tripping). One decision fixes all of them, so it is reported once rather than per element; the detail of each element is logged at debug. An attribute libsbml writes into no document, the core `id` and `name` of a comp reference, is reported the same way and without advice, see [Model composition](comp.md#what-round-trips).
- **Content the document cannot carry** - the key value pairs and the user defined constraints of fbc version 3 in an fbc version 2 document, or in one which declares no fbc - is one error per kind of content, with how many pieces on how many elements, an example and the version to declare. Declaring fbc version 3 keeps all of them at once, so this too is reported once rather than per element.
- **An annotation resource which is written as given** is one warning per collection, see [Annotations](annotations.md#resources-which-are-written-as-given).

Writing a model definition also gives advice on the definition itself, which is not repeated for a model which was parsed from a file:

- **A parameter or compartment which is `constant=False` and never changed** is one warning per kind of element, with every id. Changing a value takes an assignment rule, a rate rule, an algebraic rule, an event assignment or, for a parameter, a user defined constraint of fbc which names it as a variable; an initial assignment does not count. An element of the comp interface - one with a port, or one which replaces an element of a submodel or is replaced by one - is left out, because what changes it can live in another model. The usual cause is a rule which was forgotten or a target which was misspelled.

## Checking a libsbml call

`check` is the helper the package itself uses around libsbml calls, which return a status code instead of raising:

```python
from sbmlutils.validation import check

check(species.setId("glc"), "set id on species")
```

It returns `True` when the call succeeded and logs what failed otherwise.
