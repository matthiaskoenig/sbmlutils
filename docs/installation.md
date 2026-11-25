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

## Output and logging

`sbmlutils` keeps what you asked to see apart from what helps to trace a problem.

**Output is printed.** The files `create_model` writes, the report of a validation with its findings, the summary of a flattening or a download are printed on the rich console of the package, `sbmlutils.console.console`, with colors, tables and links to the files. Writing a model prints, e.g.:

```
SBML written to glucose_uptake.xml  model 'glucose_uptake', 0.03 s
valid /home/user/models/glucose_uptake.xml  0.004 s
```

Silence the output for a block of code with `quiet`, or for the whole program with `console.quiet`:

```python
from sbmlutils.console import console, quiet

with quiet():
    create_model(model, filepath="model.xml")

console.quiet = True  # nothing is printed from here on
```

Results have a rich representation of their own, which prints them on any rich console: `console.print(result.validation)` shows the findings of a validation as a table grouped by error id.

```python
from sbmlutils.console import console

result = create_model(model, filepath="model.xml")
console.print(result.validation)
```

**Logging is for problems.** Warnings about content which is lost or a definition which should be fixed, such as a missing `name` or a unit which has no place in the document, and the errors of libsbml calls which failed, go to the standard `logging` module, below the `sbmlutils` logger; debug detail goes there too, and the package logs nothing at `INFO`. `sbmlutils` does not configure logging, it leaves handlers, levels and formatting to the application:

```python
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("sbmlutils").setLevel(logging.ERROR)  # hide the warnings
```

For scripts and interactive work the warnings can be shown on the rich console, next to the output, colored by their level:

```python
from sbmlutils import log

log.enable_rich_logging()
```

Warnings which repeat on many elements are logged once per kind with a count, so even a model with thousands of elements gives a few readable lines, see [How it works](architecture.md#output-and-reporting).
