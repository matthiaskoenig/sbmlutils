"""Test the logging of the package."""

import logging
from collections.abc import Iterator

import pytest
from rich.console import Console
from rich.logging import RichHandler

from sbmlutils import log


@pytest.fixture
def package_logger() -> Iterator[logging.Logger]:
    """Restore the handlers and the level of the package logger after a test.

    Yields:
        The `sbmlutils` logger.
    """
    logger = logging.getLogger(log.PACKAGE_LOGGER)
    handlers = list(logger.handlers)
    level = logger.level
    yield logger
    logger.handlers[:] = handlers
    logger.setLevel(level)


def _rich_handlers(logger: logging.Logger) -> list[logging.Handler]:
    """Get the rich handlers of a logger."""
    return [h for h in logger.handlers if isinstance(h, RichHandler)]


def test_package_does_not_configure_logging(package_logger: logging.Logger) -> None:
    """Test that importing the package adds no handler which outputs anything."""
    assert all(isinstance(h, logging.NullHandler) for h in package_logger.handlers)


def test_enable_rich_logging_logs_on_the_console(
    package_logger: logging.Logger,
) -> None:
    """Test that the messages of a module logger are written on the console."""
    console = Console(record=True, width=200)

    logger = log.enable_rich_logging(level=logging.WARNING, console=console)

    assert logger is package_logger
    assert logger.level == logging.WARNING
    module_logger = logging.getLogger("sbmlutils.tests.module")
    module_logger.info("hidden %s", "info")
    module_logger.warning("shown %s", "warning")
    text = console.export_text()
    assert "shown warning" in text
    assert "hidden info" not in text


def test_enable_rich_logging_replaces_the_handler(
    package_logger: logging.Logger,
) -> None:
    """Test that a second call replaces the handler instead of adding one."""
    first = Console(record=True, width=200)
    second = Console(record=True, width=200)

    log.enable_rich_logging(console=first)
    log.enable_rich_logging(console=second)

    assert len(_rich_handlers(package_logger)) == 1
    logging.getLogger("sbmlutils.tests.module").info("logged once")
    assert "logged once" not in first.export_text()
    assert second.export_text().count("logged once") == 1
