"""Semantic verification of the package round trip: comp by flattening and simulating.

`tests/structural.py` compares the package content of a document with the package content of its round trip, element by element and attribute by attribute. That proves that the same content is there; it cannot prove that a tool which *interprets* the document reads the same model out of it, because the comparison reads both sides through libsbml, the very library which writes them. An independent interpreter closes that gap:

- **layer 2, comp**: `sbmlutils.comp.flatten_sbml` resolves the submodels of the original and of its round trip into two flat models, and roadrunner simulates both. `comp_semantic_diff` compares the trajectories with the tolerances of `tests/test_roundtrip.py`. The round trip is compared against the **original**, never against the expected result of the SBML test suite: a case which roadrunner gets wrong is wrong on both sides and is still a valid comparison of the two.

Every case falls into exactly one of three classes, and the class of every case is asserted, so that no case is passed over silently:

- **(a)** both sides flatten and simulate, and the trajectories agree,
- **(b)** the **original** cannot be judged - it does not flatten or does not simulate - so a comparison against it says nothing about the round trip and the structural layer stands alone for it. Such a case is named in `COMP_NOT_JUDGEABLE` with its reason,
- **(c)** the original can be judged and the round trip differs from it: a defect, named in `COMP_DEFECTS` with its cause. A case which changes class fails its test.

The comparison is a function which takes two documents and returns their differences, as `structural_diff` does, and the mutation tests at the end damage one comp construct of a round-tripped document and assert that the comparison reports exactly that damage: a comparison which only lives inside an `assert` cannot be shown to bite.

The whole sweep runs every case in a python process of its own, see `run_case_isolated` of `tests/test_roundtrip.py`, whose worker this module is as well: flattening and simulating are both native code, and a crash there must end one case instead of the session. It takes about 110 s against the 1.3 s of the structural sweep over the same cases, so it is deselected with the `sbml_testsuite` marker and the default run judges `COMP_SUBSET` and `COMP_ICG_BODY`.
"""

import os
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import libsbml
import pytest
from structural import comparable_document
from test_package_roundtrip import COMP_CASES, _expected_constructs, fixture_idfn
from test_roundtrip import (
    CaseResult,
    Outcome,
    Simulation,
    _condense,
    _record,
    _simulate,
    assert_simulations_equal,
    requires_roadrunner,
    requires_testsuite,
    run_case_isolated,
    testsuite_case,
)

from sbmlutils.comp import flatten_sbml
from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import COMP_ICG_BODY

#: this module, which is also the worker of `run_case_isolated`, see the
#: `__main__` block at its end
WORKER: Path = Path(__file__)


# ---------------------------------------------------------------------------
# layer 2: comp, by flattening and simulating
# ---------------------------------------------------------------------------
def external_sources(sbml_path: Path) -> list[Path]:
    """Collect the files the external model definitions of a document name.

    A file which is named may name files of its own, so the sources are followed to the end. A `comp:source` which is a URL, or which names a file that is not there, resolves to no file and is left out: the round trip preserves such a reference as it is.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the existing files named by a `comp:source` of the document or of a file it names, without the document itself
    """
    found: dict[Path, None] = {}
    pending: list[Path] = [sbml_path.resolve()]
    while pending:
        current = pending.pop()
        doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(current))
        comp: libsbml.CompSBMLDocumentPlugin | None = doc.getPlugin("comp")
        if comp is None:
            continue
        definition: libsbml.ExternalModelDefinition
        for definition in comp.getListOfExternalModelDefinitions():
            if not definition.isSetSource():
                continue
            source = (current.parent / definition.getSource()).resolve()
            if (
                source.is_file()
                and source != sbml_path.resolve()
                and source not in found
            ):
                found[source] = None
                pending.append(source)
    return list(found)


