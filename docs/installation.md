# Installation

`sbmlutils` requires python >= 3.11 and is available from [pypi](https://pypi.python.org/pypi/sbmlutils). It is tested on Linux, macOS and Windows.

## With uv

[uv](https://docs.astral.sh/uv/) is the recommended way to install the package. In a project it is added as a dependency, which resolves and locks it together with the rest of the environment:

```bash
uv add sbmlutils
```

Into an existing virtual environment it is installed through the pip interface of uv:

```bash
uv venv --python 3.14
uv pip install sbmlutils
```

## With pip

```bash
pip install sbmlutils
```

## Development version

The current state of the `develop` branch is installed directly from GitHub:

```bash
uv add "sbmlutils @ git+https://github.com/matthiaskoenig/sbmlutils.git@develop"
```

or, with pip,

```bash
pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop
```

To work on the repository itself, with the test and documentation tooling, see [Development](development.md).

## Optional dependencies

Two features need packages which are not installed with `sbmlutils`:

| feature | package | install |
| --- | --- | --- |
| [cobrapy models](fbc.md#cobrapy) (`sbmlutils.fbc.cobra`) | `cobra` | `pip install sbmlutils[cobra]` |
| [visualization](visualization.md) (`sbmlutils.cytoscape`) | a running [Cytoscape](https://cytoscape.org) | see the guide |

`py4cytoscape` itself is a dependency, but it needs a running Cytoscape instance to talk to.

## Logging

`sbmlutils` does not configure logging. It logs to loggers below the `sbmlutils` logger and leaves handlers, levels and formatting to the application, so the messages of the package stay under your control:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("sbmlutils").setLevel(logging.WARNING)
```

For scripts and interactive work the rich output of the package can be turned on explicitly:

```python
from sbmlutils import log

log.enable_rich_logging()
```
