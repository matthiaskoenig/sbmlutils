"""Report the round-trip simulation pass rate over the SBML test suite.

Run the sweep over the l3v2 semantic cases and print a summary, for local runs
and for tracking progress on
https://github.com/matthiaskoenig/sbmlutils/issues/469:

    uv run python scripts/roundtrip_report.py
    uv run python scripts/roundtrip_report.py --limit 150
    uv run python scripts/roundtrip_report.py --case 00001 --case 01124

This is the `test_roundtrip_sweep` of `tests/test_roundtrip.py` run in
parallel. Every case runs in a python process of its own, see
`run_case_isolated`: libroadrunner has crashed in native code, at varying
cases, in a sweep which ran every case in one process, and no `try/except`
can catch that. Isolated, a crash ends one case instead of the sweep, and it
is reported as an outcome of its own, apart from the genuine round-trip
failures. A case is killed after `--timeout` seconds.

The pass rate is `passed / (passed + failed)`: the cases whose original does
not simulate, is not deterministic, or whose process crashed or timed out say
nothing about the round trip. A failure is listed with its reason from
`KNOWN_FAILURES`, or as unexpected. The round-tripped SBML and the outcome of
every case are kept in `.roundtrip_tmp/<case>/` for inspection.
"""

import argparse
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT: Path = Path(__file__).parent.parent

sys.path.insert(0, str(ROOT / "tests"))

from test_roundtrip import (  # noqa: E402
    KNOWN_FAILURES,
    NONDETERMINISTIC,
    SWEEP_CASES,
    CaseResult,
    Outcome,
    run_case_isolated,
)

#: the scratch directory, one directory per case
TMP_DIR: Path = ROOT / ".roundtrip_tmp"


def run_case(sbml_path: Path, timeout: float) -> tuple[str, CaseResult]:
    """Run a single case in a process of its own.

    Args:
        sbml_path: path of the SBML file of the case
        timeout: seconds after which the case is killed

    Returns:
        the case id and its result
    """
    case = sbml_path.name[:5]
    case_dir = TMP_DIR / case
    shutil.rmtree(case_dir, ignore_errors=True)
    if case in NONDETERMINISTIC:
        return case, CaseResult(Outcome.NOT_DETERMINISTIC, "", NONDETERMINISTIC[case])

    case_dir.mkdir(parents=True)
    return case, run_case_isolated(sbml_path, case_dir, timeout=timeout)


def print_report(results: list[tuple[str, CaseResult]], seconds: float) -> None:
    """Print the summary of a sweep.

    Args:
        results: the case id and the result of every case
        seconds: the wall time of the sweep
    """
    counts = Counter(result.outcome for _, result in results)
    print(f"cases          : {len(results)} in {seconds:.0f} s")
    for outcome in Outcome:
        if counts[outcome]:
            print(f"  {counts[outcome]:>5}  {outcome}")

    comparable = counts[Outcome.PASSED] + counts[Outcome.FAILED]
    if comparable:
        rate = 100.0 * counts[Outcome.PASSED] / comparable
        print(f"\npass rate      : {counts[Outcome.PASSED]}/{comparable} = {rate:.1f}%")

    # the failures grouped by their known reason
    reasons: dict[str, list[str]] = defaultdict(list)
    for case, result in results:
        if result.outcome == Outcome.FAILED:
            reasons[KNOWN_FAILURES.get(case, "UNEXPECTED")].append(case)
    if reasons:
        print(f"\n{Outcome.FAILED}:")
        for reason, cases in sorted(reasons.items(), key=lambda item: -len(item[1])):
            print(f"  {len(cases):>5}  {reason}")
            print(f"         {' '.join(cases)}")
    unexpected = [
        (case, result)
        for case, result in results
        if result.outcome == Outcome.FAILED and case not in KNOWN_FAILURES
    ]
    for case, result in unexpected:
        print(f"  {case}  [{result.stage}]  {result.detail}")

    # a known failure which passes fails the strict xfail of the sweep
    fixed = [
        case
        for case, result in results
        if result.outcome == Outcome.PASSED and case in KNOWN_FAILURES
    ]
    if fixed:
        print(f"\nknown failures which pass, remove them: {' '.join(fixed)}")

    for outcome in [Outcome.CRASHED, Outcome.TIMED_OUT, Outcome.WORKER_ERROR]:
        listed = [
            (case, result) for case, result in results if result.outcome == outcome
        ]
        if listed:
            print(f"\n{outcome}:")
            for case, result in listed:
                print(f"  {case}  [{result.stage}]  {result.detail}")

    # there are many of these, so they are summarized by their reason, without
    # the formula or id it quotes and the C++ function it names
    reasons = defaultdict(list)
    for case, result in results:
        if result.outcome in (Outcome.NOT_SIMULATABLE, Outcome.NOT_DETERMINISTIC):
            reason = re.sub(r"'[^']*'", "'...'", result.detail.split(", at ")[0])
            reasons[f"{result.outcome}: {reason}"].append(case)
    if reasons:
        print()
        for reason, cases in sorted(reasons.items(), key=lambda item: -len(item[1])):
            print(f"  {len(cases):>5}  {reason}")
            print(f"         {' '.join(cases)}")


def main() -> None:
    """Run the sweep and print the pass rate."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--limit", type=int, default=0, help="only the first N cases")
    parser.add_argument(
        "--case", action="append", default=[], help="only this case, repeatable"
    )
    parser.add_argument(
        "--jobs", type=int, default=8, help="cases run in parallel (default: 8)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="seconds after which a case is killed (default: 300)",
    )
    args = parser.parse_args()

    cases = SWEEP_CASES
    if args.case:
        cases = [path for path in cases if path.name[:5] in args.case]
    if args.limit:
        cases = cases[: args.limit]

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        results = list(executor.map(lambda path: run_case(path, args.timeout), cases))
    print_report(results, time.perf_counter() - start)


if __name__ == "__main__":
    main()
