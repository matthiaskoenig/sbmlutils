"""Round-trip tests.

A round trip is `SBML -> sbml_to_model -> create_model -> SBML`. It must
preserve the simulation behaviour of the model: simulating the original and
simulating the round-tripped document must give the same trajectories.

The models are the semantic cases of the vendored SBML test suite. They are
test data of the repository and are excluded from the distribution, see
`[tool.hatch.build]` in `pyproject.toml`, so they are resolved from the
checkout, see `SEMANTIC_DIR`, and never from the installed package: tox
installs sbmlutils from a wheel, which does not contain them.

Only the l3v2 flavour of each case is round tripped. The round trip writes
SBML L3V2, so round tripping an L1 or L2 file is a conversion rather than a
round trip, which is not expected to preserve the file attribute for
attribute.

roadrunner is the optional `examples` extra, which `dev` and the tox test
environment pull in. It is `None` when it is not installed, which is what
these tests skip on, following the `cobra` pattern of `sbmlutils.fbc.cobra`.

The full sweep runs every case in a python process of its own, see
`run_case_isolated`. libroadrunner has crashed in native code, at varying
cases, in a sweep which ran every case in one process. Such a crash cannot be
caught and ends the whole session; isolated, it ends a single case. This
module is also the worker of that process, see the `__main__` block at its
end.
"""

import json
import logging
import re
import signal
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from sbmlutils.factory import Compartment, Model, create_model
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

#: the semantic cases of the vendored SBML test suite, resolved from the
#: checkout, see the module docstring; `SBML_TESTSUITE_DIR` only names the
#: directory, it points into the installed package
SEMANTIC_DIR: Path = (
    Path(__file__).parent.parent
    / "src"
    / "sbmlutils"
    / "resources"
    / "models"
    / Path(SBML_TESTSUITE_DIR).name
    / "semantic"
)

requires_testsuite = pytest.mark.skipif(
    not SEMANTIC_DIR.is_dir(), reason="requires the vendored SBML test suite"
)

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

#: the selection names and the data of a simulation
Simulation = tuple[list[str], np.ndarray]


def _simulate(sbml_path: Path) -> Simulation:
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


def roundtrip_sbml(sbml_path: Path, tmp_path: Path) -> Path:
    """Round trip an SBML file through the internal model.

    Args:
        sbml_path: path of the SBML file to round trip
        tmp_path: directory the round-tripped SBML is written to

    Returns:
        the path of the round-tripped SBML
    """
    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )
    return roundtrip_path


def _selection_keys(columns: list[str]) -> list[tuple[str, int]]:
    """Key every selection by its name and by the occurrence of the name.

    A name can be selected twice: a parameter with the id `time` is selected
    next to the time itself, see case 01820. The occurrence pairs the
    selections of two simulations in their order instead of colliding on the
    name.

    Args:
        columns: the selection names of a simulation

    Returns:
        the `(name, occurrence)` key of every selection
    """
    seen: Counter[str] = Counter()
    keys: list[tuple[str, int]] = []
    for column in columns:
        keys.append((column, seen[column]))
        seen[column] += 1
    return keys


def assert_simulations_equal(
    reference: Simulation, roundtrip: Simulation, name: str
) -> None:
    """Assert that two simulations have the same selections and trajectories.

    Args:
        reference: the simulation of the original
        roundtrip: the simulation of the round-tripped SBML
        name: the name of the SBML file, for the error message

    Raises:
        AssertionError: if the selections or the trajectories differ
    """
    columns_ref, data_ref = reference
    columns_rt, data_rt = roundtrip
    keys_ref = _selection_keys(columns_ref)
    keys_rt = _selection_keys(columns_rt)

    assert set(keys_ref) == set(keys_rt), (
        f"selections differ after the round trip of '{name}': "
        f"{sorted({key[0] for key in set(keys_ref) ^ set(keys_rt)})}"
    )
    for k, key in enumerate(keys_ref):
        np.testing.assert_allclose(
            data_rt[:, keys_rt.index(key)],
            data_ref[:, k],
            rtol=RTOL,
            atol=ATOL,
            err_msg=f"'{name}' differs in selection '{key[0]}'",
        )


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
    reference = _simulate(sbml_path)
    roundtrip_path = roundtrip_sbml(sbml_path, tmp_path)
    assert_simulations_equal(reference, _simulate(roundtrip_path), sbml_path.name)


class Outcome(StrEnum):
    """How a case which ran in a process of its own ended."""

    #: the round-tripped model simulates like the original
    PASSED = "passed"
    #: the original simulates, but the round trip raises or the round-tripped
    #: model simulates differently: a genuine round-trip failure
    FAILED = "failed"
    #: roadrunner cannot simulate the original, e.g. an algebraic rule, so
    #: there is nothing to compare against
    NOT_SIMULATABLE = "original does not simulate"
    #: the process crashed in native code, which is no evidence that the
    #: round trip is wrong
    CRASHED = "crashed in native code"
    #: the process was killed after the timeout
    TIMED_OUT = "timed out"
    #: the original does not simulate the same twice, see `NONDETERMINISTIC`;
    #: the sweep sets it without running the case
    NOT_DETERMINISTIC = "original is not deterministic"
    #: the worker exited without recording an outcome, a bug of the harness
    WORKER_ERROR = "worker error"


@dataclass
class CaseResult:
    """The result of a case which ran in a process of its own.

    Attributes:
        outcome: how the case ended
        stage: the stage the case was in when it ended
        detail: the error of a failure, the signal of a crash
    """

    outcome: Outcome
    stage: str
    detail: str


#: the file the worker records its stage and its outcome in
OUTCOME_FILE: str = "outcome.json"


def _record(case_dir: Path, stage: str, outcome: Outcome | None, detail: str) -> None:
    """Record the stage and the outcome of a case, in the worker.

    The stage is recorded before it starts, so that the stage a process was
    killed in is known.

    Args:
        case_dir: the directory of the case
        stage: the stage the case is in
        outcome: the outcome, `None` while the case is still running
        detail: the error of a failure
    """
    (case_dir / OUTCOME_FILE).write_text(
        json.dumps({"stage": stage, "outcome": outcome, "detail": detail})
    )


def _condense(err: Exception) -> str:
    """Condense an exception into a single line.

    An `assert_allclose` message spans several lines, of which the one naming
    the selection is the informative one.

    Args:
        err: the exception to condense

    Returns:
        the type of the exception and the informative line of its message
    """
    lines = [line.strip() for line in str(err).splitlines() if line.strip()]
    informative = [line for line in lines if "differs in selection" in line]
    return f"{type(err).__name__}: {(informative or lines or [''])[0]}"


