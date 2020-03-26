import pytest

from sbmlutils.units import *
from sbmlutils.factory import *
from sbmlutils.modelcreator.creator import CoreModel
from sbmlutils.validation import check_doc


def check_model_dict(d):
    """Check that no errors."""
    # create model and print SBML
    core_model = CoreModel.from_dict(model_dict=d)
    core_model.create_sbml()
    assert core_model.doc is not None
    [Nall, Nerr, Nwar] = check_doc(core_model.doc, units_consistency=False)
    assert Nerr == 0


def test_assign_distribution():
    model_dict = {
        'mid': 'distrib_assignment',
        'packages': ['distrib'],
        'model_units': ModelUnits(time=UNIT_hr, extent=UNIT_KIND_MOLE,
                                  substance=UNIT_KIND_MOLE,
                                  length=UNIT_m, area=UNIT_m2,
                                  volume=UNIT_KIND_LITRE),
        'units': [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
        'parameters': [
            Parameter(sid="p1", value=0.0, unit=UNIT_mM)
        ],
        'assignments': [
            InitialAssignment('p1', 'normal(0 mM, 1 mM)'),
        ]
    }
    check_model_dict(model_dict)


def test_normal_distribution():
    model_dict = {
        'mid': 'normal',
        'packages': ['distrib'],
        'parameters': [
            Parameter('y', value=1.0),
            Parameter('z', value=1.0),
        ],
        'assignments': [
            InitialAssignment('y', 'normal(z, 10)'),
        ]
    }
    check_model_dict(model_dict)


def test_trunctated_normal_distribution():
    model_dict = {
        'mid': 'truncated_normal',
        'packages': ['distrib'],
        'parameters': [
            Parameter('y', value=1.0),
            Parameter('z', value=1.0),
        ],
        'assignments': [
            InitialAssignment('y', 'normal(z, 10, z-2, z+2)'),
        ]
    }
    check_model_dict(model_dict)


def test_conditional_event():
    model_dict = {
        'mid': 'conditional_events',
        'packages': ['distrib'],
        'parameters': [
            Parameter('x', value=1.0, constant=False)
        ],
        'events': [
            Event(
                "E0",
                trigger="time>2 && x<1",
                priority="uniform(0, 1)",
                trigger_initialValue=True, trigger_persistent=False,
                assignments={"x": "3"}
            ),
            Event(
                "E1",
                trigger="time>2 && x<1",
                priority="uniform(0, 2)",
                trigger_initialValue=True, trigger_persistent=False,
                assignments={"x": "5"}
            )
        ]
    }
    check_model_dict(model_dict)


def test_overview_distributions():
    model_dict = {
        'mid': 'all_distributions',
        'packages': ['distrib'],
        'assignments': [
            InitialAssignment('p_normal_1', 'normal(0, 1)'),
            InitialAssignment('p_normal_2', 'normal(0, 1, 0, 10)'),
            InitialAssignment('p_uniform', 'uniform(5, 10)'),
            InitialAssignment('p_bernoulli', 'bernoulli(0.4)'),
            InitialAssignment('p_binomial_1', 'binomial(100, 0.3)'),
            InitialAssignment('p_binomial_2', 'binomial(100, 0.3, 0, 2)'),
            InitialAssignment('p_cauchy_1', 'cauchy(0, 1)'),
            InitialAssignment('p_cauchy_2', 'cauchy(0, 1, 0, 5)'),
            InitialAssignment('p_chisquare_1', 'chisquare(10)'),
            InitialAssignment('p_chisquare_2', 'chisquare(10, 0, 10)'),
            InitialAssignment('p_exponential_1', 'exponential(1.0)'),
            InitialAssignment('p_exponential_2', 'exponential(1.0, 0, 10)'),
            InitialAssignment('p_gamma_1', 'gamma(0, 1)'),
            InitialAssignment('p_gamma_2', 'gamma(0, 1, 0, 10)'),
            InitialAssignment('p_laplace_1', 'laplace(0, 1)'),
            InitialAssignment('p_laplace_2', 'laplace(0, 1, 0, 10)'),
            InitialAssignment('p_lognormal_1', 'lognormal(0, 1)'),
            InitialAssignment('p_lognormal_2', 'lognormal(0, 1, 0, 10)'),
            InitialAssignment('p_poisson_1', 'poisson(0.5)'),
            InitialAssignment('p_poisson_2', 'poisson(0.5, 0, 10)'),
            InitialAssignment('p_raleigh_1', 'rayleigh(0.5)'),
            InitialAssignment('p_raleigh_2', 'rayleigh(0.5, 0, 10)'),
        ]
    }
    check_model_dict(model_dict)

def test_basic_uncertainty_example():
    import libsbml
    model_dict = {
        'mid': 'basic_example_1',
        'packages': ['distrib'],
        'compartments': [
            Compartment("C", value=1.0)
        ],
        'species': [
            Species(sid="s1", compartment="C", initialAmount=3.22,
                    uncertainties=[
                        Uncertainty(uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.3)
                        ])
                    ])
        ],
    }
    check_model_dict(model_dict)


