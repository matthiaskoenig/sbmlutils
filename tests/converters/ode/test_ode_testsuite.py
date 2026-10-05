"""Test the generated python, julia and R against roadrunner on the SBML test suite.

Every case is the l3v2 flavour of a semantic case of the vendored test suite, see
`tests/test_roundtrip.py`, simulated to `T_END` at `T_STEPS` time points. A case with
a construct the code does not support (`OdeSystem.unsupported`) must refuse to
render; every other case must simulate as roadrunner: every column of `simulate`
(the states, the assigned values and the constants which events change) against its
roadrunner selection. The tolerances of a case with events are relaxed, an event
time is located to the tolerance of the integration.

`CURATED` runs in the default test run, the full sweeps `test_python_sweep`,
`test_julia_sweep` and `test_r_sweep` behind the `sbml_testsuite` marker. A case
whose events are not deterministic is skipped (`NONDETERMINISTIC`), as is a case
roadrunner does not simulate, which has no reference (the fbc cases, an
integration which fails); a known failure is a strict xfail with its reason
(`KNOWN_FAILURES`).

The julia and the R code of the cases runs in few processes of julia and R, which
compile the integrator (julia) and load the packages once for many cases
(`run_jobs`); the julia tests skip without julia, see `SBMLUTILS_JULIA`, the R tests
without R and deSolve, see `SBMLUTILS_RSCRIPT`.

`scripts/ode_report.py` runs the sweeps and reports their pass rates. It checks every
case in a python process of its own (`run_case_isolated` of `tests/test_roundtrip.py`),
which roadrunner and the integrators run in, so that a crash in native code ends one
case; this module is the worker of that process, see `run_worker` and the `__main__`
block at its end.
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    # the worker runs as a script, which finds `ode_helpers` next to it, but not
    # `test_roundtrip`
    sys.path.insert(0, str(Path(__file__).parents[2]))

import functools
from collections.abc import Callable

import numpy as np
import pytest
from ode_helpers import (
    Job,
    JobOutput,
    assert_table_as_roadrunner,
    assert_trajectory_as_roadrunner,
    julia_simulate_job,
    python_module,
    r_simulate_job,
    read_job_output,
    require_language,
    run_jobs,
)
from test_roundtrip import (
    NONDETERMINISTIC,
    SWEEP_CASES,
    T_END,
    T_STEPS,
    Outcome,
    _record,
    requires_testsuite,
    sbml_case_idfn,
    suite_case,
)

from sbmlutils.converters.ode import OdeSystem

roadrunner = pytest.importorskip("roadrunner")
pytest.importorskip("scipy")

# the first three cases (in their order, without the nondeterministic ones) whose
# l3v2 model has a construct, found by searching the model for it; together they
# cover every construct of SBML core the export handles or refuses
# fmt: off
CURATED: list[str] = [
    "00007", "00008", "00009",  # boundary species
    "00025", "00034", "00035",  # function definitions
    "00026", "00041", "00071",  # events
    "00027", "00036", "00037",  # initial assignments
    "00029", "00030", "00038",  # assignment rules
    "00031", "00032", "00033",  # rate rules
    "00039", "00040", "00182",  # algebraic rules, unsupported
    "00051", "00052", "00053",  # compartments which are not constant
    "00057", "00058",           # local parameters, with 00027
    "00060", "00061", "00062",  # species in amount
    "00072", "00073",           # delays, with 00071
    "00190", "00191", "00192",  # piecewise
    "00928", "00995", "00996",  # triggers with the initial value false
    "00930", "00931", "00934",  # priorities
    "00932", "00935", "00963",  # events which are not persistent
    "00936", "00978", "00980",  # values from the time of the execution
    "00937", "00938", "00939",  # the delay csymbol, unsupported
    "00960", "00961", "01000",  # avogadro
    "00969", "00970", "00971",  # species references with an id
    "00975", "00976", "00977",  # conversion factors
    "01124", "01125", "01126",  # comp, flattened
    "01248", "01249", "01250",  # rateOf
    "01488",                    # math of the time out of its domain in a function
    "01506",                    # an event changes the size, a rate rule rescales
    "01779",                    # an event assigns a concentration held as amount
]
# fmt: on

# the cases whose simulation in a format differs from roadrunner, with the reason
_WINDOW_01511 = (
    "the trigger holds for 0.025 time units, from t = 0.45 to 0.475, between two "
    "steps of the integrator of roadrunner at the time points of the case, which "
    "misses it (with 1001 time points it executes the event); the {} code evaluates "
    "the triggers inside each step, finds the trigger and executes the event"
)
KNOWN_FAILURES: dict[tuple[str, str], str] = {
    ("python", "01511"): _WINDOW_01511.format("python"),
    ("julia", "01511"): _WINDOW_01511.format("julia"),
    ("r", "01511"): _WINDOW_01511.format("R"),
    ("r", "01106"): (
        "the trigger `X >= 2` holds from t = 1, a time point, where roadrunner and "
        "the python and julia code report the values after the event; X' = 1 from "
        "X = 1, and the integration of deSolve::lsoda gives X(1) = "
        "1.9999999999999998, one ulp below 2, so that the event executes at "
        "1.0000000000000002 and the time point has the values before it. The "
        "rounding cannot be resolved by a tolerance at the time points: case 00963 "
        "executes events 1.4e-16 after a time point, where roadrunner reports the "
        "values before them"
    ),
}

# the processes of julia and of R of the full sweep, which run in parallel
PROCESSES = 4

# the body of the job of a case, by language
SIMULATE_JOBS = {
    "julia": julia_simulate_job(T_END, T_STEPS),
    "r": r_simulate_job(T_END, T_STEPS),
}


@functools.cache
def _reference_error(sbml_path: Path) -> str | None:
    """Why roadrunner does not simulate a case, `None` if it does.

    Without a simulation of roadrunner a case has no reference: an fbc model, an
    integration which fails (01148 grows as the exponential of 1e9 t^2).
    """
    try:
        roadrunner.RoadRunner(str(sbml_path)).simulate(0.0, T_END, T_STEPS)
    except RuntimeError as error:
        return str(error)
    return None


def _tolerances(system: OdeSystem) -> tuple[float, float]:
    """The relative and absolute tolerances of the comparison, relaxed for events.

    An event time is located to the tolerance of the integration, which shifts the
    values after it.
    """
    return (1e-4, 1e-6) if system.events else (1e-6, 1e-9)


Stage = Callable[[str], None]
"""A function which is told the stage a check enters, see `run_worker`."""


def _no_stage(stage: str) -> None:
    """Ignore the stage of a check, which only the worker records."""


def check_python_case(
    sbml_path: Path, tmp_path: Path, stage: Stage = _no_stage
) -> OdeSystem:
    """Check the python code of a case: it refuses to render or simulates right.

    Args:
        sbml_path: path of the SBML file of the case
        tmp_path: directory of the python file
        stage: is told the stage the check enters

    Returns:
        the system of the case

    Raises:
        pytest.skip.Exception: if roadrunner does not simulate the case
    """
    stage("read the model")
    system = OdeSystem.from_sbml(sbml_path)
    if system.unsupported:
        stage("refuse to render")
        with pytest.raises(NotImplementedError):
            system.render("python")
        return system
    stage("simulate the reference")
    error = _reference_error(sbml_path)
    if error is not None:
        pytest.skip(f"roadrunner does not simulate the case: {error}")
    stage("render")
    module = python_module(system, tmp_path / f"case_{sbml_path.name[:5]}.py")
    stage("simulate and compare")
    # math out of its domain is nan or inf as in roadrunner, e.g. case 01488
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        assert_trajectory_as_roadrunner(sbml_path, module, *_tolerances(system))
    return system


def check_job_case(
    language: str,
    sbml_path: Path,
    output: Callable[[], JobOutput],
    stage: Stage = _no_stage,
) -> OdeSystem:
    """Check the julia or R code of a case: it refuses to render or simulates right.

    Args:
        language: `julia` or `r`
        sbml_path: path of the SBML file of the case
        output: the output of the job of the case, see `_case_job`
        stage: is told the stage the check enters

    Returns:
        the system of the case

    Raises:
        pytest.skip.Exception: if roadrunner does not simulate the case
    """
    stage("read the model")
    system = OdeSystem.from_sbml(sbml_path)
    if system.unsupported:
        stage("refuse to render")
        with pytest.raises(NotImplementedError):
            system.render(language)
        return system
    stage("simulate the reference")
    error = _reference_error(sbml_path)
    if error is not None:
        pytest.skip(f"roadrunner does not simulate the case: {error}")
    # the code of the job, rendered again to report an error of its own case
    stage("render")
    system.render(language)
    stage("run the code")
    table = output().table()
    stage("compare")
    assert_table_as_roadrunner(sbml_path, table, *_tolerances(system))
    return system


def _case_job(language: str, sbml_path: Path, reference: bool = True) -> Job | None:
    """The job which simulates the code of a case, `None` if there is nothing to run.

    A case without a job is skipped, refuses to render or fails to render, which
    `check_job_case` reports.

    Args:
        language: `julia` or `r`
        sbml_path: path of the SBML file of the case
        reference: whether a case which roadrunner does not simulate has no job,
            which simulates the case with roadrunner
    """
    if sbml_path.name[:5] in NONDETERMINISTIC:
        return None
    try:
        system = OdeSystem.from_sbml(sbml_path)
        if system.unsupported:
            return None
        if reference and _reference_error(sbml_path) is not None:
            return None
        code = system.render(language)
    except Exception:
        # the check of the case reports the error
        return None
    return Job(code, SIMULATE_JOBS[language])


def _detail(error: BaseException) -> str:
    """The type of an error and its first line, with the next one after a colon.

    A failure of julia or R code is `The julia code failed:` and the error of the
    code on the next line.
    """
    lines = [line.strip() for line in str(error).splitlines() if line.strip()]
    if len(lines) > 1 and lines[0].endswith(":"):
        lines[0] = f"{lines[0]} {lines[1]}"
    return f"{type(error).__name__}: {lines[0] if lines else ''}"


def run_worker(
    sbml_path: Path, case_dir: Path, fmt: str, job_path: Path | None = None
) -> None:
    """Check the code of a case in a format and record its outcome, in the worker.

    The outcome is that of the test of the case, see `check_python_case` and
    `check_job_case`: passed, unsupported (the code refuses to render), not
    simulatable (roadrunner does not simulate the case, there is no reference) or
    failed, recorded with `_record` of `tests/test_roundtrip.py`.

    Args:
        sbml_path: path of the SBML file of the case
        case_dir: directory of the case, which the python code and the outcome are
            written to
        fmt: `python`, `julia` or `r`
        job_path: the code of the julia or R job of the case, which ran, see
            `run_jobs`; `None` without a job
    """
    current = "start"

    def stage(name: str) -> None:
        nonlocal current
        current = name
        _record(case_dir, name, None, "")

    def output() -> JobOutput:
        if job_path is None:
            raise FileNotFoundError("The case has no job.")
        return read_job_output(fmt, job_path)

    try:
        if fmt == "python":
            system = check_python_case(sbml_path, case_dir, stage)
        else:
            system = check_job_case(fmt, sbml_path, output, stage)
    except pytest.skip.Exception as error:
        _record(case_dir, current, Outcome.NOT_SIMULATABLE, str(error))
    except (Exception, pytest.fail.Exception) as error:
        _record(case_dir, current, Outcome.FAILED, _detail(error))
    else:
        if system.unsupported:
            constructs = sorted({construct for construct, _ in system.unsupported})
            _record(case_dir, current, Outcome.UNSUPPORTED, ", ".join(constructs))
        else:
            _record(case_dir, current, Outcome.PASSED, "")


Suite = Callable[[str, str, list[Path], Path], JobOutput]


@pytest.fixture(scope="module")
def suite(tmp_path_factory: pytest.TempPathFactory) -> Suite:
    """The output of the julia or R job of a case.

    The jobs of all cases of a language and a group (`curated`, `sweep`) run on the
    first request of one of them, with `PROCESSES` processes for the sweep.
    """
    outputs: dict[tuple[str, str], dict[str, JobOutput]] = {}

    def output(
        language: str, group: str, paths: list[Path], sbml_path: Path
    ) -> JobOutput:
        require_language(language)
        if (language, group) not in outputs:
            jobs = {}
            for path in paths:
                job = _case_job(language, path)
                if job is not None:
                    jobs[f"case_{path.name[:5]}"] = job
            processes = 1 if group == "curated" else PROCESSES
            outputs[language, group] = run_jobs(
                language,
                jobs,
                tmp_path_factory.mktemp(f"{language}_{group}"),
                processes,
            )
        return outputs[language, group][f"case_{sbml_path.name[:5]}"]

    return output


def _mark(fmt: str, case: str, request: pytest.FixtureRequest) -> None:
    """Skip a nondeterministic case, mark a known failure as a strict xfail."""
    if case in NONDETERMINISTIC:
        pytest.skip(f"the events are not deterministic: {NONDETERMINISTIC[case]}")
    reason = KNOWN_FAILURES.get((fmt, case))
    if reason is not None:
        request.applymarker(pytest.mark.xfail(reason=reason, strict=True))


@requires_testsuite
@pytest.mark.parametrize("case", CURATED)
def test_python_curated(
    case: str, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """The python code of a curated case simulates as roadrunner."""
    _mark("python", case, request)
    check_python_case(suite_case(case), tmp_path)


@requires_testsuite
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_python_sweep(
    sbml_path: Path, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """The python code of every l3v2 case simulates as roadrunner."""
    _mark("python", sbml_path.name[:5], request)
    check_python_case(sbml_path, tmp_path)


def _check_curated(
    language: str, case: str, suite: Suite, request: pytest.FixtureRequest
) -> None:
    """Check the julia or R code of a curated case."""
    _mark(language, case, request)
    paths = [suite_case(c) for c in CURATED]
    sbml_path = suite_case(case)
    check_job_case(
        language, sbml_path, lambda: suite(language, "curated", paths, sbml_path)
    )


def _check_sweep(
    language: str, sbml_path: Path, suite: Suite, request: pytest.FixtureRequest
) -> None:
    """Check the julia or R code of a case of the sweep."""
    _mark(language, sbml_path.name[:5], request)
    check_job_case(
        language, sbml_path, lambda: suite(language, "sweep", SWEEP_CASES, sbml_path)
    )


@requires_testsuite
@pytest.mark.parametrize("case", CURATED)
def test_julia_curated(case: str, suite: Suite, request: pytest.FixtureRequest) -> None:
    """The julia code of a curated case simulates as roadrunner."""
    _check_curated("julia", case, suite, request)


@requires_testsuite
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_julia_sweep(
    sbml_path: Path, suite: Suite, request: pytest.FixtureRequest
) -> None:
    """The julia code of every l3v2 case simulates as roadrunner."""
    _check_sweep("julia", sbml_path, suite, request)


@requires_testsuite
@pytest.mark.parametrize("case", CURATED)
def test_r_curated(case: str, suite: Suite, request: pytest.FixtureRequest) -> None:
    """The R code of a curated case simulates as roadrunner."""
    _check_curated("r", case, suite, request)


@requires_testsuite
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_r_sweep(sbml_path: Path, suite: Suite, request: pytest.FixtureRequest) -> None:
    """The R code of every l3v2 case simulates as roadrunner."""
    _check_sweep("r", sbml_path, suite, request)


def test_curated_cases_exist() -> None:
    """The curated and the known failing cases are cases of the test suite."""
    swept = {sbml_path.name[:5] for sbml_path in SWEEP_CASES}
    if not swept:
        pytest.skip("the SBML test suite is not vendored")
    assert len(CURATED) == len(set(CURATED))
    assert set(CURATED) <= swept
    assert {case for _, case in KNOWN_FAILURES} <= swept


@requires_testsuite
@pytest.mark.parametrize("fmt", ["python", "julia", "r"])
def test_report(
    fmt: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`scripts/ode_report.py` checks the cases of a format in processes of their own.

    Case 00001 passes, case 00039 has an algebraic rule, which is unsupported.
    """
    if fmt != "python":
        require_language(fmt)
    from scripts import ode_report

    monkeypatch.setattr(ode_report, "TMP_DIR", tmp_path)
    ode_report.main(["--case", "00001", "--case", "00039", "--format", fmt])
    output = capsys.readouterr().out
    assert "  1  algebraic rule" in output
    rows = [line for line in output.splitlines() if line.startswith(f"| {fmt} |")]
    assert rows == [f"| {fmt} | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 100.0% |"]
    assert (tmp_path / fmt / "00001" / "outcome.json").exists()


if __name__ == "__main__":
    # the worker of `run_case_isolated`: `python test_ode_testsuite.py <sbml_path>
    # <case_dir> <format> [<job_path>]` checks the case and records its outcome in
    # `case_dir`, see `scripts/ode_report.py`
    run_worker(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        sys.argv[3],
        Path(sys.argv[4]) if len(sys.argv) > 4 else None,
    )
