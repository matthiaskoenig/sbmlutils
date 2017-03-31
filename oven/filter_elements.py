from __future__ import print_function
import libsbml

print(libsbml.__version__)


class TestFilter(libsbml.ElementFilter):
    def __init__(self):
        # call the constructor of the base class
        libsbml.ElementFilter.__init__(self)

    # The function performing the filtering, here we just check
    # that we have a valid element, and that it has notes.
    def filter(self, element):

        return False


doc = libsbml.SBMLDocument()
model = doc.createModel()

# without filter
elements = doc.getListOfAllElements()
print("unfiltered", len(elements))

# with filter
filter = TestFilter()
elements_filtered = doc.getListOfAllElements(filter)
print("filtered", len(elements_filtered))

