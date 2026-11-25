"""The rich console the package prints its output on.

`sbmlutils` separates **output** from **logging**:

- Output is what a user asked to see: the files `create_model` writes, the
  report of a validation with its findings, the summary of a flattening, a
  download. It is printed on `console`, the rich console of this module, with
  colors, tables and links.
- Logging is for tracing problems and for debugging: a warning about content
  which is lost or a definition which should be fixed, the error of a libsbml
  call which failed, and debug detail. It goes to the standard `logging`
  module and is configured by the application, see `sbmlutils.log`.

The console prints to standard output. Silence it for a block of code with
`quiet`, or for the whole program by setting `console.quiet = True`:

```python
from sbmlutils.console import console, quiet

with quiet():
    create_model(model, filepath="model.xml")

console.quiet = True
```

Scripts and examples print on the same console, so their output and the
output of the package look the same:

```python
from sbmlutils.console import console

console.print(model)
console.rule("Section", style="white")
```

Importing this module has no side effects on the interpreter. To get rich
representations in an interactive session, install them explicitly with
`rich.pretty.install()`.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.theme import Theme

custom_theme = Theme(
    {
        "success": "green",
        "info": "blue",
        "warning": "orange3",
        "error": "red",
    }
)

#: the console the package prints its output on
console = Console(theme=custom_theme, log_time=False)


@contextmanager
def quiet() -> Generator[None]:
    """Suppress the output of the package inside the context.

    Logging is not affected, warnings and errors are still logged. The
    console is shared by every thread, so the output of another thread is
    suppressed as well while the context is active.

    Yields:
        None
    """
    previous = console.quiet
    console.quiet = True
    try:
        yield
    finally:
        console.quiet = previous


def path_text(path: Path | str) -> Text:
    """Get a path as text which a terminal shows as a link to the file.

    Args:
        path: the path of a file, relative paths are resolved

    Returns:
        the path as it was given, linked to the absolute file URI
    """
    try:
        uri = Path(path).resolve().as_uri()
    except ValueError:
        return Text(str(path))
    return Text(str(path), style=Style(link=uri))
