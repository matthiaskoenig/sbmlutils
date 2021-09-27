"""Module for logging.

Using rich for output formating.
"""
import logging

from rich.logging import RichHandler

from sbmlutils.console import console


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get new custom logger for name."""
    formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]",
    )

    # handler = logging.StreamHandler()
    handler = RichHandler(
        markup=False, rich_tracebacks=True, show_time=False, console=console
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
