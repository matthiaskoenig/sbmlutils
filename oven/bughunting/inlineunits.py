try:
    import libsbml
except ImportError:
    import tesbml as libsbml

doc = libsbml.SBMLDocument(3, 2)
model = doc.createModel()
model.id = "test_inline_unit"

ud = model.createUnitDefinition()
ud.setId("m")
u = model.createUnit()
u.setKind(libsbml.UNIT_KIND_METRE)
u.setExponent(1.0)
u.setScale(1)
u.setMultiplier(1.0)
ud.addUnit(u)

p = model.createParameter()
p.id = "p"
p.constant = False
p.units = "m"

rule = model.createAssignmentRule()
rule.variable = "p"
ast = libsbml.parseL3FormulaWithModel("5.0 m", model)
rule.setMath(ast)

formula = libsbml.formulaToL3String(ast)
print(formula)


libsbml.writeSBMLToFile(doc, "/home/mkoenig/Desktop/inline_units_py.xml")
