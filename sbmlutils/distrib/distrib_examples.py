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



def uncertainty_uncert_parameter():
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

    # add an annotation with SBO terms
    # TODO

    # --------------------------------------------
    # Set of all UncertParameters
    # --------------------------------------------
    # create second uncertainty which contains all the individual uncertainties
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty
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


    # build generic uncertainty for parameter
    # 5.0 (mean) +- 0.3 (std) [2.0 - 8.0]
    uncertainty = p_distrib.createUncertainty()  # type: libsbml.Uncertainty

    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    up_mean = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
    up_mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
    up_mean.setValue(5.0)
    up_mean.setUnits(unit)

    return doc


if __name__ == "__main__":

    functions = [
        # distrib_normal,
        # distrib_all,
        # uncertainty_distribution,
        uncertainty_uncert_parameter,
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

