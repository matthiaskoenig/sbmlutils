"""ICG model factory."""
from pathlib import Path
from typing import Any, Dict

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbmlutils.comp import flatten_sbml
from sbmlutils.console import console
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.icg.model_body import model_body
from sbmlutils.examples.icg.model_liver import model as model_liver
from sbmlutils.factory import create_model
from sbmlutils.log import get_logger


logger = get_logger(__name__)


def create_models(results_path: Path, create_tissues: bool = True) -> Dict[str, Any]:
    """Create tissue and whole-body model."""

    results: Dict[str, Any] = {}
    if create_tissues:
        fac_res_liver = create_model(
            model=model_liver,
            filepath=results_path / f"{model_liver.sid}.xml",
        )
        results["icg_liver"] = {
            "path": fac_res_liver.sbml_path,
            "entry": ManifestEntry(
                location=f"./models/{fac_res_liver.sbml_path.name}",
                format=EntryFormat.SBML_L3V1,
                master=False,
            ),
        }

    # create whole-body model
    fac_res_body = create_model(
        model=model_body,
        filepath=results_path / f"{model_body.sid}.xml",
    )
    results["icg_body"] = {
        "path": fac_res_body.sbml_path,
        "entry": ManifestEntry(
            location=f"./models/{fac_res_body.sbml_path.name}",
            format=EntryFormat.SBML_L3V1,
            master=False,
        ),
    }

    sbml_path = results["icg_body"]["path"]
    sbml_path_flat = results_path / f"{model_body.sid}_flat.xml"
    flatten_sbml(sbml_path, sbml_flat_path=sbml_path_flat)

    results["icg_body_flat"] = {
        "path": sbml_path_flat,
        "entry": ManifestEntry(
            location=f"./models/{sbml_path_flat.name}",
            format=EntryFormat.SBML_L3V1,
            master=True,
        ),
    }

    # create omex
    omex = Omex()
    for info in results.values():
        omex.add_entry(entry_path=info["path"], entry=info["entry"])
    omex.to_omex(omex_path=results_path / "icg_model.omex")

    console.print(omex.manifest.dict())

    return results


if __name__ == "__main__":
    from sbmlutils.examples.icg import MODEL_BASE_PATH

    results = create_models(MODEL_BASE_PATH, create_tissues=True)
    for k, key in enumerate(results):
        delete_session = True if k == 0 else False
        sbml_path = results[key]["path"]
        print(sbml_path)
        visualize_sbml(sbml_path=sbml_path, delete_session=delete_session)