def run_worker(sbml_path: Path, case_dir: Path) -> None:
    """Round trip a case and record its outcome, in the worker process.

    Args:
        sbml_path: path of the SBML file to round trip
        case_dir: directory of the case, which the round-tripped SBML and the
            outcome are written to
    """
    stage = "simulate the original"
    _record(case_dir, stage, None, "")
    try:
        reference = _simulate(sbml_path)
    except Exception as err:
        _record(case_dir, stage, Outcome.NOT_SIMULATABLE, _condense(err))
        return

    try:
        stage = "round trip"
        _record(case_dir, stage, None, "")
        roundtrip_path = roundtrip_sbml(sbml_path, case_dir)

        stage = "simulate the round trip"
        _record(case_dir, stage, None, "")
        roundtrip = _simulate(roundtrip_path)

        stage = "compare"
        _record(case_dir, stage, None, "")
        assert_simulations_equal(reference, roundtrip, sbml_path.name)
    except Exception as err:
        _record(case_dir, stage, Outcome.FAILED, _condense(err))
        return

    _record(case_dir, stage, Outcome.PASSED, "")


def _crash(returncode: int) -> str | None:
    """Name the crash a process ended with.

    A process which crashed in native code is killed by a signal on POSIX,
    which `subprocess` reports as a negative return code. On Windows it exits
    with the NTSTATUS of the exception, e.g. `0xC0000005` for an access
    violation, which is an error status from `0xC0000000` on.

    Args:
        returncode: the return code of the process

    Returns:
        the signal or the status of the crash, `None` if it did not crash
    """
    if returncode < 0:
        try:
            return signal.Signals(-returncode).name
        except ValueError:
            return f"signal {-returncode}"
    if sys.platform == "win32" and returncode >= 0xC0000000:
        return f"0x{returncode:08X}"
    return None


