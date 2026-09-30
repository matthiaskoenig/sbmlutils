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
