"""Measure imports, validation and reporting in fresh processes.

Run ``python scripts/performance_report.py --size 10000`` from an installed
checkout. Output is JSON; Unix peak RSS includes native library allocations.
Timing thresholds are deliberately left to the calling benchmark environment.
"""

import argparse
import importlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

CASES = (
    "import_io",
    "import_factory",
    "validate_full",
    "validate_fast",
    "report_full",
    "report_light",
    "report_unnamed",
)


def peak_memory_mib() -> float | None:
    """Read peak process RSS, including native allocations, where available."""
    try:
        import resource
    except ImportError:
        return None
    divisor = 1024**2 if sys.platform == "darwin" else 1024
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divisor


def measure(case: str, size: int) -> dict[str, object]:
    """Measure one workflow after preparing its synthetic model."""
    logging.disable(logging.CRITICAL)
    if case.startswith("import_"):
        module = "sbmlutils.io.sbml" if case == "import_io" else "sbmlutils.factory"
        started = time.perf_counter()
        importlib.import_module(module)
        return {
            "case": case,
            "seconds": time.perf_counter() - started,
            "peak_memory_mib": peak_memory_mib(),
        }

    import libsbml

    from sbmlutils.report.sbmlinfo import SBMLDocumentInfo
    from sbmlutils.validation import ValidationOptions, validate_doc

    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("benchmark")
    for k in range(size):
        if case == "report_unnamed":
            model.createConstraint().setMath(libsbml.parseL3Formula("true"))
        else:
            parameter = model.createParameter()
            parameter.setId(f"p{k}")
            parameter.setValue(k)
            parameter.setConstant(True)
            parameter.setUnits("dimensionless")

    before = peak_memory_mib()
    started = time.perf_counter()
    if case.startswith("validate_"):
        options = (
            ValidationOptions.fast(log_errors=False)
            if case == "validate_fast"
            else ValidationOptions(log_errors=False)
        )
        result = validate_doc(doc, options)
        if not result.is_valid():
            raise RuntimeError("The benchmark model did not validate")
    else:
        lightweight = case == "report_light"
        report = SBMLDocumentInfo(
            doc,
            include_derived_units=not lightweight,
            include_xml=not lightweight,
            include_math=not lightweight,
        )
        # Exercise serialization without retaining a complete JSON string.
        with Path(os.devnull).open("w") as stream:
            report.write_json(stream)

    return {
        "case": case,
        "elements": size,
        "seconds": time.perf_counter() - started,
        "before_peak_memory_mib": before,
        "peak_memory_mib": peak_memory_mib(),
    }


def main() -> None:
    """Run each case in a fresh process to isolate imports and peak RSS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=4000)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    if args.size < 1:
        parser.error("--size must be positive")
    if args.case is not None:
        print(json.dumps(measure(args.case, args.size)))
        return
    measurements = []
    for case in CASES:
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--case",
                case,
                "--size",
                str(args.size),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        measurements.append(json.loads(result.stdout))
    print(json.dumps(measurements, indent=2))


if __name__ == "__main__":
    main()
