"""Round-trip tests.

A round trip is `SBML -> sbml_to_model -> create_model -> SBML`. It must
preserve the simulation behaviour of the model: simulating the original and
simulating the round-tripped document must give the same trajectories.

The models are the semantic cases of the vendored SBML test suite. They are
test data of the repository and are not part of the distribution, so they are
resolved from `sbmlutils.resources.SBML_TESTSUITE_DIR`.

roadrunner is the optional `examples` extra, which `dev` and the tox test
environment pull in. It is `None` when it is not installed, which is what
these tests skip on, following the `cobra` pattern of `sbmlutils.fbc.cobra`.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import SBML_TESTSUITE_DIR
from sbmlutils.validation import ValidationOptions

if TYPE_CHECKING:
    import roadrunner
else:
    try:
        import roadrunner
    except ImportError:
        roadrunner = None

requires_roadrunner = pytest.mark.skipif(
    roadrunner is None, reason="requires libroadrunner"
)

#: the semantic cases of the vendored SBML test suite
SEMANTIC_DIR: Path = Path(SBML_TESTSUITE_DIR) / "semantic"

#: uniform timecourse the round-trip comparison simulates
T_END: float = 10.0
T_STEPS: int = 51

#: tolerances of the trajectory comparison
RTOL: float = 1e-4
ATOL: float = 1e-6


def testsuite_case(case: str, level_version: str = "l3v2") -> Path:
    """Resolve a semantic test suite case to its SBML path.

    Args:
        case: the five digit case id, e.g. `"00001"`
        level_version: the SBML level and version flavour, e.g. `"l3v2"`

    Returns:
        the path of the SBML file of the case
    """
    return SEMANTIC_DIR / case / f"{case}-sbml-{level_version}.xml"


#: not a test despite the name, pytest's default collection matches on the
#: "test" prefix alone and would otherwise try to collect this helper
testsuite_case.__test__ = False  # ty: ignore[unresolved-attribute]


def _simulate(sbml_path: Path) -> tuple[list[str], np.ndarray]:
    """Simulate a uniform timecourse of the given SBML.

    Args:
        sbml_path: path of the SBML file to simulate

    Returns:
        the selection names and the simulation data
    """
    rr = roadrunner.RoadRunner(str(sbml_path))
    rr.timeCourseSelections = [
        "time",
        *rr.model.getFloatingSpeciesIds(),
        *rr.model.getBoundarySpeciesIds(),
        *rr.model.getGlobalParameterIds(),
    ]
    result = rr.simulate(0.0, T_END, T_STEPS)
    return list(result.colnames), np.array(result)


def assert_roundtrip_simulates_equal(sbml_path: Path, tmp_path: Path) -> None:
    """Assert that a round trip preserves the simulation behaviour.

    Simulates the given SBML, round trips it through the internal model and
    simulates the result, then compares the trajectories selection by
    selection.

    Args:
        sbml_path: path of the SBML file to round trip
        tmp_path: directory the round-tripped SBML is written to

    Raises:
        AssertionError: if the selections or the trajectories differ
    """
    columns_ref, data_ref = _simulate(sbml_path)

    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    columns_rt, data_rt = _simulate(roundtrip_path)

    assert set(columns_ref) == set(columns_rt), (
        f"selections differ after the round trip of '{sbml_path.name}': "
        f"{sorted(set(columns_ref) ^ set(columns_rt))}"
    )
    for k, column in enumerate(columns_ref):
        np.testing.assert_allclose(
            data_rt[:, columns_rt.index(column)],
            data_ref[:, k],
            rtol=RTOL,
            atol=ATOL,
            err_msg=f"'{sbml_path.name}' differs in selection '{column}'",
        )


#: cases which round trip correctly today, they guard against regressions
CASES_BASELINE: list[str] = ["00001", "00002", "00003", "00004", "00005", "00006"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_BASELINE)
def test_roundtrip_baseline(case: str, tmp_path: Path) -> None:
    """Test that cases which round trip today keep round tripping."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


#: every l3v2 semantic case of the vendored suite
SWEEP_CASES: list[Path] = sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml"))


def sbml_case_idfn(sbml_path: Path) -> str:
    """Inject the case name into the test name."""
    return sbml_path.name


@requires_roadrunner
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_roundtrip_sweep(sbml_path: Path, tmp_path: Path) -> None:
    """Round trip every l3v2 semantic case of the SBML test suite.

    This is the full sweep behind the `sbml_testsuite` marker, it is
    deselected in the default test run.
    """
    assert_roundtrip_simulates_equal(sbml_path, tmp_path)


