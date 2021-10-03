import libsbml
import pytest

from sbmlutils.factory import UnitDefinition
from sbmlutils.report.units import udef_to_string


testdata_str = [
    ("pmol", "pmol", "pmol"),
    ("hr", "hr", "hr"),
    ("ml_per_l", "ml/l", "ml/l"),
    ("mmole_per_min", "mmole/min", "mmol/min"),
    ("m3", "meter^3", "m^3"),
    ("m3", "meter^3/second", "m^3/s"),
    ("mM", "mmole/liter", "mmol/l"),
    ("ml_per_s_kg", "ml/s/kg", "ml/s/kg"),
    ("dimensionless", "dimensionless", "-"),
    ("item", "item", "item"),
]
testdata_latex = [
    ("pmol", "pmol", "pmol"),
    ("hr", "hr", "hr"),
    ("ml_per_l", "ml/l", "\\frac{ml}{l}"),
    ("mmole_per_min", "mmole/min", "\\frac{mmol}{min}"),
    ("m3", "meter^3", "m^3"),
    ("m3", "meter^3/second", "\\frac{m^3}{s}"),
    ("mM", "mmole/liter", "\\frac{mmol}{l}"),
    ("ml_per_s_kg", "ml/s/kg", "\\frac{ml}{s \cdot kg}"),
    ("dimensionless", "dimensionless", "-"),
    ("item", "item", "item"),
]


@pytest.mark.parametrize("uid, definition, expected", testdata_str)
def test_unit_definition_str(uid: str, definition: str, expected: str) -> None:
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    unit = UnitDefinition(uid, definition)
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def, model=model, format="str") == expected


@pytest.mark.parametrize("uid, definition, expected", testdata_latex)
def test_unit_definition_latex(uid: str, definition: str, expected: str) -> None:
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    unit = UnitDefinition(uid, definition)
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def, model=model, format="latex") == expected
