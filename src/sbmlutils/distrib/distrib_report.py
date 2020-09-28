"""
Writing report with distrib information.
"""

from sbmlutils.report import sbmlreport


if __name__ == "__main__":
    for path in [
        "./distrib_normal.xml",
        "./distrib_all.xml",
        "./uncertainty_distribution.xml",
        "./uncertainty_uncertspan.xml",
        "./uncertainty_uncertvalue.xml",
    ]:
        print(path)
        sbmlreport.create_report(path, target_dir="./results/")