def roundtrip_comp_document(sbml_path: Path, out_dir: Path) -> Path:
    """Round trip a comp document into a directory in which it can be flattened.

    Two things are needed for the round trip of a comp model to flatten, and both are about the files its external model definitions name:

    - the round trip is written at the level and version of the source. libsbml resolves a `comp:source` only when the document it finds has the level and version of the document which references it, see `test_roundtrip_of_an_l3v1_comp_model_validates_at_its_own_version` of `tests/test_package_roundtrip.py`, so an L3V1 model whose external file is L3V1 has to be written as L3V1. Every comp case of the test suite is L3V2 already, `COMP_ICG_BODY` is the L3V1 model this matters for.
    - every file a `comp:source` names is copied next to the round trip. The round trip preserves such a reference rather than resolving it, so the file has to be where the reference points.

    Args:
        sbml_path: path of the SBML file to round trip
        out_dir: directory the round trip and the files it references are written to

    Returns:
        the path of the round-tripped SBML
    """
    for source in external_sources(sbml_path):
        try:
            relative = source.relative_to(sbml_path.resolve().parent)
        except ValueError:
            # a source outside the directory of the document, which no model of
            # the corpus has; it is copied by its name
            relative = Path(source.name)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, target)

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    roundtrip_path = out_dir / "roundtrip.xml"
    create_model(
        model=sbml_to_model(sbml_path),
        filepath=roundtrip_path,
        sbml_level=doc.getLevel(),
        sbml_version=doc.getVersion(),
        validate=False,
    )
    return roundtrip_path


def flatten(sbml_path: Path, flat_path: Path) -> Path:
    """Flatten a comp document, leaving the working directory as it was.

    `sbmlutils.comp.flatten_sbml` changes the working directory to the directory of the file, so that libsbml resolves a `comp:source` relative to it, and changes it back when it returns - but not when the flattening raises. The working directory is therefore restored here, and both paths are made absolute before the call, since a relative output path would be written relative to the source directory instead of the one the caller means.

    Args:
        sbml_path: path of the comp SBML file
        flat_path: path the flattened SBML is written to

    Returns:
        the path of the flattened SBML

    Raises:
        ValueError: if libsbml cannot flatten the document
    """
    working_dir = Path.cwd()
    absolute = flat_path.resolve()
    try:
        flatten_sbml(sbml_path.resolve(), absolute)
    finally:
        os.chdir(working_dir)
    return flat_path


def _flat_simulation(sbml_path: Path, flat_path: Path) -> tuple[Simulation | None, str]:
    """Flatten a comp document and simulate the flat model.

    Args:
        sbml_path: path of the comp SBML file
        flat_path: path the flattened SBML is written to

    Returns:
        the simulation and an empty reason, or `None` and why the document does not flatten or does not simulate
    """
    try:
        flatten(sbml_path, flat_path)
    except Exception as err:
        return None, f"does not flatten: {_condense(err)}"
    try:
        return _simulate(flat_path), ""
    except Exception as err:
        return None, f"does not simulate: {_condense(err)}"


@dataclass(frozen=True)
class CompComparison:
    """The semantic comparison of a comp document and its round trip.

    Attributes:
        baseline: why the original cannot be judged, an empty string when it flattens and simulates
        differences: every difference of the round trip from the original, empty when they agree
    """

    baseline: str
    differences: list[str]


#: the flattened original and the flattened round trip, in the work directory
#: `comp_semantic_diff` is given
ORIGINAL_FLAT: str = "original-flat.xml"
ROUNDTRIP_FLAT: str = "roundtrip-flat.xml"


