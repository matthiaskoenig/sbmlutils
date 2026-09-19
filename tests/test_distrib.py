"""Test distrib functionality."""

import logging
from pathlib import Path
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
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import (
    DISTRIB_COMP_FLAT_SBML,
    DISTRIB_COMP_SBML,
    DISTRIB_UNCERTAINTIES_SBML,
    EXAMPLES_DIR,
    RESOURCES_DIR,
)
from sbmlutils.validation import ValidationOptions, validate_doc

#: every fixture of the repository which carries an uncertainty
DISTRIB_FIXTURES: list[Path] = [
    RESOURCES_DIR / "distrib" / "uncertainty.xml",
    RESOURCES_DIR / "distrib" / "e_coli_core_expression.xml",
    DISTRIB_UNCERTAINTIES_SBML,
    DISTRIB_COMP_SBML,
    DISTRIB_COMP_FLAT_SBML,
    EXAMPLES_DIR / "model.xml",
]


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


def _uncertainty_document(*uncertainties: Uncertainty) -> libsbml.SBMLDocument:
    """Write the uncertainties on a parameter and read the SBML back.

    Args:
        uncertainties: the uncertainties of the parameter `p1`

    Returns:
        the document read back from the written SBML; the caller has to hold
        it, libsbml objects do not keep their document alive
    """
    model = Model(
        "uncertainty_fields",
        packages=[Package.DISTRIB_V1],
        parameters=[
            Parameter("p1", value=1.0, uncertainties=list(uncertainties)),
            Parameter("p2", value=2.0),
        ],
    )
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()
    doc_read: libsbml.SBMLDocument = libsbml.readSBMLFromString(
        libsbml.writeSBMLToString(doc)
    )
    return doc_read


def _children(
    doc: libsbml.SBMLDocument, index: int = 0
) -> list[libsbml.UncertParameter]:
    """Get the children of an uncertainty of the parameter `p1`.

    Args:
        doc: a document written by `_uncertainty_document`, which the caller holds
        index: the position of the uncertainty in the list of uncertainties

    Returns:
        the uncert parameters and spans of the uncertainty, in document order
    """
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(index)
    )
    return [
        uncertainty.getUncertParameter(k)
        for k in range(uncertainty.getNumUncertParameters())
    ]


def test_uncert_parameter_writes_a_definition_url() -> None:
    """Test that the definitionURL of an external parameter is written.

    A `distrib:definitionURL` is how an uncert parameter names the
    distribution or the external parameter it stands for, e.g. a term of
    ProbOnto.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertParameters=[
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
                    value=0.25,
                    definitionURL="http://purl.obolibrary.org/obo/STATO_0000068",
                )
            ]
        )
    )

    (child,) = _children(doc)
    assert child.getTypeAsString() == "externalParameter"
    assert child.getDefinitionURL() == "http://purl.obolibrary.org/obo/STATO_0000068"


def test_uncert_parameter_writes_math() -> None:
    """Test that the math of a distribution uncert parameter is written.

    An uncert parameter of the type `distribution` states the distribution as
    math, a call of a distrib csymbol.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertParameters=[
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
                    definitionURL="http://www.sbml.org/sbml/symbols/distrib/normal",
                    math="normal(1 mole, 3 mole)",
                )
            ]
        )
    )

    (child,) = _children(doc)
    assert child.isSetMath()
    assert libsbml.formulaToL3String(child.getMath()) == "normal(1 mole, 3 mole)"


