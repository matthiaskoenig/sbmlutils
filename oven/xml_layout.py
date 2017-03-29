from __future__ import print_function
from os.path import join as pjoin
import libsbml

directory = './emd_files/'
in_file = pjoin(directory, 'diauxic_bounds.xml')
out_file = pjoin(directory, 'diauxic_bounds_out.xml')

doc = libsbml.readSBMLFromFile(in_file)
sbml_str = libsbml.writeSBMLToString(doc)
print(sbml_str)