def comp_semantic_diff(
    original_path: Path, roundtrip_path: Path, work_dir: Path
) -> CompComparison:
    """Compare a comp document and its round trip by flattening and simulating both.

    Both documents are flattened with `sbmlutils.comp.flatten_sbml` and the flat models are simulated with roadrunner over the uniform timecourse of `tests/test_roundtrip.py`; the trajectories are compared selection by selection with its tolerances. A round trip which does not flatten, does not simulate, or which simulates differently is a difference; the original doing so is not, it is the baseline this comparison has nothing to compare against.

    Args:
        original_path: path of the comp SBML file
        roundtrip_path: path of the SBML file to compare against it, the round trip of the original or a damaged copy of it
        work_dir: directory the two flattened models are written to, as `ORIGINAL_FLAT` and `ROUNDTRIP_FLAT`

    Returns:
        the comparison of the two documents
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    reference, failure = _flat_simulation(original_path, work_dir / ORIGINAL_FLAT)
    if reference is None:
        return CompComparison(f"the original {failure}", [])

    roundtrip, failure = _flat_simulation(roundtrip_path, work_dir / ROUNDTRIP_FLAT)
    if roundtrip is None:
        return CompComparison("", [f"the round trip {failure}"])

    try:
        assert_simulations_equal(reference, roundtrip, original_path.name)
    except AssertionError as err:
        return CompComparison("", [_condense(err)])
    return CompComparison("", [])


def run_comp_worker(sbml_path: Path, case_dir: Path) -> None:
    """Compare a comp case with its round trip and record the outcome, in the worker.

    The outcome is the class of the case: `PASSED` is class (a), `NOT_SIMULATABLE` is class (b), the original which cannot be judged, and `FAILED` is class (c), a defect of the round trip.

    Args:
        sbml_path: path of the comp SBML file
        case_dir: directory of the case, which the round trip, the flattened models and the outcome are written to
    """
    stage = "round trip"
    _record(case_dir, stage, None, "")
    try:
        roundtrip_path = roundtrip_comp_document(sbml_path, case_dir)
    except Exception as err:
        # a round trip which cannot even be written is a defect of the round
        # trip, unless the original cannot be judged in the first place
        stage = "flatten and simulate the original"
        _record(case_dir, stage, None, "")
        _, baseline = _flat_simulation(sbml_path, case_dir / ORIGINAL_FLAT)
        outcome = Outcome.NOT_SIMULATABLE if baseline else Outcome.FAILED
        _record(
            case_dir,
            stage,
            outcome,
            baseline or f"does not round trip: {_condense(err)}",
        )
        return

    stage = "flatten and simulate"
    _record(case_dir, stage, None, "")
    comparison = comp_semantic_diff(sbml_path, roundtrip_path, case_dir)
    if comparison.baseline:
        _record(case_dir, stage, Outcome.NOT_SIMULATABLE, comparison.baseline)
    elif comparison.differences:
        _record(case_dir, stage, Outcome.FAILED, "; ".join(comparison.differences))
    else:
        _record(case_dir, stage, Outcome.PASSED, "")


def judgement(result: CaseResult) -> tuple[str, str]:
    """Name the class of a case which ran in a process of its own.

    Args:
        result: the result of the case

    Returns:
        the class of the case, `"a"`, `"b"` or `"c"`, and the reason of a case which is not class (a). A case whose process crashed or timed out is class (c): it was not shown to agree, and a crash which happens is something to look at rather than to pass over
    """
    if result.outcome == Outcome.PASSED:
        return "a", ""
    if result.outcome == Outcome.NOT_SIMULATABLE:
        return "b", result.detail
    return "c", f"{result.outcome} in '{result.stage}': {result.detail}"


# ---------------------------------------------------------------------------
# layer 2: the cases and their classes
# ---------------------------------------------------------------------------
#: the comp cases of the SBML test suite whose **original** cannot be judged
#: semantically, class (b), with the reason. The reason starts with what the
#: original does not do, which is asserted against the recorded outcome; the
#: rest of it is the cause. Every one of them is a limitation of roadrunner on
#: the flat model, none is a limitation of the flattening: no comp case of the
#: suite fails to flatten.
COMP_NOT_JUDGEABLE: dict[str, str] = {
    "01142": (
        "does not simulate: roadrunner supports neither the algebraic rule nor "
        "the delay of the flat model"
    ),
    "01148": (
        "does not simulate: CVODE does not reach the end of the timecourse "
        "within its 20000 internal steps"
    ),
    "01173": "does not simulate: roadrunner supports no delay",
    "01174": (
        "does not simulate: roadrunner supports neither the algebraic rule nor "
        "the delay of the flat model"
    ),
    "01176": "does not simulate: roadrunner supports no delay",
    "01350": "does not simulate: roadrunner supports no algebraic rule",
    "01359": "does not simulate: roadrunner supports no algebraic rule",
    "01368": "does not simulate: roadrunner supports no algebraic rule",
    "01377": "does not simulate: roadrunner supports no algebraic rule",
    "01386": "does not simulate: roadrunner supports no algebraic rule",
}

#: the comp cases whose original flattens and simulates and whose round trip
#: does not, or simulates differently, class (c), with the cause. Every comp
#: case of the suite which can be judged agrees with its round trip, so this is
#: empty; a case which stops agreeing belongs here with its cause rather than
#: being skipped.
COMP_DEFECTS: dict[str, str] = {}

#: the comp cases the default run judges, which the whole sweep behind the
#: `sbml_testsuite` marker judges again. Together with `COMP_ICG_BODY` they
#: carry every comp construct of the corpus but one, see
#: `test_the_default_comp_subset_covers_every_judgeable_construct`.
COMP_SUBSET: list[str] = [
    "01127",  # an initial assignment in a model definition
    "01133",  # a replacedBy with an sBaseRef chain
    "01155",  # a delay in a model definition
    "01159",  # a local parameter in a model definition
    "01165",  # an external model definition, at L3V2
    "01169",  # deletions, and most of the core content of a model definition
    "01378",  # a modifier species reference in a model definition
]

#: the one comp construct of the corpus which no case in the default run
#: carries: every case with an algebraic rule in a model definition is class
#: (b), roadrunner cannot simulate the flat model, so none of them can be part
#: of a subset which is judged
COMP_UNJUDGEABLE_CONSTRUCT: str = "comp.modelDefinition.algebraicRule"


def _comp_constructs(sbml_path: Path) -> set[str]:
    """Get the comp constructs of a document, as the structural layer counts them.

    Args:
        sbml_path: path of the SBML file

    Returns:
        every comp construct the document has, without the package declaration
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    return {
        construct
        for construct in _expected_constructs(comparable_document(doc))
        if construct.startswith("comp.") and construct != "comp.package"
    }


