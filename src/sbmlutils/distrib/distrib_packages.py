"""Example testing uncertainty with libsbml packages."""
import logging
import os
import tempfile
from pathlib import Path

import libsbml


def add_uncertainty_example(tmp: bool = False) -> None:
    """Add uncertainty to a model."""
    output_dir = str(Path(__file__).parent)
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(
        os.path.join(output_dir, "e_coli_core.xml")
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
    print(gp)
    gp_distrib: libsbml.DistribSBasePlugin = gp.getPlugin("distrib")
    print(gp_distrib)

    if gp_distrib:
        uncertainty: libsbml.Uncertainty = gp_distrib.createUncertainty()

        up_mean: libsbml.UncertParameter = uncertainty.createUncertParameter()
        up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
        up_mean.setValue(2.5)
    else:
        logging.error("DistribSBasePlugin not working for fbc:GeneProduct.")

    # store model with gene expression data
    if tmp:
        with tempfile.NamedTemporaryFile(suffix=".xml") as f_sbml:
            libsbml.writeSBMLToFile(doc, f_sbml.name)
    else:
        libsbml.writeSBMLToFile(
            doc, os.path.join(output_dir, "e_coli_core_expression.xml")
        )


if __name__ == "__main__":
    add_uncertainty_example(tmp=False)