def test_uncert_span_writes_a_definition_url_and_math() -> None:
    """Test that a span carries a definitionURL and math as well.

    `distrib:uncertSpan` is a `distrib:uncertParameter` with two bounds in
    SBML, so it carries every attribute of one.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertSpans=[
                UncertSpan(
                    type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                    valueLower=1.0,
                    valueUpper=4.0,
                    definitionURL="http://purl.obolibrary.org/obo/STATO_0000035",
                    math="1 + 3",
                )
            ]
        )
    )

    (child,) = _children(doc)
    assert child.getDefinitionURL() == "http://purl.obolibrary.org/obo/STATO_0000035"
    assert libsbml.formulaToL3String(child.getMath()) == "1 + 3"


def test_uncert_parameter_writes_nested_uncert_parameters() -> None:
    """Test that the uncert parameters of an uncert parameter are written.

    SBML allows a `distrib:listOfUncertParameters` under an uncert parameter
    of the type `distribution`, which is how the parameters of an external
    distribution are given, see `resources/distrib/uncertainty.xml`.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertParameters=[
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
                    value=1.0,
                    definitionURL="http://www.probonto.org/ontology#PROB_k0000782",
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
                            value=0.4,
                            name="success probability",
                            definitionURL=(
                                "http://www.probonto.org/ontology#PROB_k0000789"
                            ),
                        )
                    ],
                )
            ]
        )
    )

    (child,) = _children(doc)
    assert child.getNumUncertParameters() == 1
    nested: libsbml.UncertParameter = child.getUncertParameter(0)
    assert nested.getTypeAsString() == "externalParameter"
    assert nested.getValue() == 0.4
    assert nested.getName() == "success probability"
    assert nested.getDefinitionURL() == "http://www.probonto.org/ontology#PROB_k0000789"


@pytest.mark.parametrize(
    "type_, written",
    [
        (libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION, "distribution"),
        (libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER, "externalParameter"),
    ],
)
def test_uncertainty_writes_a_distribution_and_an_external_parameter(
    type_: int, written: str
) -> None:
    """Test that the two types an uncertainty could not write are written.

    `distribution` and `externalParameter` were refused by the type check of
    `Uncertainty.create_sbml`: the element was dropped with an error, and a
    distribution could only be written through the `formula` shortcut.
    """
    doc = _uncertainty_document(
        Uncertainty(uncertParameters=[UncertParameter(type=type_, value=0.5)])
    )

    (child,) = _children(doc)
    assert child.getTypeAsString() == written


def test_uncertainty_keeps_the_order_of_its_children() -> None:
    """Test that the children are written in the order they are given in.

    The `distrib:listOfUncertParameters` holds the parameters and the spans
    of an uncertainty in one list, so `uncertParameters` is that list and
    takes both; a span before a parameter stays before it.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertParameters=[
                UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0),
                UncertSpan(
                    type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                    valueLower=1.0,
                    valueUpper=9.0,
                ),
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.3
                ),
            ]
        )
    )

    assert [child.getElementName() for child in _children(doc)] == [
        "uncertParameter",
        "uncertSpan",
        "uncertParameter",
    ]


def test_uncertainty_writes_the_spans_of_the_span_argument_first() -> None:
    """Test that the `uncertSpans` argument writes its spans before the parameters.

    `uncertSpans` is the authoring style of two lists, which has no place for
    an order between them; the spans are written first, which is the order
    such an uncertainty has always been written in.
    """
    doc = _uncertainty_document(
        Uncertainty(
            uncertParameters=[
                UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0)
            ],
            uncertSpans=[
                UncertSpan(
                    type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                    valueLower=1.0,
                    valueUpper=9.0,
                )
            ],
        )
    )

    assert [child.getElementName() for child in _children(doc)] == [
        "uncertSpan",
        "uncertParameter",
    ]


def test_uncertainty_of_a_formula_writes_one_distribution_parameter() -> None:
    """Test that the formula shortcut writes exactly one distribution parameter.

    `formula` is the authoring shortcut for an uncert parameter of the type
    `distribution` with the definitionURL of the distribution it names and
    the formula as its math. It is normalized into that parameter when the
    uncertainty is constructed, so it is written exactly once, and it is the
    last child, after the explicitly given ones.
    """
    uncertainty = Uncertainty(
        formula="normal(2.0, 2.0)",
        uncertParameters=[
            UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.0)
        ],
    )
    doc = _uncertainty_document(uncertainty)

    children = _children(doc)
    assert [child.getTypeAsString() for child in children] == ["mean", "distribution"]
    distribution = children[1]
    assert (
        distribution.getDefinitionURL()
        == "http://www.sbml.org/sbml/symbols/distrib/normal"
    )
    assert libsbml.formulaToL3String(distribution.getMath()) == "normal(2, 2)"


def test_uncertainty_of_a_formula_is_written_once_per_document() -> None:
    """Test that writing one uncertainty twice writes one distribution each time.

    A model definition is written more than once in the tests and the
    examples, so the normalization of `formula` must not accumulate children
    on the object.
    """
    uncertainty = Uncertainty(formula="normal(2.0, 2.0)")

    first = _uncertainty_document(uncertainty)
    second = _uncertainty_document(uncertainty)

    assert len(_children(first)) == 1
    assert len(_children(second)) == 1


def test_uncert_parameter_without_a_value_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a parameter which states nothing is reported and not refused.

    Neither SBML nor libsbml requires a value of an uncert parameter: libsbml
    writes, reads and validates a `distrib:uncertParameter` which carries
    nothing but its type. A parameter which states nothing is an authoring
    mistake all the same, so it is reported; refusing it in the constructor
    would make a document which libsbml reads impossible to hold.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        parameter = UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN)

    assert parameter.value is None
    errors = [
        record.getMessage()
        for record in caplog.records
        if "states nothing about the value" in record.getMessage()
    ]
    assert len(errors) == 1, caplog.records


def _bound_errors(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Get the messages about a bound of a span which is not stated.

    Args:
        caplog: the captured records of `sbmlutils.factory`

    Returns:
        every message which reports a bound
    """
    return [
        record.getMessage()
        for record in caplog.records
        if "bound of" in record.getMessage()
    ]


