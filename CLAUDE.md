# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project

`sbmlutils` is a python library for models in the Systems Biology Markup Language (SBML), built on
libsbml: model creation from a python definition, annotation, validation, reports, converters and
support for the `comp`, `fbc`, `distrib` and `layout` packages. Pure library, no CLI entry points.
Requires python >= 3.11, packaged with hatchling (version is read from `src/sbmlutils/__init__.py`).
Runtime dependencies are `python-libsbml`, `antimony` and `libroadrunner` (SBML and simulation),
`pymetadata` (annotations and COMBINE archives), `pydantic`, `pint`, `numpy`, `pandas`, `rich`,
`lxml`, `jinja2`, `markdown-it-py`, `xmltodict`, `openpyxl`, `matplotlib`, `requests` and
`py4cytoscape`. `cobra` is the optional `cobra` extra.

## Commands

```bash
# environment (uv based)
uv sync --extra dev
uv run pre-commit install

# tests
pytest                                        # all tests
pytest tests/test_factory.py                  # single file
pytest tests/test_factory.py::test_model_units  # single test
tox r -e py3.14                               # single tox env (py3.11-3.14 available)
tox run-parallel                              # full matrix + ty

# lint / format / types
ruff check
ruff format
tox -e ty                       # ty type check (config in [tool.ty] in pyproject.toml)
uvx ty check                    # same check, straight from the working tree

# examples, they are modules of the `examples` package and not part of sbmlutils
python -m examples.species
python -m examples.tutorial.minimal_model
```

Release steps are in `docs/development.md` (there is no separate `RELEASE.md`); version bumps go
through `uvx bump-my-version bump [major|minor|patch]` (updates `src/sbmlutils/__init__.py` and
`CITATION.cff`), and pushing the tag triggers the PyPI release workflow.

