import pandas as pd

from sbmlutils.resources import MODELS_DIR
from sbmlutils.metadata.validator import validate_sbml_annotations

if __name__ == "__main__":
    sbml_faure2006 = MODELS_DIR / "qual" / "Faure2006_MammalianCellCycle.sbml"
    results: pd.DataFrame = validate_sbml_annotations(sbml_faure2006)
