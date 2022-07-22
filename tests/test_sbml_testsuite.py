"""Testing the biomodels module."""
from pathlib import Path

import pytest

from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import SBML_TESTSUITE_DIR
from sbmlutils.validation import ValidationOptions


sbml_paths = Path(SBML_TESTSUITE_DIR).glob("**/*.xml")


def sbml_paths_idfn(sbml_path: Path) -> str:
    """Inject path in tests name."""
    return f"{sbml_path.name}"


@pytest.mark.skip("not testing testsuite")
@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_parse_model(tmp_path: Path, sbml_path: Path) -> None:
    """Test parsing of SBML testsuite models."""
    model = sbml_to_model(
        source=sbml_path,
        validate=True,
        validation_options=ValidationOptions(units_consistency=False),
    )
    assert model
