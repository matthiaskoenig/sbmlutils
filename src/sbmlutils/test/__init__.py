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

REPRESSILATOR_SBML = MODELS_DIR / "repressilator" / "BIOMD0000000012_urn.xml"

# --- Combine Archives ---
OMEX_SHOWCASE = DATA_DIR / "omex" / "CombineArchiveShowCase.omex"


# --- Data ---
csv_filepath = DATA_DIR / "data" / "test.csv"

# fetch individual models under the testsuite

TESTSUITE_PATH = DATA_DIR / "testsuite"

# distrib
distrib_model_ids = (
    [i for i in range(40, 48)]
    + [49, 50, 51, 52, 56, 65, 69]
    + [i for i in range(69, 104)]
)
DISTRIB_PATHS = [TESTSUITE_PATH / "distrib" / "testsuite" / "uncertainty.xml"]
for level_ver in ["l3v1", "l3v2"]:
    for i in distrib_model_ids:
        DISTRIB_PATHS.append(
            TESTSUITE_PATH / "distrib" / "testsuite" / f"00{i:0>3}-sbml-{level_ver}.xml"
        )

# dfba
diauxic_types = ["bounds", "fba", "top", "update"]
DFBA_PATHS = [TESTSUITE_PATH / "dfba" / f"diauxic_{type}.xml" for type in diauxic_types]

# interpolation
interpolation_types = ["constant", "cubic", "linear"]
INTERPOLATION_PATHS = []
for type in interpolation_types:
    INTERPOLATION_PATHS.append(TESTSUITE_PATH / "interpolation" / f"data1_{type}.xml")

# manipulation
MANIP_PATHS = []
for id in range(1, 5):
    MANIP_PATHS.append(
        TESTSUITE_PATH / "manipulation" / "merge" / f"BIOMD000000000{id}.xml"
    )
    MANIP_PATHS.append(
        TESTSUITE_PATH / "manipulation" / "output" / f"BIOMD000000000{id}_L3.xml"
    )
MANIP_PATHS.append(
    TESTSUITE_PATH / "manipulation" / "output" / "merged.xml",
)
MANIP_PATHS.append(
    TESTSUITE_PATH / "manipulation" / "output" / "merged_flat.xml",
)

# sbml
SBML_PATHS = [
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
]

# concatenated model paths for uncertainty tests
UNCERTAINTY_MODEL_PATHS = (
    DISTRIB_PATHS + MANIP_PATHS + DFBA_PATHS + INTERPOLATION_PATHS + SBML_PATHS
)
