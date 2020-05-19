from pathlib import Path
from sbmlutils.comp import flattenSBMLFile
from sbmlutils.report import sbmlreport


def flatten_sbml(sbml_path: Path, sbml_path_flat: Path):
    flattenSBMLFile(str(sbml_path.resolve()), output_path=str(sbml_path_flat.resolve()))

    # create model report
    # sbmlreport.create_report(str(sbml_path_flat), report_dir=str(results_path))


if __name__ == "__main__":
    sbml_path = Path("test10.xml")
    sbml_path_flat = Path("test10_flat.xml")

    flatten_sbml(sbml_path, sbml_path_flat)