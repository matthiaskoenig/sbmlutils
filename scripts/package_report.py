"""Report how much of the fbc, distrib and comp content survives a round trip.

Round trip every document of the package corpus and compare the document read with the document written by `structural_diff` of `tests/structural.py`, then print for every construct in how many cases it occurs and in how many of them it is preserved, for local runs and for tracking progress on https://github.com/matthiaskoenig/sbmlutils/issues/469:

    uv run python scripts/package_report.py
    uv run python scripts/package_report.py --corpus testsuite
    uv run python scripts/package_report.py --case 01132 --case e_coli_core

Simulation and validation are blind to these packages, see the docstring of `tests/structural.py`, so this report is the measure of the package round trip, as `scripts/roundtrip_report.py` is of SBML core.

The corpus is

- `testsuite`: the l3v2 semantic cases of the SBML test suite which declare fbc, comp or distrib, resolved from the checkout,
- `fixtures`: every SBML file of `sbmlutils.resources` which declares one of them, outside the SBML test suite and the biomodels archives, and of the vendored distrib test suite only the l3v2 flavour.

A construct is preserved in a case if the case has it and the round trip reports no difference for it, neither a changed or lost element nor an added one. An element is preserved if the round trip reports no difference for it. A case whose round trip raises preserves nothing, and it is listed with its error.

Every case runs in a python process of its own, as in `scripts/roundtrip_report.py`: a crash in native code ends one case instead of the sweep, and it is reported apart from the round-trip failures. A case is killed after `--timeout` seconds, which can leave its result file truncated; such a case is reported as a failed one and never ends the sweep either. The round-tripped SBML and the result of every case are kept in `.package_tmp/<case>/` for inspection.
"""

import argparse
import gzip
import json
import shutil
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import libsbml

ROOT: Path = Path(__file__).parent.parent

sys.path.insert(0, str(ROOT / "tests"))

from structural import (  # noqa: E402
    PACKAGES,
    diff_snapshots,
    roundtrip_document,
    snapshots,
)

#: the scratch directory, one directory per case
TMP_DIR: Path = ROOT / ".package_tmp"

#: the packaged resources, the fixtures are found in
RESOURCES_DIR: Path = ROOT / "src" / "sbmlutils" / "resources"

#: the file the worker records its stage and its result in
RESULT_FILE: str = "result.json"

#: the namespace of each package, as every version of it starts
_NAMESPACES: tuple[str, ...] = tuple(
    f"http://www.sbml.org/sbml/level3/version1/{package}/version"
    for package in PACKAGES
)


def declares_package(sbml_path: Path) -> bool:
    """Test whether an SBML file declares fbc, distrib or comp.

    Args:
        sbml_path: path of an SBML file, possibly gzipped

    Returns:
        whether the start of the file names the namespace of one of the packages
    """
    if sbml_path.suffix == ".gz":
        with gzip.open(sbml_path, "rt", encoding="utf-8") as f:
            start = f.read(4000)
    else:
        with sbml_path.open(encoding="utf-8") as f:
            start = f.read(4000)
    return any(namespace in start for namespace in _NAMESPACES)


def testsuite_cases(semantic_dir: Path) -> list[tuple[str, Path]]:
    """Get the package cases of the SBML test suite.

    Args:
        semantic_dir: the directory of the semantic cases

    Returns:
        the name and the path of every l3v2 case which declares a package
    """
    return [
        (sbml_path.name[:5], sbml_path)
        for sbml_path in sorted(semantic_dir.glob("*/*-sbml-l3v2.xml"))
        if declares_package(sbml_path)
    ]


def fixtures() -> list[tuple[str, Path]]:
    """Get the package fixtures of the packaged resources.

    Returns:
        the name, the path relative to the resources, and the path of every SBML file which declares a package, see the module docstring
    """
    excluded = ("sbml-test-suite", "biomodels")
    paths = sorted(
        path
        for path in RESOURCES_DIR.rglob("*")
        if path.name.endswith((".xml", ".xml.gz"))
        and not any(part.startswith(excluded) for part in path.parts)
        and not path.name.endswith("-sbml-l3v1.xml")
    )
    return [
        (str(path.relative_to(RESOURCES_DIR)), path)
        for path in paths
        if declares_package(path)
    ]


def _write_result(case_dir: Path, result: dict[str, object]) -> None:
    """Record the stage and the result of a case, in the worker."""
    (case_dir / RESULT_FILE).write_text(json.dumps(result), encoding="utf-8")


