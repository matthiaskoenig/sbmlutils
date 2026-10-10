# Round-trip preservation diagnostics

## Contract

`sbml_to_model` continues to return a `Model`. Its read-only
`preservation_diagnostics` tuple reports known content losses separately from
construction and serialized-document validation. Findings use the existing
immutable diagnostic structure (code, severity, message, count, example) and
retain no native objects. Repeated causes are grouped within one parse.

`sbml_to_model(..., strict_preservation=True)` raises `PreservationError` with the
findings rather than returning a model with known losses. In default mode the
parser returns the supported content as before.

`create_model(..., strict_preservation=True)` rejects a model carrying known
parser losses before writing. `FactoryResult.preservation_diagnostics` exposes
those losses even in default mode. Merging models carries findings from every
input. Construction strictness and serialized SBML validation remain independent.

Coverage includes model history, unsupported package elements, document-level
metadata, custom non-RDF annotation children, existing reported parser drops,
FBC association-node metadata and unsupported secondary variables, comp
substance conversion factors, and reserved mathematical symbol ambiguity.
Empty unsupported package declarations alone are not reported as content loss.
This is a known-loss detector, not an exhaustive structural equivalence proof;
unknown XML discarded by libSBML and arbitrary RDF outside extracted CVTerms
are outside its coverage. The source document is never overwritten by parsing.

## Implementation plan

1. Reproduce a groups loss through public parse/create APIs before editing.
2. Add the immutable exception snapshot and model/result preservation fields.
3. Perform a linear preflight traversal and instrument existing parser drops.
4. Isolate diagnostic collection per parse; reject strict parse losses after
   collection and strict write losses before document construction.
5. Verify groups/layout/history/annotation cases, core controls, count grouping,
   merged inputs, and overwrite protection; run offline tests and tooling.

## Completed verification

- Original public-path reproduction lost a groups definition without structured
  findings. The implemented parser reports it; strict writing preserves the
  existing destination.
- Offline suite: 1,809 passed, 44 skipped, 1,819 deselected in 42.90 seconds.
  Live network, slow, and full SBML test-suite sweeps were excluded.
- Parser/round-trip targeted suite: 531 passed. Factory targeted suite: 350
  passed. Minimum-dependency parser/factory suite: 454 passed.
- Final preservation regression file: 9 passed on primary and minimum-dependency
  environments, including the association and math tests added after the broad run.
- Ruff lint and formatting, ty, documentation build, and whitespace checks pass.
- Synthetic 10,000-parameter parse: median 0.1522 seconds with the scan disabled
  versus 0.1682 seconds enabled (three timed runs after warmup in this environment).
  This is an overhead measurement, not a general performance guarantee.
