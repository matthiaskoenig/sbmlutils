import libsbml

from sbmlutils.distrib import distrib_examples, distrib_packages
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.validation import validate_doc


class U(Units):
    """UnitsDefinition."""

    hr = UnitDefinition("hr")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")


def test_distrib_examples() -> None:
    distrib_examples.create_examples(tmp=True)


def test_add_uncertainty_example() -> None:
    distrib_packages.add_uncertainty_example(tmp=True)


def check_model(model: Model) -> libsbml.SBMLDocument:
    """Check that no errors in given model."""
    # create model and print SBML
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()

    assert doc
    vresults = validate_doc(doc, units_consistency=False)

    # debugging
    if vresults.error_count > 0:
        error_log: libsbml.SBMLErrorLog = doc.getErrorLog()
        print(error_log.toString())

    assert vresults.is_valid()
    return doc


def test_assign_distribution() -> None:
    model_dict = {
        "sid": "distrib_assignment",
        "packages": ["distrib"],
        "model_units": ModelUnits(
            time=U.hr,
            extent=U.mole,
            substance=U.mole,
            length=U.meter,
            area=U.m2,
            volume=U.liter,
        ),
        "units": U,
        "parameters": [Parameter(sid="p1", value=0.0, unit=U.mM)],
        "assignments": [
            InitialAssignment("p1", "normal(0 mM, 1 mM)"),
        ],
    }
    model: Model = Model(**model_dict)  # type: ignore
    check_model(model)


def test_normal_distribution() -> None:
    model_dict = {
        "sid": "normal",
        "packages": ["distrib"],
        "parameters": [
            Parameter("y", value=1.0),
            Parameter("z", value=1.0),
        ],
        "assignments": [
            InitialAssignment("y", "normal(z, 10)"),
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_trunctated_normal_distribution() -> None:
    model_dict = {
        "sid": "truncated_normal",
        "packages": ["distrib"],
        "parameters": [
            Parameter("y", value=1.0),
            Parameter("z", value=1.0),
        ],
        "assignments": [
            InitialAssignment("y", "normal(z, 10, z-2, z+2)"),
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_conditional_event() -> None:
    model_dict = {
        "sid": "conditional_events",
        "packages": ["distrib"],
        "parameters": [Parameter("x", value=1.0, constant=False)],
        "events": [
            Event(
                "E0",
                trigger="time>2 && x<1",
                priority="uniform(0, 1)",
                trigger_initialValue=True,
                trigger_persistent=False,
                assignments={"x": "3"},
            ),
            Event(
                "E1",
                trigger="time>2 && x<1",
                priority="uniform(0, 2)",
                trigger_initialValue=True,
                trigger_persistent=False,
                assignments={"x": "5"},
            ),
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_overview_distributions() -> None:
    model_dict = {
        "sid": "all_distributions",
        "packages": ["distrib"],
        "assignments": [
            InitialAssignment("p_normal_1", "normal(0, 1)"),
            InitialAssignment("p_normal_2", "normal(0, 1, 0, 10)"),
            InitialAssignment("p_uniform", "uniform(5, 10)"),
            InitialAssignment("p_bernoulli", "bernoulli(0.4)"),
            InitialAssignment("p_binomial_1", "binomial(100, 0.3)"),
            InitialAssignment("p_binomial_2", "binomial(100, 0.3, 0, 2)"),
            InitialAssignment("p_cauchy_1", "cauchy(0, 1)"),
            InitialAssignment("p_cauchy_2", "cauchy(0, 1, 0, 5)"),
            InitialAssignment("p_chisquare_1", "chisquare(10)"),
            InitialAssignment("p_chisquare_2", "chisquare(10, 0, 10)"),
            InitialAssignment("p_exponential_1", "exponential(1.0)"),
            InitialAssignment("p_exponential_2", "exponential(1.0, 0, 10)"),
            InitialAssignment("p_gamma_1", "gamma(0, 1)"),
            InitialAssignment("p_gamma_2", "gamma(0, 1, 0, 10)"),
            InitialAssignment("p_laplace_1", "laplace(0, 1)"),
            InitialAssignment("p_laplace_2", "laplace(0, 1, 0, 10)"),
            InitialAssignment("p_lognormal_1", "lognormal(0, 1)"),
            InitialAssignment("p_lognormal_2", "lognormal(0, 1, 0, 10)"),
            InitialAssignment("p_poisson_1", "poisson(0.5)"),
            InitialAssignment("p_poisson_2", "poisson(0.5, 0, 10)"),
            InitialAssignment("p_raleigh_1", "rayleigh(0.5)"),
            InitialAssignment("p_raleigh_2", "rayleigh(0.5, 0, 10)"),
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_basic_uncertainty_example() -> None:
    import libsbml

    model_dict = {
        "sid": "basic_example_1",
        "packages": ["distrib"],
        "compartments": [Compartment("C", value=1.0)],
        "species": [
            Species(
                sid="s1",
                compartment="C",
                initialAmount=3.22,
                uncertainties=[
                    Uncertainty(
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.3,
                            )
                        ]
                    )
                ],
            )
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_multiple_uncertainties() -> None:
    model_dict = {
        "sid": "multiple_uncertainties",
        "packages": ["distrib"],
        "model_units": ModelUnits(
            time=U.hr,
            extent=U.mole,
            substance=U.mole,
            length=U.meter,
            area=U.m2,
            volume=U.liter,
        ),
        "units": U,
        "parameters": [
            Parameter(
                sid="p1",
                value=5.0,
                unit=U.mM,
                uncertainties=[
                    Uncertainty(
                        "p1_uncertainty_1",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                value=5.0,
                                unit=U.mM,
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.3,
                                unit=U.mM,
                            ),
                        ],
                        uncertSpans=[
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                valueLower=2.0,
                                valueUpper=8.0,
                                unit=U.mM,
                            ),
                        ],
                    ),
                    Uncertainty(
                        "p1_uncertainty_2",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                value=4.5,
                                unit=U.mM,
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=1.1,
                                unit=U.mM,
                            ),
                        ],
                        uncertSpans=[
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                valueLower=1.0,
                                valueUpper=10.0,
                                unit=U.mM,
                            ),
                        ],
                    ),
                ],
            )
        ],
        "assignments": [
            InitialAssignment("p1", "normal(0 mM, 1 mM)"),
        ],
    }
    doc: libsbml.SBMLDocument = check_model(Model(**model_dict))  # type: ignore
    assert doc
    model: libsbml.Model = doc.getModel()
    assert model
    p: libsbml.Parameter = model.getParameter("p1")
    assert p
    p_distrib: libsbml.DistribSBasePlugin = p.getPlugin("distrib")
    assert p_distrib
    list_uncertainties: libsbml.ListOfUncertainties = p_distrib.getListOfUncertainties()

    assert list_uncertainties
    n_uncertainties = p_distrib.getNumUncertainties()
    assert n_uncertainties == 2
    for k in range(n_uncertainties):
        uc: libsbml.Uncertainty = p_distrib.getUncertainty(k)
        assert uc
        assert uc.isSetId()


def test_define_random_variable() -> None:
    import libsbml

    model_dict = {
        "sid": "random_variable",
        "packages": ["distrib"],
        "parameters": [
            Parameter("shape_Z", value=10.0),
            Parameter("scale_Z", value=0.1),
            Parameter(
                "Z",
                value=0.1,
                uncertainties=[
                    Uncertainty(
                        formula="gamma(shape_Z, scale_Z)",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=1.03
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=0.97
                            ),
                        ],
                    )
                ],
            ),
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_parameters_and_spans() -> None:
    model_dict = {
        "sid": "parameters_spans",
        "packages": ["distrib"],
        "parameters": [
            Parameter(
                "p",
                uncertainties=[
                    Uncertainty(
                        formula="normal(0, 1)",  # distribution
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
                                value=1.0,
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_KURTOSIS, value=2.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=3.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEDIAN, value=4.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MODE, value=5.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE, value=6.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_SKEWNESS, value=7.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=8.0,
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR, value=9.0
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=10.0
                            ),
                        ],
                        uncertSpans=[
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
                                valueLower=1.0,
                                valueUpper=2.0,
                            ),
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
                                valueLower=2.0,
                                valueUpper=3.0,
                            ),
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
                                valueLower=3.0,
                                valueUpper=4.0,
                            ),
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                valueLower=4.0,
                                valueUpper=5.0,
                            ),
                        ],
                    )
                ],
            )
        ],
    }
    check_model(Model(**model_dict))  # type: ignore


