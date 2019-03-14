"""
Code for working with the libsbml distrib package
"""
import libsbml
from sbmlutils import validation
from sbmlutils.validation import check

# TODO: function to check for distributions in ast_nodes (creates flag with the information)
# TODO: read the example cases


def distrib_example1():
    """ Create simple distrib model.

    :return:
    """
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("distrib", True)

    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = model.createParameter()  # type: libsbml.Parameter
    p.setId("p1")
    p.setValue(1.0)
    p.setConstant(False)

    # initial assignment
    assignment = model.createInitialAssignment()  # type: libsbml.InitialAssignment
    assignment.setSymbol("p1")
    ast_node = libsbml.parseL3FormulaWithModel("normal(0, 1.0)", model)
    assignment.setMath(ast_node)

    return doc


def distrib_units1():
    """ Create simple distrib model.

    :return:
    """
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("distrib", True)

    model = doc.createModel()  # type: libsbml.Model

    # parameter
    p = model.createParameter()  # type: libsbml.Parameter
    p.setId("p1")
    p.setValue(1.0)
    p.setConstant(False)
    unit = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
    check(p.setUnits(unit), "setting units")

    # initial assignment
    assignment = model.createInitialAssignment()  # type: libsbml.InitialAssignment
    assignment.setSymbol("p1")
    ast_node = libsbml.parseL3FormulaWithModel("1.0 mole * normal(0, 1.0)", model)
    assignment.setMath(ast_node)

    return doc


def distrib_example2():
    """ Create simple distrib model.

    :return:
    """
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("distrib", True)

    model = doc.createModel()  # type: libsbml.Model
    model_dist = model.getPlugin("distrib")  # type: libsbml.DistribModelPlugin

    # extended math approach
    formulas_data = [
        ('p_normal_1', 'normal(0, 1)'),
        ('p_normal_2', 'normal(0, 1, 0, 10'),
        ('p_uniform', 'uniform(5, 10)'),
        ('p_bernoulli', 'bernoulli(0.4)'),
        ('p_binomial_1', 'binomial(100, 0.3)'),
        ('p_binomial_2', 'binomial(100, 0.3, 0, 2)'),
        ('p_cauchy_1', 'cauchy(0, 1)'),
        ('p_cauchy_2', 'cauchy(0, 1, 0, 5)'),
        ('p_chisquare_1', 'chisquare(10)'),
        ('p_chisquare_2', 'chisquare(10, 0, 10'),
        ('p_exponential_1', 'exponential(1.0)'),
        ('p_exponential_2', 'exponential(1.0, 0, 10'),
        ('p_gamma_1', 'gamma(0, 1)'),
        ('p_gamma_2', 'gamma(0, 1, 0, 10'),
        ('p_laplace_1', 'laplace(0, 1)'),
        ('p_laplace_2', 'laplace(0, 1, 0, 10'),
        ('p_lognormal_1', 'lognormal(0, 1)'),
        ('p_lognormal_2', 'lognormal(0, 1, 0, 10)'),
        ('p_poisson_1', 'poisson(0.5)'),
        ('p_poisson_2', 'poisson(0.5, 0, 10)'),
        ('p_raleigh_1', 'raleigh(0.5)'),
        ('p_raleigh_2', 'raleigh(0.5, 0, 10)'),
    ]

    # create parameters with distribution assignments
    for pid, formula in formulas_data:
        print("{} = {}".format(pid, formula))
        p = model.createParameter()  # type: libsbml.Parameter
        p.setId(pid)
        p.setValue(1.0)
        p.setConstant(False)
        assignment = model.createInitialAssignment()  # type: libsbml.InitialAssignment
        assignment.setSymbol(pid)
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        assignment.setMath(ast_node)

    return doc


def uncertainty_example():
    """ Create simple distrib model.

    :return:
    """
    sbml_level = 3
    sbml_version = 1
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("distrib", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("distrib", True)

    model = doc.createModel()  # type: libsbml.Model
    model_dist = model.getPlugin("distrib")  # type: libsbml.DistribModelPlugin

    p = model.createParameter()  # type: libsbml.Parameter
    p.setId("p1")
    p.setValue(1.0)
    p.setConstant(False)
    p_distrib = p.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin

    # build uncertainty for the parameter
    uncertainty = libsbml.Uncertainty()  # type: libsbml.Uncertainty
    ex_p1 = libsbml.ExternalParameter()  # type: libsbml.ExternalParameter
    ex_p1.setId("ex_p1")
    uncertainty.addExternalParameter(ex_p1)
    p_distrib.setUncertainty(uncertainty)

    return doc


if __name__ == "__main__":

    # for f_creator in
    functions = [distrib_example1, distrib_example2, uncertainty_example]
    for f_creator in [distrib_units1]:
        name = f_creator.__name__
        print(name)
        # distrib_example1()
        doc = f_creator()
        sbml = libsbml.writeSBMLToString(doc)
        print("-" * 80)
        print(sbml)
        print("-" * 80)

        libsbml.writeSBMLToFile(doc, "./{}.xml".format(name))

        validation.check_doc(doc)
