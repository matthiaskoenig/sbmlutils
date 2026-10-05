"""Test the julia code of the ODE export against roadrunner.

The julia code is run with `julia_command` (`SBMLUTILS_JULIA`, default `julia`), the
tests which run it skip without julia. The jobs of the tests run in two julia
processes, see `run_julia_jobs`: the jobs of the right hand side (`simulator=False`,
which loads NaNMath and SpecialFunctions only), and the jobs of `simulate`, which
load OrdinaryDiffEq and DataFrames and compile the integrator once for all of them.
"""

import functools
import re
import time
from collections.abc import Callable
from pathlib import Path

import libsbml
import numpy as np
import ode_helpers
import pandas as pd
import pytest
from ode_helpers import (
    EVENT_MODELS,
    FORMULAS,
    JULIA_NAMES_JOB,
    JULIA_POINT_VALUES_JOB,
    TWO_EVENTS,
    Job,
    JobOutput,
    assert_table_as_roadrunner,
    assert_values_as_roadrunner,
    edit_sbml,
    julia_command,
    julia_simulate_job,
    model_sbml,
    run_julia_jobs,
    sbml_with_rate,
    toolchain_missing,
)

import sbmlutils
from sbmlutils.converters.ode import FORMATS, OdeSystem
from sbmlutils.converters.ode.formats import context
from sbmlutils.converters.ode.symbols import RESERVED, code_names
from sbmlutils.resources import (
    COMP_DEX_LIVER,
    COMP_SPT_LIVER,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    MODELS_DIR,
    REPRESSILATOR_SBML,
    VDP_SBML,
)

INTERPOLATION_LINEAR_SBML = MODELS_DIR / "interpolation" / "data1_linear.xml"

# the models of the python tests, see `test_ode_python.py`
MODELS: list[Path] = [
    DEMO_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
    COMP_DEX_LIVER,
    COMP_SPT_LIVER,
    INTERPOLATION_LINEAR_SBML,
    GALACTOSE_SINGLECELL_SBML,
]

# a model with function definitions, assignment rules, an initial assignment of a
# constant and a species in a variable compartment, held as its amount
RULES = """
    function mm(S, km)
        S / (km + S)
    end
    function hill(S, k, n)
        S^n / (k^n + S^n)
    end
    compartment c = 2; c' = 0.1
    species A in c = 3; species B in c = 1
    vmax = 2; km = 0.5; scale = 1.5
    total := A + B
    ratio := A / total
    keff = 2 * vmax
    J1: A -> B; keff * mm(A, km) * c
    J2: B -> ; vmax * hill(B, 1, 2)
"""

# models of the right hand side, by the name of their job, as SBML or a path
POINT_MODELS: dict[str, str | Path] = {
    **{f"formula_{k}": sbml_with_rate(f) for k, f in enumerate(FORMULAS)},
    **{f"model_{path.stem}": path for path in MODELS},
    "rules": model_sbml(RULES),
    "stateless": model_sbml("k = 2; y := k * time; z := y^2"),
    # ids which are julia keywords, names of the code or write-only
    "reserved": model_sbml("""
        compartment c = 1
        species begin in c = 2; species p in c = 1
        let = 0.5; t_ = 2; XIDS = 1; f_y = 3; initial_values = 0.1; _ = 2
        ccall = 1; cglobal = 2; eval = 3; include = 4
        R1: begin -> p; let * begin * t_ * XIDS * _
        R2: p -> ; initial_values * f_y * p * ccall * cglobal * eval * include
    """),
    # math of the time out of its domain is inf, not an error (case 01488)
    "time_domain": model_sbml("""
        function f(a)
            piecewise(0, a > 1e300, a)
        end
        y := f(1 / time)
    """),
}

