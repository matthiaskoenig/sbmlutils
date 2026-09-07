"""Test session configuration.

Two things are set up for the whole test session:

- **matplotlib never opens a window.** The `Agg` backend is selected before
  pyplot is imported anywhere, so a figure created by an example or by a test
  is rendered into a buffer instead of into a window. Without it a test which
  plots blocks on a machine with a display and fails on one without.
- **the examples are importable.** They are not part of the package, they live
  in `examples/` at the root of the repository, see `examples/README.md`.
  pytest puts the directory of this file on `sys.path`, so that
  `tests/examples/test_examples.py` can import the model definition of every
  example and check that it creates a valid model.
"""

import matplotlib

matplotlib.use("Agg", force=True)
