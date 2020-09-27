"""
Resources for testing
"""
from pathlib import Path

TEST_DIR = Path(__file__).parent  # directory of test files
DATA_DIR = TEST_DIR / "data"  # directory of data for tests
MODELS_DIR = DATA_DIR / "models"

# --- Models ---
BASIC_SBML = MODELS_DIR / "basic" / "basic_7.xml"

DEMO_SBML = MODELS_DIR / "demo" / "Koenig_demo_14.xml"
DEMO_SBML_NO_ANNOTATIONS = MODELS_DIR / "demo" / "Koenig_demo_14_no_annotations.xml"
DEMO_ANNOTATIONS = MODELS_DIR / "demo" / "demo_annotations.xlsx"

GALACTOSE_SINGLECELL_SBML = MODELS_DIR / "galactose" / "galactose_30.xml"
GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS = (
    MODELS_DIR / "galactose" / "galactose_30_no_annotations.xml"
)
GALACTOSE_TISSUE_SBML = MODELS_DIR / "galactose" / "Galactose_v128_Nc20_dilution.xml"
GALACTOSE_ANNOTATIONS = MODELS_DIR / "galactose" / "galactose_annotations.xlsx"

GLUCOSE_SBML = MODELS_DIR / "glucose" / "Hepatic_glucose_3.xml"

VDP_SBML = MODELS_DIR / "van_der_pol" / "van_der_pol.xml"

FBC_SBML = MODELS_DIR / "fbc" / "diauxic_fba.xml"

GZ_SBML = MODELS_DIR / "iAT_PLT_636.xml.gz"

# --- Combine Archives ---
OMEX_SHOWCASE = DATA_DIR / "omex" / "CombineArchiveShowCase.omex"


# --- Data ---
csv_filepath = DATA_DIR / "data" / "test.csv"