# the further jobs of the right hand side
POINT_JOBS: dict[str, Callable[[], Job]] = {
    "negative_base": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("""
                compartment c = 1; species A in c = -1
                y := A^0.5 + root(3, A)
                R1: A -> ; k * A^1.5
                k = 1
            """)
        ).render("julia", simulator=False),
        """
        x0, p = m.initial_values()
        dx = zeros(1)
        m.f!(dx, x0, p, 0.0)
        emit(io, "dx", dx)
        emit(io, "y", m.f_y(x0, p, 0.0))
        """,
    ),
    "initial_values_take_constants": lambda: Job(
        OdeSystem.from_sbml(model_sbml(RULES)).render("julia", simulator=False),
        """
        p = copy(m.P0)
        p[findfirst(==("vmax"), m.PIDS)] = 10.0
        passed = copy(p)
        x0, p_new = m.initial_values(p)
        emit(io, "p_new", p_new)
        emit(io, "unchanged", [isequal(p, passed)])
        emit(io, "x0", x0)
        emit(io, "x0_default", m.initial_values()[1])
        """,
    ),
    "events_without_simulator": lambda: Job(
        OdeSystem.from_sbml(model_sbml(TWO_EVENTS)).render("julia", simulator=False),
        """
        x, p = m.initial_values()
        emit(io, "ids", [event.id for event in m.EVENTS])
        emit(io, "triggers", m.event_triggers(x, p, 0.0))
        emit(io, "conditions", m.event_conditions(x, p, 0.0))
        event = m.EVENTS[1]
        emit(io, "delay", [event.delay(x, p, 0.0)])
        emit(io, "priority", [event.priority(x, p, 0.0)])
        x_new, p_new = event.assign(x, p, 0.0, event.values(x, p, 0.0))
        emit(io, "x_new", x_new)
        emit(io, "p_new", p_new)
        emit(io, "x", x)
        emit(io, "simulate", [isdefined(m, :simulate)])
        """,
    ),
}

# the jobs of `simulate`, the models of the event tests of the python code included
SIMULATE_JOBS: dict[str, Callable[[], Job]] = {
    "repressilator": lambda: Job(
        OdeSystem.from_sbml(REPRESSILATOR_SBML).render("julia"), julia_simulate_job()
    ),
    **{
        f"events_{name}": functools.partial(
            lambda antimony: Job(
                OdeSystem.from_sbml(model_sbml(antimony)).render("julia"),
                julia_simulate_job(),
            ),
            antimony,
        )
        for name, antimony in EVENT_MODELS.items()
        if name != "infinite_cascade"
    },
    "stateless": lambda: Job(
        OdeSystem.from_sbml(model_sbml("k = 2; y := k * time; z := y^2")).render(
            "julia"
        ),
        julia_simulate_job(4.0, 5),
    ),
    "x0_and_p": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species A = 2; R1: A -> ; k * A; k = 1")
        ).render("julia"),
        """
        p = copy(m.P0)
        p[findfirst(==("k"), m.PIDS)] = 2.0
        emit_table(io, m.simulate(1.0; points=3, p, x0=[4.0]))
        """,
    ),
    "max_steps": lambda: Job(
        OdeSystem.from_sbml(VDP_SBML).render("julia"),
        """
        emit(io, "MAX_STEPS", [m.MAX_STEPS])
        try
            quietly(() -> m.simulate(10.0; max_steps=5))
        catch error
            emit(io, "error", [sprint(showerror, error)])
        end
        """,
    ),
    "many_points": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species S = 1; R1: S -> ; k * S; k = 1")
        ).render("julia"),
        """
        df = m.simulate(10.0; points=m.MAX_STEPS + 2)
        emit(io, "S", [df[end, "S"], size(df, 1)])
        """,
    ),
    "window_dtmax": lambda: Job(
        OdeSystem.from_sbml(model_sbml(EVENT_MODELS["window"])).render("julia"),
        """
        emit(io, "B", [m.simulate(4.0; points=21)[end, "B"]])
        emit(io, "B_dtmax", [m.simulate(4.0; points=21, dtmax=1.0)[end, "B"]])
        emit(io, "TRIGGER_POINTS", [m.TRIGGER_POINTS])
        """,
    ),
    "infinite_cascade": lambda: Job(
        OdeSystem.from_sbml(model_sbml(EVENT_MODELS["infinite_cascade"])).render(
            "julia"
        ),
        """
        emit(io, "MAX_CASCADE", [m.MAX_CASCADE])
        try
            quietly(() -> m.simulate(2.0))
        catch error
            emit(io, "error", [sprint(showerror, error)])
        end
        """,
    ),
    **{
        f"pole{k}": functools.partial(
            lambda event: Job(
                OdeSystem.from_sbml(model_sbml(f"x = 1; x' = x^2{event}")).render(
                    "julia"
                ),
                """
                try
                    quietly(() -> m.simulate(2.0))
                catch error
                    emit(io, "error", [sprint(showerror, error)])
                end
                """,
            ),
            event,
        )
        for k, event in enumerate(["", "; E1: at time > 5: x = 2"])
    },
    **{
        f"without_time_{name}": functools.partial(
            lambda antimony: Job(
                OdeSystem.from_sbml(model_sbml(antimony)).render("julia"),
                """
                x0, _ = m.initial_values()
                emit(io, "x0", x0)
                df = m.simulate(0.0)
                emit(io, "rows", [size(df, 1)])
                emit(io, "times", df[!, "time"])
                emit(io, "states", vec(Matrix(df[!, m.XIDS])))
                single = m.simulate(5.0; points=1)
                emit(io, "single_times", single[!, "time"])
                emit(io, "single_states", vec(Matrix(single[!, m.XIDS])))
                """,
            ),
            antimony,
        )
        for name, antimony in [
            ("events", EVENT_MODELS["rounding"]),
            ("states", "S = 1; S' = -S"),
        ]
    },
    # a constant rate and a first step which the end of the integration shortens,
    # which OrdinaryDiffEq 7 interpolates with its full length
    "first_step": lambda: Job(
        OdeSystem.from_sbml(model_sbml("species S = 1; R1: -> S; k; k = 1")).render(
            "julia"
        ),
        julia_simulate_job(0.18, 3, "dtmax=1.0"),
    ),
    "reserved_simulate": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species A = 1; R1: A -> ; simulate * A; simulate = 1")
        ).render("julia"),
        julia_simulate_job(1.0, 2),
    ),
}