@requires_testsuite
def test_the_comp_cases_and_their_classes_are_found() -> None:
    """Test that the sweep is parametrized and that every listed case exists.

    An empty parametrization is a single skip, so a sweep which found no case would pass without judging anything, and a class list which names a case the suite does not have would never be checked.
    """
    assert len(COMP_CASES) == 123
    cases = {sbml_path.name[:5] for sbml_path in COMP_CASES}
    assert set(COMP_NOT_JUDGEABLE) <= cases
    assert set(COMP_DEFECTS) <= cases
    assert set(COMP_SUBSET) <= cases
    assert set(COMP_NOT_JUDGEABLE) & set(COMP_DEFECTS) == set()
    assert set(COMP_SUBSET) & (set(COMP_NOT_JUDGEABLE) | set(COMP_DEFECTS)) == set()


@requires_testsuite
def test_the_default_comp_subset_covers_every_judgeable_construct() -> None:
    """Test that the cases of the default run carry every comp construct of the sweep.

    The whole sweep takes about 175 s against the 1.3 s of the structural sweep over the same cases, so it runs behind the `sbml_testsuite` marker and the default run judges `COMP_SUBSET` and `COMP_ICG_BODY`. That is only representative as long as those carry every comp construct the other cases have. The single exception is `COMP_UNJUDGEABLE_CONSTRUCT`: an algebraic rule in a model definition, which only class (b) cases have, since roadrunner cannot simulate a flat model with one.
    """
    covered: set[str] = _comp_constructs(COMP_ICG_BODY)
    for case in COMP_SUBSET:
        covered |= _comp_constructs(testsuite_case(case))
    swept: set[str] = set()
    for sbml_path in COMP_CASES:
        swept |= _comp_constructs(sbml_path)

    assert swept - covered == {COMP_UNJUDGEABLE_CONSTRUCT}


@requires_roadrunner
def test_comp_semantics_of_icg_body(tmp_path: Path) -> None:
    """Test that the round trip of `COMP_ICG_BODY` flattens and simulates like the original.

    The model is a whole-body PBPK model whose liver is a submodel of an external model definition, the one model of the repository with a `comp:source` to another file. The flattened original is asserted to hold the content of that submodel first, so that an agreement cannot mean that nothing was resolved.
    """
    roundtrip_path = roundtrip_comp_document(COMP_ICG_BODY, tmp_path)
    assert [source.name for source in external_sources(COMP_ICG_BODY)] == [
        "icg_liver.xml"
    ]

    comparison = comp_semantic_diff(COMP_ICG_BODY, roundtrip_path, tmp_path)

    assert "LI__" in (tmp_path / ORIGINAL_FLAT).read_text(), (
        "the liver submodel was not resolved into the flat original"
    )
    assert comparison == CompComparison("", [])


@requires_roadrunner
@requires_testsuite
@pytest.mark.parametrize("case", COMP_SUBSET)
def test_comp_semantics_of_a_representative_case(case: str, tmp_path: Path) -> None:
    """Test that a comp case of the default subset agrees with its round trip.

    These are class (a) by definition: a case which stops agreeing is a defect and belongs in `COMP_DEFECTS`, and a case whose original stops being simulable belongs in `COMP_NOT_JUDGEABLE` and has no place in the subset.
    """
    sbml_path = testsuite_case(case)
    roundtrip_path = roundtrip_comp_document(sbml_path, tmp_path)

    assert comp_semantic_diff(sbml_path, roundtrip_path, tmp_path) == (
        CompComparison("", [])
    )


