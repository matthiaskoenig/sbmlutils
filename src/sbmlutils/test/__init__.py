"""
Resources for testing
"""
from pathlib import Path
from typing import List

from sbmlutils import RESOURCES_DIR, EXAMPLES_DIR

TESTDATA_DIR = RESOURCES_DIR / "testdata"

# -------------------------------------------------------------------------------------
# COMBINE ARCHIVES
# -------------------------------------------------------------------------------------
OMEX_SHOWCASE = TESTDATA_DIR / "omex" / "CombineArchiveShowCase.omex"
OMEX_COMPMODELS = TESTDATA_DIR / "omex" / "CompModels.omex"
OMEX_ICGMODEL = TESTDATA_DIR / "omex" / "icg_model.omex"
OMEX_OMEPRAZOLEMODEL = TESTDATA_DIR / "omex" / "omeprazole_model.omex"

API_EXAMPLES_OMEX = [
    OMEX_ICGMODEL,
    OMEX_OMEPRAZOLEMODEL,
    OMEX_COMPMODELS,
    OMEX_SHOWCASE,
]

# -------------------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------------------
MODELS_DIR = RESOURCES_DIR / "models"
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

GZ_SBML = MODELS_DIR / "iAT_PLT_636.xml.gz"
REPRESSILATOR_SBML = MODELS_DIR / "repressilator" / "BIOMD0000000012_urn.xml"

# fbc
FBC_ECOLI_CORE_SBML = MODELS_DIR / "fbc" / "e_coli_core.xml.gz"
FBC_DIAUXIC_GROWTH_SBML = MODELS_DIR / "fbc" / "diauxic_fba.xml"
FBC_RECON3D_SBML = MODELS_DIR / "fbc" / "Recon3D.xml.gz"

# comp
COMP_ICG_LIVER = MODELS_DIR / "comp" / "icg_liver.xml"
COMP_ICG_BODY_FLAT = MODELS_DIR / "comp" / "icg_body_flat.xml"
COMP_ICG_BODY = MODELS_DIR / "comp" / "icg_body.xml"

COMP_DEX_CYP2D6 = MODELS_DIR / "comp" / "cyp2d6.xml"
COMP_DEX_LIVER = MODELS_DIR / "comp" / "dex_liver.xml"
COMP_DEX_INTESTINE = MODELS_DIR / "comp" / "dex_intestine.xml"
COMP_DEX_KIDNEY = MODELS_DIR / "comp" / "dex_kidney.xml"
COMP_DEX_BODY_FLAT = MODELS_DIR / "comp" / "dex_body_flat.xml"
COMP_DEX_BODY = MODELS_DIR / "comp" / "dex_body.xml"

# distrib
DISTRIB_DISTRIBUTIONS_SBML = RESOURCES_DIR / "examples" / "distrib_distributions.xml"
DISTRIB_UNCERTAINTIES_SBML = RESOURCES_DIR / "examples" / "distrib_uncertainties.xml"
DISTRIB_COMP_SBML = RESOURCES_DIR / "examples" / "distrib_comp.xml"
DISTRIB_COMP_FLAT_SBML = RESOURCES_DIR / "examples" / "distrib_comp_flat.xml"


def all_distrib_paths() -> List[Path]:
    """Get distrib paths"""

    distrib_model_ids = (
        [i for i in range(40, 48)]
        + [49, 50, 51, 52, 56, 65, 69]
        + [i for i in range(69, 104)]
    )

    # FIXME: EXCLUDING FAILING TESTS DUE TO https://github.com/matthiaskoenig/sbmlutils/issues/208
    distrib_model_ids = [
        i for i in distrib_model_ids if i not in [45, 46, 85, 86, 94, 95]
    ]

    distrib_paths = [
        DISTRIB_UNCERTAINTIES_SBML,
        DISTRIB_DISTRIBUTIONS_SBML,
        DISTRIB_COMP_SBML,
        DISTRIB_COMP_FLAT_SBML,
    ]
    for level_ver in ["l3v1", "l3v2"]:
        for i in distrib_model_ids:
            distrib_paths.append(
                MODELS_DIR / "distrib" / "testsuite" / f"00{i:0>3}-sbml-{level_ver}.xml"
            )
    return distrib_paths


distrib_paths = all_distrib_paths()


# dfba
dfba_paths = [
    MODELS_DIR / "dfba" / f"diauxic_{t}.xml" for t in ["bounds", "fba", "top", "update"]
]

# interpolation
interpolation_paths = [
    MODELS_DIR / "interpolation" / f"data1_{type}.xml"
    for t in ["constant", "cubic", "linear"]
]

example_ids = [
    "amount_species",
    "annotation",
    "assignment",
    "boundary_condition",
    "compartment_species_reaction",
    "complete_model",
    "distrib_comp",
    "distrib_distributions",
    "distrib_uncertainties",
    "fbc_example",
    "fbc_mass_charge",
    "linear_chain",
    "minimal_model",
    "minimal_model_comp",
    "model_composition",
    "model_definitions",
    "multiple_substance_units",
    "nan",
    "notes",
    "random_network",
    "reaction",
    "simple_reaction_with_units",
    "unit_definitions",
    "units_namespace",
]

API_EXAMPLES_MODEL = [
    REPRESSILATOR_SBML,
    COMP_ICG_BODY_FLAT,
    COMP_ICG_BODY,
    COMP_ICG_LIVER,
    GLUCOSE_SBML,
    COMP_DEX_BODY,
    COMP_DEX_BODY_FLAT,
    COMP_DEX_CYP2D6,
    COMP_DEX_INTESTINE,
    COMP_DEX_KIDNEY,
    COMP_DEX_LIVER,
    DISTRIB_DISTRIBUTIONS_SBML,
    DISTRIB_UNCERTAINTIES_SBML,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
] + [EXAMPLES_DIR / f"{eid}.xml" for eid in example_ids]


# concatenated model paths for uncertainty tests
ALL_SBML_PATHS = (
    [
        BASIC_SBML,
        DEMO_SBML,
        GALACTOSE_SINGLECELL_SBML,
        GLUCOSE_SBML,
        GZ_SBML,
        REPRESSILATOR_SBML,
        VDP_SBML,
    ]
    + distrib_paths
    + dfba_paths
    + interpolation_paths
)

BIOMODELS_CURATED_PATH = MODELS_DIR / "biomodels_curated"


def sbml_paths_idfn(sbml_path: Path) -> str:
    """Helper function to inject Path in test name."""
    return sbml_path.name