Documentation is [Zensical](https://zensical.org/): markdown sources in `docs/`, configured in
`zensical.toml`, built into the gitignored `site/` (`uv run zensical build --clean`,
`uv run zensical serve` for the preview). The API reference is rendered from the docstrings by
mkdocstrings; a page in `docs/api/` is just `::: sbmlutils.<module>`, so nothing is generated into
the repository. `scripts/llms_txt.py` runs after the build and writes the agent facing files
(`llms.txt`, `llms-full.txt` and the markdown of every page) into `site/`. The `documentation`
workflow runs both and publishes the site from `develop`.

## Architecture

**`factory.py` — the model definition.** The main module, 3700 lines and the entry point of the
package. A model is a `Model` holding `Compartment`, `Species`, `Parameter`, `Reaction`, rule, event
and package objects; `create_model(model, filepath)` walks them, calls `create_sbml` on each and
writes the validated SBML. Every element derives from `Sbase`, which carries `sid`, `name`,
`metaId`, `sboTerm`, `notes`, `annotations`, `port`, `uncertainties` and `keyValuePairs`, and
implements the two-step creation: `create_sbml(model)` creates the libsbml object, `_set_fields`
sets the attributes on it. `Sbase._set_fields` declares both parameters as `Any` on purpose: every
concrete subclass narrows the created object to the one libsbml type it creates, and only a
`Document` is set without a model, so a precise base signature would make every override an LSP
violation. Annotations are accepted as a `Sequence` (covariant) and stored as a `list`, so a model
definition can pass its natural `list[tuple[BQB, str]]` and still append afterwards. `Units` is the
base of the unit class of a model: a `UnitDefinition` parses an expression like `mmole/min/l` with
pint and writes the SBML unit definition; the id of a definition must not be an SBML base unit kind
(`UnitDefinition("litre")` is invalid, `UnitDefinition("l", "liter")` is not).

**`io/sbml.py`, `validation.py` — reading, writing, checking.** `read_sbml` accepts a path, an SBML
string or a URL, `write_sbml` writes a file or returns the string. `validate_sbml`/`validate_doc`
run the libsbml consistency checks configured by `ValidationOptions` (all on by default, the unit
check is the expensive one) and return a `ValidationResult` with the errors and warnings. Validation
reports, it never blocks: `create_model` writes the file either way. `check()` wraps a libsbml call,
which returns a status code instead of raising.

**`parser.py` — the inverse direction.** `sbml_to_model` reads an SBML file back into the `Model` of
`factory.py`, `antimony_to_sbml`/`antimony_to_model` do the same for antimony.

**`report/sbmlinfo.py` — the content of a model.** `SBMLDocumentInfo` walks a document and produces
the dictionary the sbml4humans report renders: every element with its equation as a readable string,
its math as latex (`report/mathml.py`), its unit as `mmol/min/l` (`report/units.py`) and its
annotations. Every element gets a primary key which is cached on the libsbml object, so the report
can link between elements. The frontend and the http api which serve this live in
[matthiaskoenig/sbml4humans](https://github.com/matthiaskoenig/sbml4humans), they were moved out of
this repository in 0.10.0; `report/sbmlreport.py` stays, it is the client which opens a model on
sbml4humans.de.

**`comp/`, `fbc/`, `layout/`, `manipulation/` — the packages.** `comp.flatten_sbml` resolves the
submodels of a hierarchical model into a flat one (it changes the working directory, since libsbml
resolves external model definitions relative to the file). `manipulation.merge_models` combines
several models into one comp model, which is what `create_model` does with several definitions.
`fbc/cobra.py` is the bridge to cobrapy, which is optional and therefore imported in a
`try`/`except`, with `cobra = None` as the fallback the tests skip on.

**`converters/` — SBML into something else.** `odefac.SBML2ODE` derives the ODE system and renders
it as python, R, julia, markdown or latex through the jinja2 templates in `resources/converters/`;
`xpp.py` converts XPP/XPPAUT ode files to SBML; `copasi.py` writes the ids into the names.
`mathml.py` evaluates MathML with a star import of `math`, which is why it is exempt from `F403`.

**`data/interpolation.py`** turns a table of data points into an SBML model whose assignment rules
evaluate a constant, linear or cubic spline interpolation.

`console.py` (rich console, for scripts and examples) and `log.py` provide the shared
output/logging. Modules get their logger from the standard library with
`logging.getLogger(__name__)`. The package never configures logging: no handlers, no levels, only a
`NullHandler` on the `sbmlutils` logger; `log.enable_rich_logging()` is the opt-in for scripts.
Library code logs, it does not print, and log calls use lazy `%s` formatting rather than f-strings
(enforced by ruff `G`).

## Conventions

- Type checking is done with [ty](https://docs.astral.sh/ty/) (mypy was removed in 0.10.0).
  `[tool.ty.terminal] error-on-warning = true` means warnings fail the check, so the tree must stay
  at zero diagnostics; the checked python version is inferred from `project.requires-python`.
  Suppress a diagnostic with a rule-specific `# ty: ignore[rule-name]`, never a blanket
  `# type: ignore`. ty also runs as a pre-commit hook (`--extra dev`).
- libsbml has no type stubs and builds its objects through SWIG, so annotate the libsbml objects
  explicitly and use the getters (`getVariable()`) rather than the attributes SWIG synthesizes
  (`variable`), which the type checker cannot see.
- Every module, class and function carries full type annotations and a docstring. New docstrings are
  google style, older ones still use the `:param:` form.
- `examples/` at the top level holds the runnable examples, they are not part of the package and are
  run as modules (`python -m examples.species`). A model definition imports the names of
  `sbmlutils.factory` with a star import, which is the documented style, so `F403`/`F405` are
  ignored for `examples/` and `tests/`. An example writes into the current working directory and
  never opens a window: a plotting example saves its figure to a file, and the `conftest.py` at the
  root selects the `Agg` backend for the test session.
- Test fixtures and the packaged models live in `src/sbmlutils/resources/`; `resources/__init__.py`
  names them. `API_EXAMPLES_MODEL` and `API_EXAMPLES_OMEX` are used by the sbml4humans api.
- Release notes go in `release-notes/` as part of a release commit.