@requires_roadrunner
@requires_testsuite
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", COMP_CASES, ids=fixture_idfn)
def test_comp_semantics_of_every_case(sbml_path: Path, tmp_path: Path) -> None:
    """Judge every comp case of the SBML test suite against its round trip.

    This is the whole sweep, it is deselected in the default test run. Every case runs in a python process of its own, see `run_case_isolated`, since flattening and simulating are native code and a crash must end one case instead of the session. The class of every case is asserted, so that a case which stops being judgeable, or which starts differing, fails rather than passing quietly.
    """
    case = sbml_path.name[:5]
    expected = (
        "b" if case in COMP_NOT_JUDGEABLE else "c" if case in COMP_DEFECTS else "a"
    )

    result = run_case_isolated(sbml_path, tmp_path, worker=WORKER)
    found, detail = judgement(result)

    assert found == expected, f"class ({found}) instead of ({expected}): {detail}"
    reason = COMP_NOT_JUDGEABLE.get(case) or COMP_DEFECTS.get(case)
    if reason is not None:
        kind = reason.split(":")[0]
        assert detail.startswith(f"the original {kind}"), (
            f"'{case}' is class ({found}) for another reason than '{kind}': {detail}"
        )


# ---------------------------------------------------------------------------
# layer 2: the damages the comparison has to see
# ---------------------------------------------------------------------------
def _drop_submodel(doc: libsbml.SBMLDocument) -> None:
    """Drop the first submodel of the main model."""
    comp: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    comp.getListOfSubmodels().remove(0)


def _drop_replaced_element(sid: str) -> Callable[[libsbml.SBMLDocument], None]:
    """Drop the replaced element of the element of an id, which is then no longer replaced."""

    def damage(doc: libsbml.SBMLDocument) -> None:
        element: libsbml.SBase = doc.getModel().getElementBySId(sid)
        assert element is not None, f"no element '{sid}'"
        comp: libsbml.CompSBasePlugin = element.getPlugin("comp")
        assert comp.getNumReplacedElements() == 1, f"'{sid}' has no replaced element"
        comp.getListOfReplacedElements().remove(0)

    return damage


#: a damage of the comp content of a round-tripped document, the part of the
#: difference the comparison has to report, and what the damage means. Each is
#: applied to the round trip of `COMP_ICG_BODY`; the three replaced elements
#: named here are the ones whose loss changes the flat model, the other three
#: replace a value of the liver submodel with the same value.
COMP_DAMAGES: list[tuple[str, Callable[[libsbml.SBMLDocument], None], str]] = [
    (
        "drop the submodel",
        _drop_submodel,
        "the round trip does not flatten",
    ),
    (
        "drop the replaced element of the liver plasma volume",
        _drop_replaced_element("Vli_plasma"),
        "differs in selection 'LI__bil_ext'",
    ),
    (
        "drop the replaced element of the liver plasma concentration",
        _drop_replaced_element("Cli_plasma_icg"),
        "selections differ",
    ),
]


@requires_roadrunner
@pytest.mark.parametrize(
    "damage, expected",
    [(damage, expected) for _, damage, expected in COMP_DAMAGES],
    ids=[name for name, _, _ in COMP_DAMAGES],
)
def test_comp_semantic_diff_sees_a_damaged_round_trip(
    damage: Callable[[libsbml.SBMLDocument], None], expected: str, tmp_path: Path
) -> None:
    """Test that the comparison of layer 2 reports a damaged round trip.

    A comparison which reports nothing on a damaged document verifies nothing, so each damage is applied to the round trip of `COMP_ICG_BODY`, which the comparison reports as unchanged undamaged, see `test_comp_semantics_of_icg_body`. Dropping the submodel leaves the six replaced elements referring to a submodel which is not there, which libsbml refuses to flatten; dropping a replaced element leaves the liver with its own value, which changes the flat model.
    """
    roundtrip_path = roundtrip_comp_document(COMP_ICG_BODY, tmp_path)
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    damage(doc)
    damaged_path = tmp_path / "damaged.xml"
    assert libsbml.writeSBMLToFile(doc, str(damaged_path)) == 1

    comparison = comp_semantic_diff(COMP_ICG_BODY, damaged_path, tmp_path)

    assert comparison.baseline == ""
    assert len(comparison.differences) == 1
    assert expected in comparison.differences[0], comparison.differences


if __name__ == "__main__":
    # the worker of `run_case_isolated`: `python test_package_semantics.py
    # <sbml_path> <case_dir>` compares the case with its round trip and records
    # the class of the case in `case_dir`
    run_comp_worker(Path(sys.argv[1]), Path(sys.argv[2]))
