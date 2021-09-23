import libsbml

from sbmlutils.factory import UnitDefinition
from sbmlutils.report.units import udef_to_string


doc = libsbml.SBMLDocument()
model: libsbml.Model = doc.createModel()


def test_unit_def1() -> None:
    unit = UnitDefinition("mM", "mmole/liter")
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def) == "(mole)/(m^3)"


def test_unit_def2() -> None:
    unit = UnitDefinition("dimensionless")
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def) == ""


def test_unit_def3() -> None:
    unit = UnitDefinition("pmol")
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def) == "1e-12*mole"
