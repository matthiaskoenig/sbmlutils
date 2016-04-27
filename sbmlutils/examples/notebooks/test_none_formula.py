from libsbml import *
ast_node = parseL3Formula(None)


sbmlns = SBMLNamespaces(3, 1)
doc = SBMLDocument(sbmlns)
model = doc.createModel()
pid = 'p1'
p1 = model.createParameter()
p1.setId(pid)
rule = model.createAssignmentRule()
rule.setVariable(pid)

getLastParseL3Error()


# ast_node = parseL3FormulaWithModel('A', None)
# print(ast_node)

# ast_node = libsbml.parseL3FormulaWithModel(formula, model)