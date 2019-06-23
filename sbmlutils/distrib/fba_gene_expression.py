"""
Example model to store gene expression data as uncertainties.
"""
import libsbml


def uncertainty():
    """ Create uncertainty with UncertParameter.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = _create_parameter("p1", model=model)  # type: libsbml.Parameter
    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    # --------------------------------------------
    # Build generic uncertainty for parameter
    # --------------------------------------------
    # 5.0 (mean) +- 0.3 (std) [2.0 - 8.0]

    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
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
    check(uncertainty.addUncertParameter(up_range), "add the span")

    check(uncertainty.setAnnotation("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
        <p>Experimental data from study</p>
    </body>
    """), "set annotations")

    # add an annotation with SBO terms
    uncertainty.setMetaId("meta_uncertainty1")
    cv1 = libsbml.CVTerm()
    cv1.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
    cv1.setBiologicalQualifierType(6)  # "BQB_IS_DESCRIBED_BY"
    cv1.addResource("https://identifiers.org/pubmed/123456")
    check(uncertainty.addCVTerm(cv1), "add cv term")

    cv2 = libsbml.CVTerm()
    cv2.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
    cv2.setBiologicalQualifierType(10)  # "BQB_HAS_PROPERTY"
    cv2.addResource("http://purl.obolibrary.org/obo/ECO_0006016")
    check(uncertainty.addCVTerm(cv2), "add cv term")

    # --------------------------------------------
    # Set of all UncertParameters
    # --------------------------------------------
    # create second uncertainty which contains all the individual uncertainties
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("UncertParameter example")
    for k, parameter_type in enumerate([
            libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
            libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
            libsbml.DISTRIB_UNCERTTYPE_MEAN,
            libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
            libsbml.DISTRIB_UNCERTTYPE_MODE,
            libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
            libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
            libsbml.DISTRIB_UNCERTTYPE_VARIANCE]):

        up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
        up.setType(parameter_type)
        up.setValue(k)
        up.setUnits(unit)

    # --------------------------------------------
    # Set of all UncertSpans
    # --------------------------------------------
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("UncertSpan example")
    for k, parameter_type in enumerate([
            libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
            libsbml.DISTRIB_UNCERTTYPE_RANGE]):

        up_range = libsbml.UncertSpan()
        up_range.setType(parameter_type)
        up_range.setValueLower(k-1.0)
        up_range.setValueUpper(k+1.0)
        up_range.setUnits(unit)
        check(uncertainty.addUncertParameter(up_range), "add the span")

    # --------------------------------------------
    # Use math for distribution definition
    # --------------------------------------------
    # 5.0 dimensionless * normal(1.0 mole, 3.0 mole)
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("math example: 5.0 dimensionless * normal(1.0 mole, 3.0 mole)")
    up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
    up.setDefinitionURL("http://www.sbml.org/sbml/symbols/distrib/normal")
    ast = libsbml.parseL3FormulaWithModel("5.0 dimensionless * normal(1.0 mole, 3.0 mole)",
                                          model)
    if not ast:
        raise ValueError
    up.setMath(ast)

    # --------------------------------------------
    # Use externalParameter
    # --------------------------------------------
    # https://sites.google.com/site/probonto/
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("ExternalParameter example")
    up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up.setType(libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER)
    up.setName("skewness")
    up.setValue(0.25)
    up.setUnits(unit)
    up.setDefinitionURL("http://purl.obolibrary.org/obo/STATO_0000068")

    # --------------------------------------------
    # Use external distribution definition
    # --------------------------------------------
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    uncertainty.setName("External distribution example")
    up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
    up.setName("Geometric 1")
    up.setDefinitionURL("http://www.probonto.org/ontology#PROB_k0000782")
    up.setUnits(unit)

    # success probability of Geometric-1
    up_mean_geo1 = up.createUncertParameter()  # type: libsbml.UncertParameter
    up_mean_geo1.setType(libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER)
    up_mean_geo1.setName("success probability of Geometric 1")
    up_mean_geo1.setValue(0.4)
    up_mean_geo1.setDefinitionURL("http://www.probonto.org/ontology#PROB_k0000789")

    return doc