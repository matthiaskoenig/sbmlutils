"""
Try to set SBOTerm on reaction.
"""
import libsbml

# using L3V2, so I don't need species on reaction
doc = libsbml.SBMLDocument(3, 1)
model = doc.createModel()
model.setId('test model')
r = model.createReaction()
r.setSBOTerm('SBO:0000631')

sbml_str = libsbml.writeSBMLToString(doc)
print(sbml_str)
