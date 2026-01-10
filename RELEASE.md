# Release information

## make release
* update release notes in `release-notes` with commit
* make sure all tests run (`tox -p`)
* check formating and linting (`ruff check`)
* test bump version (`uvx bump-my-version bump [major|minor|patch] --dry-run -vv`)
* bump version (`uvx bump-my-version bump [major|minor|patch]`)
* `git push --tags` (triggers release)
* `git push`
* test installation in virtualenv from pypi
```bash
uv venv --python 3.14
uv pip install sbmlutils
```

# Install development dependencies:
```bash
# install core dependencies
uv sync
# install dev dependencies
uv pip install -r pyproject.toml --extra dev
# install test dependencies
uv pip install -r pyproject.toml --extra test
# install tox testing
uv tool install tox --with tox-uv
```

## Testing
See information on https://github.com/tox-dev/tox-uv
Run single tox target
```bash
tox r -e py312
```
Run all tests in parallel
```bash
tox run-parallel
```

# Setup pre-commit
```bash
uv pip install pre-commit
pre-commit install
pre-commit run
```
