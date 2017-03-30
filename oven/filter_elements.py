from __future__ import print_function
import libsbml

print(libsbml.__version__)

def filter():
    return False

doc = libsbml.SBMLDocument()
model = doc.createModel()

# without filter
elements = doc.getListOfAllElements()

# with filter
elements_filtered = doc.getListOfAllElements(filter)

