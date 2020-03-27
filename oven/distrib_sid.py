import libsbml

sbml_level = 3
sbml_version = 1
sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
sbmlns.addPackageNamespace("distrib", 1)
doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
doc.setPackageRequired("distrib", True)
model = doc.createModel()  # type: libsbml.Model

# parameter
p = model.createParameter()  # type: libsbml.Parameter
p.setId("p1")
p.setValue(1.0)
p.setConstant(False)
unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
p.setUnits(unit)

p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

# --------------------------------------------
# Build generic uncertainty for parameter
# --------------------------------------------
# 5.0 (mean) +- 0.3 (std) [2.0 - 8.0]

uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
uncertainty.setId("uncertainty1")
uncertainty.setName("Basic example: 5.0 +- 0.3 [2.0 - 8.0]")
up_mean = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
up_mean.setValue(5.0)

sbml_str = libsbml.writeSBMLToString(doc)
print(sbml_str)