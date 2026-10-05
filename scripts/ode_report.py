"""Report the pass rate of the ODE export over the SBML test suite.

Run the sweeps of `tests/converters/ode/test_ode_testsuite.py` over the l3v2 semantic cases and print a summary per format, for local runs and for the table of the documentation:

    uv run python scripts/ode_report.py
    uv run python scripts/ode_report.py --format julia --format r
    uv run python scripts/ode_report.py --case 00001 --case 01124 --limit 150

The format is `python` unless `--format` is given, which is repeatable. The julia and R code runs with the commands of `SBMLUTILS_JULIA` and `SBMLUTILS_RSCRIPT`, see `tests/converters/ode/ode_helpers.py`; the jobs of these run in a directory of the temporary directory, which a docker command has to mount (`-v /tmp:/tmp`).

Every case is checked in a python process of its own, see `run_case_isolated` of `tests/test_roundtrip.py`, whose worker is `tests/converters/ode/test_ode_testsuite.py`: roadrunner and the integrators are native code, and a crash ends one case instead of the report. A case is killed after `--timeout` seconds. The julia and R code of the cases runs before, in `--processes` processes of julia or R (`run_jobs`), which compile the integrator and load the packages once for many cases; a job which takes longer than `--timeout` seconds, its compilation included, or ends its process is reported as timed out or crashed, and the jobs which had not finished run again.

The outcomes are those of the tests of the sweep: passed, failed, unsupported (the code refuses to render a construct, counted by construct), no reference (roadrunner does not simulate the case, the tests skip it), not deterministic (`NONDETERMINISTIC`, the tests skip it), crashed, timed out and worker error. The pass rate is `passed / (passed + failed)`. A failure is listed with its reason from `KNOWN_FAILURES`, or as unexpected with its error; every known failure of a format is listed with its reason. The code and the outcome of every case are kept in `.ode_tmp/<format>/<case>/` for inspection.
"""

import argparse
import shutil
import sys
import tempfile
import time
from collections import Counter, defaultdict
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT: Path = Path(__file__).parent.parent
ODE_TESTS: Path = ROOT / "tests" / "converters" / "ode"

sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests"), str(ODE_TESTS)]

import pytest  # noqa: E402
from ode_helpers import LANGUAGES, Job, JobsError, run_jobs  # noqa: E402
from roundtrip_report import reason_of, run_case  # noqa: E402
from test_roundtrip import (  # noqa: E402
    NONDETERMINISTIC,
    SWEEP_CASES,
    CaseResult,
    Outcome,
    run_case_isolated,
)

try:
    from test_ode_testsuite import KNOWN_FAILURES, PROCESSES, _case_job
except pytest.skip.Exception as missing:
    # the sweep skips without roadrunner, the reference, and scipy, the integrator
    sys.exit(f"The ODE report needs roadrunner and scipy: {missing}")

TMP_DIR: Path = ROOT / ".ode_tmp"
"""The scratch directory, a directory per format and case."""

WORKER: Path = ODE_TESTS / "test_ode_testsuite.py"
"""The worker of `run_case_isolated`, which checks a case in a format."""

FORMATS: list[str] = ["python", "julia", "r"]
"""The formats of code."""

LABELS: dict[Outcome, str] = {
    Outcome.PASSED: "passed",
    Outcome.FAILED: "failed",
    Outcome.UNSUPPORTED: "unsupported",
    Outcome.NO_REFERENCE: "no reference",
    Outcome.NOT_DETERMINISTIC: "not deterministic",
    Outcome.CRASHED: "crashed",
    Outcome.TIMED_OUT: "timed out",
    Outcome.WORKER_ERROR: "worker error",
}
"""The outcomes in the order of the report, with their names in the ODE export."""

Results = list[tuple[str, CaseResult]]
"""The case id and the result of every case of a format."""


def run_python_case(sbml_path: Path, timeout: float) -> tuple[str, CaseResult]:
    """Check the python code of a case in a process of its own.

    Args:
        sbml_path: path of the SBML file of the case
        timeout: seconds after which the case is killed

    Returns:
        the case id and its result
    """
    return run_case(sbml_path, timeout, TMP_DIR / "python", WORKER, ["python"])