def test_sabiork_uncertainty() -> None:
    model_dict = {
        "sid": "sabiork_parameter",
        "packages": ["distrib"],
        "model_units": ModelUnits(
            time=U.hr,
            extent=U.mole,
            substance=U.mole,
            length=U.meter,
            area=U.m2,
            volume=U.liter,
        ),
        "units": U,
        "parameters": [
            Parameter(
                sid="Km_glc",
                name="Michelis-Menten constant glucose",
                value=5.0,
                unit=U.mM,
                sboTerm=SBO.MICHAELIS_CONSTANT,
                uncertainties=[
                    Uncertainty(
                        sid="uncertainty1",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.07
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.97,
                            ),
                        ],
                        annotations=[
                            (BQB.IS, "sabiork.kineticrecord/793"),  # entry in SABIO-RK
                            (BQB.HAS_TAXON, "taxonomy/9606"),  # homo sapiens
                            (BQB.IS, "ec-code/2.7.1.2"),  # glucokinase
                            (BQB.IS, "uniprot/P35557"),  # Glucokinase homo sapiens
                            (BQB.IS, "bto/BTO:0000075"),  # liver
                        ],
                    ),
                    Uncertainty(
                        sid="uncertainty2",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.7
                            ),
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.11,
                            ),
                        ],
                        annotations=[
                            (BQB.IS, "sabiork.kineticrecord/2581"),
                            # entry in SABIO-RK
                            (BQB.HAS_TAXON, "taxonomy/9606"),  # homo sapiens
                            (BQB.IS, "ec-code/2.7.1.2"),  # glucokinase
                            (BQB.IS, "uniprot/P35557"),  # Glucokinase homo sapiens
                            (BQB.IS, "bto/BTO:0000075"),  # liver
                        ],
                    ),
                ],
            )
        ],
    }
    check_model(Model(**model_dict))  # type: ignore
