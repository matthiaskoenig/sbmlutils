"""Test distrib functionality."""

import logging
from typing import Any

import libsbml
import pytest

from examples.distrib import (
    distrib_comp,
    distrib_packages_examples,
    distrib_uncertainties,
    distrib_uncertainty,
)
from sbmlutils.factory import *
from sbmlutils.metadata import BQB, SBO
from sbmlutils.validation import ValidationOptions, validate_doc


class U(Units):
    """UnitsDefinition."""

    hr = UnitDefinition("hr")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")


def test_distrib_examples() -> None:
    """Test distrib examples."""
    distrib_packages_examples.create_examples()


def test_add_uncertainty_example() -> None:
    """Test add uncertainty example."""
    distrib_uncertainty.add_uncertainty_example()


def check_model(model: Model) -> libsbml.SBMLDocument:
    """Check that no errors in given model."""
    # create model and print SBML
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()

    assert doc
    vresults = validate_doc(doc, options=ValidationOptions(units_consistency=False))

    # debugging
    if vresults.error_count > 0:
        error_log: libsbml.SBMLErrorLog = doc.getErrorLog()
        print(error_log.toString())

    assert vresults.is_valid()
    return doc


def test_assign_distribution() -> None:
    """Test assign distribution."""
    model_dict: dict[str, Any] = {
        "sid": "distrib_assignment",
        "packages": [Package.DISTRIB_V1],
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
    model: Model = Model(**model_dict)
    check_model(model)


def test_normal_distribution() -> None:
    """Test normal distribution."""
    model_dict: dict[str, Any] = {
        "sid": "normal",
        "packages": [Package.DISTRIB_V1],
        "parameters": [
            Parameter("y", value=1.0),
            Parameter("z", value=1.0),
        ],
        "assignments": [
            InitialAssignment("y", "normal(z, 10)"),
        ],
    }
    check_model(Model(**model_dict))


def test_trunctated_normal_distribution() -> None:
    """Test truncated normal distribution."""
    model_dict: dict[str, Any] = {
        "sid": "truncated_normal",
        "packages": [Package.DISTRIB_V1],
        "parameters": [
            Parameter("y", value=1.0),
            Parameter("z", value=1.0),
        ],
        "assignments": [
            InitialAssignment("y", "normal(z, 10, z-2, z+2)"),
        ],
    }
    check_model(Model(**model_dict))


def test_conditional_event() -> None:
    """Test conditional event."""
    model_dict: dict[str, Any] = {
        "sid": "conditional_events",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_overview_distributions() -> None:
    """Test all distributions."""
    model_dict: dict[str, Any] = {
        "sid": "all_distributions",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_basic_uncertainty_example() -> None:
    """Test basic uncertainty example."""
    import libsbml

    model_dict: dict[str, Any] = {
        "sid": "basic_example_1",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_multiple_uncertainties() -> None:
    """Test multiple uncertainties."""
    model_dict: dict[str, Any] = {
        "sid": "multiple_uncertainties",
        "packages": [Package.DISTRIB_V1],
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
    doc: libsbml.SBMLDocument = check_model(Model(**model_dict))
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
    """Test definition of random variable."""
    import libsbml

    model_dict: dict[str, Any] = {
        "sid": "random_variable",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_parameters_and_spans() -> None:
    """Test parameters and spans."""
    model_dict: dict[str, Any] = {
        "sid": "parameters_spans",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_sabiork_uncertainty() -> None:
    """Test SabioRK uncertainty."""
    model_dict: dict[str, Any] = {
        "sid": "sabiork_parameter",
        "packages": [Package.DISTRIB_V1],
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
    check_model(Model(**model_dict))


def test_uncert_parameter_writes_var() -> None:
    """Test that an UncertParameter with a var writes it.

    `create_sbml` called `setValue(uncertParameter.var)` instead of `setVar`.
    """
    doc = libsbml.SBMLDocument(3, 1)
    doc.enablePackage(
        "http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True
    )
    model = doc.createModel()
    parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setConstant(True)

    uncertainty = Uncertainty(
        uncertParameters=[
            UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, var="p2")
        ]
    )
    uncertainty.create_sbml(parameter, model)

    up = parameter.getPlugin("distrib").getUncertainty(0).getUncertParameter(0)
    assert up.getVar() == "p2"


def test_uncert_span_writes_var_upper() -> None:
    """Test that an UncertSpan with a varUpper writes it.

    `create_sbml` called `up_span.setValueLower(uncertSpan.varUpper)` instead
    of `up_span.setVarUpper(uncertSpan.varUpper)`, so the upper bound
    variable reference was never written and instead clobbered the lower
    numeric value.
    """
    doc = libsbml.SBMLDocument(3, 1)
    doc.enablePackage(
        "http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True
    )
    model = doc.createModel()
    parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setConstant(True)

    uncertainty = Uncertainty(
        uncertSpans=[
            UncertSpan(
                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                valueLower=1.0,
                varUpper="p2",
            )
        ]
    )
    uncertainty.create_sbml(parameter, model)

    # `UncertSpan` is stored (and retrieved) as an `UncertParameter` in
    # libsbml's distrib implementation.
    span = parameter.getPlugin("distrib").getUncertainty(0).getUncertParameter(0)
    assert span.getValueLower() == 1.0
    assert span.getVarUpper() == "p2"


#: the sboTerm written on the children of the uncertainty in the metadata tests
UNCERT_SBO = "SBO:0000612"


@pytest.fixture
def uncert_metadata_doc() -> libsbml.SBMLDocument:
    """Write an uncertainty whose children carry every metadata field.

    The model is serialized and read back, so that the assertions are made on
    a document which went through the SBML writer and parser, not on the
    objects the factory created.

    Returns:
        the document read back from the written SBML; the test has to hold it,
        libsbml objects do not keep their document alive
    """
    model = Model(
        "uncert_metadata",
        packages=[Package.DISTRIB_V1, Package.FBC_V3],
        parameters=[
            Parameter(
                "p1",
                value=1.0,
                uncertainties=[
                    Uncertainty(
                        "u1",
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                                value=5.0,
                                sid="up_mean",
                                name="mean of p1",
                                metaId="meta_up_mean",
                                sboTerm=UNCERT_SBO,
                                annotations=[(BQB.IS, "chebi/CHEBI:15377")],
                                notes="mean of the measurements",
                                keyValuePairs=[
                                    KeyValuePair(
                                        key="source",
                                        value="sabiork",
                                        uri="https://example.org/kvp",
                                    )
                                ],
                            )
                        ],
                        uncertSpans=[
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                valueLower=1.0,
                                valueUpper=9.0,
                                sid="up_range",
                                name="range of p1",
                                metaId="meta_up_range",
                                sboTerm=UNCERT_SBO,
                                annotations=[(BQB.IS, "chebi/CHEBI:15377")],
                                notes="range of the measurements",
                                keyValuePairs=[
                                    KeyValuePair(
                                        key="source",
                                        value="sabiork",
                                        uri="https://example.org/kvp",
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()
    doc_read: libsbml.SBMLDocument = libsbml.readSBMLFromString(
        libsbml.writeSBMLToString(doc)
    )
    return doc_read


def _uncert_child(doc: libsbml.SBMLDocument, sid: str) -> libsbml.UncertParameter:
    """Get the child of the uncertainty with the given id.

    A span is stored and read back as an `UncertParameter` in the same list,
    so both children are looked up by their id rather than by their position.

    Args:
        doc: the document written by the `uncert_metadata_doc` fixture
        sid: the id of the uncert parameter or span

    Returns:
        the libsbml.UncertParameter with this id
    """
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    children: libsbml.ListOfUncertParameters = uncertainty.getListOfUncertParameters()
    for k in range(children.size()):
        child: libsbml.UncertParameter = children.get(k)
        if child.getId() == sid:
            return child
    raise AssertionError(f"No uncert parameter '{sid}' in '{uncertainty}'.")


@pytest.mark.parametrize("sid", ["up_mean", "up_range"])
def test_uncert_child_writes_meta_id_and_sbo_term(
    uncert_metadata_doc: libsbml.SBMLDocument, sid: str
) -> None:
    """Test that a metaId and an sboTerm are written on a child of an uncertainty."""
    child = _uncert_child(uncert_metadata_doc, sid)
    assert child.getMetaId() == f"meta_{sid}"
    assert child.getSBOTermID() == UNCERT_SBO


@pytest.mark.parametrize("sid", ["up_mean", "up_range"])
def test_uncert_child_writes_id_and_name(
    uncert_metadata_doc: libsbml.SBMLDocument, sid: str
) -> None:
    """Test that an id and a name are written on a child of an uncertainty."""
    child = _uncert_child(uncert_metadata_doc, sid)
    assert child.getId() == sid
    assert child.getName() == ("mean of p1" if sid == "up_mean" else "range of p1")


@pytest.mark.parametrize("sid", ["up_mean", "up_range"])
def test_uncert_child_writes_notes(
    uncert_metadata_doc: libsbml.SBMLDocument, sid: str
) -> None:
    """Test that notes are written on a child of an uncertainty."""
    child = _uncert_child(uncert_metadata_doc, sid)
    assert child.isSetNotes()
    assert "of the measurements" in child.getNotesString()


@pytest.mark.parametrize("sid", ["up_mean", "up_range"])
def test_uncert_child_writes_annotations(
    uncert_metadata_doc: libsbml.SBMLDocument, sid: str
) -> None:
    """Test that annotations are written on a child of an uncertainty."""
    child = _uncert_child(uncert_metadata_doc, sid)
    assert child.getNumCVTerms() == 1
    cvterm: libsbml.CVTerm = child.getCVTerm(0)
    assert cvterm.getBiologicalQualifierType() == libsbml.BQB_IS
    assert cvterm.getResourceURI(0).endswith("CHEBI:15377")


@pytest.mark.parametrize("sid", ["up_mean", "up_range"])
def test_uncert_child_writes_key_value_pairs(
    uncert_metadata_doc: libsbml.SBMLDocument, sid: str
) -> None:
    """Test that fbc key value pairs are written on a child of an uncertainty."""
    child = _uncert_child(uncert_metadata_doc, sid)
    child_fbc: libsbml.FbcSBasePlugin = child.getPlugin("fbc")
    assert child_fbc is not None
    assert child_fbc.getNumKeyValuePairs() == 1
    kvp: libsbml.KeyValuePair = child_fbc.getKeyValuePair(0)
    assert kvp.getKey() == "source"
    assert kvp.getValue() == "sabiork"
    assert kvp.getUri() == "https://example.org/kvp"


def test_uncert_child_without_id_writes_no_id() -> None:
    """Test that a child of an uncertainty without an id is written without one."""
    model = Model(
        "uncert_without_id",
        packages=[Package.DISTRIB_V1],
        parameters=[
            Parameter(
                "p1",
                value=1.0,
                uncertainties=[
                    Uncertainty(
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0
                            )
                        ],
                        uncertSpans=[
                            UncertSpan(
                                type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                                valueLower=1.0,
                                valueUpper=9.0,
                            )
                        ],
                    )
                ],
            )
        ],
    )
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    children: libsbml.ListOfUncertParameters = uncertainty.getListOfUncertParameters()
    assert children.size() == 2
    for k in range(children.size()):
        assert not children.get(k).isSetId()
    assert "distrib:id" not in libsbml.writeSBMLToString(doc)


@pytest.mark.parametrize("field", ["uncertainties", "port", "replacedBy"])
def test_uncert_children_do_not_offer_the_model_bound_fields(field: str) -> None:
    """Test that the `Sbase` fields which need the model are not offered.

    A child of an uncertainty is written without the `libsbml.Model`, so the
    three fields which are written from the model are refused by the
    constructor instead of being accepted and dropped, see the class
    docstrings.
    """
    with pytest.raises(TypeError):
        UncertParameter(
            type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
            value=1.0,
            **{field: None},
        )
    with pytest.raises(TypeError):
        UncertSpan(
            type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
            valueLower=1.0,
            valueUpper=2.0,
            **{field: None},
        )


def test_uncert_child_writes_no_nested_uncertainties() -> None:
    """Test that a child of an uncertainty writes no uncertainties of its own.

    The children of an uncertainty are written with `model=None`, which is
    what keeps `Sbase._set_fields` from descending into the `uncertainties` of
    an element. The field is not offered by the constructor, so it is set here
    the only way it can be set, on the object, and nothing is written for it.
    """
    up = UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0)
    up.uncertainties = [
        Uncertainty(
            uncertParameters=[
                UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=1.0)
            ]
        )
    ]
    model = Model(
        "nested_uncertainties",
        packages=[Package.DISTRIB_V1],
        parameters=[
            Parameter(
                "p1", value=1.0, uncertainties=[Uncertainty(uncertParameters=[up])]
            )
        ],
    )
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    child: libsbml.UncertParameter = uncertainty.getUncertParameter(0)
    child_distrib: libsbml.DistribSBasePlugin = child.getPlugin("distrib")
    assert child_distrib.getNumUncertainties() == 0


def test_distrib_examples_log_no_authoring_hint(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that the children of an uncertainty log no authoring hint.

    An uncert parameter and a span have no name and no sboTerm in any of the
    examples, and neither is a hint worth logging on them: both are optional
    on an element which is identified by its type.
    """
    with caplog.at_level(logging.WARNING, logger="sbmlutils.factory"):
        Document(model=distrib_uncertainties.model).create_sbml()
        Document(model=distrib_comp.model).create_sbml()

    hints = [
        record.getMessage()
        for record in caplog.records
        if "should be set on" in record.getMessage()
        and (
            "UncertParameter" in record.getMessage()
            or "UncertSpan" in record.getMessage()
        )
    ]
    assert not hints, hints
