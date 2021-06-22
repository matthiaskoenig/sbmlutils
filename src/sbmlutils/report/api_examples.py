from sbmlutils.test import (
    ICG_BODY,
    ICG_BODY_FLAT,
    ICG_LIVER,
    MODEL_DEFINITIONS_SBML,
    RECON3D_SBML,
    REPRESSILATOR_SBML,
)


# Data and Endpoints for Example Models
examples_info = {
    "repressilator": {
        "file": REPRESSILATOR_SBML,
        "model": {
            "fetchId": "repressilator",
            "name": "Elowitz2000 - Repressilator",
            "id": "BIOMD0000000012",
            "sbo": None,
            "metaId": "_000001",
        },
    },
    "model_definitions": {
        "file": MODEL_DEFINITIONS_SBML,
        "model": {
            "fetchId": "model_definitions",
            "name": "",
            "id": "model_definitions_example",
            "sbo": None,
            "metaId": None,
        },
    },
    "recon3d": {
        "file": RECON3D_SBML,
        "model": {
            "fetchId": "recon3d",
            "name": None,
            "id": "Recon3D",
            "sbo": None,
            "metaId": None,
        },
    },
    "icg_liver": {
        "file": ICG_LIVER,
        "model": {
            "fetchId": "icg_liver",
            "name": "icg_liver",
            "id": "icg_liver",
            "sbo": None,
            "metaId": "meta_icg_liver",
        },
    },
    "icg_body_flat": {
        "file": ICG_BODY_FLAT,
        "model": {
            "fetchId": "icg_body_flat",
            "name": "icg_body",
            "id": "icg_body",
            "sbo": None,
            "metaId": "meta_icg_body",
        },
    },
    "icg_body": {
        "file": ICG_BODY,
        "model": {
            "fetchId": "icg_body",
            "name": "icg_body",
            "id": "icg_body",
            "sbo": None,
            "metaId": "meta_icg_body",
        },
    },
}
