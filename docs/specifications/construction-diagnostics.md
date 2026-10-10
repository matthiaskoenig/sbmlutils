# Construction diagnostics and strict authoring

## Problem and scope

A valid serialized SBML document can omit requested attributes or content.
Today the factory logs these losses and silently creates parameters for unknown
rule and initial-assignment targets. Callers cannot inspect construction losses
in `FactoryResult`. This specification covers construction diagnostics and strict
authoring, the first two priorities of the review. Parser round-trip preservation,
optional dependency extras, and broader performance budgets are separate work.

## Contract

- `FactoryResult.diagnostics` is an immutable tuple of structured findings,
  independent of final SBML validation and available even with `validate=False`.
- Each finding has a stable code, severity, message, count, and one example.
  Repeated losses with the same cause are grouped to avoid per-element memory
  growth. Findings retain strings and integers, never native SBML objects.
- Capture existing unsupported attributes, unwritten attributes, unsupported
  content, failed checked libSBML operations, annotation canonicalization
  fallback, and automatic creation of assignment/rule parameters.
- Existing logging and permissive behavior remain the defaults.
- `create_model(strict=True)` rejects construction losses, failed checked
  operations, and undeclared initial-assignment/assignment-rule/rate-rule targets.
  It raises `ConstructionError` carrying the diagnostics before writing SBML or
  optional exports. An existing destination remains untouched on this rejection.
- Annotation canonicalization fallback is informational: the original resource
  is retained, so this alone does not reject strict construction.
- Strict construction and `raise_on_error` are independent. The latter validates
  final serialized SBML, and may leave an invalid file for diagnosis as before.
- Context-local collection isolates concurrent and nested creation. Collection
  is opt-in outside `create_model`; direct element creation keeps its API.

## Limits

Diagnostics cover instrumented construction operations, not arbitrary native
calls or every possible parser round-trip loss. Strict construction does not
replace SBML validation or guarantee every requested entity is preserved.
Invalid formulas or duplicate targets that already raise keep their exceptions.

## Acceptance

Public creation tests reproduce losses and typo targets, inspect structured
results, and prove strict rejection does not overwrite a destination. Known
symbols succeed in strict mode; permissive unknown targets still create
parameters. Group counts and context isolation are tested independently.
