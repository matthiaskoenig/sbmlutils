"""Test the generated python against roadrunner on the SBML test suite.

Every case is the l3v2 flavour of a semantic case of the vendored test suite, see
`tests/test_roundtrip.py`, simulated to `T_END` at `T_STEPS` time points. A case with
a construct the code does not support (`OdeSystem.unsupported`) must refuse to
render; every other case must simulate as roadrunner: every column of `simulate`
(the states, the assigned values and the constants which events change) against its
roadrunner selection. The tolerances of a case with events are relaxed, an event
time is located to the tolerance of the integration.

`CURATED` runs in the default test run, the full sweep `test_python_sweep` behind
the `sbml_testsuite` marker. A case whose events are not deterministic is skipped
(`NONDETERMINISTIC`), as is a case roadrunner does not simulate, which has no
reference (the fbc cases, an integration which fails); a known failure is a strict
xfail with its reason (`KNOWN_FAILURES`).
"""

from pathlib import Path

import numpy as np
import pytest
from ode_helpers import assert_trajectory_as_roadrunner, python_module
from test_roundtrip import (
    NONDETERMINISTIC,
    SWEEP_CASES,
    T_END,
    T_STEPS,
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

# the cases whose python simulation differs from roadrunner, with the reason
KNOWN_FAILURES: dict[tuple[str, str], str] = {}


def check_python_case(sbml_path: Path, tmp_path: Path) -> None:
    """Check the python code of a case: it refuses to render or simulates right.

    Args:
        sbml_path: path of the SBML file of the case
        tmp_path: directory of the python file
    """
    system = OdeSystem.from_sbml(sbml_path)
    if system.unsupported:
        with pytest.raises(NotImplementedError):
            system.render("python")
        return
    try:
        roadrunner.RoadRunner(str(sbml_path)).simulate(0.0, T_END, T_STEPS)
    except RuntimeError as error:
        # no reference: an fbc model, an integration which fails (01148 grows as
        # the exponential of 1e9 t^2)
        pytest.skip(f"roadrunner does not simulate the case: {error}")
    module = python_module(system, tmp_path / f"case_{sbml_path.name[:5]}.py")
    # an event time is located to the tolerance of the integration
    tolerances = {"rtol": 1e-4, "atol": 1e-6} if system.events else {}
    # math out of its domain is nan or inf as in roadrunner, e.g. case 01488
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        assert_trajectory_as_roadrunner(sbml_path, module, **tolerances)


def _mark(case: str, request: pytest.FixtureRequest) -> None:
    """Skip a nondeterministic case, mark a known failure as a strict xfail."""
    if case in NONDETERMINISTIC:
        pytest.skip(f"the events are not deterministic: {NONDETERMINISTIC[case]}")
    reason = KNOWN_FAILURES.get(("python", case))
    if reason is not None:
        request.applymarker(pytest.mark.xfail(reason=reason, strict=True))


@requires_testsuite
@pytest.mark.parametrize("case", CURATED)
def test_python_curated(
    case: str, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """The python code of a curated case simulates as roadrunner."""
    _mark(case, request)
    check_python_case(suite_case(case), tmp_path)


@requires_testsuite
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_python_sweep(
    sbml_path: Path, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """The python code of every l3v2 case simulates as roadrunner."""
    _mark(sbml_path.name[:5], request)
    check_python_case(sbml_path, tmp_path)


def test_curated_cases_exist() -> None:
    """The curated and the known failing cases are cases of the test suite."""
    swept = {sbml_path.name[:5] for sbml_path in SWEEP_CASES}
    if not swept:
        pytest.skip("the SBML test suite is not vendored")
    assert len(CURATED) == len(set(CURATED))
    assert set(CURATED) <= swept
    assert {case for _, case in KNOWN_FAILURES} <= swept
