"""
Definition of data and files for the tests.
The files are located in the data directory.
"""
import os
from os.path import join as pjoin

test_dir = os.path.dirname(os.path.abspath(__file__))  # directory of test files
data_dir = pjoin(test_dir, 'data')  # directory of data for tests


################################################################
# comp
################################################################
# ExternalModelDefinitions
DFBA_EMD_SBML = pjoin(data_dir, 'dfba/diauxic_top.xml')

################################################################
# Data
################################################################
csv_filepath = pjoin(data_dir, 'data', 'test.csv')


################################################################
# Models
################################################################
BASIC_SBML = pjoin(data_dir, 'models/basic/basic_7.xml')

# demo -----------------------
DEMO_SBML = pjoin(data_dir, 'models/demo/Koenig_demo_12.xml')
DEMO_SBML_NO_ANNOTATIONS = pjoin(data_dir, 'models/demo/Koenig_demo_12_no_annotations.xml')
DEMO_ANNOTATIONS = pjoin(data_dir, 'models/demo/demo_annotations.xlsx')

# galactose ------------------
GALACTOSE_SINGLECELL_SBML = pjoin(data_dir, 'models/galactose/galactose_30.xml')
GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS = pjoin(data_dir, 'models/galactose/galactose_30_no_annotations.xml')
GALACTOSE_TISSUE_SBML = pjoin(data_dir, 'models/galactose/Galactose_v128_Nc20_dilution.xml')
GALACTOSE_ANNOTATIONS = pjoin(data_dir, 'models/galactose/galactose_annotations.xlsx')

# glucose ------------------
GLUCOSE_SBML = pjoin(data_dir, 'models/glucose/Hepatic_glucose_3.xml')

# van_der_pol ---------------
VDP_SBML = pjoin(data_dir, 'models/van_der_pol/van_der_pol.xml')
