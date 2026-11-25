"""Fixtures shared by the tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def forbid_chdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Work in `tmp_path` and fail as soon as anything changes the directory.

    The working directory is global to the process, a library function which
    changes it breaks every other thread of the process.

    Args:
        tmp_path: the temporary directory of the test, the working directory
        monkeypatch: the fixture which undoes both after the test

    Returns:
        the working directory of the test
    """
    monkeypatch.chdir(tmp_path)

    def chdir(path: str | os.PathLike[str]) -> None:
        """Refuse to change the working directory."""
        raise AssertionError(f"working directory changed to '{path}'")

    monkeypatch.setattr(os, "chdir", chdir)
    return tmp_path


@pytest.fixture(autouse=True)
def wide_console(monkeypatch: pytest.MonkeyPatch) -> None:
    """Print the output of the package on one line per line in every test.

    The console of the package wraps at 80 columns when it does not print to a
    terminal, which splits a long path or message which a test looks for in
    the captured output. The width is restored after the test.

    Args:
        monkeypatch: the fixture which restores the width
    """
    from sbmlutils.console import console

    monkeypatch.setattr(console, "width", 1000)
