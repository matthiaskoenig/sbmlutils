"""Uncertainty information added to an existing model.

The example reads the packaged *E. coli* core model and adds the uncertainty of
a parameter with the libsbml distrib package.

Run it from the root of the repository:

```bash
python -m examples.distrib.distrib_uncertainty
```
"""

import logging
import tempfile
from pathlib import Path

import libsbml

from sbmlutils import RESOURCES_DIR

logger = logging.getLogger(__name__)


def add_uncertainty_example(output_dir: Path | None = None) -> None:
    """Add the uncertainty of a gene product to the E. coli core model.

    Args:
        output_dir: directory the model is written to, a temporary directory
            which is removed afterwards when it is `None`.
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(
        str(RESOURCES_DIR / "distrib" / "e_coli_core.xml")
    )

    # activate distrib
    doc.enablePackage(
        "http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True
    )
    doc.setPackageRequired("distrib", True)

    model: libsbml.Model = doc.getModel()
    model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")

    # write gene expression data
    gp = model_fbc.getGeneProduct(0)
    gp_distrib: libsbml.DistribSBasePlugin = gp.getPlugin("distrib")

    if gp_distrib:
        uncertainty: libsbml.Uncertainty = gp_distrib.createUncertainty()

        up_mean: libsbml.UncertParameter = uncertainty.createUncertParameter()
        up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
        up_mean.setValue(2.5)
    else:
        logger.error("DistribSBasePlugin not working for fbc:GeneProduct.")

    # store model with gene expression data
    with tempfile.TemporaryDirectory() as tmp_dir:
        directory = output_dir if output_dir else Path(tmp_dir)
        libsbml.writeSBMLToFile(doc, str(directory / "e_coli_core_expression.xml"))


if __name__ == "__main__":
    add_uncertainty_example(output_dir=Path.cwd())
