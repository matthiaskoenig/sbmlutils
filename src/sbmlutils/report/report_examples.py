from sbmlutils.test import BIOMODELS_CURATED_PATH
from sbmlutils.report import sbmlreport

from pathlib import Path

# Failing 62;
# [25, 237, 248, 255, 273, 326, 412, 429, 445, 446, 450, 547, 564, 568]
sbml_paths = [BIOMODELS_CURATED_PATH / f"BIOMD0000000446.xml.gz"]

for p in sbml_paths:
    print(p)
    sbmlreport.create_report(sbml_path=p, output_dir=Path(__file__).parent / "_results",
                             math_type="latex", validate=False)