def run_worker(sbml_path: Path, case_dir: Path) -> None:
    """Round trip a case and record what it preserves, in the worker process.

    The stage is recorded before it starts, so that the stage a process was killed in is known. The documents are held until the comparison is done, since libsbml objects do not keep their document alive. The census of what the case has is the snapshot of the document read and is recorded before the round trip runs, so `snapshots` is called twice rather than `structural_diff` once; the comparison policy stays where it belongs either way.

    Args:
        sbml_path: path of the SBML file to round trip
        case_dir: directory the round-tripped SBML and the result are written to
    """
    result: dict[str, object] = {"stage": "read the original", "error": None}
    _write_result(case_dir, result)
    doc_in: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    # the source against itself: the census of what the case has, taken before
    # the round trip runs, so that a case the round trip kills still counts the
    # constructs it has
    before, _ = snapshots(doc_in, doc_in)
    present: dict[str, list[str]] = defaultdict(list)
    for construct, element_id in before:
        present[construct].append(element_id)
    result["present"] = present

    result["stage"] = "round trip"
    _write_result(case_dir, result)
    try:
        _, doc_out = roundtrip_document(sbml_path, case_dir)
        result["stage"] = "compare"
        _write_result(case_dir, result)
        _, after = snapshots(doc_in, doc_out)
    except Exception as err:
        lines = [line for line in str(err).splitlines() if line.strip()]
        result["error"] = f"{type(err).__name__}: {(lines or [''])[0][:200]}"
        result["traceback"] = traceback.format_exc()
        _write_result(case_dir, result)
        return

    differing: dict[str, set[str]] = defaultdict(set)
    added: dict[str, set[str]] = defaultdict(set)
    for difference in diff_snapshots(before, after):
        key = (difference.construct, difference.element_id)
        target = differing if key in before else added
        target[difference.construct].add(difference.element_id)
    result["differing"] = {c: sorted(ids) for c, ids in differing.items()}
    result["added"] = {c: sorted(ids) for c, ids in added.items()}
    result["stage"] = "done"
    _write_result(case_dir, result)


@dataclass
class CaseResult:
    """The result of a case which ran in a process of its own.

    Attributes:
        name: the name of the case
        outcome: `compared`, `round trip failed`, `crashed in native code`, `timed out` or `worker error`
        stage: the stage the case was in when it ended
        detail: the error of a failure, the signal of a crash
        present: the element ids of every construct of the document read
        differing: the element ids of every construct which differ or are lost
        added: the element ids of every construct which only the document written has
    """

    name: str
    outcome: str
    stage: str
    detail: str
    present: dict[str, list[str]] = field(default_factory=dict)
    differing: dict[str, list[str]] = field(default_factory=dict)
    added: dict[str, list[str]] = field(default_factory=dict)