def run_case_isolated(
    sbml_path: Path,
    case_dir: Path,
    timeout: float = 300.0,
    worker: Path = Path(__file__),
) -> CaseResult:
    """Round trip a case in a python process of its own.

    A crash in native code ends the process of the case, and it is reported as
    `Outcome.CRASHED` with the stage it happened in. A fresh interpreter is
    started rather than a fork, since importing roadrunner starts native
    threads, which a fork does not survive safely.

    Args:
        sbml_path: path of the SBML file to round trip
        case_dir: directory of the case, which the round-tripped SBML and the
            outcome are written to
        timeout: seconds after which the process is killed
        worker: the script run as `worker <sbml_path> <case_dir>`, this
            module; a test substitutes one which crashes

    Returns:
        the result of the case
    """
    try:
        process = subprocess.run(
            [sys.executable, str(worker), str(sbml_path), str(case_dir)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        process = None

    outcome_path = case_dir / OUTCOME_FILE
    recorded: dict[str, Any] = (
        json.loads(outcome_path.read_text())
        if outcome_path.exists()
        else {"stage": "start the worker", "outcome": None, "detail": ""}
    )
    stage: str = recorded["stage"]
    if process is None:
        return CaseResult(Outcome.TIMED_OUT, stage, f"after {timeout:.0f} s")
    crash = _crash(process.returncode)
    if crash is not None:
        return CaseResult(Outcome.CRASHED, stage, crash)
    if recorded["outcome"] is not None:
        return CaseResult(Outcome(recorded["outcome"]), stage, recorded["detail"])

    stderr = process.stderr.strip().splitlines()
    return CaseResult(
        Outcome.WORKER_ERROR,
        stage,
        f"exit code {process.returncode}: {stderr[-1] if stderr else ''}",
    )


#: a stand-in for the worker, which records a stage and then ends as named by
#: its first argument: it crashes in native code, it hangs, or it exits
#: without an outcome.
#:
#: The crash differs by platform. On POSIX, reading address 0 through ctypes
#: is a real segmentation fault, and the process is killed by SIGSEGV. On
#: Windows it is not: ctypes wraps every foreign call in structured exception
#: handling and turns the access violation into a python `OSError`, so the
#: process exits normally with code 1. The Windows worker therefore ends with
#: exactly the status a native access violation leaves, `0xC0000005`, through
#: `TerminateProcess`, which is an ordinary call rather than a fault, so there
#: is nothing for ctypes to intercept. The explicit argtypes keep the 64-bit
#: process handle from being truncated to a 32-bit int.
_FAKE_WORKER: str = """
import ctypes, json, sys, time
from pathlib import Path

(Path(sys.argv[2]) / "outcome.json").write_text(
    json.dumps({"stage": "simulate the round trip", "outcome": None, "detail": ""})
)
if sys.argv[1] == "crash":
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        # STATUS_ACCESS_VIOLATION, the exit status of a native segfault
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(), 0xC0000005)
    else:
        import resource

        # no core dump, which takes seconds and stays on the machine
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        ctypes.string_at(0)
elif sys.argv[1] == "hang":
    time.sleep(60)
sys.exit(3)
"""


@pytest.mark.parametrize(
    "ending, timeout, outcome",
    [
        ("crash", 60.0, Outcome.CRASHED),
        ("hang", 1.0, Outcome.TIMED_OUT),
        ("exit", 60.0, Outcome.WORKER_ERROR),
    ],
)
def test_run_case_isolated_reports_how_a_worker_ended(
    ending: str, timeout: float, outcome: Outcome, tmp_path: Path
) -> None:
    """Test that a crash, a hang and an exit without an outcome are reported.

    None of them occurs in the sweep on demand, so a stand-in worker ends
    that way. A crash must be reported as a crash, with the stage it happened
    in, and never as a round-trip failure.
    """
    worker = tmp_path / "worker.py"
    worker.write_text(_FAKE_WORKER)
    case_dir = tmp_path / "case"
    case_dir.mkdir()

    result = run_case_isolated(Path(ending), case_dir, timeout, worker=worker)

    assert result.outcome == outcome, result
    assert result.stage == "simulate the round trip"
    assert result.detail


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


#: cases whose original does not simulate the same twice, so a comparison of
#: trajectories says nothing about the round trip. Found by simulating the
#: original of every case with two or more events 100 times: in each, events
#: with the same or no priority trigger at once, and SBML leaves their order to
#: chance. A single simulation of each looks deterministic often enough that
#: a sweep can pass them by luck.
NONDETERMINISTIC: dict[str, str] = dict.fromkeys(
    [
        "00952", "00953", "00962", "00964", "00965", "00966", "01466",
        "01588", "01590", "01591", "01599", "01605", "01626", "01627",
    ],
    "events with the same or no priority trigger at once, their order is random",
)  # fmt: skip

#: the comp cases which fail: `sbml_to_model` drops the submodels,
#: replacements, deletions and ports, so the model roadrunner flattens loses
#: their content. Every one declares a `comp:submodel`, and every one passes
#: when the original is flattened with libsbml before the round trip.
# fmt: off
CASES_COMP: list[str] = [
    "01126", "01127", "01128", "01129", "01130", "01131", "01132", "01133",
    "01134", "01135", "01136", "01137", "01138", "01139", "01140", "01143",
    "01144", "01145", "01146", "01147", "01152", "01153", "01154", "01155",
    "01156", "01157", "01158", "01159", "01160", "01161", "01164", "01165",
    "01167", "01168", "01169", "01170", "01171", "01172", "01175", "01177",
    "01178", "01179", "01180", "01181", "01182", "01183", "01344", "01345",
    "01346", "01347", "01348", "01349", "01351", "01352", "01353", "01354",
    "01355", "01356", "01357", "01358", "01360", "01361", "01362", "01363",
    "01364", "01365", "01366", "01367", "01369", "01370", "01371", "01372",
    "01373", "01374", "01375", "01376", "01378", "01379", "01380", "01381",
    "01382", "01383", "01384", "01385", "01387", "01388", "01390", "01391",
    "01392", "01393", "01394", "01467", "01468", "01469", "01470", "01471",
    "01472", "01473", "01474", "01475", "01476", "01477", "01778",
]
# fmt: on

#: math round trips as an L3 infix string. `libsbml.formulaToL3String` spells
#: a MathML constant or csymbol by its name (`pi`, `INF`, `NaN`, `time`,
#: `avogadro`), and `libsbml.parseL3FormulaWithModel` reads that name back as
#: the element of that id if the model has one, as the constant otherwise.
_SHADOWED = "an id shadows a MathML constant in the L3 infix math"

#: cases which do not round trip yet, with the reason, see
#: https://github.com/matthiaskoenig/sbmlutils/issues/469
KNOWN_FAILURES: dict[str, str] = {
    **dict.fromkeys(CASES_COMP, "comp is not round tripped, it is out of scope"),
    "01760": (
        f"{_SHADOWED}: the local parameter `avogadro` comes back as the "
        "avogadro csymbol, local parameters are not in scope of the parser"
    ),
    "01762": (
        f"{_SHADOWED}: the avogadro csymbol and the local parameter "
        "`avogadro` of one formula both come back as the csymbol"
    ),
    "01763": (
        f"{_SHADOWED}: the avogadro csymbol and the parameter `avogadro` of "
        "one formula both come back as the parameter"
    ),
    "01811": f"{_SHADOWED}: `<infinity/>` comes back as the parameter `INF`",
    "01813": f"{_SHADOWED}: `<notanumber/>` comes back as the parameter `NaN`",
    "01819": f"{_SHADOWED}: `<pi/>` comes back as the parameter `pi`",
    "01821": f"{_SHADOWED}: the time csymbol comes back as the parameter `time`",
}


def test_sweep_finds_the_test_suite() -> None:
    """Test that the sweep and the case lists resolve the vendored test suite.

    An empty glob parametrizes the sweep with no case at all, which pytest
    reports as a single skip, so a sweep which found nothing would pass
    without testing anything. That happened under tox while the suite was
    resolved from the installed package, which is a wheel without it.
    """
    assert SEMANTIC_DIR.is_dir(), f"the SBML test suite is missing: {SEMANTIC_DIR}"
    assert len(SWEEP_CASES) == 1690
    listed = {*NONDETERMINISTIC, *KNOWN_FAILURES}
    swept = {sbml_path.name[:5] for sbml_path in SWEEP_CASES}
    assert listed <= swept, f"listed cases which do not exist: {listed - swept}"


@requires_roadrunner
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_roundtrip_sweep(
    sbml_path: Path, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """Round trip every l3v2 semantic case of the SBML test suite.

    This is the full sweep behind the `sbml_testsuite` marker, it is
    deselected in the default test run. Every case runs in a process of its
    own, see `run_case_isolated`. A case whose original does not simulate, or
    whose process crashed in native code, is skipped: neither is evidence
    about the round trip.
    """
    case = sbml_path.name[:5]
    if case in NONDETERMINISTIC:
        pytest.skip(f"the original is not deterministic: {NONDETERMINISTIC[case]}")
    if case in KNOWN_FAILURES:
        request.applymarker(pytest.mark.xfail(reason=KNOWN_FAILURES[case], strict=True))

    result = run_case_isolated(sbml_path, tmp_path)
    if result.outcome in (Outcome.NOT_SIMULATABLE, Outcome.CRASHED):
        pytest.skip(f"{result.outcome} in '{result.stage}': {result.detail}")
    assert result.outcome == Outcome.PASSED, (
        f"{result.outcome} in '{result.stage}': {result.detail}"
    )


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


def _notes_of_elements(sbml_path: Path) -> dict[str, str]:
    """Collect the notes of the model and of its elements.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the notes string of every element which has notes, keyed by the
        element name and its id
    """
    import libsbml

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    model: libsbml.Model = doc.getModel()
    elements: list[libsbml.SBase] = [
        model,
        *model.getListOfUnitDefinitions(),
        *model.getListOfCompartments(),
        *model.getListOfSpecies(),
        *model.getListOfParameters(),
        *model.getListOfRules(),
        *model.getListOfReactions(),
        *model.getListOfEvents(),
    ]
    return {
        f"{element.getElementName()} {element.getId()}": element.getNotesString()
        for element in elements
        if element.isSetNotes()
    }


def _notes_text(notes: str) -> str:
    """Get the text of notes, with its whitespace collapsed.

    Args:
        notes: the notes string, markup included

    Returns:
        the text of the notes without the markup
    """
    return " ".join(re.sub(r"<[^>]*>", " ", notes).split())


def test_roundtrip_preserves_notes(tmp_path: Path) -> None:
    """Test that the notes of every element survive a round trip.

    Notes used to be stored as markdown and rendered on write, so notes read
    from a file came back nested and their text was mutated, `2*3*4` became
    `2<em>3</em>4`. The notes of the repressilator are sequences of `<p>`
    elements, which are wrapped into a `<body>`, an equivalent form, so the
    text is compared rather than the markup.
    """
    from sbmlutils.resources import REPRESSILATOR_SBML

    source = _notes_of_elements(Path(REPRESSILATOR_SBML))
    roundtrip = _notes_of_elements(roundtrip_sbml(Path(REPRESSILATOR_SBML), tmp_path))

    assert len(source) > 10, "the repressilator has notes on its elements"
    assert roundtrip.keys() == source.keys(), "elements lost or gained notes"
    for key, notes in roundtrip.items():
        assert notes.count("<notes") == 1, f"notes of '{key}' were nested"
        assert notes.count("<body") <= 1, f"notes of '{key}' were nested"
        assert _notes_text(notes) == _notes_text(source[key]), key


#: a complete XHTML document as notes, the form CellDesigner writes on every
#: element and many older BioModels files have
HTML_NOTES: str = (
    '<html xmlns="http://www.w3.org/1999/xhtml">'
    "<head><title>CellDesigner notes</title></head>"
    "<body><p>2*3*4 and <b>bold</b></p></body>"
    "</html>"
)


def test_roundtrip_preserves_html_notes(tmp_path: Path) -> None:
    """Test that notes rooted at `<html>` are a fixed point of the round trip.

    Notes may be a complete XHTML document, a body, or a sequence of block
    elements. Only a body was kept as it was, so an `<html>` document came
    back inside a `<body>`, which is not valid XHTML and which libsbml's
    consistency check does not report.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model: libsbml.Model = doc.createModel("m")
    sbml_model.setNotes(HTML_NOTES)
    c: libsbml.Compartment = sbml_model.createCompartment()
    c.setId("c")
    c.setConstant(True)
    c.setSize(1.0)
    c.setNotes(HTML_NOTES)
    species: libsbml.Species = sbml_model.createSpecies()
    species.setId("S1")
    species.setCompartment("c")
    species.setInitialAmount(1.0)
    species.setConstant(False)
    species.setBoundaryCondition(False)
    species.setHasOnlySubstanceUnits(False)
    species.setNotes(HTML_NOTES)
    p: libsbml.Parameter = sbml_model.createParameter()
    p.setId("k")
    p.setValue(1.0)
    p.setConstant(True)
    p.setNotes(HTML_NOTES)
    reaction: libsbml.Reaction = sbml_model.createReaction()
    reaction.setId("r1")
    reaction.setReversible(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("S1")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    reaction.createKineticLaw().setMath(libsbml.parseL3Formula("k * S1"))
    reaction.setNotes(HTML_NOTES)

    source_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(source_path))
    first_dir = tmp_path / "first"
    first_dir.mkdir()
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    first = roundtrip_sbml(source_path, first_dir)
    second = roundtrip_sbml(first, second_dir)

    source = _notes_of_elements(source_path)
    assert len(source) == 5
    for key, notes in source.items():
        assert notes.count("<html") == 1, key
    assert _notes_of_elements(first) == source
    assert _notes_of_elements(second) == source


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


def _unit_references(sbml_path: Path) -> dict[str, Any]:
    """Collect the unit definitions and every unit reference of a model.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the units of every unit definition, keyed by its id, and the unit
        every model attribute, compartment, species, parameter and local
        parameter references, keyed by the element
    """
    import libsbml

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    model: libsbml.Model = doc.getModel()
    references: dict[str, Any] = {}

    udef: libsbml.UnitDefinition
    for udef in model.getListOfUnitDefinitions():
        references[f"unitDefinition {udef.getId()}"] = [
            (u.getKind(), u.getExponent(), u.getScale(), u.getMultiplier())
            for u in udef.getListOfUnits()
        ]
    for attribute in ("time", "substance", "extent", "length", "area", "volume"):
        getter = f"get{attribute.capitalize()}Units"
        references[f"model {attribute}Units"] = getattr(model, getter)()

    c: libsbml.Compartment
    for c in model.getListOfCompartments():
        references[f"compartment {c.getId()} units"] = c.getUnits()
    s: libsbml.Species
    for s in model.getListOfSpecies():
        references[f"species {s.getId()} substanceUnits"] = s.getSubstanceUnits()
    p: libsbml.Parameter
    for p in model.getListOfParameters():
        references[f"parameter {p.getId()} units"] = p.getUnits()
    r: libsbml.Reaction
    for r in model.getListOfReactions():
        if r.isSetKineticLaw():
            lp: libsbml.LocalParameter
            for lp in r.getKineticLaw().getListOfLocalParameters():
                key = f"localParameter {r.getId()}.{lp.getId()} units"
                references[key] = lp.getUnits()
    return references


#: cases which declare unit definitions, reference them from the model, the
#: compartments and the species; no l3v2 case gives a parameter a unit
CASES_UNIT_REFERENCES: list[str] = ["00038", "00054"]


@pytest.mark.parametrize("case", CASES_UNIT_REFERENCES)
def test_roundtrip_preserves_unit_definitions(case: str, tmp_path: Path) -> None:
    """Test that the unit definitions and every unit reference are preserved.

    The units of a definition are compared kind, exponent, scale and
    multiplier, the references by the unit id of the model attributes, of
    every compartment, species and parameter.
    """
    sbml_path = testsuite_case(case)
    roundtrip_path = roundtrip_sbml(sbml_path, tmp_path)

    references = _unit_references(sbml_path)
    assert any(key.startswith("unitDefinition") for key in references)
    assert any(
        key.startswith("species") and unit for key, unit in references.items()
    ), f"'{case}' references no substanceUnits, it would not test them"
    assert _unit_references(roundtrip_path) == references


def test_roundtrip_preserves_parameter_units(tmp_path: Path) -> None:
    """Test that the units of a parameter and of a local parameter survive.

    No l3v2 semantic case of the test suite gives a parameter or a local
    parameter a unit, so the source is built with libsbml. It references a
    unit definition and a base unit kind from each kind of element.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model: libsbml.Model = doc.createModel("m")
    sbml_model.setTimeUnits("second")
    sbml_model.setExtentUnits("mmol")
    sbml_model.setSubstanceUnits("mmol")

    udef: libsbml.UnitDefinition = sbml_model.createUnitDefinition()
    udef.setId("mmol")
    unit: libsbml.Unit = udef.createUnit()
    unit.setKind(libsbml.UNIT_KIND_MOLE)
    unit.setExponent(1.0)
    unit.setScale(-3)
    unit.setMultiplier(1.0)

    c: libsbml.Compartment = sbml_model.createCompartment()
    c.setId("c")
    c.setConstant(True)
    c.setSpatialDimensions(3)
    c.setSize(1.0)
    c.setUnits("litre")

    species: libsbml.Species = sbml_model.createSpecies()
    species.setId("S1")
    species.setCompartment("c")
    species.setInitialAmount(1.0)
    species.setSubstanceUnits("mmol")
    species.setConstant(False)
    species.setBoundaryCondition(False)
    species.setHasOnlySubstanceUnits(False)

    for sid, units in (("p_mmol", "mmol"), ("p_second", "second")):
        p: libsbml.Parameter = sbml_model.createParameter()
        p.setId(sid)
        p.setValue(1.0)
        p.setUnits(units)
        p.setConstant(True)

    reaction: libsbml.Reaction = sbml_model.createReaction()
    reaction.setId("r1")
    reaction.setReversible(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("S1")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    klaw: libsbml.KineticLaw = reaction.createKineticLaw()
    lp: libsbml.LocalParameter = klaw.createLocalParameter()
    lp.setId("k")
    lp.setValue(0.1)
    lp.setUnits("mmol")
    klaw.setMath(libsbml.parseL3Formula("k"))

    sbml_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))
    roundtrip_path = roundtrip_sbml(sbml_path, tmp_path)

    references = _unit_references(sbml_path)
    assert references["parameter p_mmol units"] == "mmol"
    assert references["parameter p_second units"] == "second"
    assert references["localParameter r1.k units"] == "mmol"
    assert _unit_references(roundtrip_path) == references


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
CASES_CONVERSION_FACTOR: list[str] = ["00976", "00977", "01000"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_CONVERSION_FACTOR)
def test_roundtrip_conversion_factor(case: str, tmp_path: Path) -> None:
    """Test that a species conversionFactor survives a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


#: cases which use events
CASES_EVENTS: list[str] = ["00026", "00041", "00071", "00072", "00073", "00074"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_EVENTS)
def test_roundtrip_events(case: str, tmp_path: Path) -> None:
    """Test that events survive a round trip."""
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


def _optional_ids(sbml_path: Path) -> list[tuple[str, str, str | None]]:
    """Collect the optional id of every rule and every event of a model.

    libsbml aliases `Rule.getId` to the variable of an assignment or rate
    rule, so the id of a rule is read with `getIdAttribute`.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the element name, the variable or the trigger, and the id of every
        rule and every event, `None` for an element without an id
    """
    import libsbml

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    model: libsbml.Model = doc.getModel()
    ids: list[tuple[str, str, str | None]] = []
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        ids.append(
            (
                rule.getElementName(),
                rule.getVariable(),
                rule.getIdAttribute() if rule.isSetIdAttribute() else None,
            )
        )
    event: libsbml.Event
    for event in model.getListOfEvents():
        trigger = (
            libsbml.formulaToL3String(event.getTrigger().getMath())
            if event.isSetTrigger() and event.getTrigger().isSetMath()
            else ""
        )
        ids.append(
            (
                event.getElementName(),
                trigger,
                event.getId() if event.isSetId() else None,
            )
        )
    return ids


#: cases with an element whose id is optional and not set: an assignment rule
#: (00029), a rate rule (00031), an algebraic rule (00039) and an event (00928)
CASES_WITHOUT_IDS: list[str] = ["00029", "00031", "00039", "00928"]


@pytest.mark.parametrize("case", CASES_WITHOUT_IDS)
def test_roundtrip_invents_no_ids(case: str, tmp_path: Path) -> None:
    """Test that a round trip gives no id to an element which had none.

    The id of a rule or an event is optional. `AssignmentRule` and `RateRule`
    generated one for a rule without an id, which was written from SBML L3V2
    on: 727 assignment rule ids and 619 rate rule ids in the l3v2 cases of the
    test suite, whose rules have no id. The parser named an event without an
    id `event<k>`. A generated id changes nothing in a simulation, so only a
    structural comparison sees it.
    """
    sbml_path = testsuite_case(case)
    source = _optional_ids(sbml_path)
    assert source, f"'{case}' has no rule or event, it would not test them"
    assert all(sid is None for _, _, sid in source), source

    # the order of the rules is not preserved, `Model` keeps each kind in a
    # list of its own
    assert sorted(_optional_ids(roundtrip_sbml(sbml_path, tmp_path)), key=str) == (
        sorted(source, key=str)
    )


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


def _elements_with_math(sbml_path: Path) -> list[tuple[str, str, bool]]:
    """Collect every element of a model which has math, or may have it.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the element name, the element it belongs to or assigns, and whether
        its math is set, of every function definition, initial assignment,
        rule, kinetic law, constraint, and trigger, priority, delay and
        event assignment of an event
    """
    import libsbml

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    model: libsbml.Model = doc.getModel()
    elements: list[tuple[str, str, bool]] = []

    def add(sbase: Any, key: str) -> None:
        # any libsbml object with math, `libsbml.SBase` declares no `isSetMath`
        elements.append((sbase.getElementName(), key, sbase.isSetMath()))

    fd: libsbml.FunctionDefinition
    for fd in model.getListOfFunctionDefinitions():
        add(fd, fd.getId())
    ia: libsbml.InitialAssignment
    for ia in model.getListOfInitialAssignments():
        add(ia, ia.getSymbol())
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        add(rule, rule.getVariable())
    reaction: libsbml.Reaction
    for reaction in model.getListOfReactions():
        if reaction.isSetKineticLaw():
            add(reaction.getKineticLaw(), reaction.getId())
    event: libsbml.Event
    for k, event in enumerate(model.getListOfEvents()):
        key = event.getId() or f"event {k}"
        if event.isSetTrigger():
            add(event.getTrigger(), key)
        if event.isSetPriority():
            add(event.getPriority(), key)
        if event.isSetDelay():
            add(event.getDelay(), key)
        ea: libsbml.EventAssignment
        for ea in event.getListOfEventAssignments():
            add(ea, f"{key} {ea.getVariable()}")
    constraint: libsbml.Constraint
    for constraint in model.getListOfConstraints():
        add(constraint, constraint.getId())
    return elements


#: cases with an element without math, which SBML allows from L3V2 on: an
#: initial assignment (01234), an assignment rule (01235), a rate rule
#: (01236), an event assignment (01237), a trigger (01238), an event without a
#: trigger (01239), a delay (01241), a priority (01242), an algebraic rule
#: (01244), a constraint (01247) and a function definition (01271)
CASES_WITHOUT_MATH: list[str] = [
    "01234", "01235", "01236", "01237", "01238", "01239", "01241", "01242",
    "01244", "01247", "01271",
]  # fmt: skip


@pytest.mark.parametrize("case", CASES_WITHOUT_MATH)
def test_roundtrip_preserves_elements_without_math(case: str, tmp_path: Path) -> None:
    """Test that an element without math survives a round trip without math.

    The parser dropped every element without math, and an event whose
    trigger had none, with all its assignments. None of them carries
    semantics, so the simulation sweep passed these cases; only a structural
    comparison sees the loss.
    """
    sbml_path = testsuite_case(case)
    source = _elements_with_math(sbml_path)
    if case == "01239":
        assert all(name != "trigger" for name, _, _ in source), source
    else:
        assert not all(is_set for _, _, is_set in source), source

    # the order of the rules is not preserved, `Model` keeps each kind in a
    # list of its own
    assert sorted(_elements_with_math(roundtrip_sbml(sbml_path, tmp_path))) == (
        sorted(source)
    )


def test_roundtrip_preserves_kinetic_law_without_math(tmp_path: Path) -> None:
    """Test that a kinetic law without math keeps its local parameters.

    No case of the test suite has a kinetic law without math, so the source is
    built with libsbml. The parser dropped such a kinetic law together with
    its local parameters.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model: libsbml.Model = doc.createModel("m")
    c: libsbml.Compartment = sbml_model.createCompartment()
    c.setId("c")
    c.setConstant(True)
    c.setSize(1.0)
    species: libsbml.Species = sbml_model.createSpecies()
    species.setId("S1")
    species.setCompartment("c")
    species.setInitialAmount(1.0)
    species.setConstant(False)
    species.setBoundaryCondition(False)
    species.setHasOnlySubstanceUnits(False)
    reaction: libsbml.Reaction = sbml_model.createReaction()
    reaction.setId("r1")
    reaction.setReversible(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("S1")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    klaw: libsbml.KineticLaw = reaction.createKineticLaw()
    lp: libsbml.LocalParameter = klaw.createLocalParameter()
    lp.setId("k")
    lp.setValue(0.1)

    sbml_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))
    roundtrip_path = roundtrip_sbml(sbml_path, tmp_path)

    assert _elements_with_math(roundtrip_path) == [("kineticLaw", "r1", False)]
    rt_doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    rt_klaw: libsbml.KineticLaw = rt_doc.getModel().getReaction("r1").getKineticLaw()
    assert rt_klaw.getLocalParameter(0).getId() == "k"


def test_roundtrip_trigger_priority_delay_metadata(tmp_path: Path) -> None:
    """Test that the metadata of a trigger, priority and delay survive a round trip.

    `Event` held its trigger, priority and delay as formula strings, which
    have no place for the id, name, metaid, sboTerm, notes and annotations of
    the element, so the parser dropped them. No case of the test suite gives
    them metadata, so the source is built with libsbml, and both directions
    are checked: `sbml_to_model` reads the metadata into the `Trigger`,
    `Priority` and `Delay`, and `create_model` writes it back out.
    """
    import libsbml

    from sbmlutils.factory import Delay, Priority, Trigger
    from sbmlutils.metadata import BQB

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model: libsbml.Model = doc.createModel("m")
    p1: libsbml.Parameter = sbml_model.createParameter()
    p1.setId("p1")
    p1.setValue(0.0)
    p1.setConstant(False)
    event: libsbml.Event = sbml_model.createEvent()
    event.setId("e1")
    event.setUseValuesFromTriggerTime(True)
    trigger: libsbml.Trigger = event.createTrigger()
    trigger.setMath(libsbml.parseL3Formula("time >= 10"))
    # the two flags differ, so that a parser which swaps them fails
    trigger.setInitialValue(True)
    trigger.setPersistent(False)
    priority: libsbml.Priority = event.createPriority()
    priority.setMath(libsbml.parseL3Formula("1"))
    delay: libsbml.Delay = event.createDelay()
    delay.setMath(libsbml.parseL3Formula("2"))
    ea: libsbml.EventAssignment = event.createEventAssignment()
    ea.setVariable("p1")
    ea.setMath(libsbml.parseL3Formula("10"))

    #: the element, its id prefix and the resource of its annotation
    children: list[tuple[Any, str, str]] = [
        (trigger, "t", "https://identifiers.org/GO:0000001"),
        (priority, "pr", "https://identifiers.org/GO:0000002"),
        (delay, "d", "https://identifiers.org/GO:0000003"),
    ]
    for child, prefix, resource in children:
        child.setId(f"{prefix}1")
        child.setMetaId(f"{prefix}_meta")
        child.setName(f"{prefix}name")
        child.setSBOTerm("SBO:0000064")
        child.setNotes(
            f'<body xmlns="http://www.w3.org/1999/xhtml"><p>{prefix} notes</p></body>'
        )
        cv = libsbml.CVTerm()
        cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
        cv.setBiologicalQualifierType(libsbml.BQB_IS)
        cv.addResource(resource)
        child.addCVTerm(cv)

    source_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(source_path))

    # direction 1: SBML -> Model
    model = sbml_to_model(source_path)
    parsed = model.events[0]
    assert isinstance(parsed.trigger, Trigger)
    assert isinstance(parsed.priority, Priority)
    assert isinstance(parsed.delay, Delay)
    assert parsed.trigger.math == "time >= 10"
    assert parsed.trigger.persistent is False
    assert parsed.trigger.initialValue is True
    assert parsed.priority.math == "1"
    assert parsed.delay.math == "2"
    for element, (_, prefix, resource) in zip(
        (parsed.trigger, parsed.priority, parsed.delay), children, strict=True
    ):
        assert element.sid == f"{prefix}1"
        assert element.metaId == f"{prefix}_meta"
        assert element.name == f"{prefix}name"
        assert element.sboTerm == "SBO:0000064"
        assert element.notes is not None
        assert f"{prefix} notes" in element.notes
        assert element.annotations == [(BQB.IS, resource)]

    # direction 2: Model -> SBML
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    rt_doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    rt_event: libsbml.Event = rt_doc.getModel().getEvent("e1")
    rt_trigger: libsbml.Trigger = rt_event.getTrigger()
    assert libsbml.formulaToL3String(rt_trigger.getMath()) == "time >= 10"
    assert rt_trigger.getPersistent() is False
    assert rt_trigger.getInitialValue() is True
    assert libsbml.formulaToL3String(rt_event.getPriority().getMath()) == "1"
    assert libsbml.formulaToL3String(rt_event.getDelay().getMath()) == "2"
    for rt_child, (_, prefix, resource) in zip(
        (rt_trigger, rt_event.getPriority(), rt_event.getDelay()),
        children,
        strict=True,
    ):
        assert rt_child.getId() == f"{prefix}1"
        assert rt_child.getMetaId() == f"{prefix}_meta"
        assert rt_child.getName() == f"{prefix}name"
        assert rt_child.getSBOTermID() == "SBO:0000064"
        assert f"{prefix} notes" in rt_child.getNotesString()
        assert rt_child.getNumCVTerms() == 1
        assert rt_child.getCVTerm(0).getResourceURI(0) == resource


