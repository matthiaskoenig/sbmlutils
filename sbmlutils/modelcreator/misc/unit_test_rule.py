from __future__ import print_function, division
from libsbml import *

doc = readSBMLFromFile("Sturis1991_1.xml")
model = doc.getModel()

rule = model.getRule(0)
print(rule)
derived_units = rule.getDerivedUnitDefinition()
str = UnitDefinition_printUnits(derived_units)
print(str)
UnitDefinition_reorder(derived_units)
str = UnitDefinition_printUnits(derived_units)
print(str)





