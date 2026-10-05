"""Test that the documentation shows the current output of the ODE export.

The page `docs/ode.md` includes the files of `docs/images/ode`, which
`examples/converters/ode.py` writes (`python -m examples.converters.ode
docs/images/ode`). A change of the export which changes them fails here until they
are written again, so the documentation never shows an output the export no longer
writes. The version of sbmlutils in the files is not compared, it changes with every
release.
"""

import re
from pathlib import Path

import pytest

from examples.converters.ode import SUFFIXES, compile_typst, export
from sbmlutils.resources import REPRESSILATOR_SBML

DOCS_DIR: Path = Path(__file__).parents[3] / "docs" / "images" / "ode"
"""The files of the ODE export in the documentation."""

pytestmark = pytest.mark.skipif(
    not DOCS_DIR.is_dir(), reason="the documentation is only part of the repository"
)

VERSION = re.compile(r"sbmlutils \d+\.\d+\.\d+\S*")
"""The version of sbmlutils which wrote a file."""


def _text(path: Path) -> str:
    """The text of a file without the version of sbmlutils which wrote it."""
    return VERSION.sub("sbmlutils VERSION", path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def exported(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    """The files of the repressilator, written by the example."""
    return export(REPRESSILATOR_SBML, tmp_path_factory.mktemp("ode"), "repressilator")


def test_every_format_is_shown(exported: list[Path]) -> None:
    """The example writes one file per format and the markdown fragment."""
    assert [p.name for p in exported] == [
        *(f"repressilator{suffix}" for suffix in SUFFIXES.values()),
        "repressilator_fragment.md",
    ]


@pytest.mark.parametrize(
    "name",
    [
        *(f"repressilator{suffix}" for suffix in SUFFIXES.values()),
        "repressilator_fragment.md",
    ],
)
def test_docs_are_current(name: str, exported: list[Path]) -> None:
    """The file in the documentation is the one the export writes now."""
    (path,) = (p for p in exported if p.name == name)
    assert _text(DOCS_DIR / name) == _text(path), (
        f"docs/images/ode/{name} is outdated, run "
        "`python -m examples.converters.ode docs/images/ode`"
    )


def test_typst_pages_are_current(exported: list[Path]) -> None:
    """The documentation shows every page of the compiled typst document."""
    pytest.importorskip("typst")
    (typ,) = (p for p in exported if p.suffix == ".typ")
    pages = compile_typst(typ)
    assert sorted(p.name for p in DOCS_DIR.glob("repressilator-*.svg")) == sorted(
        p.name for p in pages
    )
