"""Testing COPASI functionality."""

from pathlib import Path

from sbmlutils.converters import copasi
from sbmlutils.resources import REPRESSILATOR_SBML


def test_write_ids_to_names(tmp_path: Path) -> None:
    """Test write ids to names."""
    outfile = tmp_path / "out.xml"
    copasi.write_ids_to_names(REPRESSILATOR_SBML, outfile)
    assert outfile
