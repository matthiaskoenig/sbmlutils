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

TESTSUITE_PATH = DATA_DIR / "testsuite"

# --- Combine Archives ---
OMEX_SHOWCASE = DATA_DIR / "omex" / "CombineArchiveShowCase.omex"


# --- Data ---
csv_filepath = DATA_DIR / "data" / "test.csv"


# collect all models
sbml_paths = [
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
]


# distrib
distrib_model_ids = (
    [i for i in range(40, 48)]
    + [49, 50, 51, 52, 56, 65, 69]
    + [i for i in range(69, 104)]
)

# FIXME: EXCLUDING FAILING TESTS DUE TO https://github.com/matthiaskoenig/sbmlutils/issues/208
distrib_model_ids = [i for i in distrib_model_ids if i not in [45, 46, 85, 86, 94, 95]]

distrib_paths = [TESTSUITE_PATH / "distrib" / "testsuite" / "uncertainty.xml"]
for level_ver in ["l3v1", "l3v2"]:
    for i in distrib_model_ids:
        distrib_paths.append(
            TESTSUITE_PATH / "distrib" / "testsuite" / f"00{i:0>3}-sbml-{level_ver}.xml"
        )

# dfba
diauxic_types = ["bounds", "fba", "top", "update"]
dfba_paths = [TESTSUITE_PATH / "dfba" / f"diauxic_{type}.xml" for type in diauxic_types]

# interpolation
interpolation_types = ["constant", "cubic", "linear"]
interpolation_paths = []
for type in interpolation_types:
    interpolation_paths.append(TESTSUITE_PATH / "interpolation" / f"data1_{type}.xml")

# manipulation
manipulation_paths = []
for id in range(1, 5):
    manipulation_paths.append(
        TESTSUITE_PATH / "manipulation" / "merge" / f"BIOMD000000000{id}.xml"
    )
manipulation_paths.append(
    TESTSUITE_PATH / "manipulation" / "output" / "merged.xml",
)

# concatenated model paths for uncertainty tests
ALL_SBML_PATHS = (
    sbml_paths + distrib_paths + dfba_paths + manipulation_paths + interpolation_paths
)

BIOMODELS_CURATED_PATH = MODELS_DIR / "biomodels_curated"


def sbml_paths_idfn(sbml_path: Path) -> str:
    """Helper function to inject Path in test name."""
    return sbml_path.name