def test_roundtrip_event_children_without_math_and_absent(tmp_path: Path) -> None:
    """Test that an element without math and an absent element stay apart.

    A trigger or priority without math, which SBML allows from L3V2 on, is
    read as a `Trigger` or `Priority` whose math is `None`, and written back
    without math. An absent trigger, priority or delay is read as `None` and
    not written.
    """
    import libsbml

    from sbmlutils.factory import Priority, Trigger

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model: libsbml.Model = doc.createModel("m")
    p1: libsbml.Parameter = sbml_model.createParameter()
    p1.setId("p1")
    p1.setValue(0.0)
    p1.setConstant(False)
    # an event with a trigger and a priority without math, and no delay
    e1: libsbml.Event = sbml_model.createEvent()
    e1.setId("e1")
    e1.setUseValuesFromTriggerTime(True)
    t1: libsbml.Trigger = e1.createTrigger()
    t1.setInitialValue(False)
    t1.setPersistent(True)
    e1.createPriority()
    ea1: libsbml.EventAssignment = e1.createEventAssignment()
    ea1.setVariable("p1")
    ea1.setMath(libsbml.parseL3Formula("1"))
    # an event without a trigger and without a priority, with a delay
    e2: libsbml.Event = sbml_model.createEvent()
    e2.setId("e2")
    e2.setUseValuesFromTriggerTime(True)
    delay: libsbml.Delay = e2.createDelay()
    delay.setMath(libsbml.parseL3Formula("2"))

    source_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(source_path))

    model = sbml_to_model(source_path)
    parsed_e1, parsed_e2 = model.events
    assert isinstance(parsed_e1.trigger, Trigger)
    assert parsed_e1.trigger.math is None
    assert isinstance(parsed_e1.priority, Priority)
    assert parsed_e1.priority.math is None
    assert parsed_e1.delay is None
    assert parsed_e2.trigger is None
    assert parsed_e2.priority is None
    assert parsed_e2.delay is not None
    assert parsed_e2.delay.math == "2"

    roundtrip_path = roundtrip_sbml(source_path, tmp_path)
    assert sorted(_elements_with_math(roundtrip_path)) == sorted(
        _elements_with_math(source_path)
    )
    rt_doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    rt_model: libsbml.Model = rt_doc.getModel()
    assert not rt_model.getEvent("e1").isSetDelay()
    assert not rt_model.getEvent("e2").isSetTrigger()
    assert not rt_model.getEvent("e2").isSetPriority()