# the names of every rendering of the parse test, see `test_julia_names_are_reserved`
PARSED: dict[str, tuple[str, bool]] = {
    "rules": (RULES, True),
    "rules_rhs": (RULES, False),
    "events": (TWO_EVENTS, True),
    "events_rhs": (TWO_EVENTS, False),
    "stateless_events": (EVENT_MODELS["without_states"], True),
}


def _code(antimony: str, **options: object) -> str:
    """The julia code of a model written in antimony."""
    return OdeSystem.from_sbml(model_sbml(antimony)).render("julia", **options)


def _point_jobs() -> dict[str, Job]:
    """The jobs of the right hand side."""
    jobs = {
        name: Job(
            OdeSystem.from_sbml(sbml).render("julia", simulator=False),
            JULIA_POINT_VALUES_JOB,
        )
        for name, sbml in POINT_MODELS.items()
    }
    jobs.update({name: job() for name, job in POINT_JOBS.items()})
    for name, (antimony, simulator) in PARSED.items():
        jobs[f"parse_{name}"] = Job(
            _code(antimony, simulator=simulator),
            JULIA_NAMES_JOB,
        )
    return jobs


@pytest.fixture(scope="module")
def julia(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str], JobOutput]:
    """The output of a job of the module, by its name.

    The jobs of the right hand side and the jobs of `simulate` run in a julia
    process each, on the first request of one of their jobs.
    """
    if julia_command() is None:
        toolchain_missing("julia", "SBMLUTILS_JULIA")
    outputs: dict[str, JobOutput] = {}

    def output(name: str) -> JobOutput:
        if name not in outputs:
            if name in SIMULATE_JOBS:
                jobs = {n: job() for n, job in SIMULATE_JOBS.items()}
                directory = tmp_path_factory.mktemp("julia_simulate")
            else:
                jobs = _point_jobs()
                directory = tmp_path_factory.mktemp("julia_points")
            for job_name, job in jobs.items():
                path = (directory / f"{job_name}.jl").absolute()
                jobs[job_name] = Job(job.code, job.run.replace("{path}", str(path)))
            outputs.update(run_julia_jobs(jobs, directory))
        return outputs[name]

    return output


# --- correctness against roadrunner ---------------------------------------------------


@pytest.mark.parametrize("name", list(POINT_MODELS))
def test_julia_as_roadrunner(name: str, julia: Callable[[str], JobOutput]) -> None:
    """The julia of a model computes the values of roadrunner.

    The formulas cover every construct of the math, the models of the python tests
    every construct of a model, initial assignments (#438) included.
    """
    assert_values_as_roadrunner(POINT_MODELS[name], julia(name).point_values())


def test_julia_rules_and_functions(julia: Callable[[str], JobOutput]) -> None:
    """Function definitions, rules, an initial assignment and an amount state."""
    values = julia("rules").point_values()
    assert values.xids == ["c", "n_A", "n_B"]
    assert values.p[values.pids.index("keff")] == 4.0
    assert values.x0[values.xids.index("n_A")] == pytest.approx(6.0)


