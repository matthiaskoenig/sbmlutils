"""
Code for storing gene expression as uncertainties.
"""
import libsbml

if __name__ == "__main__":
    import numpy as np

    doc = libsbml.readSBMLFromFile("e_coli_core.xml")  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model
    model_fbc = model.getPlugin('fbc')  # type: libsbml.FbcModelPlugin

    # create random gene expression values

    num_gp = model_fbc.getNumGeneProducts()
    np.random.seed(1234)
    expression_rand = np.random.rand(num_gp)

    for k, gp in enumerate(model_fbc.getListOfGeneProducts()):
        print(gp)
        gp_distrib = gp.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin
        print(gp_distrib)

        # --------------------------------------------
        # Store gene expression as uncertainty for parameter
        # --------------------------------------------
        # 5.0 (mean) +- 0.3 (std) [2.0 - 8.0]

        uncertainty = gp_distrib.createUncertainty()  # type: libsbml.Uncertainty

        up_mean = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
        up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
        up_mean.setValue(expression_rand[k])

    # store model with gene expression data
    doc = libsbml.readSBMLFromFile("e_coli_core.xml")  # type: libsbml.SBMLDocument
    libsbml.writeSBMLToFile(doc, "e_coli_core_expression.xml")
