"""
Creates SBML reports with sbmlutils for all curated
models in the latest biomodel release.

Models are 31th Biomodels Release
https://www.ebi.ac.uk/biomodels/content/news/biomodels-release-26th-june-2017
"""

import os
from sbmlutils.report import sbmlreport


def biomodel_reports(biomodels_folder="r31", output_folder="r31_reports"):
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

    sbmlreport.create_sbml_reports(sorted(biomodels), out_dir=output_path,
                                   validate=False)


def biomodel_report(biomodel_id, biomodels_folder="r30",
                    output_folder="r30_reports"):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    biomodel_path = os.path.join(dir_path, biomodels_folder)
    output_path = os.path.join(dir_path, output_folder)
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    sbmlreport.create_sbml_report(os.path.join(biomodel_path, biomodel_id), out_dir=output_path, validate=False)


if __name__ == "__main__":
    biomodel_reports()
