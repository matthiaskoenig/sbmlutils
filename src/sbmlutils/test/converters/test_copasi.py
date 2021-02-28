from pathlib import Path

from sbmlutils.converters import copasi
from sbmlutils.test import REPRESSILATOR_SBML


def test_write_ids_to_names(tmp_path: Path) -> None:
    outfile = tmp_path / "out.xml"
    copasi.write_ids_to_names(REPRESSILATOR_SBML, outfile)
    assert outfile
