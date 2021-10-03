import libsbml
import pytest

from sbmlutils.factory import UnitDefinition
from sbmlutils.report.units import udef_to_string


doc = libsbml.SBMLDocument()
model: libsbml.Model = doc.createModel()

testdata = [
    ("mM", "mmole/liter", "(0.001*mole)/(liter)"),
    ("dimensionless", "dimensionless", ""),
    ("pmol", "pmol", "1e-12*mole"),
    ("hr", "hr", "3600.0*s"),
    ("ml_per_l", "ml/l", "(0.001*liter)/(liter)"),
]


@pytest.mark.parametrize("uid, definition, expected", testdata)
def test_unit_definition(uid: str, definition: str, expected: str) -> None:
    unit = UnitDefinition(uid, definition)
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def) == expected