def test_julia_reserved_ids(julia: Callable[[str], JobOutput]) -> None:
    """Ids which are julia keywords, names of the code or `_` are renamed and run."""
    values = julia("reserved").point_values()
    assert values.xids == ["begin", "p"]
    assert {"let", "t_", "XIDS", "f_y", "initial_values", "_"} <= set(values.pids)
    assert {"ccall", "cglobal", "eval", "include"} <= set(values.pids)


def test_julia_time_out_of_its_domain(julia: Callable[[str], JobOutput]) -> None:
    """Math of the time out of its domain is `Inf`, not an error (case 01488)."""
    assert julia("time_domain").floats("y0").tolist() == [0.0]


def test_julia_negative_base_with_fractional_exponent_is_nan(
    julia: Callable[[str], JobOutput],
) -> None:
    """A power of a negative state with a fractional exponent is NaN, no error."""
    output = julia("negative_base")
    assert np.isnan(output.floats("dx")).all()
    assert np.isnan(output.floats("y")).all()


def test_julia_initial_values_take_constants(
    julia: Callable[[str], JobOutput],
) -> None:
    """`initial_values` evaluates the initial values with the constants passed."""
    output = julia("initial_values_take_constants")
    pids = julia("rules").strings("PIDS")
    assert output.floats("p_new")[pids.index("keff")] == 20.0
    # the constants passed are not changed
    assert output.strings("unchanged") == ["true"]
    assert output.floats("x0").tolist() == julia("rules").floats("x0").tolist()


def test_julia_simulate_matches_roadrunner(
    julia: Callable[[str], JobOutput],
) -> None:
    """The simulator integrates the repressilator as roadrunner."""
    system = OdeSystem.from_sbml(REPRESSILATOR_SBML)
    df = julia("repressilator").table()
    assert list(df.columns) == ["time", *system.states, *system.assigned]
    assert_table_as_roadrunner(REPRESSILATOR_SBML, df)


def test_julia_simulate_from_x0_and_p(julia: Callable[[str], JobOutput]) -> None:
    """The simulator starts from the states and the constants passed."""
    df = julia("x0_and_p").table()
    assert list(df.columns) == ["time", "A", "R1"]
    assert df["A"].tolist() == pytest.approx(4.0 * np.exp(-2.0 * df["time"]), rel=1e-6)


def test_julia_model_without_states(julia: Callable[[str], JobOutput]) -> None:
    """A model of assignment rules only has no states and simulates."""
    df = julia("stateless").table()
    assert list(df.columns) == ["time", "y", "z"]
    assert df["z"].tolist() == pytest.approx([0.0, 4.0, 16.0, 36.0, 64.0])


def test_julia_reserved_id_simulate(julia: Callable[[str], JobOutput]) -> None:
    """An id `simulate` is renamed, the simulator runs."""
    df = julia("reserved_simulate").table()
    assert df["A"].tolist() == pytest.approx([1.0, np.exp(-1.0)], rel=1e-6)


def test_julia_simulate_max_steps(julia: Callable[[str], JobOutput]) -> None:
    """More steps of the integrator than `max_steps` throw an error."""
    output = julia("max_steps")
    assert output.floats("MAX_STEPS").tolist() == [100000]
    assert "more than 5 steps" in output.strings("error")[0]


def test_julia_simulate_max_steps_scale_with_the_points(
    julia: Callable[[str], JobOutput],
) -> None:
    """The default limit of the steps grows with the steps the time points force."""
    value, rows = julia("many_points").floats("S")
    assert rows == 100002
    assert value == pytest.approx(np.exp(-10.0), rel=1e-6)


@pytest.mark.parametrize("name", ["events", "states"])
def test_julia_simulate_without_time(
    name: str, julia: Callable[[str], JobOutput]
) -> None:
    """`simulate(0)` is the initial state at each time point, one point is t = 0."""
    output = julia(f"without_time_{name}")
    x0 = output.floats("x0").tolist()
    assert output.floats("rows").tolist() == [101]
    assert output.floats("times").tolist() == [0.0] * 101
    # the matrix of the states column by column
    assert output.floats("states").tolist() == [v for v in x0 for _ in range(101)]
    assert output.floats("single_times").tolist() == [0.0]
    assert output.floats("single_states").tolist() == x0


