"""Example creation of report for debugging."""

if __name__ == "__main__":
    from pathlib import Path

    from sbmlutils.report import sbmlreport
    from sbmlutils.test import BIOMODELS_CURATED_PATH, GLUCOSE_SBML

    # 760, 802
    # sbml_paths = [BIOMODELS_CURATED_PATH / "BIOMD0000000791.xml.gz"]
    sbml_paths = [GLUCOSE_SBML]
    for p in sbml_paths:
        sbmlreport.create_report(
            sbml_path=p,
        )