@pytest.mark.parametrize(
    "kwargs, missing",
    [
        ({}, ["lower", "upper"]),
        ({"valueLower": 1.0}, ["upper"]),
        ({"varLower": "p2"}, ["upper"]),
        ({"valueUpper": 9.0}, ["lower"]),
        ({"varUpper": "p2"}, ["lower"]),
    ],
)
def test_uncert_span_reports_every_bound_it_does_not_state(
    kwargs: dict[str, Any], missing: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """Test that each bound a span does not state is reported on its own.

    A span states an interval, so it needs a lower and an upper bound, each
    as a value or as the variable it is read from. A span with one bound was
    refused by the constructor before the round trip needed every document
    libsbml reads to be expressible, and then went unreported: the check of
    the data model only sees whether an element states anything at all.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE, **kwargs)

    errors = _bound_errors(caplog)
    assert len(errors) == len(missing), caplog.records
    for bound, message in zip(missing, errors, strict=True):
        assert f"The {bound} bound of" in message
        assert f"value{bound.capitalize()}" in message
        assert f"var{bound.capitalize()}" in message


@pytest.mark.parametrize(
    "kwargs",
    [
        {"valueLower": 1.0, "valueUpper": 9.0},
        {"varLower": "p2", "varUpper": "p3"},
        {"math": "normal(1, 2)"},
        {"definitionURL": "http://purl.obolibrary.org/obo/STATO_0000035"},
        {
            "uncertParameters": [
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER, value=0.4
                )
            ]
        },
    ],
)
def test_uncert_span_which_states_its_interval_is_not_reported(
    kwargs: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a span which states its interval otherwise is not reported.

    Both bounds, math, the definitionURL of an external distribution and the
    uncert parameters of one each state what the interval is, so none of them
    is a span with a bound missing.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE, **kwargs)

    assert _bound_errors(caplog) == []


def test_distrib_fixtures_report_no_missing_bound(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that no uncertainty of the repository is reported by these checks.

    A check which fires on the documents of the repository is noise, so every
    fixture which carries an uncertainty is parsed, which builds every span
    and every uncert parameter of it.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        for sbml_path in DISTRIB_FIXTURES:
            sbml_to_model(sbml_path)

    assert _bound_errors(caplog) == []
    assert [
        record.getMessage()
        for record in caplog.records
        if "states nothing about the value" in record.getMessage()
    ] == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"value": 1.0},
        {"var": "p2"},
        {"definitionURL": "http://www.probonto.org/ontology#PROB_k0000782"},
        {"math": "normal(1, 2)"},
        {
            "uncertParameters": [
                UncertParameter(
                    type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER, value=0.4
                )
            ]
        },
    ],
)
def test_uncert_parameter_which_states_a_value_is_not_reported(
    kwargs: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    """Test that every way of stating the value counts as one.

    A value, the variable it is read from, the definitionURL of an external
    distribution, math and the uncert parameters of an external distribution
    each state what the value is.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION, **kwargs)

    assert [
        record.getMessage()
        for record in caplog.records
        if "states nothing about the value" in record.getMessage()
    ] == []


