# Examples

Runnable examples for sbmlutils. They are **not** part of the package: they are not installed with `pip install sbmlutils`, they are read and run from a checkout of the repository.

The examples simulate with [libroadrunner](https://libroadrunner.org) and plot with matplotlib, which are the `examples` extra of the package (`pip install sbmlutils[examples]`, or `uv sync --extra dev` in a checkout).

Every example is a module of the `examples` package, so it is run from the root of the repository with

```bash
python -m examples.species
python -m examples.tutorial.minimal_model
python -m examples.fbc.fbc_v2
```

An example writes the model it creates into the current working directory, and an example which plots writes the figure next to it. No example opens a window: matplotlib figures are saved to a file, never shown, so that the examples also run on a machine without a display.

## What is where

| path | content |
| --- | --- |
| `examples/*.py` | one SBML concept per module: species, parameters, reactions, units, notes, annotations, assignments, algebraic rules |
| `examples/tutorial/` | the models of the [model creation tutorial](https://matthiaskoenig.github.io/sbmlutils/creation/) |
| `examples/fbc/` | flux balance constraints (fbc), version 2 and 3 |
| `examples/distrib/` | distributions and uncertainties (distrib) |
| `examples/combine_archive/` | COMBINE archives (OMEX) built from a model |
| `examples/merge_models/` | merging models into a comp model |
| `examples/converters/` | conversion of an ode file to SBML and of a model into an ODE system |
| `examples/interpolation/` | interpolation of data points as an SBML model |
| `examples/demo/`, `examples/tiny/`, `examples/dallaman/`, `examples/icg/` | complete models, from a small demo to a whole body physiological model |

`examples/templates.py` holds the creators and the terms of use shared by the models.

## Tests

`tests/examples/test_examples.py` builds every model of `examples_models` and runs every script of `examples_create`, and `tests/examples/test_example_scripts.py` runs the examples which convert, merge, interpolate or simulate as `python -m examples.<module>` in a temporary working directory. An example which breaks fails the test suite.