def test_julia_simulate_first_step(julia: Callable[[str], JobOutput]) -> None:
    """A first step which the end of the integration shortens is interpolated right.

    OrdinaryDiffEq 7 interpolates such a step with its full length, the largest step
    is capped at the end of the integration.
    """
    df = julia("first_step").table()
    assert df["S"].tolist() == pytest.approx([1.0, 1.09, 1.18], rel=1e-12)


@pytest.mark.parametrize("name", ["pole0", "pole1"])
def test_julia_simulate_raises_for_a_state_without_bound(
    name: str, julia: Callable[[str], JobOutput]
) -> None:
    """A state which grows without bound throws, it does not integrate for ever.

    `x' = x^2` with `x(0) = 1` is `1 / (1 - t)`, which has a pole at t = 1.
    """
    assert "The integration failed at t = 1.0" in julia(name).strings("error")[0]


# --- events ---------------------------------------------------------------------------
# The trajectories of models with events are compared with the relaxed tolerances of
# the test suite sweep: an event time is located to the tolerance of the integration,
# which shifts the values after it.

EVENT_RTOL = 1e-4
EVENT_ATOL = 1e-6


def _events_as_roadrunner(name: str, julia: Callable[[str], JobOutput]) -> pd.DataFrame:
    """Assert that a model of `EVENT_MODELS` simulates as roadrunner.

    Returns:
        the simulation of the julia code
    """
    df = julia(f"events_{name}").table()
    assert_table_as_roadrunner(
        model_sbml(EVENT_MODELS[name]), df, rtol=EVENT_RTOL, atol=EVENT_ATOL
    )
    return df


@pytest.mark.parametrize(
    "name", [name for name in EVENT_MODELS if name != "infinite_cascade"]
)
def test_julia_events_as_roadrunner(
    name: str, julia: Callable[[str], JobOutput]
) -> None:
    """The julia of every event model of the python tests simulates as roadrunner."""
    _events_as_roadrunner(name, julia)


def test_julia_two_events(julia: Callable[[str], JobOutput]) -> None:
    """The table has the constants which events change."""
    df = _events_as_roadrunner("two_events", julia)
    assert list(df.columns) == ["time", "S", "R1", "k", "total"]
    assert df["k"].iloc[-1] == 1.0


@pytest.mark.parametrize(("relation", "before"), [(">=", False), (">", True)])
def test_julia_event_at_a_time_point(
    relation: str, before: bool, julia: Callable[[str], JobOutput]
) -> None:
    """At a time point of the output the values are those after its events."""
    df = _events_as_roadrunner(f"at_time_point[{relation}]", julia)
    row = df[np.isclose(df["time"], 2.0)].iloc[0]
    assert row["A"] == pytest.approx(2.0 if before else 10.0)


def test_julia_event_at_a_time_point_to_the_rounding(
    julia: Callable[[str], JobOutput],
) -> None:
    """An event at a time point to the rounding of the integration is at it.

    The integration finds `A <= 1.88` about 1e-14 after t = 2.4 (as in case 01675);
    the execution at 3.4 is at the time point 3.4 nevertheless.
    """
    df = _events_as_roadrunner("rounding", julia)
    assert df[np.isclose(df["time"], 3.4)]["B"].iloc[0] == 1.0


@pytest.mark.parametrize("relation", [">=", ">"])
def test_julia_event_at_t0(relation: str, julia: Callable[[str], JobOutput]) -> None:
    """A trigger which holds at t = 0 fires there if its initial value is false."""
    df = _events_as_roadrunner(f"at_t0[{relation}]", julia)
    fired = 1.0 if relation == ">=" else 0.0
    assert df["B"].iloc[0] == fired
    assert df["C"].iloc[-1] == 1.0 - fired
    assert df["D"].iloc[-1] == 3.0


def test_julia_event_priority(julia: Callable[[str], JobOutput]) -> None:
    """Events at the same time execute in the order of their priorities."""
    df = _events_as_roadrunner("priority", julia)
    assert df[np.isclose(df["time"], 2.0)]["B"].iloc[0] == 4.0
    assert df["B"].iloc[-1] == 17.0


def test_julia_event_delay(julia: Callable[[str], JobOutput]) -> None:
    """A delayed event executes after its delay, each time its trigger turns true."""
    df = _events_as_roadrunner("delay", julia)
    assert df["n"].iloc[-1] == 4.0
    assert df["S"].iloc[-1] == pytest.approx(4.831581402482879, rel=1e-6)