def test_roundtrip_constraints(tmp_path: Path) -> None:
    """Test that constraints survive a round trip.

    Case 01247 is the only l3v2 semantic case with a `<listOfConstraints>`,
    and its one `<constraint/>` has neither a `<math>` nor a `<message>`
    child. A constraint is not simulable by roadrunner, so this is a
    structural assertion rather than a trajectory comparison, and it also
    compares the math/message presence rather than only the count, so that a
    parser which invents or mangles either would still be caught.
    """
    import libsbml

    sbml_path = testsuite_case("01247")
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
    assert m_out.getNumConstraints() == m_in.getNumConstraints()

    c_in: libsbml.Constraint = m_in.getConstraint(0)
    c_out: libsbml.Constraint = m_out.getConstraint(0)
    assert c_out.isSetMath() == c_in.isSetMath()
    assert c_out.isSetMessage() == c_in.isSetMessage()


def test_roundtrip_constraint_math_and_message(tmp_path: Path) -> None:
    """Test that a constraint's math and message survive a round trip intact.

    No semantic test-suite case carries a constraint with both a `<math>` and
    a `<message>`, so this builds one directly with libsbml, following the
    pattern of `test_roundtrip_rule_keeps_its_own_id`. It also guards against
    the message-nesting failure mode Task 3 found for notes: libsbml's
    `Constraint.getMessageString()` returns the message already wrapped in
    its own `<message>` element, and feeding that string back into
    `Constraint.setMessage` unchanged would double-wrap it, exactly as an
    unprocessed `getNotesString()` used to double-wrap notes.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model = doc.createModel("m")
    p: libsbml.Parameter = sbml_model.createParameter()
    p.setId("p")
    p.setValue(3.0)
    p.setConstant(True)

    constraint: libsbml.Constraint = sbml_model.createConstraint()
    constraint.setId("c1")
    constraint.setMath(libsbml.parseL3Formula("p > 0"))
    constraint.setMessage(
        '<body xmlns="http://www.w3.org/1999/xhtml"><p>p must be positive</p></body>'
    )

    sbml_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))

    model = sbml_to_model(sbml_path)
    assert len(model.constraints) == 1
    assert model.constraints[0].math == "p > 0"
    assert model.constraints[0].message is not None
    # the parsed message is `getMessageString()`'s output, which is wrapped
    # in its own `<message>` element; that element must not appear twice.
    assert model.constraints[0].message.count("<message") == 1

    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    rt_model = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()
    rt_constraint: libsbml.Constraint = rt_model.getConstraint(0)
    assert rt_constraint.isSetMath()
    assert libsbml.formulaToL3String(rt_constraint.getMath()) == "p > 0"
    assert rt_constraint.isSetMessage()
    # a nested `<message><message>...` would round trip to two `<p>` children
    # instead of one.
    message_node = rt_constraint.getMessage()
    body_node = message_node.getChild(0)
    assert body_node.getName() == "body"
    assert body_node.getNumChildren() == 1
    assert body_node.getChild(0).getName() == "p"


#: cases which use modifiers in a reaction
#: 00039 also carries an algebraic rule, which roadrunner cannot simulate
#: (see `test_parse_algebraic_rule_without_id`), so it is excluded here even
#: though it uses a modifier.
CASES_MODIFIERS: list[str] = ["00063", "00064", "00065"]

#: cases whose reactions have a variable stoichiometry
CASES_VARIABLE_STOICHIOMETRY: list[str] = ["00969", "00970", "00971"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_MODIFIERS + CASES_VARIABLE_STOICHIOMETRY)
def test_roundtrip_species_references(case: str, tmp_path: Path) -> None:
    """Test that modifiers and variable stoichiometry survive a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


