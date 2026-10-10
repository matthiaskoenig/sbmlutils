# Validation

libsbml validates a document against the SBML specification and reports what it finds as a list of errors. `sbmlutils` runs those checks, groups the results and logs a report which says what is wrong and where.

## Validating a file

```python
from sbmlutils.io import validate_sbml

results = validate_sbml("model.xml")
print(results.error_count, results.warning_count, results.all_count)
print(results.is_valid())
```

`validate_sbml` accepts a path or an SBML string and returns a `ValidationResult` with the errors and warnings and a count of each severity. Validation reports, it never raises for the content: a source which cannot be read as SBML, e.g. malformed XML, gives a result with the read errors. Only a path which does not exist raises a `FileNotFoundError`. `validate_doc` does the same for an `SBMLDocument` which is already read.

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

`ValidationOptions.fast()` disables only unit analysis and keeps the structural,
identifier and other checks enabled. Use the default options for comprehensive
validation before sharing or simulating a model. Unit analysis can allocate much
more memory than reading the model itself.

`modeling_practice` reports style recommendations (an unset unit, a parameter which is never used) rather than errors, so it is the first one to turn off when the report gets noisy.

## While the model is created

`create_model` validates what it writes:

```python
from sbmlutils.factory import ValidationOptions, create_model

result = create_model(
    model=model,
    filepath="model.xml",
    validate=True,
    validation_options=ValidationOptions(units_consistency=False),
)
```

The final file is validated after any spreadsheet annotations are applied.
Validation reports, it does not block by default: the file is written either way,
and `result.validation` contains the errors and warnings. `validate=False` skips
the check and leaves `result.validation` as `None`.

Pass `raise_on_error=True` to `create_model` to raise `SBMLValidationError` (a
`ValueError` subclass from `sbmlutils.validation`) when the final file has errors.
The exception's `result` contains the findings without another validation.
This also enables validation if `validate=False` was
passed. The written file remains available for diagnosis; optional Antimony and
Markdown exports are not created on validation failure.

## The report

The report of a validation lists the counts per category and then every message with its severity, its category, the line it is on and the explanation from the specification. It is logged on the `sbmlutils` loggers and nothing is shown unless logging is configured, see [Installation](installation.md#logging). With `log.enable_rich_logging()` a report looks like this:

```
ERROR    Validate SBML                                         validation.py:542
         <SBMLDocument>
         valid                    : FALSE
         validation error(s)      : 2
         validation warnings(s)   : 0
             general              : True
             identifier           : True
             mathml               : True
             overdetermined       : True
             sbo                  : True
             units                : True
         check time (s)           : 0.000
ERROR    E0: SBML component consistency (core, L2, code)       validation.py:391
         [Error] The presence of a species requires a compartment
         If a model defines any species, then the model must also define at least
         one compartment.
         Reference: L3V2 Section 4.6.3
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

## Structured construction diagnostics

`create_model` returns construction findings in `FactoryResult.diagnostics`,
including when `validate=False`. These immutable, grouped findings have `code`,
`severity`, `message`, `count`, and one `example`. They describe reported input
losses and implicit parameter creation separately from final SBML validation.

```python
result = create_model(model, filepath, validate=False)
for finding in result.diagnostics:
    print(finding.code, finding.count, finding.message, finding.example)
```

Use `strict=True` to reject reported construction losses, failed checked libSBML
operations, and unknown initial-assignment or assignment/rate-rule targets before
writing. Declare the target parameter explicitly in strict mode. The default
still creates it automatically. `ConstructionError`, imported from
`sbmlutils.validation`, carries a `diagnostics` tuple. A construction rejection
preserves any existing destination and skips optional exports.

`strict=True` and `raise_on_error=True` serve independent purposes: combine them
to reject construction findings and validate the serialized final model.
Validation failures can still leave the written file for diagnosis. Informational
annotation canonicalization fallback retains the original resource and does not
cause strict rejection. Diagnostics cover existing instrumented writers, rather
than all possible parser round-trip losses or arbitrary native calls.

The stable codes are `unsupported_attribute`, `unwritten_attribute`,
`unsupported_content`, `libsbml_operation_failed`, `implicit_parameter`, and
`annotation_resource_fallback`. Missing optional authoring metadata and existing
constant-parameter advice remain log messages, without rejecting strict creation.
