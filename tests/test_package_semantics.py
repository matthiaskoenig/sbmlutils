"""Semantic verification of the package round trip: comp by simulation, fbc by flux balance analysis.

`tests/structural.py` compares the package content of a document with the package content of its round trip, element by element and attribute by attribute. That proves that the same content is there; it cannot prove that a tool which *interprets* the document reads the same model out of it, because the comparison reads both sides through libsbml, the very library which writes them. Two independent interpreters close that gap, each on the package it understands:

- **layer 2, comp**: `sbmlutils.comp.flatten_sbml` resolves the submodels of the original and of its round trip into two flat models, and roadrunner simulates both. `comp_semantic_diff` compares the trajectories with the tolerances of `tests/test_roundtrip.py`. The round trip is compared against the **original**, never against the expected result of the SBML test suite: a case which roadrunner gets wrong is wrong on both sides and is still a valid comparison of the two.
- **layer 3, fbc**: cobrapy reads the original and its round trip as two constraint based models, and `fbc_semantic_diff` compares the stoichiometric matrix, the flux bounds, the objective, the gene reaction rule of every reaction, the genes, the metabolites with their compartment, formula and charge, and the solution of the flux balance problem. The reference is the original as libsbml's own converters bring it to the versions the round trip writes, which is the policy of `tests/structural.py`, see `comparable_file`.

Every case falls into exactly one of three classes, and the class of every case is asserted, so that no case is passed over silently:

- **(a)** both sides flatten and simulate, or load, and everything compared agrees,
- **(b)** the **original** cannot be judged - it does not flatten, does not simulate or does not load - so a comparison against it says nothing about the round trip and the structural layer stands alone for it. Such a case is named in `COMP_NOT_JUDGEABLE` or `FBC_NOT_LOADABLE` with its reason,
- **(c)** the original can be judged and the round trip differs from it: a defect, named in `COMP_DEFECTS` or `FBC_DEFECTS` with its cause. A case which changes class fails its test.

Each comparison is a function which takes two documents and returns their differences, as `structural_diff` does, and the mutation tests at the end of each layer damage one construct of a round-tripped document and assert that the comparison reports exactly that damage: a comparison which only lives inside an `assert` cannot be shown to bite.

The whole comp sweep runs every case in a python process of its own, see `run_case_isolated` of `tests/test_roundtrip.py`, whose worker this module is as well: flattening and simulating are both native code, and a crash there must end one case instead of the session. It takes about 110 s against the 1.3 s of the structural sweep over the same cases, so it is deselected with the `sbml_testsuite` marker and the default run judges `COMP_SUBSET` and `COMP_ICG_BODY`.

Layer 3 needs cobrapy, which is the optional `cobra` extra: its tests skip when it is absent, following the pattern of `sbmlutils.fbc.cobra`, and the tox `cobra` environment is the one which runs them.
"""

