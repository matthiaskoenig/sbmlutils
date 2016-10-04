"""
Definition of data and files for the tests.
"""

import os

import sbmlutils.examples.models.basic.Cell as basic_cell
import sbmlutils.examples.models.demo.Cell as demo_cell
import sbmlutils.examples.models.glucose.Cell as glucose_cell

test_dir = os.path.dirname(os.path.abspath(__file__))

################################################################
# Models
################################################################
basic_id = "{}_{}".format(basic_cell.mid, basic_cell.version)
basic_sbml = os.path.join(test_dir, 'models/basic/results', '{}.xml'.format(basic_id))

# demo -----------------------
demo_id = "{}_{}".format(demo_cell.mid, demo_cell.version)
demo_sbml = os.path.join(test_dir, 'models/demo/results', '{}.xml'.format(demo_id))
demo_sbml_no_annotations = os.path.join(test_dir, 'models/demo/results', '{}_no_annotations.xml'.format(demo_id))
demo_annotations = os.path.join(test_dir, 'models/demo', 'demo_annotations.xlsx.csv')

# galactose ------------------
galactose_id = 'galactose_30'
galactose_singlecell_sbml = os.path.join(test_dir, 'models/galactose/results', '{}.xml'.format(galactose_id))
galactose_singlecell_sbml_no_annotations = os.path.join(test_dir, 'models/galactose/results', '{}_no_annotations.xml'.format(galactose_id))
galactose_tissue_sbml = os.path.join(test_dir, 'models/galactose/results', 'Galactose_v128_Nc20_dilution.xml')
galactose_annotations = os.path.join(test_dir, 'models/galactose', 'galactose_annotations.xlsx.csv')

# glucose ------------------
glucose_id = "{}_{}".format(glucose_cell.mid, glucose_cell.version)
glucose_sbml = os.path.join(test_dir, 'models/glucose/results', '{}.xml'.format(glucose_id))

# small -----------------------
small_id = 'small_6'
small_sbml = os.path.join(test_dir, 'models/small', '{}.xml'.format(small_id))

# van_der_pol ---------------
vdp_id = "van_der_pol"
vdp_sbml = os.path.join(test_dir, 'models/van_der_pol', '{}.xml'.format(vdp_id))


################################################################
# Data
################################################################
csv_filepath = os.path.join(test_dir, 'data', 'test.csv')

