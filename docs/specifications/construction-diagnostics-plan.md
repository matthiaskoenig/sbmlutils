# Implementation plan

1. Reproduce automatic creation of a typo parameter through `create_model` and
   confirm the absence of structured diagnostics. Completed before changes.
2. Add immutable diagnostic values, a context-local grouped collector, and an
   exception snapshot. Instrument checked native failures and existing loss
   recorders without replacing current grouped logs.
3. Record implicit parameter creation for initial assignments and variable
   rules. In strict scope, leave the unknown symbol undeclared and reject the
   completed construction before writing.
4. Expose diagnostics and the opt-in strict flag through the factory. Document
   the distinction from serialized validation and the precise coverage limits.
5. Add public-path regression tests for losses, strict authoring, preservation
   of an existing destination, grouping, and nested/concurrent isolation.
6. Run targeted tests, then the offline suite, lint, formatting, type checking,
   and documentation build. Record actual results after implementation.

## Completed validation

Implemented steps 1-6 with permissive defaults and opt-in strict construction.

- Offline suite: 1,801 passed, 44 skipped, 1,819 deselected (48.33 seconds).
  Live network, slow, and SBML test-suite sweeps were excluded.
- Factory/validation suite: 399 passed on both the primary environment and
  Python 3.12 with minimum dependencies using current source.
- After the broad run, the final annotation preservation test brought the new
  regression file to 10 passing tests.
- Ruff lint and formatting, ty type checking, documentation build, and diff
  whitespace checks passed.
