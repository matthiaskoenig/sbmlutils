"""
Definition of data and files for the tests.
The files are located in the resources directory.
"""

import os
from os.path import join as pjoin

test_dir = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.abspath(pjoin(pjoin(test_dir, os.pardir), os.pardir))
print(resources_dir)


################################################################
# comp
################################################################
# ExternalModelDefinitions
DFBA_EMD_SBML = pjoin(resources_dir, 'dfba/diauxic_top.xml')

################################################################
# Data
################################################################
csv_filepath = pjoin(resources_dir, 'data', 'test.csv')


################################################################
# Models
################################################################
import sbmlutils.examples.models.basic.Cell as basic_cell
import sbmlutils.examples.models.demo.Cell as demo_cell
import sbmlutils.examples.models.glucose.Cell as glucose_cell

basic_id = "{}_{}".format(basic_cell.mid, basic_cell.version)
basic_sbml = pjoin(resources_dir, 'models/basic/results', '{}.xml'.format(basic_id))

# demo -----------------------
demo_id = "{}_{}".format(demo_cell.mid, demo_cell.version)
demo_sbml = pjoin(resources_dir, 'models/demo/results', '{}.xml'.format(demo_id))
demo_sbml_no_annotations = pjoin(resources_dir, 'models/demo/results', '{}_no_annotations.xml'.format(demo_id))
demo_annotations = pjoin(resources_dir, 'models/demo', 'demo_annotations.xlsx.csv')

# galactose ------------------
galactose_id = 'galactose_30'
galactose_singlecell_sbml = pjoin(resources_dir, 'models/galactose/results', '{}.xml'.format(galactose_id))
galactose_singlecell_sbml_no_annotations = pjoin(resources_dir, 'models/galactose/results', '{}_no_annotations.xml'.format(galactose_id))
galactose_tissue_sbml = pjoin(resources_dir, 'models/galactose/results', 'Galactose_v128_Nc20_dilution.xml')
galactose_annotations = pjoin(resources_dir, 'models/galactose', 'galactose_annotations.xlsx.csv')

# glucose ------------------
glucose_id = "{}_{}".format(glucose_cell.mid, glucose_cell.version)
glucose_sbml = pjoin(resources_dir, 'models/glucose/results', '{}.xml'.format(glucose_id))

# small -----------------------
small_id = 'small_6'
small_sbml = pjoin(resources_dir, 'models/small', '{}.xml'.format(small_id))

# van_der_pol ---------------
vdp_id = "van_der_pol"
vdp_sbml = pjoin(resources_dir, 'models/van_der_pol', '{}.xml'.format(vdp_id))



