"""
Code for working with the libsbml distrib package
"""
import libsbml
from sbmlutils import validation
from sbmlutils.validation import check

# TODO: function to check for distributions in ast_nodes (creates flag with the information)
# TODO: read the example cases


def _distrib_doc():
    """ Creates a distrib document. """
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("distrib", True)

    return doc


def _create_parameter(pid, model: libsbml.Model):
    # parameter
    p = model.createParameter()  # type: libsbml.Parameter
    p.setId(pid)
    p.setValue(1.0)
    p.setConstant(False)
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    p.setUnits(unit)
    return p


def distrib_normal():
    """ Create simple distrib model.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = _create_parameter("p1", model=model)  # type: libsbml.Parameter

    # initial assignment
    assignment = model.createInitialAssignment()  # type: libsbml.InitialAssignment
    assignment.setSymbol("p1")
    ast_node = libsbml.parseL3FormulaWithModel("1.0 mole * normal(0, 1.0)", model)
    assignment.setMath(ast_node)

    return doc


def distrib_all():
    """ Create simple distrib model.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    # extended math approach
    formulas_data = [
        ('p_normal_1', 'normal(0, 1)'),
        ('p_normal_2', 'normal(0, 1, 0, 10)'),
        ('p_uniform', 'uniform(5, 10)'),
        ('p_bernoulli', 'bernoulli(0.4)'),
        ('p_binomial_1', 'binomial(100, 0.3)'),
        ('p_binomial_2', 'binomial(100, 0.3, 0, 2)'),
        ('p_cauchy_1', 'cauchy(0, 1)'),
        ('p_cauchy_2', 'cauchy(0, 1, 0, 5)'),
        ('p_chisquare_1', 'chisquare(10)'),
        ('p_chisquare_2', 'chisquare(10, 0, 10)'),
        ('p_exponential_1', 'exponential(1.0)'),
        ('p_exponential_2', 'exponential(1.0, 0, 10)'),
        ('p_gamma_1', 'gamma(0, 1)'),
        ('p_gamma_2', 'gamma(0, 1, 0, 10)'),
        ('p_laplace_1', 'laplace(0, 1)'),
        ('p_laplace_2', 'laplace(0, 1, 0, 10)'),
        ('p_lognormal_1', 'lognormal(0, 1)'),
        ('p_lognormal_2', 'lognormal(0, 1, 0, 10)'),
        ('p_poisson_1', 'poisson(0.5)'),
        ('p_poisson_2', 'poisson(0.5, 0, 10)'),
        ('p_raleigh_1', 'rayleigh(0.5)'),
        ('p_raleigh_2', 'rayleigh(0.5, 0, 10)'),
    ]

    # create parameters with distribution assignments
    for pid, formula in formulas_data:
        print("{} = {}".format(pid, formula))
        p = _create_parameter(pid, model=model)  # type: libsbml.Parameter
        assignment = model.createInitialAssignment()  # type: libsbml.InitialAssignment
        assignment.setSymbol(pid)
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            raise IOError("{}, {}".format(formula,
                                          libsbml.getLastParseL3Error()))
        assignment.setMath(ast_node), "setting math"

    return doc


def uncertainty_distribution():
    """ Create uncertainty based on distribution.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = _create_parameter("p1", model=model)  # type: libsbml.Parameter
    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    # build uncertainty for the parameter
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
    distribution = uncertainty.createDistribution()  # type: libsbml.Distribution
    ast_node = libsbml.parseL3FormulaWithModel("normal(0, 1)", model)  # type: libsbml.ASTNode
    distribution.setMath(ast_node)
    return doc


def uncertainty_uncertvalue():
    """ Create uncertainty based on UncertStatisticSpan.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = _create_parameter("p1", model=model)  # type: libsbml.Parameter
    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    # build uncertainty for the parameter
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty

    # UncertValue
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    for f in [
        uncertainty.createCoefficientOfVariation,
        uncertainty.createKurtosis,
        uncertainty.createMean,
        uncertainty.createMedian,
        uncertainty.createMode,
        uncertainty.createSampleSize,
        uncertainty.createSkewness,
        uncertainty.createStandardDeviation,
        uncertainty.createStandardError,
        uncertainty.createVariance,
        ]:

        uncert_value = f()  # type: libsbml.UncertValue
        uncert_value.setValue(1.0)
        uncert_value.setUnits(unit)

    uncertainty = p_distrib.getUncertainty()  # type: libsbml.Uncertainty
    uncertainty.getMe

    return doc


def uncertainty_uncertspan():
    """ Create uncertainty based on UncertSpan.

    :return:
    """
    doc = _distrib_doc()
    model = doc.createModel()  # type: libsbml.Model

    p = _create_parameter("p1", model=model)  # type: libsbml.Parameter
    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    # build uncertainty for the parameter
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty

    # UncertSpan
    print("UncertSpan")
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    uncert_span = uncertainty.createConfidenceInterval()  # type: libsbml.UncertStatisticSpan
    uncert_span.setValueLower(1.0)
    uncert_span.setValueUpper(10.0)


    # External Parameter
    # p_distrib.setUncertainty(uncertainty)
    return doc


if __name__ == "__main__":

    functions = [
        distrib_normal,
        distrib_all,
        uncertainty_distribution,
        uncertainty_uncertvalue,
        uncertainty_uncertspan
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
        sbml_path = "./{}.xml".format(name)

        libsbml.writeSBMLToFile(doc, sbml_path)
        validation.check_doc(doc)

