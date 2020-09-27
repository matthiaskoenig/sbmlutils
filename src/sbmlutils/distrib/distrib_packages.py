"""
Example testing uncertainty with libsbml packages
"""
import logging

import libsbml
import numpy as np


if __name__ == "__main__":

    doc = libsbml.readSBMLFromFile("e_coli_core.xml")  # type: libsbml.SBMLDocument

    # activate distrib
    doc.enablePackage(
        "http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True
    )
    doc.setPackageRequired("distrib", True)

    model = doc.getModel()  # type: libsbml.Model
    model_fbc = model.getPlugin("fbc")  # type: libsbml.FbcModelPlugin

    # --------------------------------
    # [2] write gene expression data
    # --------------------------------
    gp = model_fbc.getGeneProduct(0)
    print(gp)
    gp_distrib = gp.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin
    print(gp_distrib)

    if gp_distrib:
        uncertainty = gp_distrib.createUncertainty()  # type: libsbml.Uncertainty

        up_mean = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
        up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
        up_mean.setValue(2.5)
    else:
        logging.error("DistribSBasePlugin not working for fbc:GeneProduct.")

    # store model with gene expression data
    libsbml.writeSBMLToFile(doc, "e_coli_core_expression.xml")
