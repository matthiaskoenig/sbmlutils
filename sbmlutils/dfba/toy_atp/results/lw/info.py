from __future__ import print_function, absolute_import, division
import os
from sbmlutils.report import sbmlreport




if __name__ == "__main__":
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          'v3')
    files = []
    for file in os.listdir(folder):
        if file.endswith(".xml"):
            print(os.path.join(folder, file))
            files.append(os.path.join(folder, file))

    sbmlreport.create_sbml_reports(files, out_dir=folder, validate=True)
