"""
Example script to read SBML multi information
"""

import libsbml


doc = libsbml.readSBMLFromFile("multi_example_1.xml")  # type: libsbml.SBMLDocument
model = doc.getModel()  # type: libsbml.Model

multi_model = model.getPlugin("multi")  # type: libsbml.MultiModelPlugin


print("\nSPECIES 9")
# The trick is to get the MultiSpeciesPlugin for the species
# This has all the additional attributes.
# In general, always get the plugins from the core elements to access
# additional attributes defined in the packages
s = model.getElementBySId("species_9")  # type: libsbml.Species
s_multi = s.getPlugin("multi")  # type: libsbml.MultiSpeciesPlugin

print(s)
print(s_multi)
print(s_multi.getSpeciesType())
