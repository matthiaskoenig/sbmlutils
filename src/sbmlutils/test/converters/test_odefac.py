from pathlib import Path

import libsbml
import pytest

from sbmlutils.converters.odefac import SBML2ODE
from sbmlutils.io import read_sbml
from sbmlutils.test import DEMO_SBML, GALACTOSE_SINGLECELL_SBML


test_models = [
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
]


@pytest.mark.parametrize("sbml_path", test_models)
def test_odefac_to_R(sbml_path: Path, tmp_path: Path) -> None:
    """Create R code for given model."""
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    sbml2ode = SBML2ODE(doc=doc)
    out_path = tmp_path / "model.R"
    sbml2ode.to_R(out_path)
    assert out_path.exists()


@pytest.mark.parametrize("sbml_path", test_models)
def test_odefac_to_python(sbml_path: Path, tmp_path: Path) -> None:
    """Create python code for given model."""
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    sbml2ode = SBML2ODE(doc=doc)
    out_path = tmp_path / "model.py"
    sbml2ode.to_python(out_path)
    assert out_path.exists()
