"""
libSEDML overwrites libSBML functions ?!
"""

# import libsbml
# import libsedml

# # create SBML model
# import antimony
# antimony.loadAntimonyString("""
# model test
#     J0: S1 -> S2; k1*S1;
#     S1 = 10.0; S2 = 0; k1=1.0;
# end
# """)
# sbml_str = antimony.getSBMLString('test')
# print('***')
# print(sbml_str)
# print('***')

from __future__ import print_function

sbml_str = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Created by libAntimony version v2.8.1 on 2016-02-11 15:30 with libSBML version 5.12.1. -->
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="test" name="test">
    <listOfCompartments>
      <compartment sboTerm="SBO:0000410" id="default_compartment" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="S1" compartment="default_compartment" initialConcentration="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="S2" compartment="default_compartment" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="k1" value="1" constant="true"/>
    </listOfParameters>
    <listOfReactions>
      <reaction id="J0" reversible="true" fast="false">
        <listOfReactants>
          <speciesReference species="S1" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="S2" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci> k1 </ci>
              <ci> S1 </ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>
"""

import libsedml
import libsbml

# load doc with libsbml
doc = libsbml.readSBMLFromString(sbml_str)
model = doc.getModel()
print(type(doc))
print(type(model))

print('*' * 80)  # Everything good until here

# importing libsedml overwrites the libsbml.getModel !!!
# suddenly libsedml.Model is returned when calling getModel on doc !
model = doc.getModel()
print(type(doc))
print(type(model))  # <class 'libsedml.Model'> ??

# not even this works any more
model = libsbml.SBMLDocument.getModel(doc)
print(type(model))  # <class 'libsedml.Model'>

print(model.getId())



print(libsbml.__version__)  # Updated to revision 22780
print(libsedml.getLibSEDMLVersion())  # commit 31d92030c91e21d9db7