def read_result(result_path: Path) -> tuple[dict[str, object], str]:
    """Read what a worker recorded about its case.

    A worker killed by the timeout or by a native crash can leave a truncated file behind. That must end its case and not the sweep, which is what running every case in a process of its own is for, so an unreadable result is reported as the failure of that case.

    Args:
        result_path: path of the result file of the case

    Returns:
        what the worker recorded, empty if nothing readable is there, and why it could not be read, empty if it could
    """
    if not result_path.exists():
        return {}, ""
    try:
        recorded: object = json.loads(result_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        return {}, f"{RESULT_FILE} unreadable: {type(err).__name__}"
    if not isinstance(recorded, dict):
        return {}, f"{RESULT_FILE} holds {type(recorded).__name__}, not an object"
    return recorded, ""


def run_case(
    name: str, sbml_path: Path, timeout: float, crash: Callable[[int], str | None]
) -> CaseResult:
    """Round trip a case in a python process of its own.

    Args:
        name: the name of the case
        sbml_path: path of the SBML file of the case
        timeout: seconds after which the process is killed
        crash: names the crash a return code stands for, `None` if it stands for none, see `test_roundtrip._crash`

    Returns:
        the result of the case
    """
    case_dir = TMP_DIR / name.replace("/", "__")
    shutil.rmtree(case_dir, ignore_errors=True)
    case_dir.mkdir(parents=True)
    try:
        process = subprocess.run(
            [sys.executable, __file__, "--worker", str(sbml_path), str(case_dir)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        process = None

    recorded, unreadable = read_result(case_dir / RESULT_FILE)
    stage = str(recorded.get("stage", "start the worker"))
    present = recorded.get("present", {})
    if not isinstance(present, dict):
        present = {}
    if process is None:
        detail = f"after {timeout:.0f} s"
        return CaseResult(
            name,
            "timed out",
            stage,
            f"{detail}, {unreadable}" if unreadable else detail,
            present,
        )
    signal = crash(process.returncode)
    if signal is not None:
        return CaseResult(name, "crashed in native code", stage, signal, present)
    if recorded.get("error"):
        return CaseResult(
            name, "round trip failed", stage, str(recorded["error"]), present
        )
    if stage != "done" or unreadable:
        stderr = process.stderr.strip().splitlines()
        detail = f"exit code {process.returncode}: {stderr[-1] if stderr else ''}"
        return CaseResult(
            name,
            "worker error",
            stage,
            f"{unreadable}, {detail}" if unreadable else detail,
            present,
        )
    differing = recorded.get("differing", {})
    added = recorded.get("added", {})
    if not isinstance(differing, dict) or not isinstance(added, dict):
        return CaseResult(
            name, "worker error", stage, f"{RESULT_FILE} is incomplete", present
        )
    return CaseResult(name, "compared", stage, "", present, differing, added)


@dataclass
class ConstructRow:
    """The preservation of one construct over the corpus.

    Attributes:
        cases: the cases which have the construct
        cases_preserved: the cases which have it and preserve it completely
        elements: the elements of the construct in all cases
        elements_preserved: the elements for which no difference is reported
        cases_added: the cases in which the round trip adds elements of it
    """

    cases: int = 0
    cases_preserved: int = 0
    elements: int = 0
    elements_preserved: int = 0
    cases_added: int = 0


def construct_table(results: list[CaseResult]) -> dict[str, ConstructRow]:
    """Count for every construct how often it occurs and is preserved.

    Args:
        results: the result of every case

    Returns:
        the row of every construct, sorted by construct
    """
    rows: dict[str, ConstructRow] = defaultdict(ConstructRow)
    for result in results:
        compared = result.outcome == "compared"
        for construct, element_ids in result.present.items():
            row = rows[construct]
            row.cases += 1
            row.elements += len(element_ids)
            if not compared:
                continue
            differing = set(result.differing.get(construct, []))
            row.elements_preserved += len(set(element_ids) - differing)
            if not differing and construct not in result.added:
                row.cases_preserved += 1
        for construct in result.added:
            rows[construct].cases_added += 1
    return dict(sorted(rows.items()))


def print_report(results: list[CaseResult], seconds: float) -> None:
    """Print the construct table and the cases which did not compare.

    Args:
        results: the result of every case
        seconds: the wall time of the sweep
    """
    outcomes: dict[str, list[CaseResult]] = defaultdict(list)
    for result in results:
        outcomes[result.outcome].append(result)
    print(f"cases          : {len(results)} in {seconds:.0f} s")
    for outcome, listed in outcomes.items():
        print(f"  {len(listed):>5}  {outcome}")

    header = (
        f"\n{'construct':<46} {'cases':>6} {'preserved':>10}"
        f" {'elements':>9} {'preserved':>10} {'added in':>9}"
    )
    print(header)
    print("-" * (len(header) - 1))
    for construct, row in construct_table(results).items():
        print(
            f"{construct:<46} {row.cases:>6} {row.cases_preserved:>10}"
            f" {row.elements:>9} {row.elements_preserved:>10} {row.cases_added:>9}"
        )

    for outcome, listed in outcomes.items():
        if outcome == "compared":
            continue
        print(f"\n{outcome}:")
        for result in listed:
            print(f"  {result.name}  [{result.stage}]  {result.detail}")


def main() -> None:
    """Run the sweep and print the report."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--corpus",
        choices=["all", "testsuite", "fixtures"],
        default="all",
        help="the part of the corpus to sweep (default: all)",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="only the cases whose name contains this, repeatable",
    )
    parser.add_argument(
        "--jobs", type=int, default=8, help="cases run in parallel (default: 8)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="seconds after which a case is killed (default: 600)",
    )
    parser.add_argument(
        "--worker", nargs=2, metavar=("SBML", "CASE_DIR"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    if args.worker:
        run_worker(Path(args.worker[0]), Path(args.worker[1]))
        return

    # the test module imports roadrunner, which the worker does not need
    from test_roundtrip import SEMANTIC_DIR, _crash

    corpus: list[tuple[str, Path]] = []
    if args.corpus in ("all", "testsuite"):
        corpus += testsuite_cases(SEMANTIC_DIR)
    if args.corpus in ("all", "fixtures"):
        corpus += fixtures()
    if args.case:
        corpus = [(n, p) for n, p in corpus if any(c in n for c in args.case)]

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        results = list(
            executor.map(lambda case: run_case(*case, args.timeout, _crash), corpus)
        )
    print_report(results, time.perf_counter() - start)


if __name__ == "__main__":
    main()
