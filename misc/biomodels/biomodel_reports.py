"""
Creates SBML reports with sbmlutils for all curated
models in the latest biomodel release.

Models are 31th Biomodels Release
https://www.ebi.ac.uk/biomodels/content/news/biomodels-release-26th-june-2017
"""

import os
from pprint import pprint
from sbmlutils.report import sbmlreport


def model_reports(biomodels_folder, reports_folder):
    """ Create sbmlreports for all biomodels.

    :return:
    """
    #if not os.path.exists(reports_folder):
    #    os.mkdir(reports_folder)

    # get all SBML files
    sbml_paths = []
    for f in os.listdir(biomodels_folder):
        if f.endswith('.xml'):
            f_path = os.path.join(biomodels_folder, f)
            if os.path.isfile(f_path):
                sbml_paths.append(f_path)
    pprint(sbml_paths)

    sbmlreport.create_reports(sorted(sbml_paths)[:10], output_dir=reports_folder,
                              validate=False)


if __name__ == "__main__":
    biomodels_folder = "/home/mkoenig/biomodels/releases/R31_2017-06-26/curated"
    reports_folder = "/home/mkoenig/biomodels/reports"

    model_reports(biomodels_folder=biomodels_folder,
                  reports_folder=reports_folder)