#: every distribution of distrib, with a formula which calls it with an arity
#: it accepts
DISTRIBUTION_FORMULAS: list[tuple[str, str]] = [
    ("normal", "normal(0, 1)"),
    ("uniform", "uniform(0, 1)"),
    ("bernoulli", "bernoulli(0.5)"),
    ("binomial", "binomial(10, 0.5)"),
    ("cauchy", "cauchy(0, 1)"),
    ("chisquare", "chisquare(2)"),
    ("exponential", "exponential(1)"),
    ("gamma", "gamma(2, 1)"),
    ("laplace", "laplace(0, 1)"),
    ("lognormal", "lognormal(0, 1)"),
    ("poisson", "poisson(0.5)"),
    ("rayleigh", "rayleigh(0.5)"),
]


@pytest.mark.parametrize("distribution, formula", DISTRIBUTION_FORMULAS)
def test_uncertainty_of_a_formula_writes_the_url_of_its_distribution(
    distribution: str, formula: str
) -> None:
    """Test that every distribution of distrib is recognized by its own name.

    The shortcut searched the text of the formula for the name of a
    distribution, which is the wrong question to ask: `lognormal(0, 1)`
    contains `normal`, so it was written as the distribution which happened to
    match, and `rayleigh` was never matched at all while the table spelled it
    `raleigh`.
    """
    doc = _uncertainty_document(Uncertainty(formula=formula))

    (child,) = _children(doc)
    assert child.getTypeAsString() == "distribution"
    assert (
        child.getDefinitionURL()
        == f"http://www.sbml.org/sbml/symbols/distrib/{distribution}"
    )
    assert libsbml.formulaToL3String(child.getMath()) == formula


@pytest.mark.parametrize(
    "formula",
    [
        # an identifier which contains the name of a distribution
        "normalization * 2",
        "gamma_rate + 1",
        # a distribution which is not what the formula computes
        "5 * normal(0, 1)",
        # no distribution anywhere
        "2.0 * p2",
    ],
)
def test_uncertainty_of_a_formula_which_calls_no_distribution_writes_no_url(
    formula: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that only a call of a distribution names a distribution.

    The name of a distribution can occur in a formula without the formula
    being a draw from it: as part of an identifier, or in a term of a larger
    expression. The uncert parameter of such a formula is written as it has
    always been written, without a definitionURL and without math, and the
    formula is named in an error, since the shortcut cannot express it.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        doc = _uncertainty_document(Uncertainty(formula=formula))

    (child,) = _children(doc)
    assert child.getTypeAsString() == "distribution"
    assert not child.isSetDefinitionURL()
    assert not child.isSetMath()
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
    ]
    assert len(errors) == 1, errors
    assert formula in errors[0]
    assert "not a call of a distribution" in errors[0]


def test_uncertainty_of_an_unparsable_formula_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a formula which does not parse is reported, not raised on.

    The formula is parsed to find out which distribution it calls, so a
    formula which is not a formula at all is met here rather than in the
    writer; the uncert parameter is written without a definitionURL and
    without math.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        doc = _uncertainty_document(Uncertainty(formula="normal("))

    (child,) = _children(doc)
    assert not child.isSetDefinitionURL()
    assert not child.isSetMath()
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
    ]
    assert len(errors) == 1, errors
    assert "could not be parsed" in errors[0] and "normal(" in errors[0]
