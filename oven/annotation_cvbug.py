import libsbml
from sbmlutils.validation import check

doc = libsbml.SBMLDocument(3, 2)  # type: libsbml.SBMLDocument
model = doc.createModel()  # type: libsbml.Model
p = model.createParameter()  # type: libsbml.Parameter
p.setId("p")

check(p.setAnnotation("""
<body xmlns='http://www.w3.org/1999/xhtml'>
    <p>First annotation</p>
</body>
"""), "set annotations")

# add an annotation with SBO terms
p.setMetaId("meta_uncertainty1")
cv1 = libsbml.CVTerm()
cv1.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
cv1.setBiologicalQualifierType(6)  # "BQB_IS_DESCRIBED_BY"
cv1.addResource("https://identifiers.org/pubmed/123456")
check(p.addCVTerm(cv1), "add cv term")

sbml = libsbml.writeSBMLToString(doc)
print("-" * 80)
print(sbml)
print("-" * 80)

check(p.setAnnotation("""
<body xmlns='http://www.w3.org/1999/xhtml'>
    <p>New annotation.</p>
</body>
"""), "set annotations")

sbml = libsbml.writeSBMLToString(doc)
print("-" * 80)
print(sbml)
print("-" * 80)