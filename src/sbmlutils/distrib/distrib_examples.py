"""Code for working with the libsbml distrib package."""
import tempfile

import libsbml

from sbmlutils import validation
from sbmlutils.validation import check


# TODO: function to check for distributions in ast_nodes
# TODO: read the example cases


def _distrib_doc() -> libsbml.SBMLDocument:
    """Create distrib document."""
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("distrib", True)

    return doc


def _create_parameter(pid: str, model: libsbml.Model) -> libsbml.Parameter:
    p: libsbml.Parameter = model.createParameter()
    p.setId(pid)
    p.setValue(1.0)
    p.setConstant(False)
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    p.setUnits(unit)
    return p


def distrib_normal() -> libsbml.SBMLDocument:
    """Create simple distrib model.

    :return:
    """
    doc: libsbml.SBMLDocument = _distrib_doc()
    model: libsbml.Model = doc.createModel()

    # parameter
    _: libsbml.Parameter = _create_parameter("p1", model=model)

    # initial assignment
    assignment: libsbml.InitialAssignment = model.createInitialAssignment()
    assignment.setSymbol("p1")
    ast_node = libsbml.parseL3FormulaWithModel("1.0 mole * normal(0, 1.0)", model)
    assignment.setMath(ast_node)

    return doc


def distrib_all() -> libsbml.SBMLDocument:
    """Create simple distrib model.

    :return:
    """
    doc: libsbml.SBMLDocument = _distrib_doc()
    model: libsbml.Model = doc.createModel()

    # extended math approach
    formulas_data = [
        ("p_normal_1", "normal(0, 1)"),
        ("p_normal_2", "normal(0, 1, 0, 10)"),
        ("p_uniform", "uniform(5, 10)"),
        ("p_bernoulli", "bernoulli(0.4)"),
        ("p_binomial_1", "binomial(100, 0.3)"),
        ("p_binomial_2", "binomial(100, 0.3, 0, 2)"),
        ("p_cauchy_1", "cauchy(0, 1)"),
        ("p_cauchy_2", "cauchy(0, 1, 0, 5)"),
        ("p_chisquare_1", "chisquare(10)"),
        ("p_chisquare_2", "chisquare(10, 0, 10)"),
        ("p_exponential_1", "exponential(1.0)"),
        ("p_exponential_2", "exponential(1.0, 0, 10)"),
        ("p_gamma_1", "gamma(0, 1)"),
        ("p_gamma_2", "gamma(0, 1, 0, 10)"),
        ("p_laplace_1", "laplace(0, 1)"),
        ("p_laplace_2", "laplace(0, 1, 0, 10)"),
        ("p_lognormal_1", "lognormal(0, 1)"),
        ("p_lognormal_2", "lognormal(0, 1, 0, 10)"),
        ("p_poisson_1", "poisson(0.5)"),
        ("p_poisson_2", "poisson(0.5, 0, 10)"),
        ("p_raleigh_1", "rayleigh(0.5)"),
        ("p_raleigh_2", "rayleigh(0.5, 0, 10)"),
    ]

    # create parameters with distribution assignments
    for pid, formula in formulas_data:
        print("{} = {}".format(pid, formula))
        _: libsbml.Parameter = _create_parameter(pid, model=model)
        assignment: libsbml.InitialAssignment = model.createInitialAssignment()
        assignment.setSymbol(pid)
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            raise IOError(f"{formula}, {libsbml.getLastParseL3Error()}")
        assignment.setMath(ast_node), "setting math"

    return doc


