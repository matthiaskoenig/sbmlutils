from libsbml import *
import tempfile

# create simple model
doc = SBMLDocument(3, 1)
m = doc.createModel()
m.setId('test')

s = m.createSpecies()
s.setId('S1')

p = m.createParameter()
p.setId('P1')

# write to file
writer = SBMLWriter()
f = tempfile.NamedTemporaryFile('w', suffix=".xml")
writer.writeSBML(doc, f.name)

with open(f.name, 'r') as fin:
    print(fin.read())