def test_multiple_uncertainties():
    import libsbml
    model_dict = {
        'mid': 'multiple_uncertainties',
        'packages': ['distrib'],
        'model_units': ModelUnits(time=UNIT_hr, extent=UNIT_KIND_MOLE,
                                  substance=UNIT_KIND_MOLE,
                                  length=UNIT_m, area=UNIT_m2,
                                  volume=UNIT_KIND_LITRE),
        'units': [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
        'parameters': [
            Parameter(sid="p1", value=5.0, unit=UNIT_mM,
                      uncertainties=[
                          Uncertainty('p1_uncertainty_1', uncertParameters=[
                              UncertParameter(
                                  type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                  value=5.0, unit=UNIT_mM),
                              UncertParameter(
                                  type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                  value=0.3, unit=UNIT_mM),
                              UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                         valueLower=2.0, valueUpper=8.0,
                                         unit=UNIT_mM),
                          ]),
                          Uncertainty('p1_uncertainty_2', uncertParameters=[
                              UncertParameter(
                                  type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                  value=4.5, unit=UNIT_mM),
                              UncertParameter(
                                  type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                  value=1.1, unit=UNIT_mM),
                              UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                         valueLower=1.0, valueUpper=10.0,
                                         unit=UNIT_mM),
                          ])
                      ])
        ],
        'assignments': [
            InitialAssignment('p1', 'normal(0 mM, 1 mM)'),
        ]
    }
    check_model_dict(model_dict)


def test_define_random_variable():
    import libsbml
    model_dict = {
        'mid': 'random_variable',
        'packages': ['distrib'],
        'parameters': [
            Parameter("shape_Z", value=10.0),
            Parameter("scale_Z", value=0.1),
            Parameter("Z", value=0.1,
                      uncertainties=[
                          Uncertainty(formula="gamma(shape_Z, scale_Z)",
                                      uncertParameters=[
                                          UncertParameter(
                                              type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                              value=1.03),
                                          UncertParameter(
                                              type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
                                              value=0.97),
                                      ])
                      ])
        ]
    }
    check_model_dict(model_dict)


def test_paramerts_and_spans():
    import libsbml
    model_dict = {
        'mid': 'parameters_spans',
        'packages': ['distrib'],
        'parameters': [
            Parameter("p",
                      uncertainties=[
                          Uncertainty(
                              formula="normal(0, 1)",  # distribution
                              uncertParameters=[
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
                                      value=1.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
                                      value=2.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                      value=3.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
                                      value=4.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_MODE,
                                      value=5.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
                                      value=6.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
                                      value=7.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                      value=8.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
                                      value=9.0),
                                  UncertParameter(
                                      type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
                                      value=10.0),
                                  UncertSpan(
                                      type=libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
                                      valueLower=1.0, valueUpper=2.0),
                                  UncertSpan(
                                      type=libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
                                      valueLower=2.0, valueUpper=3.0),
                                  UncertSpan(
                                      type=libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
                                      valueLower=3.0, valueUpper=4.0),
                                  UncertSpan(
                                      type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                      valueLower=4.0, valueUpper=5.0),
                              ])
                      ])
        ]
    }
    check_model_dict(model_dict)