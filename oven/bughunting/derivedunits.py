try:
    import libsbml
except ImportError:
    import tesbml as libsbml

doc = libsbml.readSBMLFromFile("limax_pkpd_39.xml")
for r in doc.model.reactions:  # type: libsbml.Reaction
    ud = r.getKineticLaw().getDerivedUnitDefinition()  # type: libsbml.UnitDefinition
    print(r, libsbml.UnitDefinition.printUnits(ud))
