"""Logging of the package, for tracing problems and debugging.

`sbmlutils` separates output from logging, see `sbmlutils.console`. What a
user asked to see, e.g. the files `create_model` writes or the report of a
validation, is printed on the rich console of the package. The loggers carry
what is needed to trace a problem: warnings about content which is lost or a
definition which should be fixed, errors of libsbml calls which failed, and
debug detail. The package logs nothing at INFO.

`sbmlutils` follows the convention for libraries: it only gets loggers and logs
to them, it does not configure logging. Handlers, levels and formatting are left
to the application, which keeps the messages of the package under the control of
whoever uses it.

Modules get their logger from the standard library with

```python
import logging

logger = logging.getLogger(__name__)
```

All loggers are therefore below the `sbmlutils` logger, so an application
configures them in one place:

```python
import logging

logging.getLogger("sbmlutils").setLevel(logging.ERROR)
```

For scripts and interactive work the warnings and errors can be shown on the
rich console of the package, next to its output, which is what the examples
do:

```python
from sbmlutils import log

log.enable_rich_logging()
```
"""

import logging

from rich.console import Console
from rich.logging import RichHandler

from sbmlutils.console import console as default_console

#: name of the logger all loggers of the package are below
PACKAGE_LOGGER = "sbmlutils"


def enable_rich_logging(
    level: int = logging.INFO, console: Console | None = None
) -> logging.Logger:
    """Show the warnings and errors of the package on a rich console.

    This configures logging and is meant for scripts, examples and interactive
    work. Applications should configure logging themselves instead of calling
    this. Calling it repeatedly replaces the handler instead of adding a second
    one.

    Args:
        level: level from which messages are logged
        console: console to log on, the console of the package by default

    Returns:
        The `sbmlutils` logger.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)

    # remove a handler of an earlier call, logging twice is worse than not at all
    for handler in list(logger.handlers):
        if isinstance(handler, RichHandler):
            logger.removeHandler(handler)

    handler = RichHandler(
        markup=False,
        rich_tracebacks=True,
        show_time=False,
        console=console if console is not None else default_console,
    )
    handler.setFormatter(logging.Formatter(fmt="%(message)s", datefmt="[%X]"))

    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