def uncertainty() -> libsbml.SBMLDocument:
    """Create uncertainty with UncertParameter."""
    doc: libsbml.SBMLDocument = _distrib_doc()
    model: libsbml.Model = doc.createModel()

    # parameter
    p: libsbml.Parameter = _create_parameter("p1", model=model)
    p_distrib: libsbml.DistribSBasePlugin = p.getPlugin("distrib")

    # --------------------------------------------
    # Build generic uncertainty for parameter
    # --------------------------------------------
    # 5.0 (mean) +- 0.3 (std) [2.0 - 8.0]

    uncertainty: libsbml.Uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("Basic example: 5.0 +- 0.3 [2.0 - 8.0]")
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    up_mean: libsbml.UncertParameter = uncertainty.createUncertParameter()
    up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
    up_mean.setValue(5.0)
    up_mean.setUnits(unit)

    up_sd: libsbml.UncertParameter = uncertainty.createUncertParameter()
    up_sd.setType(libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION)
    up_sd.setValue(0.3)
    up_sd.setUnits(unit)

    up_range = libsbml.UncertSpan()
    up_range.setType(libsbml.DISTRIB_UNCERTTYPE_RANGE)
    up_range.setValueLower(2.0)
    up_range.setValueUpper(8.0)
    up_range.setUnits(unit)
    check(uncertainty.addUncertParameter(up_range), "add the span")

    check(
        uncertainty.setAnnotation(
            """
    <body xmlns='http://www.w3.org/1999/xhtml'>
        <p>Experimental data from study</p>
    </body>
    """
        ),
        "set annotations",
    )

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
    uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("UncertParameter example")
    for k, parameter_type in enumerate(
        [
            libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
            libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
            libsbml.DISTRIB_UNCERTTYPE_MEAN,
            libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
            libsbml.DISTRIB_UNCERTTYPE_MODE,
            libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
            libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
            libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
        ]
    ):

        up: libsbml.UncertParameter = uncertainty.createUncertParameter()
        up.setType(parameter_type)
        up.setValue(k)
        up.setUnits(unit)

    # --------------------------------------------
    # Set of all UncertSpans
    # --------------------------------------------
    uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("UncertSpan example")
    for k, parameter_type in enumerate(
        [
            libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
            libsbml.DISTRIB_UNCERTTYPE_RANGE,
        ]
    ):

        up_range = libsbml.UncertSpan()
        up_range.setType(parameter_type)
        up_range.setValueLower(k - 1.0)
        up_range.setValueUpper(k + 1.0)
        up_range.setUnits(unit)
        check(uncertainty.addUncertParameter(up_range), "add the span")

    # --------------------------------------------
    # Use math for distribution definition
    # --------------------------------------------
    # 5.0 dimensionless * normal(1.0 mole, 3.0 mole)
    uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("math example: 5.0 dimensionless * normal(1.0 mole, 3.0 mole)")
    up = uncertainty.createUncertParameter()
    up.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
    up.setDefinitionURL("http://www.sbml.org/sbml/symbols/distrib/normal")
    ast = libsbml.parseL3FormulaWithModel(
        "5.0 dimensionless * normal(1.0 mole, 3.0 mole)", model
    )
    if not ast:
        raise ValueError
    up.setMath(ast)

    # --------------------------------------------
    # Use externalParameter
    # --------------------------------------------
    # https://sites.google.com/site/probonto/
    uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("ExternalParameter example")
    up = uncertainty.createUncertParameter()
    up.setType(libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER)
    up.setName("skewness")
    up.setValue(0.25)
    up.setUnits(unit)
    up.setDefinitionURL("http://purl.obolibrary.org/obo/STATO_0000068")

    # --------------------------------------------
    # Use external distribution definition
    # --------------------------------------------
    uncertainty = p_distrib.createUncertainty()
    uncertainty.setName("External distribution example")
    up = uncertainty.createUncertParameter()
    up.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
    up.setName("Geometric 1")
    up.setDefinitionURL("http://www.probonto.org/ontology#PROB_k0000782")
    up.setUnits(unit)

    # success probability of Geometric-1
    up_mean_geo1 = up.createUncertParameter()
    up_mean_geo1.setType(libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER)
    up_mean_geo1.setName("success probability of Geometric 1")
    up_mean_geo1.setValue(0.4)
    up_mean_geo1.setDefinitionURL("http://www.probonto.org/ontology#PROB_k0000789")

    return doc


def create_examples(tmp: bool = False) -> None:
    """Create distrib examples."""
    functions = [
        distrib_normal,
        distrib_all,
        uncertainty,
    ]
    for f_creator in functions:
        name = f_creator.__name__
        print(name)
        # distrib_example1()
        doc = f_creator()
        sbml = libsbml.writeSBMLToString(doc)
        print("-" * 80)
        print(sbml)
        print("-" * 80)

        if tmp:
            sbml_path = tempfile.mktemp()
        else:
            sbml_path = f"./{name}.xml"

        libsbml.writeSBMLToFile(doc, sbml_path)
        validation.validate_doc(doc)


if __name__ == "__main__":
    create_examples()
