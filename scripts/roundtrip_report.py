"""Report the round-trip simulation pass rate over the SBML test suite.

Run the full sweep and print a summary, for local runs and for tracking
progress on https://github.com/matthiaskoenig/sbmlutils/issues/469:

    uv run python scripts/roundtrip_report.py
    uv run python scripts/roundtrip_report.py --limit 200
"""

import argparse
import contextlib
import io
import logging
import sys
from collections import Counter
from pathlib import Path

logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from test_roundtrip import (  # noqa: E402
    SEMANTIC_DIR,
    _simulate,
    assert_roundtrip_simulates_equal,
)


def main() -> None:
    """Run the sweep and print the pass rate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="only the first N cases")
    args = parser.parse_args()

    cases = sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml"))
    if args.limit:
        cases = cases[: args.limit]

    tmp_path = Path(__file__).parent.parent / ".roundtrip_tmp"
    tmp_path.mkdir(exist_ok=True)

    outcome: Counter = Counter()
    failures: list[str] = []
    for sbml_path in cases:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _simulate(sbml_path)
        except Exception:
            outcome["skipped, the original does not simulate"] += 1
            continue
        try:
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                assert_roundtrip_simulates_equal(sbml_path, tmp_path)
            outcome["passed"] += 1
        except Exception as err:
            outcome["failed"] += 1
            failures.append(f"{sbml_path.name}: {type(err).__name__}")

    comparable = outcome["passed"] + outcome["failed"]
    print(f"cases          : {len(cases)}")
    for key, value in outcome.most_common():
        print(f"  {value:>5}  {key}")
    if comparable:
        rate = 100.0 * outcome["passed"] / comparable
        print(f"\npass rate      : {outcome['passed']}/{comparable} = {rate:.1f}%")
    print("\nfirst failures:")
    for failure in failures[:30]:
        print(f"  {failure}")


if __name__ == "__main__":
    main()