def test_roundtrip_species_reference_metadata(tmp_path: Path) -> None:
    """Test that a modifier's and reactant's metadata survive both directions.

    None of the vendored test-suite cases carry a modifier with its own id,
    name, metaId, sboTerm, notes or annotation (case 00063's modifier, for
    example, is a bare species reference), so
    `test_roundtrip_species_references` above would pass identically even if
    `set_speciesref_fields`/`parse_sbase_kwargs` wrote or parsed none of that
    metadata. This builds a source document with a fully annotated reactant
    and modifier directly with libsbml, following the pattern of
    `test_roundtrip_constraint_math_and_message`, and checks both directions:
    `sbml_to_model` populates the corresponding `EquationPart`, and
    `create_model` writes it back out to the final SBML.

    The modifier's name is deliberately space-free (`"them1"`): a
    space-containing name is rejected by libsbml itself for any
    `SimpleSpeciesReference`, see
    `test_reaction_speciesref_name_with_space_is_rejected_by_libsbml` in
    `test_factory.py`, so it would not be a name round trip failure, only a
    restatement of that separate, already-pinned libsbml limitation.
    """
    import libsbml

    doc = libsbml.SBMLDocument(3, 2)
    sbml_model = doc.createModel("m")
    c: libsbml.Compartment = sbml_model.createCompartment()
    c.setId("c")
    c.setConstant(True)
    c.setSize(1.0)
    for sid in ("S1", "S2", "M1"):
        species: libsbml.Species = sbml_model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")
        species.setConstant(False)
        species.setBoundaryCondition(False)
        species.setHasOnlySubstanceUnits(False)
        species.setInitialAmount(1.0)

    reaction: libsbml.Reaction = sbml_model.createReaction()
    reaction.setId("r1")
    reaction.setReversible(False)

    def add_cvterm(sbase: libsbml.SBase, resource: str) -> None:
        cv = libsbml.CVTerm()
        cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
        cv.setBiologicalQualifierType(libsbml.BQB_IS)
        cv.addResource(resource)
        sbase.addCVTerm(cv)

    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("S1")
    reactant.setConstant(True)
    reactant.setStoichiometry(1.0)
    reactant.setId("reac1")
    reactant.setMetaId("reac1_meta")
    reactant.setSBOTerm("SBO:0000010")
    reactant.setName("reactantname")
    reactant.setNotes(
        '<body xmlns="http://www.w3.org/1999/xhtml"><p>a reactant</p></body>'
    )
    add_cvterm(reactant, "https://identifiers.org/uniprot/P00001")

    product: libsbml.SpeciesReference = reaction.createProduct()
    product.setSpecies("S2")
    product.setConstant(True)
    product.setStoichiometry(1.0)

    modifier: libsbml.ModifierSpeciesReference = reaction.createModifier()
    modifier.setSpecies("M1")
    modifier.setId("mod1")
    modifier.setMetaId("mod1_meta")
    modifier.setSBOTerm("SBO:0000019")
    modifier.setName("them1")
    modifier.setNotes(
        '<body xmlns="http://www.w3.org/1999/xhtml"><p>a modifier</p></body>'
    )
    add_cvterm(modifier, "https://identifiers.org/uniprot/P35557")

    source_path = tmp_path / "source.xml"
    libsbml.writeSBMLToFile(doc, str(source_path))

    # direction 1: SBML -> Model
    model = sbml_to_model(source_path)
    assert len(model.reactions) == 1
    equation = model.reactions[0].equation
    assert len(equation.reactants) == 1
    assert len(equation.modifiers) == 1

    parsed_reactant = equation.reactants[0]
    assert parsed_reactant.sid == "reac1"
    assert parsed_reactant.metaId == "reac1_meta"
    assert parsed_reactant.sboTerm == "SBO:0000010"
    assert parsed_reactant.name == "reactantname"
    assert parsed_reactant.notes is not None
    assert "a reactant" in parsed_reactant.notes
    assert parsed_reactant.annotations is not None
    assert any("P00001" in str(a) for a in parsed_reactant.annotations)

    parsed_modifier = equation.modifiers[0]
    assert parsed_modifier.species == "M1"
    assert parsed_modifier.sid == "mod1"
    assert parsed_modifier.metaId == "mod1_meta"
    assert parsed_modifier.sboTerm == "SBO:0000019"
    assert parsed_modifier.name == "them1"
    assert parsed_modifier.notes is not None
    assert "a modifier" in parsed_modifier.notes
    assert parsed_modifier.annotations is not None
    assert any("P35557" in str(a) for a in parsed_modifier.annotations)

    # direction 2: Model -> SBML
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    rt_model = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()
    rt_reaction: libsbml.Reaction = rt_model.getReaction("r1")

    rt_reactant: libsbml.SpeciesReference = rt_reaction.getReactant(0)
    assert rt_reactant.getId() == "reac1"
    assert rt_reactant.getMetaId() == "reac1_meta"
    assert rt_reactant.getSBOTermID() == "SBO:0000010"
    assert rt_reactant.getName() == "reactantname"
    assert "a reactant" in rt_reactant.getNotesString()
    assert rt_reactant.getNumCVTerms() == 1
    assert "P00001" in rt_reactant.getCVTerm(0).getResourceURI(0)

    rt_modifier: libsbml.ModifierSpeciesReference = rt_reaction.getModifier(0)
    assert rt_modifier.getId() == "mod1"
    assert rt_modifier.getMetaId() == "mod1_meta"
    assert rt_modifier.getSBOTermID() == "SBO:0000019"
    assert rt_modifier.getName() == "them1"
    assert "a modifier" in rt_modifier.getNotesString()
    assert rt_modifier.getNumCVTerms() == 1
    assert "P35557" in rt_modifier.getCVTerm(0).getResourceURI(0)