import math
import os
import re
import shutil
import sys
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import libsbml
import pytest
from structural import ABSENT, comparable_document
from test_package_roundtrip import (
    COMP_CASES,
    _expected_constructs,
    _fbc_version,
    fixture_idfn,
)
from test_roundtrip import (
    SEMANTIC_DIR,
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
from sbmlutils.fbc.cobra import cobra, read_cobra_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import (
    COMP_ICG_BODY,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
)

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


def roundtrip_file(
    sbml_path: Path, out_dir: Path, sbml_level: int = 3, sbml_version: int = 2
) -> Path:
    """Round trip an SBML file through `sbml_to_model` and `create_model`.

    This is `structural.roundtrip_document` for a caller which needs the file rather than the two documents: an interpreter reads a model from a file, not from a libsbml object.

    Args:
        sbml_path: path of the SBML file to round trip
        out_dir: directory the round trip is written to
        sbml_level: the SBML level the round trip is written at
        sbml_version: the SBML version the round trip is written at

    Returns:
        the path of the round-tripped SBML
    """
    roundtrip_path = out_dir / "roundtrip.xml"
    create_model(
        model=sbml_to_model(sbml_path),
        filepath=roundtrip_path,
        sbml_level=sbml_level,
        sbml_version=sbml_version,
        validate=False,
    )
    return roundtrip_path


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
    return roundtrip_file(sbml_path, out_dir, doc.getLevel(), doc.getVersion())


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

    The whole sweep takes about 110 s against the 1.3 s of the structural sweep over the same cases, so it runs behind the `sbml_testsuite` marker and the default run judges `COMP_SUBSET` and `COMP_ICG_BODY`. That is only representative as long as those carry every comp construct the other cases have. The single exception is `COMP_UNJUDGEABLE_CONSTRUCT`: an algebraic rule in a model definition, which only class (b) cases have, since roadrunner cannot simulate a flat model with one.
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
    assert [source.name for source in external_sources(COMP_ICG_BODY)] == [
        "icg_liver.xml"
    ]
    roundtrip_path = roundtrip_comp_document(COMP_ICG_BODY, tmp_path)

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
    if case in COMP_NOT_JUDGEABLE:
        kind = COMP_NOT_JUDGEABLE[case].split(":")[0]
        assert detail.startswith(f"the original {kind}"), (
            f"'{case}' is class (b) for another reason than '{kind}': {detail}"
        )
    elif case in COMP_DEFECTS:
        kind = COMP_DEFECTS[case].split(":")[0]
        assert kind in detail, (
            f"'{case}' is class (c) for another reason than '{kind}': {detail}"
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
#: applied to the round trip of `COMP_ICG_BODY`, which has one submodel and six
#: replaced elements; the two named here are of the three whose loss changes
#: the flat model, the other three replace a value of the liver submodel with
#: the value it has anyway and are inert.
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


# ---------------------------------------------------------------------------
# layer 3: fbc, by flux balance analysis
# ---------------------------------------------------------------------------
requires_cobra = pytest.mark.skipif(cobra is None, reason="requires cobrapy")

#: the relative tolerance the objective value of the two flux balance solutions
#: is compared with, and the absolute tolerance which keeps an objective of zero
#: from failing a relative comparison
FBA_RTOL: float = 1e-6
FBA_ATOL: float = 1e-9

#: a gene reaction rule as a tree: a gene id, or an operator with its operands
_Rule = str | tuple[str, tuple["_Rule", ...]]

#: the tokens of a gene reaction rule: a parenthesis or a word
_RULE_TOKEN = re.compile(r"\(|\)|[^\s()]+")


def _parse_rule(rule: str) -> _Rule | None:
    """Parse a gene reaction rule into a tree.

    `and` binds tighter than `or`, as it does in python, whose boolean syntax a gene reaction rule is written in. A group of the same operator is spliced into its parent and the operands of a group are sorted, which is the normalization `normalized_gene_rule` states.

    Args:
        rule: the rule, e.g. `(b0902 and b0903) or b3951`

    Returns:
        the tree of the rule, `None` if it is no well formed rule
    """
    tokens = _RULE_TOKEN.findall(rule)
    position = 0

    def group(operator: str, operands: list[_Rule]) -> _Rule:
        flat: list[_Rule] = []
        for operand in operands:
            if isinstance(operand, tuple) and operand[0] == operator:
                flat.extend(operand[1])
            else:
                flat.append(operand)
        return (operator, tuple(sorted(flat, key=repr)))

    def expression(operator: str, operand: Callable[[], _Rule | None]) -> _Rule | None:
        nonlocal position
        operands: list[_Rule] = []
        while True:
            parsed = operand()
            if parsed is None:
                return None
            operands.append(parsed)
            if position >= len(tokens) or tokens[position] != operator:
                break
            position += 1
        return operands[0] if len(operands) == 1 else group(operator, operands)

    def disjunction() -> _Rule | None:
        return expression("or", conjunction)

    def conjunction() -> _Rule | None:
        return expression("and", factor)

    def factor() -> _Rule | None:
        nonlocal position
        if position >= len(tokens) or tokens[position] in (")", "and", "or"):
            return None
        token = tokens[position]
        position += 1
        if token != "(":
            return token
        inner = disjunction()
        if inner is None or position >= len(tokens) or tokens[position] != ")":
            return None
        position += 1
        return inner

    tree = disjunction()
    return tree if position == len(tokens) else None


def normalized_gene_rule(rule: str) -> str:
    """Normalize a gene reaction rule to the canonical form it is compared in.

    A rule is compared as a tree and not as a string, because the round trip flattens a nested group of the same operator, `((a and b) and c)` to `(a and b and c)`, which `and` being associative makes the same rule. The tree spells an operator in front of its operands, splices a group into its parent group of the same operator and sorts the operands of every group, so that nesting and order of the same operator make no difference and everything else does: a gene which changes, an operator which changes, an operand which is added, removed or repeated all change the canonical form. It is a normalization of the syntax and not a decision of boolean equivalence, which is why `a or (a and b)` is not the same rule as `a`.

    Args:
        rule: the rule, e.g. `(b0902 and b0903) or b3951`

    Returns:
        the canonical form, e.g. `or(and(b0902,b0903),b3951)`, or the rule itself, marked as unparsed, if it is no well formed rule
    """
    tree = _parse_rule(rule)
    if tree is None:
        return f"<unparsed> {rule}"

    def spell(node: _Rule) -> str:
        if isinstance(node, str):
            return node
        operator, operands = node
        return f"{operator}({','.join(spell(operand) for operand in operands)})"

    return spell(tree)


def _stoichiometry(model: "cobra.core.Model") -> dict[str, float]:
    """Get the stoichiometric matrix of a model as a mapping.

    The matrix is compared as a mapping rather than as a matrix, so that neither the order of the reactions nor the order of the metabolites is part of the comparison.

    Args:
        model: the cobra model

    Returns:
        the coefficient of every metabolite of every reaction, keyed by `reaction[metabolite]`
    """
    return {
        f"{reaction.id}[{metabolite.id}]": coefficient
        for reaction in model.reactions
        for metabolite, coefficient in reaction.metabolites.items()
    }


def _bounds(model: "cobra.core.Model") -> dict[str, tuple[float, float]]:
    """Get the lower and the upper flux bound of every reaction, by reaction id."""
    return {
        reaction.id: (reaction.lower_bound, reaction.upper_bound)
        for reaction in model.reactions
    }


def _objective(model: "cobra.core.Model") -> dict[str, object]:
    """Get the direction of the objective and the coefficient of every reaction in it."""
    coefficients = cobra.util.solver.linear_reaction_coefficients(model)
    objective: dict[str, object] = {
        reaction.id: coefficient for reaction, coefficient in coefficients.items()
    }
    objective["<direction>"] = model.objective.direction
    return objective


def _gene_rules(model: "cobra.core.Model") -> dict[str, str]:
    """Get the canonical form of the gene reaction rule of every reaction which has one."""
    return {
        reaction.id: normalized_gene_rule(reaction.gene_reaction_rule)
        for reaction in model.reactions
        if reaction.gene_reaction_rule.strip()
    }


def _genes(model: "cobra.core.Model") -> dict[str, str | None]:
    """Get the name of every gene of a model, by gene id."""
    return {gene.id: gene.name for gene in model.genes}


def _metabolites(model: "cobra.core.Model") -> dict[str, tuple[Any, ...]]:
    """Get the compartment, the formula and the charge of every metabolite, by id."""
    return {
        metabolite.id: (metabolite.compartment, metabolite.formula, metabolite.charge)
        for metabolite in model.metabolites
    }


def _flux_balance(model: "cobra.core.Model") -> tuple[str, float | None]:
    """Solve the flux balance problem of a model.

    cobrapy warns when the solver ends in another status than `optimal`, which two cases of the test suite do on both sides. The status is compared, so the warning says nothing the comparison does not, and it is silenced here to keep the output of the tests to what they report themselves.

    Args:
        model: the cobra model

    Returns:
        the status of the solution and the value of the objective, which is `None` for a problem which has no solution
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Solver status")
        solution = model.optimize()
    return solution.status, solution.objective_value


def _diff_mapping(
    name: str, before: dict[str, Any], after: dict[str, Any]
) -> list[str]:
    """Compare two mappings key by key.

    Args:
        name: what the mapping holds, for the message of a difference
        before: the values of the original
        after: the values of the round trip

    Returns:
        one line per key whose values differ, with the value on each side; a key on one side only is `ABSENT` on the other
    """
    differences: list[str] = []
    for key in sorted(before.keys() | after.keys()):
        value_before = before.get(key, ABSENT)
        value_after = after.get(key, ABSENT)
        if value_before != value_after:
            differences.append(f"{name} '{key}': {value_before!r} -> {value_after!r}")
    return differences


def fbc_semantic_diff(
    reference: "cobra.core.Model", roundtrip: "cobra.core.Model"
) -> list[str]:
    """Compare two constraint based models, as cobrapy reads them.

    Everything a flux balance analysis is made of is compared: the stoichiometric matrix as a mapping, so that no order is part of it, the flux bounds of every reaction, the objective with its direction and coefficients, the gene reaction rule of every reaction in the canonical form of `normalized_gene_rule`, the genes, the metabolites with their compartment, formula and charge, and finally the solution of the flux balance problem, whose objective value is compared with a relative tolerance of `FBA_RTOL`.

    Args:
        reference: the model of the original document
        roundtrip: the model of the round-tripped document

    Returns:
        every difference of the round trip from the original, empty when the two models are the same to cobrapy
    """
    differences: list[str] = []
    for name, of_model in (
        ("stoichiometry", _stoichiometry),
        ("bounds", _bounds),
        ("objective", _objective),
        ("gene reaction rule", _gene_rules),
        ("gene", _genes),
        ("metabolite", _metabolites),
    ):
        differences += _diff_mapping(name, of_model(reference), of_model(roundtrip))

    status_before, value_before = _flux_balance(reference)
    status_after, value_after = _flux_balance(roundtrip)
    if status_before != status_after:
        differences.append(
            f"flux balance status: {status_before!r} -> {status_after!r}"
        )
    elif value_before is None or value_after is None:
        if value_before is not value_after:
            differences.append(
                f"flux balance objective: {value_before!r} -> {value_after!r}"
            )
    elif not math.isclose(
        value_before, value_after, rel_tol=FBA_RTOL, abs_tol=FBA_ATOL
    ):
        differences.append(
            f"flux balance objective: {value_before!r} -> {value_after!r}"
        )
    return differences


def comparable_file(sbml_path: Path, out_dir: Path) -> Path:
    """Write the document the round trip is compared against.

    The round trip writes SBML L3V2 with fbc version 2 or 3, so a document of another level or of fbc version 1 cannot come back unchanged, only as it reads when converted. The reference is therefore the source as libsbml's own converters bring it to those versions, which is the policy of `tests/structural.py`, see `comparable_document` and the docstring of that module. It matters for the fbc version 1 cases of the test suite: their `<fbc:fluxBound>` elements become the flux bound references of fbc version 2, which is what the round trip writes and the only form cobrapy reads.

    Args:
        sbml_path: path of the SBML file
        out_dir: directory the converted document is written to

    Returns:
        the path of the document to compare against, which is the source written again where it needs no conversion
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    reference_path = out_dir / "reference.xml"
    assert libsbml.writeSBMLToFile(comparable_document(doc), str(reference_path)) == 1
    return reference_path


def fbc_semantic_diff_of_files(sbml_path: Path, roundtrip_path: Path) -> list[str]:
    """Compare a document and its round trip as cobrapy reads them.

    Args:
        sbml_path: path of the SBML file the two models are read from, the reference of `comparable_file`
        roundtrip_path: path of the round-tripped SBML, or of a damaged copy of it

    Returns:
        every difference, see `fbc_semantic_diff`
    """
    return fbc_semantic_diff(
        read_cobra_model(sbml_path), read_cobra_model(roundtrip_path)
    )


# ---------------------------------------------------------------------------
# layer 3: the fixtures, the cases and their classes
# ---------------------------------------------------------------------------
def _cause(err: Exception) -> str:
    """Condense an exception into a single line, the exception it was raised from first.

    cobrapy catches whatever goes wrong while it reads a document and raises a `CobraSBMLError` whose message is the same paragraph every time, so the exception it was raised from is the informative one.

    Args:
        err: the exception

    Returns:
        the type and the first line of the message of the cause, or of the exception itself if it has none
    """
    cause = err.__cause__ or err.__context__
    return _condense(cause if isinstance(cause, Exception) else err)


def fbc_judgement(sbml_path: Path, work_dir: Path) -> tuple[str, str]:
    """Judge an fbc document against its round trip, as cobrapy reads both.

    Args:
        sbml_path: path of the fbc SBML file
        work_dir: directory the reference and the round trip are written to

    Returns:
        the class of the document, `"a"`, `"b"` or `"c"`, and the reason of a document which is not class (a)
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        reference = read_cobra_model(comparable_file(sbml_path, work_dir))
    except Exception as err:
        return "b", f"does not load: {_cause(err)}"

    try:
        roundtrip = read_cobra_model(roundtrip_file(sbml_path, work_dir))
    except Exception as err:
        return "c", f"the round trip does not load: {_cause(err)}"

    differences = fbc_semantic_diff(reference, roundtrip)
    return ("c", "; ".join(differences)) if differences else ("a", "")


def fbc_cases() -> list[Path]:
    """Get every fbc case of the vendored SBML test suite.

    The cases are not spelled out, as in `comp_cases` of `tests/test_package_roundtrip.py`: every l3v2 case whose header names an fbc namespace is a candidate, and libsbml decides which of them declares the package. `_fbc_version` is the one which asks it, and it holds the document while it reads the version: a plugin of a document nothing holds is a proxy of freed memory, which segfaults.

    Returns:
        the path of every l3v2 case which declares fbc, of either version, by case
    """
    candidates: list[Path] = []
    for sbml_path in sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml")):
        with sbml_path.open(encoding="utf-8") as f:
            if "/fbc/version" in f.read(4000):
                candidates.append(sbml_path)
    return [path for path in candidates if _fbc_version(path) is not None]


#: every fbc case of the vendored SBML test suite, empty without the suite
FBC_CASES: list[Path] = fbc_cases()

#: the fbc cases cobrapy refuses to load, class (b), with the reason. The
#: reason starts with what the original does not do, which is asserted against
#: the judgement; the rest of it is the cause cobrapy names. Every one of them
#: is a model the SBML test suite states as it is on purpose and which cobrapy
#: will not build a linear problem from.
FBC_NOT_LOADABLE: dict[str, str] = {
    "01617": (
        "does not load: the lower flux bound of R01 is above its upper bound, "
        "`fb_0` is 10 and `fb_1` is 1"
    ),
    "01618": (
        "does not load: the upper flux bound parameter `fb_1000` of R16 has no "
        "value, so the bound is NaN"
    ),
    "01619": (
        "does not load: the lower flux bound of R16 is above its upper bound, "
        "`fb_0` is 0 and `fb_inf` is -3"
    ),
    "01620": (
        "does not load: the flux bound parameter `fb_0` of R16 is not constant, "
        "which cobrapy requires of a bound"
    ),
    "01630": (
        "does not load: the flux bound parameter `fb_0` of R16 is not constant, "
        "which cobrapy requires of a bound"
    ),
}

#: the fbc cases which cobrapy loads and whose round trip it reads as another
#: model, class (c), with the cause. Every case cobrapy loads is read as the
#: same model after the round trip, so this is empty.
FBC_DEFECTS: dict[str, str] = {}

#: the fbc models of the repository, which are real genome scale models rather
#: than test cases: `e_coli_core` with 95 reactions and `Recon3D` with 10600
FBC_FIXTURES: list[Path] = [FBC_ECOLI_CORE_SBML, FBC_RECON3D_SBML]


@requires_testsuite
def test_the_fbc_cases_and_their_classes_are_found() -> None:
    """Test that the fbc sweep is parametrized and that every listed case exists.

    An empty parametrization is a single skip, so a sweep which found no case would pass without judging anything. 12 of the 34 cases declare fbc version 1, which the round trip writes back as fbc version 2 and which the reference is converted to, see `comparable_file`.
    """
    assert len(FBC_CASES) == 34
    versions = [_fbc_version(path) for path in FBC_CASES]
    assert versions.count(1) == 12
    assert versions.count(2) == 22

    cases = {sbml_path.name[:5] for sbml_path in FBC_CASES}
    assert set(FBC_NOT_LOADABLE) <= cases
    assert set(FBC_DEFECTS) <= cases
    assert set(FBC_NOT_LOADABLE) & set(FBC_DEFECTS) == set()


@requires_cobra
@requires_testsuite
@pytest.mark.parametrize("sbml_path", FBC_CASES, ids=fixture_idfn)
def test_fbc_semantics_of_every_case(sbml_path: Path, tmp_path: Path) -> None:
    """Judge every fbc case of the SBML test suite against its round trip.

    The class of every case is asserted, so that a case which stops loading, or which starts differing, fails rather than passing quietly.
    """
    case = sbml_path.name[:5]
    expected = "b" if case in FBC_NOT_LOADABLE else "c" if case in FBC_DEFECTS else "a"

    found, detail = fbc_judgement(sbml_path, tmp_path)

    assert found == expected, f"class ({found}) instead of ({expected}): {detail}"
    if case in FBC_NOT_LOADABLE:
        kind = FBC_NOT_LOADABLE[case].split(":")[0]
        assert detail.startswith(kind), (
            f"'{case}' is class (b) for another reason than '{kind}': {detail}"
        )
    elif case in FBC_DEFECTS:
        kind = FBC_DEFECTS[case].split(":")[0]
        assert kind in detail, (
            f"'{case}' is class (c) for another reason than '{kind}': {detail}"
        )


@requires_cobra
@pytest.mark.parametrize("sbml_path", FBC_FIXTURES, ids=fixture_idfn)
def test_fbc_semantics_of_a_genome_scale_model(sbml_path: Path, tmp_path: Path) -> None:
    """Test that cobrapy reads the round trip of a genome scale model as the same model.

    The two models of the repository are the real subjects of layer 3: `e_coli_core` and `Recon3D`, which carry the fbc constructs of a published model - flux bounds, an objective, gene products and their associations, charges and chemical formulas - in the numbers a real model has them. The model is asserted to have genes and an objective first, so that an agreement cannot mean that there is nothing to compare.
    """
    reference = read_cobra_model(comparable_file(sbml_path, tmp_path))
    assert len(reference.genes) > 100
    assert _flux_balance(reference)[0] == "optimal"

    roundtrip = read_cobra_model(roundtrip_file(sbml_path, tmp_path))

    assert fbc_semantic_diff(reference, roundtrip) == []


# ---------------------------------------------------------------------------
# layer 3: the damages the comparison has to see
# ---------------------------------------------------------------------------
def _change_flux_bound(doc: libsbml.SBMLDocument) -> None:
    """Point the upper flux bound of a reaction at the zero bound of the model."""
    reaction: libsbml.Reaction = doc.getModel().getReaction("R_PFK")
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    assert plugin.getUpperFluxBound() == "cobra_default_ub"
    assert plugin.setUpperFluxBound("cobra_0_bound") == (
        libsbml.LIBSBML_OPERATION_SUCCESS
    )


def _change_gene_of_an_association(doc: libsbml.SBMLDocument) -> None:
    """Replace one gene of a gene product association with another gene of the model."""
    reaction: libsbml.Reaction = doc.getModel().getReaction("R_PFK")
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    gpa: libsbml.GeneProductAssociation = plugin.getGeneProductAssociation()
    assert gpa.getAssociation().toInfix(True) == "(G_b3916 or G_b1723)"
    # `G_b1241` is a gene product of the model already, so the genes of the
    # model do not change: only the rule of this reaction does
    assert gpa.setAssociation("G_b3916 or G_b1241", True, False) == (
        libsbml.LIBSBML_OPERATION_SUCCESS
    )


def _change_stoichiometry(doc: libsbml.SBMLDocument) -> None:
    """Change the stoichiometric coefficient of a reactant."""
    reaction: libsbml.Reaction = doc.getModel().getReaction("R_PFK")
    reactant: libsbml.SpeciesReference = reaction.getReactant("M_atp_c")
    assert reactant.getStoichiometry() == 1.0
    assert reactant.setStoichiometry(2.0) == libsbml.LIBSBML_OPERATION_SUCCESS


#: a damage of the fbc content of a round-tripped document and the difference
#: the comparison has to report for it. Each is applied to the round trip of
#: `FBC_ECOLI_CORE_SBML`; cobrapy strips the `R_`, `M_` and `G_` prefixes of
#: the ids, which is why the difference names `PFK` and `atp_c`.
FBC_DAMAGES: list[tuple[str, Callable[[libsbml.SBMLDocument], None], str]] = [
    (
        "change a flux bound",
        _change_flux_bound,
        "bounds 'PFK': (0.0, 1000.0) -> (0.0, 0.0)",
    ),
    (
        "change a gene of an association",
        _change_gene_of_an_association,
        "gene reaction rule 'PFK': 'or(b1723,b3916)' -> 'or(b1241,b3916)'",
    ),
    (
        "change a stoichiometric coefficient",
        _change_stoichiometry,
        "stoichiometry 'PFK[atp_c]': -1.0 -> -2.0",
    ),
]


@requires_cobra
@pytest.mark.parametrize(
    "damage, expected",
    [(damage, expected) for _, damage, expected in FBC_DAMAGES],
    ids=[name for name, _, _ in FBC_DAMAGES],
)
def test_fbc_semantic_diff_sees_a_damaged_round_trip(
    damage: Callable[[libsbml.SBMLDocument], None], expected: str, tmp_path: Path
) -> None:
    """Test that the comparison of layer 3 reports a damaged round trip.

    A comparison which reports nothing on a damaged document verifies nothing, so each damage is applied to the round trip of `FBC_ECOLI_CORE_SBML`, which the comparison reports as unchanged undamaged, see `test_fbc_semantics_of_a_genome_scale_model`. The changed gene is the proof that the rules are compared as rules: `b1241` is a gene of the model already, so nothing but the rule of that one reaction changes, and the comparison still names it.
    """
    roundtrip_path = roundtrip_file(FBC_ECOLI_CORE_SBML, tmp_path)
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    damage(doc)
    damaged_path = tmp_path / "damaged.xml"
    assert libsbml.writeSBMLToFile(doc, str(damaged_path)) == 1

    differences = fbc_semantic_diff_of_files(
        comparable_file(FBC_ECOLI_CORE_SBML, tmp_path), damaged_path
    )

    assert expected in differences, differences


#: a gene reaction rule, the rule it is compared against and whether the two
#: are the same rule to `normalized_gene_rule`
GENE_RULES: list[tuple[str, str, bool]] = [
    # the flattening of a nested group of the same operator, which the round
    # trip does and which `and` and `or` being associative makes the same rule
    ("((a and b) and c)", "(a and b and c)", True),
    ("(a or (b or c))", "(a or b or c)", True),
    ("((a and b) or c)", "(c or (b and a))", True),
    # a rule spelled without the parentheses of libsbml, where `and` binds
    # tighter than `or`
    ("a and b or c", "(a and b) or c", True),
    # everything else is another rule
    ("(a and b)", "(a or b)", False),
    ("((a and b) or c)", "(a and b and c)", False),
    ("(a and b and c)", "(a and b)", False),
    ("(a or b)", "(a or d)", False),
    ("(a and (b or c))", "((a and b) or c)", False),
    ("a", "(a and a)", False),
]


@pytest.mark.parametrize("before, after, same", GENE_RULES)
def test_normalized_gene_rule_is_the_stated_normalization(
    before: str, after: str, same: bool
) -> None:
    """Test that the canonical form of a rule accepts the flattening and nothing else.

    The comparison of layer 3 compares a gene reaction rule in its canonical form, because the round trip flattens a nested group of the same operator. That normalization has to be narrow: a changed gene, a changed operator, a regrouping and a repeated operand are all another rule and have to stay visible.
    """
    assert (normalized_gene_rule(before) == normalized_gene_rule(after)) == same


def test_normalized_gene_rule_marks_a_rule_it_cannot_parse() -> None:
    """Test that a rule which is no rule is not silently the same as another one.

    A rule the parser does not understand falls back to the rule itself, marked, so that two such rules compare equal only when they are the same string.
    """
    assert normalized_gene_rule("a and").startswith("<unparsed>")
    assert normalized_gene_rule("a and") != normalized_gene_rule("b and")


if __name__ == "__main__":
    # the worker of `run_case_isolated`: `python test_package_semantics.py
    # <sbml_path> <case_dir>` compares the case with its round trip and records
    # the class of the case in `case_dir`
    run_comp_worker(Path(sys.argv[1]), Path(sys.argv[2]))
