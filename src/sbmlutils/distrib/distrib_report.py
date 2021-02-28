"""Writing report with distrib information."""
from pathlib import Path

from sbmlutils.report import sbmlreport


if __name__ == "__main__":
    for filename in [
        "distrib_normal.xml",
        "distrib_all.xml",
        "uncertainty_distribution.xml",
        "uncertainty_uncertspan.xml",
        "uncertainty_uncertvalue.xml",
    ]:
        sbml_path = Path(__file__).parent / filename
        print(sbml_path)
        sbmlreport.create_report(
            sbml_path=sbml_path, output_dir=Path(__file__).parent / "results"
        )