def test_julia_event_persistent(julia: Callable[[str], JobOutput]) -> None:
    """An event which is not persistent is dropped if its trigger turns false."""
    df = _events_as_roadrunner("persistent", julia)
    assert df["B"].iloc[-1] == 0.0
    assert df["C"].iloc[-1] == 1.0
    assert df["F"].iloc[-1] == 1.0


def test_julia_event_assigns_its_threshold(
    julia: Callable[[str], JobOutput],
) -> None:
    """An event which sets its trigger to the root keeps integrating."""
    df = _events_as_roadrunner("threshold", julia)
    assert df["A"].between(1.0, 2.0).all()
    assert df["A"].iloc[-1] == pytest.approx(1.5)


def test_julia_event_model_without_states(
    julia: Callable[[str], JobOutput],
) -> None:
    """A model of events and rules only integrates nothing but its events."""
    df = _events_as_roadrunner("without_states", julia)
    assert list(df.columns) == ["time", "y", "B"]
    assert df["B"].iloc[-1] == 5.0


def test_julia_event_window_and_dtmax(julia: Callable[[str], JobOutput]) -> None:
    """A trigger which holds for half a time unit is found with the steps of `dtmax`.

    The integrator ends a step at each root of the root functions it finds, which it
    evaluates at `TRIGGER_POINTS` points of each step, with `dtmax=1` as well.
    """
    output = julia("window_dtmax")
    assert output.floats("TRIGGER_POINTS").tolist() == [10]
    assert output.floats("B").tolist() == [1.0]
    assert output.floats("B_dtmax").tolist() == [1.0]


def test_julia_event_infinite_cascade_raises(
    julia: Callable[[str], JobOutput],
) -> None:
    """Events which trigger each other at one time without end throw an error."""
    output = julia("infinite_cascade")
    assert output.floats("MAX_CASCADE").tolist() == [10000]
    assert "infinite cascade" in output.strings("error")[0]


def test_julia_events_without_simulator(julia: Callable[[str], JobOutput]) -> None:
    """`simulator=False` writes the functions of the events for a solver of one's own."""
    code = _code(TWO_EVENTS, simulator=False)
    assert "OrdinaryDiffEq" not in code
    assert "DataFrame" not in code
    output = julia("events_without_simulator")
    assert output.strings("ids") == ["E1", "E2"]
    assert output.floats("triggers").tolist() == [-5.0, -3.0]
    assert output.strings("conditions") == ["false", "false"]
    assert output.floats("delay").tolist() == [1.0]
    assert output.floats("priority").tolist() == [2.0]
    assert output.floats("x_new").tolist() == [15.0]
    assert output.floats("p_new").tolist() == [1.0, 0.5, 1.0]
    # the states passed are not changed
    assert output.floats("x").tolist() == [10.0]
    assert output.strings("simulate") == ["false"]


# --- shape of the code ----------------------------------------------------------------


@pytest.mark.parametrize("name", list(PARSED))
def test_julia_names_are_reserved(name: str, julia: Callable[[str], JobOutput]) -> None:
    """Every name the template writes, not an id of the model, is reserved.

    julia parses the code and lists its names; the names of fields, keyword
    arguments and of the entries of named tuples never clash with a variable.
    """
    antimony, simulator = PARSED[name]
    system = OdeSystem.from_sbml(model_sbml(antimony))
    ids = [q.symbol.sid for q in system.quantities]
    ids += [r.symbol.sid for r in system.reactions]
    ids += [f.symbol.sid for f in system.functions]
    ids += [e.symbol.sid for e in system.events]
    model_names = set(code_names(ids, "julia").values())
    data = context(system, FORMATS["julia"], {"simulator": simulator})
    events = data["events"]
    assert isinstance(events, list)
    model_names |= {f for e in events for f in e["functions"].values() if f}
    model = data["model"]
    assert isinstance(model, dict)
    model_names.add(str(model["module"]))
    written = {
        n for n in julia(f"parse_{name}").strings("names") if re.fullmatch(r"\w+", n)
    }
    written = {n for n in written if n.strip("_")}
    # the arguments of the function definitions
    arguments = {"S", "km", "k", "n"}
    assert written - model_names - arguments <= RESERVED["julia"]


