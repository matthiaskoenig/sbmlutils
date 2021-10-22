from sbmlutils import RESOURCES_DIR
from sbmlutils.report.api import json_for_omex
from sbmlutils.test import BIOMODELS_CURATED_PATH


sbml_paths = [
    RESOURCES_DIR / "models" / "BIOMD0000000507_urn.xml",
]

omex_path = BIOMODELS_CURATED_PATH / f"BIOMD0000000075.omex"

json_for_omex(omex_path=omex_path)