def run_language_jobs(
    language: str, cases: list[Path], timeout: float, processes: int
) -> tuple[dict[str, Path], dict[str, CaseResult]]:
    """Run the julia or R jobs of the cases which have one, see `_case_job`.

    The jobs run in a directory of the temporary directory; the files of a job
    which finished, its code and its output, are copied to the directory of its
    case. A job which stops its processes, by taking too long or by ending its
    process, is reported, and the jobs which had not finished run again.

    Args:
        language: `julia` or `r`
        cases: the paths of the SBML files of the cases
        timeout: seconds a job may take, its compilation included
        processes: the number of processes of julia or R

    Returns:
        the code of the job of each case which ran, in the directory of the case,
        and the result of each case whose job stopped its processes
    """
    suffix = LANGUAGES[language].suffix
    remaining: dict[str, Job] = {}
    for sbml_path in cases:
        job = _case_job(language, sbml_path, reference=False)
        if job is not None:
            remaining[sbml_path.name[:5]] = job
    ran: dict[str, Path] = {}
    stopped: dict[str, CaseResult] = {}
    while remaining:
        with tempfile.TemporaryDirectory(prefix=f"ode_report_{language}_") as tmp:
            directory = Path(tmp)
            try:
                outputs = run_jobs(
                    language,
                    remaining,
                    directory,
                    min(processes, len(remaining)),
                    timeout,
                )
            except JobsError as error:
                outputs = error.outputs
                message = str(error).splitlines()[0]
                print(f"{language}: {message}", file=sys.stderr)
                if error.job is not None:
                    outcome = Outcome.TIMED_OUT if error.timed_out else Outcome.CRASHED
                    stopped[error.job] = CaseResult(outcome, "run the code", message)
                elif not outputs:
                    for name in remaining:
                        stopped[name] = CaseResult(
                            Outcome.WORKER_ERROR, "run the code", message
                        )
            for name in outputs:
                case_dir = TMP_DIR / language / name
                case_dir.mkdir(parents=True, exist_ok=True)
                for file in directory.glob(f"{name}{suffix}*"):
                    shutil.copy(file, case_dir / file.name)
                ran[name] = case_dir / f"{name}{suffix}"
        remaining = {
            name: job
            for name, job in remaining.items()
            if name not in ran and name not in stopped
        }
    return ran, stopped


def run_language(
    language: str, cases: list[Path], timeout: float, jobs: int, processes: int
) -> Results:
    """Check the julia or R code of the cases.

    Args:
        language: `julia` or `r`
        cases: the paths of the SBML files of the cases
        timeout: seconds a job or a check may take
        jobs: the number of checks which run in parallel
        processes: the number of processes of julia or R

    Returns:
        the case id and the result of every case
    """
    ran, stopped = run_language_jobs(language, cases, timeout, processes)

    def check(sbml_path: Path) -> tuple[str, CaseResult]:
        case = sbml_path.name[:5]
        if case in NONDETERMINISTIC:
            return case, CaseResult(
                Outcome.NOT_DETERMINISTIC, "", NONDETERMINISTIC[case]
            )
        if case in stopped:
            return case, stopped[case]
        case_dir = TMP_DIR / language / case
        case_dir.mkdir(parents=True, exist_ok=True)
        arguments = [language, *([str(ran[case])] if case in ran else [])]
        return case, run_case_isolated(sbml_path, case_dir, timeout, WORKER, arguments)

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(check, cases))


def _shortened(text: str, width: int = 100) -> str:
    """Text on a single line of at most `width` characters."""
    line = " ".join(text.split())
    return line if len(line) <= width else line[: width - 3] + "..."


