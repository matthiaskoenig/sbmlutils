# Development

Contributions are welcome. The repository is [matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils); development happens against the `develop` branch via pull requests.

## Setup development environment

Development needs [uv](https://docs.astral.sh/uv/) and a checkout of the repository:

```bash
git clone https://github.com/matthiaskoenig/sbmlutils.git
cd sbmlutils
```

A single sync creates the virtual environment in `.venv`, installs `sbmlutils` into it in editable mode and adds the complete tooling:

```bash
uv sync --extra dev
```

The `dev` extra contains everything used below, i.e., pytest, ruff, ty, tox, pre-commit, zensical and bump-my-version, so nothing has to be installed separately. The python version is taken from `.python-version` (currently 3.14); to work against the oldest supported version instead use `uv sync --extra dev --python 3.11`, which replaces the environment.

The tools are then run either with `uv run <command>`, which uses the environment without activating it, or from the activated environment:

```bash
source .venv/bin/activate        # Linux and macOS
.venv\Scripts\activate           # Windows
```

The commands in this document are written without the `uv run` prefix; prepend it if the environment is not activated.

The last step installs the git hook:

```bash
uv run pre-commit install          # install the hook, once per checkout
uv run pre-commit run --all-files  # check the current state of the repository
```

From now on every commit is checked with ruff (lint and format) and ty, i.e., the same checks that run in continuous integration. On a commit only the changed files are looked at, `--all-files` checks the whole repository and is what a newly added hook should be tried with.

## Testing

The tests are written with pytest, tox runs them against every supported python version.

The tox environments are named after the interpreter (`py3.11` to `py3.14`, see `envlist` in `tox.ini`), a single one is run with

```bash
tox r -e py3.14
```

and the complete matrix, including the `ty` environment, in parallel with

```bash
tox run-parallel
```

This needs the interpreters to be available, which uv installs with `uv python install 3.11 3.12 3.13 3.14`. Continuous integration runs the same environments as `uvx --with tox-uv tox -e py3.14`.

To run the tests directly against the development environment use

```bash
pytest                                          # the full suite
pytest tests/test_factory.py                    # a single module
pytest tests/test_factory.py::test_model_units  # a single test
```

The `conftest.py` at the root of the repository selects the non-interactive matplotlib backend for the session and puts the repository on `sys.path`, so that `tests/examples/` can import the examples.

Some tests are skipped unless what they need is there: the models of the [SBML test suite](https://github.com/sbmlteam/sbml-test-suite) and the biomodels archives are only present in a checkout, `tests/fbc/test_cobra.py` needs cobrapy (the `cobra` extra), and `tests/test_biomodels.py` queries the live BioModels service.

The downloads of `sbmlutils.biomodels` go through the retrying session of pymetadata, which retries the transient error responses (429, 500, 502, 503, 504) with an exponential backoff and times out after 30 seconds; `test_download_file_retries_transient_error` covers this against a local server and needs no network. What retrying cannot fix is a service which is unreachable or which refuses the request — BioModels answers the GitHub runners with `403 Forbidden` — so those tests probe the service first and are skipped rather than failed.

## Linting and formatting

Linting and formatting use [ruff](https://docs.astral.sh/ruff/):

```bash
ruff check     # lint
ruff format    # format
```

The model definitions of the examples are written against the names of `sbmlutils.factory`, which they import with a star import. This is the documented style, so `F403`/`F405` are ignored for `examples/` and `tests/` in `.ruff.toml` instead of globally.

## Type checking

Type checking is performed with [ty](https://docs.astral.sh/ty/):

```bash
tox r -e ty
```

Or directly in the working tree:

```bash
uvx ty check
```

The configuration lives in `[tool.ty]` in `pyproject.toml`. Warnings are treated as errors, so the codebase is kept free of diagnostics. Suppress an unavoidable diagnostic with a rule specific `# ty: ignore[rule-name]` rather than a blanket comment.

libsbml has no type stubs and creates its objects through a SWIG layer, so ty sees an untyped API. Annotate the libsbml objects (`doc: libsbml.SBMLDocument = ...`) and use the explicit getters (`getVariable()`) rather than the attributes the SWIG layer synthesizes (`variable`), which the type checker cannot see.

## Examples

The examples are runnable scripts in `examples/`, they are not part of the package. They are run as modules from the root of the repository:

```bash
python -m examples.species
python -m examples.tutorial.minimal_model
```

An example writes what it creates into the current working directory and never opens a window: a plotting example saves its figure to a file. `tests/examples/` builds every model definition and runs the example scripts in a temporary directory, so a broken example fails the test suite. See `examples/README.md`.

## Documentation

The documentation is built with [Zensical](https://zensical.org/), the static site generator of the Material for MkDocs authors. The sources are markdown files in `docs/`, the site is configured in `zensical.toml` in the repository root. Nothing rendered is committed: the site is built by the `documentation` workflow on every push and published to [matthiaskoenig.github.io/sbmlutils](https://matthiaskoenig.github.io/sbmlutils) from the `develop` branch.

Build the site into `site/`:

```bash
uv run zensical build --clean
```

For writing, the preview rebuilds on save:

```bash
uv run zensical serve
```

The API reference is rendered from the docstrings by [mkdocstrings](https://mkdocstrings.github.io/); a page in `docs/api/` only contains the module directive:

```markdown
# factory

::: sbmlutils.factory
```

Docstrings are therefore the place to document functions and classes, the markdown files provide the narrative around them. Adding a module to the reference means adding such a page and an entry to `nav` in `zensical.toml`.

### Files for agents { #files-for-agents }

Agents and language models read markdown, not rendered html. `scripts/llms_txt.py` writes the files of the [llms.txt convention](https://llmstxt.org/) into the built site, i.e., [llms.txt](https://matthiaskoenig.github.io/sbmlutils/llms.txt) as an annotated index of all pages, [llms-full.txt](https://matthiaskoenig.github.io/sbmlutils/llms-full.txt) with the complete documentation in a single file, and the markdown of every page next to its html (`/creation.md` for `/creation/`). The markdown of the API reference is generated from the docstrings with `inspect`, since the pages themselves only contain the mkdocstrings directive.

```bash
uv run zensical build --clean
uv run python scripts/llms_txt.py
```

The `documentation` workflow runs both steps, so the files are regenerated with every push. `docs/robots.txt` points crawlers at the sitemap and at these files. Zensical will provide agent context files itself at some point, then this script can go.

## Release

A release is made from `develop`:

1. write the release notes for the version in `release-notes/`
2. make sure everything passes: `tox run-parallel`, `ruff check`, `tox r -e ty`
3. check the version bump: `uvx bump-my-version bump [major|minor|patch] --dry-run -vv`
4. bump the version: `uvx bump-my-version bump [major|minor|patch]`, which updates `src/sbmlutils/__init__.py` and `CITATION.cff`, commits and tags
5. `git push --tags`, which triggers the release workflow publishing to [pypi](https://pypi.org/project/sbmlutils/), followed by `git push`
6. test the installation from pypi in a fresh environment:

    ```bash
    uv venv --python 3.14
    uv pip install sbmlutils
    ```

7. once Zenodo has archived the release, update the citation information, i.e., `date-released` in `CITATION.cff` and the version, date and version DOI of the release in the citation of `README.md` and `docs/index.md`. `bump-my-version` only updates the version, not the date and the DOI, which are only known after the release
