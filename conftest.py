"""Make the examples importable by the tests.

The examples are not part of the package, they live in `examples/` at the root
of the repository, see `examples/README.md`. pytest puts the directory of this
file on `sys.path`, so that `tests/examples/test_examples.py` can import the
model definitions of every example and check that they create a valid model.
"""