def test_roundtrip_emits_no_authoring_warnings(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that round tripping does not warn about authoring style.

    The `name` and `sboTerm` warnings of `Sbase._set_fields` are hints for
    somebody writing a model definition. A model which came from a file has
    whatever the file had, so the hints are noise, see
    https://github.com/matthiaskoenig/sbmlutils/issues/469
    """
    model = sbml_to_model(testsuite_case("00001"))
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=tmp_path / "roundtrip.xml",
            sbml_level=3,
            sbml_version=2,
            validation_options=ValidationOptions(units_consistency=False),
        )

    authoring = [
        record.getMessage()
        for record in caplog.records
        if "should be set" in record.getMessage()
    ]
    assert authoring == [], f"round trip emitted authoring warnings: {authoring}"


def test_roundtrip_preserves_notes(tmp_path: Path) -> None:
    """Test that notes survive a round trip unchanged.

    Notes used to be stored as markdown and rendered on write, so notes read
    from a file came back nested and their text was mutated.
    """
    from sbmlutils.io.sbml import read_sbml
    from sbmlutils.resources import REPRESSILATOR_SBML

    model = sbml_to_model(REPRESSILATOR_SBML)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    doc_rt = read_sbml(roundtrip_path)
    notes_rt = doc_rt.getModel().getNotesString()
    assert notes_rt, "the model lost its notes"
    assert "<notes>" not in notes_rt[7:], "notes were nested on write"


def test_roundtrip_invents_no_cvterms(tmp_path: Path) -> None:
    """Test that a round trip adds no annotation which was not in the source.

    `Sbase._set_fields` used to inject an `Annotation(BQB.IS, f"sbo/{sboTerm}")`
    whenever an sboTerm was set, which duplicated the sboTerm attribute as a
    CVTerm and forced a metaid onto elements which had none. The same
    duplication happened a second time on the read side: `sbml_to_model` built
    an element's annotations from `SBMLDocumentInfo.sbase_dict`, which also
    synthesizes a `BQB_IS` CVTerm for the sboTerm, a behaviour meant for the
    sbml4humans report, not for a `Model` which is written back out.

    The count compares CVTerm resources rather than raw CVTerm objects,
    because `annotator.ModelAnnotator.annotate_sbase` calls libsbml's
    `addCVTerm`, which merges a new resource into an existing CVTerm of the
    same qualifier instead of adding a second CVTerm. That merging changes how
    many CVTerm objects the document has without changing which resources are
    annotated, so counting objects would fail on a benign re-serialization
    that invents nothing.
    """
    import libsbml

    from sbmlutils.resources import REPRESSILATOR_SBML

    def cvterm_resource_count(sbml_path: Path) -> int:
        model = libsbml.readSBMLFromFile(str(sbml_path)).getModel()

        def resources_of(sbase: libsbml.SBase) -> int:
            return sum(
                sbase.getCVTerm(k).getNumResources()
                for k in range(sbase.getNumCVTerms())
            )

        total = resources_of(model)
        for getter, count in (
            (model.getSpecies, model.getNumSpecies()),
            (model.getReaction, model.getNumReactions()),
            (model.getCompartment, model.getNumCompartments()),
            (model.getParameter, model.getNumParameters()),
        ):
            for k in range(count):
                total += resources_of(getter(k))
        return total

    model = sbml_to_model(REPRESSILATOR_SBML)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert cvterm_resource_count(roundtrip_path) == cvterm_resource_count(
        Path(REPRESSILATOR_SBML)
    )


#: cases whose round trip depends on unit definitions being preserved
CASES_UNITS: list[str] = ["00001", "00002", "00003", "00004"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_UNITS)
def test_roundtrip_units(case: str, tmp_path: Path) -> None:
    """Test that unit definitions and unit references survive a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


def test_roundtrip_preserves_unit_definitions(tmp_path: Path) -> None:
    """Test that the listOfUnitDefinitions and the model units are preserved."""
    import libsbml

    sbml_path = testsuite_case("00038")
    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    m_in = libsbml.readSBMLFromFile(str(sbml_path)).getModel()
    m_out = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()

    assert {
        m_out.getUnitDefinition(k).getId() for k in range(m_out.getNumUnitDefinitions())
    } == {
        m_in.getUnitDefinition(k).getId() for k in range(m_in.getNumUnitDefinitions())
    }
    assert m_out.getTimeUnits() == m_in.getTimeUnits()
    assert m_out.getCompartment(0).getUnits() == m_in.getCompartment(0).getUnits()


#: cases which use a functionDefinition
CASES_FUNCTIONS: list[str] = ["00025", "00034", "00035", "00078"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_FUNCTIONS)
def test_roundtrip_function_definitions(case: str, tmp_path: Path) -> None:
    """Test that function definitions survive a round trip.

    Dropping them produced libsbml error 10214, `a <ci> element in this
    context must refer to a function definition`, in 48 of 150 cases.
    """
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


def test_roundtrip_core_model_declares_no_fbc(tmp_path: Path) -> None:
    """Test that a core only model does not gain the fbc package.

    `parser.py` hardcoded `m.packages = [Package.FBC_V3]`, so every parsed
    model came back declaring xmlns:fbc and fbc:strict.
    """
    model = sbml_to_model(testsuite_case("00001"))
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert "fbc" not in roundtrip_path.read_text()


def test_roundtrip_invents_no_nan(tmp_path: Path) -> None:
    """Test that an unset size or value is not written as NaN.

    Case "00001" always had an explicit compartment size, so it never
    exercised this path; the test passed before the fix just as well as
    after it. "00048" declares a zero-dimensional compartment with no
    `size`, which the writer used to fill in as `size="NaN"`.
    """
    model = sbml_to_model(testsuite_case("00048"))
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert "NaN" not in roundtrip_path.read_text()


#: cases whose species carry a conversionFactor
#
# "01000" also declares a conversionFactor but is excluded here: it additionally
# exercises event priority, persistence and delay plus an avogadro csymbol and a
# local parameter shadowing a global one, none of which parser.py or factory.py
# support yet, so it fails the trajectory comparison for reasons unrelated to
# conversionFactor.
CASES_CONVERSION_FACTOR: list[str] = ["00976", "00977"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_CONVERSION_FACTOR)
def test_roundtrip_conversion_factor(case: str, tmp_path: Path) -> None:
    """Test that a species conversionFactor survives a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


def test_parse_algebraic_rule_without_id() -> None:
    """Test that parsing an id-less algebraic rule does not raise.

    `AlgebraicRule.__init__` takes `sid` as a required positional parameter;
    `parser.py`'s `parse_variable_kwargs` used to pop `sid` from the kwargs
    whenever the source rule had no id of its own, which is the case for
    every one of the 109 l3v2 test-suite cases with an `<algebraicRule>`,
    raising `TypeError: AlgebraicRule.__init__() missing 1 required
    positional argument: 'sid'` on every one of them. roadrunner cannot
    simulate algebraic rules, so this only checks that parsing succeeds and
    that no spurious id was invented.
    """
    model = sbml_to_model(testsuite_case("00039"))

    assert len(model.algebraic_rules) == 1
    assert model.algebraic_rules[0].sid is None


def test_roundtrip_rule_keeps_its_own_id(tmp_path: Path) -> None:
    """Test that a rule with a real id keeps it and does not collide.

    libsbml aliases `Rule.getId`/`isSetId` to the `variable` attribute, so a
    naive read of `getId()` reports the variable name whether or not the
    source actually declared an `id`. `parse_variable_kwargs` used to trust
    that alias, which discarded a rule's real, distinct id and replaced it
    with the variable name, a `SId` already used by the variable's own
    element, which libsbml then rejects as a duplicate id (10301) on write.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model = doc.createModel("m")
    c: libsbml.Compartment = sbml_model.createCompartment()
    c.setId("c")
    c.setConstant(False)
    c.setSpatialDimensions(3)
    c.setSize(1.0)
    rule: libsbml.AssignmentRule = sbml_model.createAssignmentRule()
    rule.setIdAttribute("realid")
    rule.setVariable("c")
    rule.setMath(libsbml.parseL3Formula("2.0"))

    sbml_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))

    model = sbml_to_model(sbml_path)
    assert model.rules[0].sid == "realid"

    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    rt_model = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()
    rt_rule: libsbml.Rule = rt_model.getRule(0)
    assert rt_rule.getIdAttribute() == "realid"
    assert rt_rule.getVariable() == "c"


#: cases whose kinetic laws carry local parameters
CASES_LOCAL_PARAMETERS: list[str] = ["00027", "00057", "00058", "00132", "00133"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_LOCAL_PARAMETERS)
def test_roundtrip_local_parameters(case: str, tmp_path: Path) -> None:
    """Test that local parameters of a kinetic law survive a round trip.

    Dropping them produced libsbml error 10215, `a <ci> element in this
    context must refer to a model component`.
    """
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
