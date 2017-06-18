"""
Create all the biomodel reports for testing.
"""

from __future__ import absolute_import, print_function
import os
from sbmlutils.report import sbmlreport


def biomodel_reports(biomodels_folder="r30", output_folder="r30_reports"):
    """ Create sbmlreports for all biomodels.

    :return:
    """
    print('-'*80)
    print('BIOMODEL REPORTS')
    print('-' * 80)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    biomodel_path = os.path.join(dir_path, biomodels_folder)
    output_path = os.path.join(dir_path, output_folder)
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # get all SBML files
    biomodels = []
    for f in os.listdir(biomodel_path):
        if f.endswith('.xml'):
            f_path = os.path.join(biomodel_path, f)
            if os.path.isfile(f_path):
                biomodels.append(f_path)

    from pprint import pprint
    pprint(biomodels)

    sbmlreport.create_sbml_reports(sorted(biomodels), out_dir=output_path, validate=False)


def biomodel_report(biomodel_id, biomodels_folder="r30", output_folder="r30_reports"):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    biomodel_path = os.path.join(dir_path, biomodels_folder)
    output_path = os.path.join(dir_path, output_folder)
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    sbmlreport.create_sbml_report(os.path.join(biomodel_path, biomodel_id), out_dir=output_path, validate=False)


def test_simulation():
    import roadrunner
    r = roadrunner.RoadRunner("./r30/BIOMD0000000266.xml")
    r.simulate(0, 100, steps=100)
    r.plot()

if __name__ == "__main__":
    # test_simulation()
    # biomodel_report(biomodel_id="BIOMD0000000266.xml")
    biomodel_reports()
