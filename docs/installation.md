# Installation

`sbmlutils` requires python >= 3.12 and is available from [pypi](https://pypi.python.org/pypi/sbmlutils). It is tested on Linux, macOS and Windows.

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

## Extras

`sbmlutils` reads, writes, annotates and validates models; it neither simulates nor plots, so the packages for that are not installed with it. The `examples` extra adds what the runnable examples need.

| extra | install | what it adds |
| --- | --- | --- |
| `examples` | `pip install sbmlutils[examples]` | `libroadrunner` and `matplotlib`, which the [examples](https://github.com/matthiaskoenig/sbmlutils/tree/develop/examples) simulate and plot with |

Install the development environment and runnable example dependencies together with `uv sync --extra dev`. See [Development](development.md).

The COBRApy integration and interpolation API have been removed. See [Migration](migration.md) for the affected imports and alternatives.

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
