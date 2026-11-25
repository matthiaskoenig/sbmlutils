# Validation

libsbml validates a document against the SBML specification and reports what it finds as a list of errors. `sbmlutils` runs those checks, groups the results and prints a report which says what is wrong and where.

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
    comp_flat_model=True,  # the flat model of a comp document
    log_errors=True,  # print every finding, not only the table
    max_findings_per_error=10,  # findings printed per error id, None for all
)
```

Every check is on by default. The unit check is the expensive and the interesting one: it recomputes the units of every formula and reports where they do not add up. A model which is still being written is validated faster with `ValidationOptions(units_consistency=False)`.

`ValidationOptions.fast()` disables only unit analysis and keeps the structural,
identifier and other checks enabled. Use the default options for comprehensive
validation before sharing or simulating a model. Unit analysis can allocate much
more memory than reading the model itself.

`modeling_practice` reports style recommendations (an unset unit, a parameter which is never used) rather than errors, so it is the first one to turn off when the report gets noisy.

libsbml validates a comp document by checking every model definition and then flattening a copy of the document and checking the flat model, which it reports as `CompFlatModelNotValid` followed by the errors of the flat model. A workflow which flattens the model with `flatten_sbml` and validates the flat model anyway skips the second check of it with `ValidationOptions(comp_flat_model=False)`, which takes about a sixth off the validation of a comp model with many model definitions.

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

The report is output: it is printed on the rich console of the package, see [Installation](installation.md#output-and-logging), and nothing about it is logged. A model without findings is one line, with the file which was validated and the time the checks took:

```
valid /home/user/models/model.xml  0.004 s
```

A model with findings gets a full report: a rule, the file, the status with the counts and the checks which were disabled, then every finding with its index, severity, error id, category, package and position, the short message in the color of its severity and the explanation of the specification below it. Where the findings repeat an error id, the table of the findings grouped by error id closes the report, so that the one fix for two thousand identical warnings is visible at a glance:

```
────────────────────────────────── Validate SBML ──────────────────────────────────
/home/user/models/model.xml
invalid: 62 error(s), 0 warning(s), checked in 0.001 s
E0 Error 99508 SBML unit consistency (core, line 5, column 6)
    Unable to verify consistency of units: encountered a model entity with no declared units
    In situations where a mathematical expression refers to a compartment, species or
    parameter, it is necessary to know the units of the object to establish unit consistency.
    ...
E3 Error 20702 SBML unit consistency (core, line 8, column 6)
    No units defined for the parameter
    If the attribute 'units' on a given Parameter object has not been set, then the unit of
    measurement associated with that parameter's value is undefined.
    Reference: L3V2 Section 4.7.3
    The <parameter> with id 'p0' does not have a 'units' attribute.
30 further finding(s) 99508 (Unable to verify consistency of units: ...) are not shown, they are in the ValidationResult.
29 further finding(s) 20702 (No units defined for the parameter) are not shown, they are in the ValidationResult.
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ severity ┃    id ┃ package ┃ count ┃ message                             ┃ lines                 ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Error    │ 99508 │ core    │    31 │ Unable to verify consistency of     │ 5, 8, 9, 10, 11, ...  │
│          │       │         │       │ units: encountered a model entity   │                       │
│          │       │         │       │ with no declared units              │                       │
│ Error    │ 20702 │ core    │    30 │ No units defined for the parameter  │ 8, 9, 10, 11, 12, ... │
│ Error    │ 20518 │ core    │     1 │ No units defined for Compartment    │ 5                     │
│          │       │         │       │ object                              │                       │
└──────────┴───────┴─────────┴───────┴─────────────────────────────────────┴───────────────────────┘
```

A large model easily repeats one finding on every element, so at most `ValidationOptions.max_findings_per_error` findings with the same error id are printed one by one (10 by default, `None` prints all of them), and the rest of each id is summarized in one line. `log_errors=False` prints only the status and the table. The `ValidationResult` always holds every finding, and prints them again on demand:

```python
from sbmlutils.console import console, quiet

with quiet():  # validate without printing
    result = validate_sbml("model.xml")

console.print(result)  # the table of the findings grouped by error id
result.show(max_per_error=3)  # the findings, colored by their severity
for group in result.groups():
    console.print(group.error_id, group.count, group.short_message)
```

`finding_text` renders a single finding the same way, e.g. one of the error log of a document read with libsbml.

## What writing a model reports

Validation judges the document which was written. Writing it reports what libsbml would not take, which no validation of the result can show, because what is not in the file cannot be found in it. These are problems, so they are logged as warnings and errors on the `sbmlutils` loggers rather than printed, see [Installation](installation.md#output-and-logging):

- **A value libsbml refuses** is an error naming the element, the attribute and the value, e.g. a charge which is not a whole number in an fbc version 2 document.
- **A formula which does not parse** is an error naming the formula, the element it belongs to (e.g. `<kineticLaw> of 'R1'`) and the reason of the libsbml parser. The element is written without math and the finding is recorded as the diagnostic `math_parse_failed`, so `strict=True` rejects the model before anything is written.
- **An attribute the document has no place for** - one which the SBML level and version, or the version of the package, does not have at all - is one warning per kind of element and attribute, with the count, an example and what to write instead, see [Reading and writing](io.md#round-tripping). One decision fixes all of them, so it is reported once rather than per element; the detail of each element is logged at debug. An attribute libsbml writes into no document, the core `id` and `name` of a comp reference, is reported the same way and without advice, see [Model composition](comp.md#what-round-trips).
- **Content the document cannot carry** - the key value pairs and the user defined constraints of fbc version 3 in an fbc version 2 document, or in one which declares no fbc - is one error per kind of content, with how many pieces on how many elements, an example and the version to declare. Declaring fbc version 3 keeps all of them at once, so this too is reported once rather than per element.
- **An annotation resource which is written as given** is one warning per collection, see [Annotations](annotations.md#resources-which-are-written-as-given).

Writing a model definition also gives advice on the definition itself, which is not repeated for a model which was parsed from a file:

- **An element without a `name` or an `sboTerm`** is hinted at once per element class, with the count and the first ids, e.g. `'name' should be set on 2000 Species elements: 'S0', 'S1', 'S2', 'S3', 'S4' and 1995 more`. A single element is named in full.
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