if __name__ == "__main__":
    # the worker of `run_case_isolated`: `python test_roundtrip.py <sbml_path>
    # <case_dir>` round trips the case and records its outcome in `case_dir`
    run_worker(Path(sys.argv[1]), Path(sys.argv[2]))


def _spatial_dimensions(sbml_path: Path) -> list[float | None]:
    """Collect the spatialDimensions of every compartment of a model.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the spatialDimensions of every compartment in document order, `None`
        for a compartment which does not set them
    """
    import libsbml

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    dimensions: list[float | None] = []
    compartment: libsbml.Compartment
    for compartment in doc.getModel().getListOfCompartments():
        dimensions.append(
            compartment.getSpatialDimensionsAsDouble()
            if compartment.isSetSpatialDimensions()
            else None
        )
    return dimensions


@requires_testsuite
def test_roundtrip_non_integral_spatial_dimensions(tmp_path: Path) -> None:
    """Test that a compartment of 2.7 spatial dimensions keeps them.

    SBML declares `spatialDimensions` a double, and case 01310 uses 2.7.
    `libsbml.Compartment.getSpatialDimensions` is the accessor of the
    unsigned integer attribute of SBML L2 and returns 0 for a value which is
    not integral, so the round trip wrote `spatialDimensions="0"`. Neither
    the simulation sweep nor validation sees that: the attribute changes no
    trajectory and 0 is a valid value.
    """
    sbml_path = testsuite_case("01310")
    assert _spatial_dimensions(sbml_path) == [2.7]

    assert _spatial_dimensions(roundtrip_sbml(sbml_path, tmp_path)) == [2.7]


@pytest.mark.parametrize("dimensions", [2.7, 3.0, 3, 0.0])
def test_roundtrip_spatial_dimensions_of_a_definition(
    dimensions: float, tmp_path: Path
) -> None:
    """Test that the spatial dimensions of a model definition survive.

    The test suite has one case with a non-integral value and none with an
    integral one written as a float, so the source is built with the factory.
    An integral value stays an integer in the document: libsbml writes the
    double `3.0` as `spatialDimensions="3"`.
    """
    sbml_path = tmp_path / "source.xml"
    create_model(
        model=Model(
            "spatial_dimensions",
            compartments=[Compartment("c", 4.0, spatialDimensions=dimensions)],
        ),
        filepath=sbml_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )
    assert _spatial_dimensions(sbml_path) == [float(dimensions)]

    roundtrip_dir = tmp_path / "roundtrip"
    roundtrip_dir.mkdir()
    roundtrip_path = roundtrip_sbml(sbml_path, roundtrip_dir)
    assert _spatial_dimensions(roundtrip_path) == [float(dimensions)]
    assert f'spatialDimensions="{dimensions:g}"' in roundtrip_path.read_text()
