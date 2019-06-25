"""
Example testing uncertainty with libsbml packages
"""
import libsbml
import numpy as np
import logging


if __name__ == "__main__":

    doc = libsbml.readSBMLFromFile("e_coli_core.xml")  # type: libsbml.SBMLDocument

    # activate distrib
    doc.enablePackage("http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True)
    doc.setPackageRequired("distrib", True)

    model = doc.getModel()  # type: libsbml.Model
    model_fbc = model.getPlugin('fbc')  # type: libsbml.FbcModelPlugin

    # -------------------
    # [1] core:Parameter
    # -------------------
    p = model.createParameter()  # type: libsbml.Parameter
    p.setId("p_test")

    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin
    print(p_distrib)

    p2 = model.getParameter("cobra_default_lb")  # type: libsbml.Parameter
    print(p)
    p2_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    uncertainty = p2_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("Basic example: 5.0 +- 0.3 [2.0 - 8.0]")
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    up_mean = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
    up_mean.setValue(5.0)
    up_mean.setUnits(unit)

    up_sd = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up_sd.setType(libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION)
    up_sd.setValue(0.3)
    up_sd.setUnits(unit)

    # up_range = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up_range = libsbml.UncertSpan()
    up_range.setType(libsbml.DISTRIB_UNCERTTYPE_RANGE)
    up_range.setValueLower(2.0)
    up_range.setValueUpper(8.0)
    up_range.setUnits(unit)
    uncertainty.addUncertParameter(up_range)

    # -------------------
    # [2] fbc:GeneProduct
    # -------------------
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
    doc = libsbml.readSBMLFromFile("e_coli_core.xml")  # type: libsbml.SBMLDocument
    libsbml.writeSBMLToFile(doc, "e_coli_core_expression.xml")
