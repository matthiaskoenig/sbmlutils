import libsbml

from sbmlutils.factory import Unit
from sbmlutils.report import formating
from sbmlutils.units import *


doc = libsbml.SBMLDocument()
model = doc.createModel()  # libsbml.model


def test_unit_def1():
    unit = Unit("mM", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_METRE, -3.0)])
    unit_def = unit.create_sbml(model)
    assert formating.unitDefinitionToString(unit_def) == "(mole)/(m^3)"


def test_unit_def2():
    unit = Unit("dimensionless", [(UNIT_KIND_DIMENSIONLESS, 1.0)])
    unit_def = unit.create_sbml(model)
    assert formating.unitDefinitionToString(unit_def) == ""


def test_unit_def3():
    unit = Unit("pmol", [(UNIT_KIND_MOLE, 1.0, -12, 1.0)])
    unit_def = unit.create_sbml(model)
    assert formating.unitDefinitionToString(unit_def) == "(10^-12)*mole"
