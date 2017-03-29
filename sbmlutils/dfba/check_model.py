"""
Script to check the model files.
"""
from __future__ import print_function, division
import os
from os import walk
from sbmlutils.validation import check_sbml
from sbmlutils.report import sbmlreport

# directory to write files to
directory = os.path.dirname(os.path.abspath(__file__))

xml_files = []
for (dirpath, dirnames, filenames) in walk(directory):
    xml_files.extend([name for name in filenames if name.endswith('.xml')])
    break

print(xml_files)


# perform a model validation
for sbml_file in xml_files:
    check_sbml(sbml_file)

# create the model reports

for sbml_file in xml_files:
    sbmlreport.create_sbml_report(sbml_file, directory)