def test_julia_layout() -> None:
    """The code reads as the model: named locals with their name and unit."""
    code = OdeSystem.from_sbml(REPRESSILATOR_SBML).render("julia")
    lines = code.splitlines()
    assert lines[0] == '"""'
    assert f"sbmlutils {sbmlutils.__version__}" in code
    assert "BIOMD0000000012_urn.xml" in code
    assert "module BIOMD0000000012" in lines
    assert lines[-1] == "end  # module BIOMD0000000012"
    # the states are unpacked one per line, with name and unit
    assert any(line.strip().startswith("PX = x[1]  # ") for line in lines)
    assert "    dx[1] = " in code
    # no trailing whitespace, no tabs, one newline at the end, no long lines
    assert not [line for line in lines if line != line.rstrip()]
    assert "\t" not in code
    assert code.endswith("\n")
    assert not code.endswith("\n\n")
    assert "\n\n\n" not in code
    assert not [line for line in lines if len(line) > 92 and "#" not in line]


def test_julia_imports() -> None:
    """The code imports only what it uses."""
    rhs = _code("species A = 1; R1: A -> ; k * A; k = 1", simulator=False)
    assert "using" not in rhs
    assert "import" not in rhs
    code = _code("species A = 1; R1: A -> ; factorial(A) * sqrt(A)", simulator=False)
    assert "using SpecialFunctions: gamma" in code
    assert "import NaNMath" in code
    simulator = OdeSystem.from_sbml(VDP_SBML).render("julia")
    assert "using DataFrames: DataFrame" in simulator
    assert "VectorContinuousCallback" not in simulator
    assert "VectorContinuousCallback" in _code(TWO_EVENTS)


@pytest.mark.parametrize(
    ("sid", "module"),
    [
        (None, "Model"),
        ("m", "M"),
        ("model1", "Model1"),
        ("_", "Model_"),
        ("_m", "_m"),
        ("a", "A_"),  # the id of a species
        ("dataFrames", "DataFrames_"),  # a module the code uses
    ],
)
def test_julia_module_name(sid: str | None, module: str) -> None:
    """The module is the model id with its first letter upper-cased, unique."""

    def set_id(model: libsbml.Model) -> None:
        if sid is None:
            model.unsetId()
        else:
            model.setId(sid)

    sbml = edit_sbml(model_sbml("species A = 1; R1: A -> ; A"), set_id)
    code = OdeSystem.from_sbml(sbml).render("julia")
    assert f"\nmodule {module}\n" in code
    assert code.endswith(f"end  # module {module}\n")


def test_julia_function_definitions() -> None:
    """A function definition is a julia function, called by the math."""
    code = _code(RULES)
    assert "mm(S, km) = S / (km + S)" in code
    assert "mm(A, km)" in code


def test_julia_amount_state_is_named() -> None:
    """The amount of a species in a variable compartment reads as its amount."""
    assert "n_A = x[2]  # amount of A" in _code(RULES)


def test_julia_format() -> None:
    """The julia format is registered with its suffix, options and 1-based indices."""
    julia = FORMATS["julia"]
    assert julia.kind == "code"
    assert julia.suffixes == (".jl",)
    assert julia.options == {"simulator": True}
    assert julia.first_index == 1


def test_julia_write_by_suffix(tmp_path: Path) -> None:
    """`write` takes the julia format from the suffix `.jl`."""
    system = OdeSystem.from_sbml(VDP_SBML)
    path = system.write(tmp_path / "vdp.jl")
    assert path.read_text(encoding="utf-8") == system.render("julia")


def test_julia_unsupported_raises() -> None:
    """A model with an algebraic rule cannot be written as julia."""
    system = OdeSystem.from_sbml(model_sbml("x = 1; y = 2; 0 = x + y - 3"))
    with pytest.raises(NotImplementedError, match="julia code"):
        system.render("julia")


def test_julia_jobs_stop_at_a_hung_job(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A job which runs longer than `JOB_TIMEOUT` stops all julia processes."""
    if julia_command() is None:
        toolchain_missing("julia", "SBMLUTILS_JULIA")
    monkeypatch.setattr(ode_helpers, "JOB_TIMEOUT", 30)
    jobs = {
        "hung": Job("module Hung end", "    sleep(3600)\n"),
        "other": Job("module Other end", "    sleep(3600)\n"),
    }
    started = time.monotonic()
    with pytest.raises(RuntimeError, match="took more than 30 seconds"):
        run_julia_jobs(jobs, tmp_path, processes=2)
    assert time.monotonic() - started < 120