def print_report(fmt: str, results: Results, seconds: float) -> None:
    """Print the summary of the sweep of a format.

    Args:
        fmt: the format
        results: the case id and the result of every case
        seconds: the wall time of the sweep
    """
    counts = Counter(result.outcome for _, result in results)
    print(f"\n== {fmt}: {len(results)} cases in {seconds:.0f} s")
    for outcome, label in LABELS.items():
        if counts[outcome]:
            print(f"  {counts[outcome]:>5}  {label}")
    comparable = counts[Outcome.PASSED] + counts[Outcome.FAILED]
    if comparable:
        rate = 100.0 * counts[Outcome.PASSED] / comparable
        print(f"pass rate: {counts[Outcome.PASSED]}/{comparable} = {rate:.1f}%")

    constructs: Counter[str] = Counter()
    for _, result in results:
        if result.outcome == Outcome.UNSUPPORTED:
            constructs.update(result.detail.split(", "))
    if constructs:
        print("\nunsupported, cases by construct:")
        for construct, count in constructs.most_common():
            print(f"  {count:>5}  {construct}")

    failures = [(c, r) for c, r in results if r.outcome == Outcome.FAILED]
    if failures:
        print("\nfailures:")
        for case, result in failures:
            reason = KNOWN_FAILURES.get((fmt, case))
            text = f"known: {reason}" if reason else f"UNEXPECTED: {result.detail}"
            print(f"  {case}  [{result.stage}]  {_shortened(text)}")

    outcomes = {case: result.outcome for case, result in results}
    known = sorted(case for f, case in KNOWN_FAILURES if f == fmt and case in outcomes)
    if known:
        print("\nknown failures:")
        for case in known:
            status = LABELS[outcomes[case]]
            note = ", remove it" if outcomes[case] == Outcome.PASSED else ""
            print(f"  {case}  {status}{note}: {KNOWN_FAILURES[fmt, case]}")

    for outcome in [Outcome.CRASHED, Outcome.TIMED_OUT, Outcome.WORKER_ERROR]:
        listed = [(c, r) for c, r in results if r.outcome == outcome]
        if listed:
            print(f"\n{LABELS[outcome]}:")
            for case, result in listed:
                print(f"  {case}  [{result.stage}]  {_shortened(result.detail)}")

    reasons: dict[str, list[str]] = defaultdict(list)
    for case, result in results:
        if result.outcome == Outcome.NO_REFERENCE:
            prefix = "roadrunner does not simulate the case: "
            reasons[reason_of(result.detail.removeprefix(prefix))].append(case)
    if reasons:
        print("\nno reference, cases by the error of roadrunner:")
        for reason, cases in sorted(reasons.items(), key=lambda item: -len(item[1])):
            print(f"  {len(cases):>5}  {_shortened(reason)}")
            print(f"         {' '.join(cases)}")


def print_table(summaries: dict[str, Results]) -> None:
    """Print the counts of every format as a markdown table.

    Args:
        summaries: the results of every format
    """
    header = ["format", "cases", *LABELS.values(), "pass rate"]
    print("\n| " + " | ".join(header) + " |")
    print("|" + "|".join("---" for _ in header) + "|")
    for fmt, results in summaries.items():
        counts = Counter(result.outcome for _, result in results)
        comparable = counts[Outcome.PASSED] + counts[Outcome.FAILED]
        rate = (
            f"{100.0 * counts[Outcome.PASSED] / comparable:.1f}%" if comparable else "-"
        )
        cells = [fmt, str(len(results)), *(str(counts[o]) for o in LABELS), rate]
        print("| " + " | ".join(cells) + " |")


def main(argv: Sequence[str] | None = None) -> None:
    """Run the sweeps and print their pass rates.

    Args:
        argv: the arguments, those of the command line if `None`
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--format",
        action="append",
        choices=FORMATS,
        help="a format of code, repeatable (default: python)",
    )
    parser.add_argument("--limit", type=int, default=0, help="only the first N cases")
    parser.add_argument(
        "--case", action="append", default=[], help="only this case, repeatable"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="seconds after which a case or a job is stopped (default: 600)",
    )
    parser.add_argument(
        "--jobs", type=int, default=8, help="cases checked in parallel (default: 8)"
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=PROCESSES,
        help=f"processes of julia or R (default: {PROCESSES})",
    )
    args = parser.parse_args(argv)

    cases = SWEEP_CASES
    if args.case:
        cases = [path for path in cases if path.name[:5] in args.case]
    if args.limit:
        cases = cases[: args.limit]

    summaries: dict[str, Results] = {}
    for fmt in dict.fromkeys(args.format or ["python"]):
        start = time.perf_counter()
        if fmt == "python":
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                results = list(
                    executor.map(
                        lambda path: run_python_case(path, args.timeout), cases
                    )
                )
        else:
            if LANGUAGES[fmt].command() is None:
                print(
                    f"\n== {fmt}: {LANGUAGES[fmt].title} is not runnable, see "
                    f"`{LANGUAGES[fmt].variable}`"
                )
                continue
            shutil.rmtree(TMP_DIR / fmt, ignore_errors=True)
            results = run_language(fmt, cases, args.timeout, args.jobs, args.processes)
        print_report(fmt, results, time.perf_counter() - start)
        summaries[fmt] = results
    print_table(summaries)


if __name__ == "__main__":
    main()
