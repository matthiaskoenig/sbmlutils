"""Test the R code of the ODE export against roadrunner.

The R code is run with `rscript_command` (`SBMLUTILS_RSCRIPT`, default `Rscript`),
the tests which run it skip without R and deSolve. The jobs of the tests run in two R
processes, see `run_r_jobs`: the jobs of the right hand side (`simulator=False`, base
R only), and the jobs of `simulate`, which integrate with `deSolve::lsoda`. The code of
a job is sourced into an environment whose parent is the base environment, so that a
job fails if the code uses more than base R and the packages it names.
"""

import functools
import re
import subprocess
import sys
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
    R_POINT_VALUES_JOB,
    TIMEOUT,
    TWO_EVENTS,
    Job,
    JobOutput,
    assert_table_as_roadrunner,
    assert_values_as_roadrunner,
    edit_sbml,
    model_sbml,
    r_simulate_job,
    rscript_command,
    run_r_jobs,
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
    # ids which are names of R, of base R, of the code or no names of R
    "reserved": model_sbml("""
        compartment c = 1
        species T in c = 2; species p in c = 1
        F = 0.5; t_ = 2; XIDS = 1; f_y = 3; initial_values = 0.1; _x = 2
        lsoda = 1; deSolve = 2; list = 3; sum = 4
        R1: T -> p; F * T * t_ * XIDS * _x * lsoda
        R2: p -> ; initial_values * f_y * p * deSolve * list * sum
    """),
    # math of the time out of its domain is inf, not an error (case 01488)
    "time_domain": model_sbml("""
        function f(a)
            piecewise(0, a > 1e300, a)
        end
        y := f(1 / time)
    """),
}

# the id of a model whose name breaks out of a comment or a string
INJECTED_NAME = (
    "A&#10;INJECTED_LF &lt;- 1&#13;INJECTED_CR &lt;- 1&#13;&#10;INJECTED_CRLF &lt;- 1"
    "&#x2028;INJECTED_LS &lt;- 1&#x85;INJECTED_NEL &lt;- 1&#9;tab"
    " &quot;); INJECTED_QUOTE &lt;- 1; c(&quot; \\&quot; ä \\u{41} \\"
)

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
        ).render("r", simulator=False),
        """
        initial <- m$initial_values()
        emit(io, "dx", m$f_dxdt(0, initial$x0, initial$p)[[1]])
        emit(io, "y", m$f_y(0, initial$x0, initial$p))
        """,
    ),
    "initial_values_take_constants": lambda: Job(
        OdeSystem.from_sbml(model_sbml(RULES)).render("r", simulator=False),
        """
        p <- m$P0
        p[["vmax"]] <- 10
        passed <- p
        initial <- m$initial_values(p)
        emit(io, "p_new", initial$p)
        emit(io, "p_names", names(initial$p))
        emit(io, "x0_names", names(initial$x0))
        emit(io, "unchanged", identical(p, passed))
        emit(io, "x0", initial$x0)
        """,
    ),
    "injected": lambda: Job(
        OdeSystem.from_sbml(sbml_with_rate("k*A", name=INJECTED_NAME)).render(
            "r", simulator=False
        ),
        """
        emit(io, "names", ls(m, all.names = TRUE))
        emit(io, "name", m$NAMES[["A"]])
        """,
    ),
    "events_without_simulator": lambda: Job(
        OdeSystem.from_sbml(model_sbml(TWO_EVENTS)).render("r", simulator=False),
        """
        initial <- m$initial_values()
        x <- initial$x0
        p <- initial$p
        emit(io, "ids", vapply(m$EVENTS, function(event) event$id, ""))
        emit(io, "triggers", m$event_triggers(0, x, p))
        emit(io, "conditions", m$event_conditions(0, x, p))
        event <- m$EVENTS[[1]]
        emit(io, "delay", event$delay(0, x, p))
        emit(io, "priority", event$priority(0, x, p))
        assigned <- event$assign(0, x, p, event$values(0, x, p))
        emit(io, "x_new", assigned$x)
        emit(io, "p_new", assigned$p)
        emit(io, "x", x)
        emit(io, "simulate", exists("simulate", envir = m, inherits = FALSE))
        emit(io, "no_delay", is.null(m$EVENTS[[2]]$delay))
        """,
    ),
}

# the jobs of `simulate`, the models of the event tests of the python code included
SIMULATE_JOBS: dict[str, Callable[[], Job]] = {
    "repressilator": lambda: Job(
        OdeSystem.from_sbml(REPRESSILATOR_SBML).render("r"), r_simulate_job()
    ),
    **{
        f"events_{name}": functools.partial(
            lambda antimony: Job(
                OdeSystem.from_sbml(model_sbml(antimony)).render("r"),
                r_simulate_job(),
            ),
            antimony,
        )
        for name, antimony in EVENT_MODELS.items()
        if name != "infinite_cascade"
    },
    "stateless": lambda: Job(
        OdeSystem.from_sbml(model_sbml("k = 2; y := k * time; z := y^2")).render("r"),
        r_simulate_job(4.0, 5),
    ),
    "x0_and_p": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species A = 2; R1: A -> ; k * A; k = 1")
        ).render("r"),
        """
        p <- m$P0
        p[["k"]] <- 2
        emit_table(io, m$simulate(1, points = 3, p = p, x0 = 4))
        """,
    ),
    "max_steps": lambda: Job(
        OdeSystem.from_sbml(VDP_SBML).render("r"),
        """
        emit(io, "MAX_STEPS", m$MAX_STEPS)
        emit(io, "error", tryCatch(
            quietly(function() m$simulate(10, max_steps = 5)),
            error = function(e) conditionMessage(e)
        ))
        """,
    ),
    "many_points": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species S = 1; R1: S -> ; k * S; k = 1")
        ).render("r"),
        """
        df <- m$simulate(10, points = m$MAX_STEPS + 2)
        emit(io, "S", c(df[nrow(df), "S"], nrow(df)))
        """,
    ),
    "window_hmax": lambda: Job(
        OdeSystem.from_sbml(model_sbml(EVENT_MODELS["window"])).render("r"),
        """
        emit(io, "B", m$simulate(4, points = 21)[21, "B"])
        emit(io, "B_hmax", m$simulate(4, points = 21, hmax = 1)[21, "B"])
        emit(io, "TRIGGER_POINTS", m$TRIGGER_POINTS)
        """,
    ),
    "short_window": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("B = 0; E1: at time > 1.01 && time < 1.06: B = B + 1")
        ).render("r"),
        """
        emit(io, "B", m$simulate(4, points = 21)[21, "B"])
        emit(io, "B_hmax", m$simulate(4, points = 21, hmax = 1)[21, "B"])
        """,
    ),
    "infinite_cascade": lambda: Job(
        OdeSystem.from_sbml(model_sbml(EVENT_MODELS["infinite_cascade"])).render("r"),
        """
        emit(io, "MAX_CASCADE", m$MAX_CASCADE)
        emit(io, "error", tryCatch(
            quietly(function() m$simulate(2)),
            error = function(e) conditionMessage(e)
        ))
        """,
    ),
    **{
        f"pole{k}": functools.partial(
            lambda event: Job(
                OdeSystem.from_sbml(model_sbml(f"x = 1; x' = x^2{event}")).render("r"),
                """
                emit(io, "error", tryCatch(
                    quietly(function() m$simulate(2)),
                    error = function(e) conditionMessage(e)
                ))
                """,
            ),
            event,
        )
        for k, event in enumerate(["", "; E1: at time > 5: x = 2"])
    },
    **{
        f"without_time_{name}": functools.partial(
            lambda antimony: Job(
                OdeSystem.from_sbml(model_sbml(antimony)).render("r"),
                """
                x0 <- m$initial_values()$x0
                emit(io, "x0", x0)
                df <- m$simulate(0)
                emit(io, "rows", nrow(df))
                emit(io, "times", df$time)
                emit(io, "states", unlist(df[m$XIDS]))
                single <- m$simulate(5, points = 1)
                emit(io, "single_times", single$time)
                emit(io, "single_states", unlist(single[m$XIDS]))
                """,
            ),
            antimony,
        )
        for name, antimony in [
            ("events", EVENT_MODELS["rounding"]),
            ("states", "S = 1; S' = -S"),
        ]
    },
    "reserved_simulate": lambda: Job(
        OdeSystem.from_sbml(
            model_sbml("species A = 1; R1: A -> ; simulate * A; simulate = 1")
        ).render("r"),
        r_simulate_job(1.0, 2),
    ),
}

# the names of every rendering of the parse test, see `test_r_names_are_reserved`
PARSED: dict[str, tuple[str, bool]] = {
    "rules": (RULES, True),
    "rules_rhs": (RULES, False),
    "events": (TWO_EVENTS, True),
    "events_rhs": (TWO_EVENTS, False),
    "stateless_events": (EVENT_MODELS["without_states"], True),
}

# the R code which lists the names of the code: every symbol of the parsed code but
# the names of arguments and of the entries of a list (`SYMBOL_SUB`) and the names
# after `$`, which never clash with a variable
NAMES_JOB = """
  data <- utils::getParseData(parse(file = r"({path})", keep.source = TRUE))
  data <- data[data$terminal, ]
  data <- data[order(data$line1, data$col1), ]
  after_dollar <- c(FALSE, data$token[-nrow(data)] == "'$'")
  symbols <- c("SYMBOL", "SYMBOL_FUNCTION_CALL", "SYMBOL_FORMALS", "SYMBOL_PACKAGE")
  emit(io, "names", sort(unique(data$text[data$token %in% symbols & !after_dollar])))
"""


def _code(antimony: str, **options: object) -> str:
    """The R code of a model written in antimony."""
    return OdeSystem.from_sbml(model_sbml(antimony)).render("r", **options)


def _point_jobs() -> dict[str, Job]:
    """The jobs of the right hand side."""
    jobs = {
        name: Job(
            OdeSystem.from_sbml(sbml).render("r", simulator=False), R_POINT_VALUES_JOB
        )
        for name, sbml in POINT_MODELS.items()
    }
    jobs.update({name: job() for name, job in POINT_JOBS.items()})
    for name, (antimony, simulator) in PARSED.items():
        jobs[f"parse_{name}"] = Job(_code(antimony, simulator=simulator), NAMES_JOB)
    return jobs


@pytest.fixture(scope="module")
def r(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str], JobOutput]:
    """The output of a job of the module, by its name.

    The jobs of the right hand side and the jobs of `simulate` run in an R process
    each, on the first request of one of their jobs.
    """
    if rscript_command() is None:
        toolchain_missing("R", "SBMLUTILS_RSCRIPT")
    outputs: dict[str, JobOutput] = {}

    def output(name: str) -> JobOutput:
        if name not in outputs:
            if name in SIMULATE_JOBS:
                jobs = {n: job() for n, job in SIMULATE_JOBS.items()}
                directory = tmp_path_factory.mktemp("r_simulate")
            else:
                jobs = _point_jobs()
                directory = tmp_path_factory.mktemp("r_points")
            for job_name, job in jobs.items():
                path = (directory / f"{job_name}.R").absolute()
                jobs[job_name] = Job(job.code, job.run.replace("{path}", str(path)))
            outputs.update(run_r_jobs(jobs, directory))
        return outputs[name]

    return output


# --- correctness against roadrunner ---------------------------------------------------


@pytest.mark.parametrize("name", list(POINT_MODELS))
def test_r_as_roadrunner(name: str, r: Callable[[str], JobOutput]) -> None:
    """The R of a model computes the values of roadrunner.

    The formulas cover every construct of the math, the models of the python tests
    every construct of a model, initial assignments (#438) included.
    """
    assert_values_as_roadrunner(POINT_MODELS[name], r(name).point_values())


def test_r_rules_and_functions(r: Callable[[str], JobOutput]) -> None:
    """Function definitions, rules, an initial assignment and an amount state."""
    values = r("rules").point_values()
    assert values.xids == ["c", "n_A", "n_B"]
    assert values.p[values.pids.index("keff")] == 4.0
    assert values.x0[values.xids.index("n_A")] == pytest.approx(6.0)


def test_r_reserved_ids(r: Callable[[str], JobOutput]) -> None:
    """Ids which are names of R or of the code, or start with `_`, run."""
    values = r("reserved").point_values()
    assert values.xids == ["T", "p"]
    assert {"F", "t_", "XIDS", "f_y", "initial_values", "_x", "lsoda"} <= set(
        values.pids
    )
    assert {"deSolve", "list", "sum"} <= set(values.pids)


def test_r_time_out_of_its_domain(r: Callable[[str], JobOutput]) -> None:
    """Math of the time out of its domain is `Inf`, not an error (case 01488)."""
    assert r("time_domain").floats("y0").tolist() == [0.0]


def test_r_negative_base_with_fractional_exponent_is_nan(
    r: Callable[[str], JobOutput],
) -> None:
    """A power of a negative state with a fractional exponent is NaN, no error."""
    output = r("negative_base")
    assert np.isnan(output.floats("dx")).all()
    assert np.isnan(output.floats("y")).all()


def test_r_initial_values_take_constants(r: Callable[[str], JobOutput]) -> None:
    """`initial_values` evaluates the initial values with the constants passed."""
    output = r("initial_values_take_constants")
    pids = r("rules").strings("PIDS")
    assert output.floats("p_new")[pids.index("keff")] == 20.0
    # named vectors, the constants passed are not changed
    assert output.strings("p_names") == pids
    assert output.strings("x0_names") == ["c", "n_A", "n_B"]
    assert output.strings("unchanged") == ["TRUE"]
    assert output.floats("x0").tolist() == r("rules").floats("x0").tolist()


def test_r_simulate_matches_roadrunner(r: Callable[[str], JobOutput]) -> None:
    """The simulator integrates the repressilator as roadrunner."""
    system = OdeSystem.from_sbml(REPRESSILATOR_SBML)
    df = r("repressilator").table()
    assert list(df.columns) == ["time", *system.states, *system.assigned]
    assert_table_as_roadrunner(REPRESSILATOR_SBML, df)


def test_r_simulate_from_x0_and_p(r: Callable[[str], JobOutput]) -> None:
    """The simulator starts from the states and the constants passed."""
    df = r("x0_and_p").table()
    assert list(df.columns) == ["time", "A", "R1"]
    assert df["A"].tolist() == pytest.approx(4.0 * np.exp(-2.0 * df["time"]), rel=1e-6)


def test_r_model_without_states(r: Callable[[str], JobOutput]) -> None:
    """A model of assignment rules only has no states and simulates."""
    df = r("stateless").table()
    assert list(df.columns) == ["time", "y", "z"]
    assert df["z"].tolist() == pytest.approx([0.0, 4.0, 16.0, 36.0, 64.0])


def test_r_reserved_id_simulate(r: Callable[[str], JobOutput]) -> None:
    """An id `simulate` is renamed, the simulator runs."""
    df = r("reserved_simulate").table()
    assert df["A"].tolist() == pytest.approx([1.0, np.exp(-1.0)], rel=1e-6)


def test_r_simulate_max_steps(r: Callable[[str], JobOutput]) -> None:
    """More steps of the integrator than `max_steps` throw an error."""
    output = r("max_steps")
    assert output.floats("MAX_STEPS").tolist() == [100000]
    assert "more than 5 steps" in output.strings("error")[0]


def test_r_simulate_max_steps_scale_with_the_points(
    r: Callable[[str], JobOutput],
) -> None:
    """The default limit of the steps grows with the steps the time points force."""
    value, rows = r("many_points").floats("S")
    assert rows == 100002
    assert value == pytest.approx(np.exp(-10.0), rel=1e-6)


@pytest.mark.parametrize("name", ["events", "states"])
def test_r_simulate_without_time(name: str, r: Callable[[str], JobOutput]) -> None:
    """`simulate(0)` is the initial state at each time point, one point is t = 0."""
    output = r(f"without_time_{name}")
    x0 = output.floats("x0").tolist()
    assert output.floats("rows").tolist() == [101]
    assert output.floats("times").tolist() == [0.0] * 101
    # the states column by column
    assert output.floats("states").tolist() == [v for v in x0 for _ in range(101)]
    assert output.floats("single_times").tolist() == [0.0]
    assert output.floats("single_states").tolist() == x0


@pytest.mark.parametrize("name", ["pole0", "pole1"])
def test_r_simulate_raises_for_a_state_without_bound(
    name: str, r: Callable[[str], JobOutput]
) -> None:
    """A state which grows without bound throws, it does not integrate for ever.

    `x' = x^2` with `x(0) = 1` is `1 / (1 - t)`, which has a pole at t = 1.
    """
    error = r(name).strings("error")[0]
    assert re.match(r"The integration failed at t = 0\.99999", error), error


# --- events ---------------------------------------------------------------------------
# The trajectories of models with events are compared with the relaxed tolerances of
# the test suite sweep: an event time is located to the tolerance of the integration,
# which shifts the values after it.

EVENT_RTOL = 1e-4
EVENT_ATOL = 1e-6


def _events_as_roadrunner(name: str, r: Callable[[str], JobOutput]) -> pd.DataFrame:
    """Assert that a model of `EVENT_MODELS` simulates as roadrunner.

    Returns:
        the simulation of the R code
    """
    df = r(f"events_{name}").table()
    assert_table_as_roadrunner(
        model_sbml(EVENT_MODELS[name]), df, rtol=EVENT_RTOL, atol=EVENT_ATOL
    )
    return df


@pytest.mark.parametrize(
    "name", [name for name in EVENT_MODELS if name != "infinite_cascade"]
)
def test_r_events_as_roadrunner(name: str, r: Callable[[str], JobOutput]) -> None:
    """The R of every event model of the python tests simulates as roadrunner."""
    _events_as_roadrunner(name, r)


def test_r_two_events(r: Callable[[str], JobOutput]) -> None:
    """The table has the constants which events change."""
    df = _events_as_roadrunner("two_events", r)
    assert list(df.columns) == ["time", "S", "R1", "k", "total"]
    assert df["k"].iloc[-1] == 1.0


@pytest.mark.parametrize(("relation", "before"), [(">=", False), (">", True)])
def test_r_event_at_a_time_point(
    relation: str, before: bool, r: Callable[[str], JobOutput]
) -> None:
    """At a time point of the output the values are those after its events."""
    df = _events_as_roadrunner(f"at_time_point[{relation}]", r)
    row = df[np.isclose(df["time"], 2.0)].iloc[0]
    assert row["A"] == pytest.approx(2.0 if before else 10.0)


def test_r_event_at_a_time_point_to_the_rounding(r: Callable[[str], JobOutput]) -> None:
    """An event at a time point to the rounding of the integration is at it.

    The integration finds `A <= 1.88` about 1e-14 after t = 2.4 (as in case 01675);
    the execution at 3.4 is at the time point 3.4 nevertheless.
    """
    df = _events_as_roadrunner("rounding", r)
    assert df[np.isclose(df["time"], 3.4)]["B"].iloc[0] == 1.0


@pytest.mark.parametrize("relation", [">=", ">"])
def test_r_event_at_t0(relation: str, r: Callable[[str], JobOutput]) -> None:
    """A trigger which holds at t = 0 fires there if its initial value is false."""
    df = _events_as_roadrunner(f"at_t0[{relation}]", r)
    fired = 1.0 if relation == ">=" else 0.0
    assert df["B"].iloc[0] == fired
    assert df["C"].iloc[-1] == 1.0 - fired
    assert df["D"].iloc[-1] == 3.0


def test_r_event_priority(r: Callable[[str], JobOutput]) -> None:
    """Events at the same time execute in the order of their priorities."""
    df = _events_as_roadrunner("priority", r)
    assert df[np.isclose(df["time"], 2.0)]["B"].iloc[0] == 4.0
    assert df["B"].iloc[-1] == 17.0


def test_r_event_delay(r: Callable[[str], JobOutput]) -> None:
    """A delayed event executes after its delay, each time its trigger turns true."""
    df = _events_as_roadrunner("delay", r)
    assert df["n"].iloc[-1] == 4.0
    assert df["S"].iloc[-1] == pytest.approx(4.831581402482879, rel=1e-6)


def test_r_event_persistent(r: Callable[[str], JobOutput]) -> None:
    """An event which is not persistent is dropped if its trigger turns false."""
    df = _events_as_roadrunner("persistent", r)
    assert df["B"].iloc[-1] == 0.0
    assert df["C"].iloc[-1] == 1.0
    assert df["F"].iloc[-1] == 1.0


def test_r_event_changes_compartment(r: Callable[[str], JobOutput]) -> None:
    """An event changes the size of a compartment, the concentrations follow."""
    df = _events_as_roadrunner("compartment", r)
    row = df[np.isclose(df["time"], 2.2)].iloc[0]
    assert row["S"] == pytest.approx(0.8025187974297124, rel=1e-6)
    assert row["T"] == pytest.approx(0.62, rel=1e-6)
    assert df["S"].iloc[-1] == pytest.approx(7.278367917708202, rel=1e-6)


def test_r_event_assigns_its_threshold(r: Callable[[str], JobOutput]) -> None:
    """An event which sets its trigger to the root keeps integrating."""
    df = _events_as_roadrunner("threshold", r)
    assert df["A"].between(1.0, 2.0).all()
    assert df["A"].iloc[-1] == pytest.approx(1.5)


def test_r_event_model_without_states(r: Callable[[str], JobOutput]) -> None:
    """A model of events and rules only integrates nothing but its events."""
    df = _events_as_roadrunner("without_states", r)
    assert list(df.columns) == ["time", "y", "B"]
    assert df["B"].iloc[-1] == 5.0


def test_r_event_window_and_hmax(r: Callable[[str], JobOutput]) -> None:
    """A trigger is checked at `TRIGGER_POINTS` points per `hmax`, as in python.

    The trigger of `window` holds from t = 1 to 1.5, which steps of 1 find at their
    points 0.1 apart. A trigger which holds for a shorter time than the distance of
    the points, from t = 1.01 to 1.06, is stepped over by steps of 1 (t = 1, 1.1) and
    found by the steps of the default, the distance of the time points.
    """
    output = r("window_hmax")
    assert output.floats("TRIGGER_POINTS").tolist() == [10]
    assert output.floats("B").tolist() == [1.0]
    assert output.floats("B_hmax").tolist() == [1.0]
    short = r("short_window")
    assert short.floats("B").tolist() == [1.0]
    assert short.floats("B_hmax").tolist() == [0.0]


def test_r_event_infinite_cascade_raises(r: Callable[[str], JobOutput]) -> None:
    """Events which trigger each other at one time without end throw an error."""
    output = r("infinite_cascade")
    assert output.floats("MAX_CASCADE").tolist() == [10000]
    assert "infinite cascade" in output.strings("error")[0]


def test_r_events_without_simulator(r: Callable[[str], JobOutput]) -> None:
    """`simulator=False` writes the functions of the events for a solver of one's own."""
    code = _code(TWO_EVENTS, simulator=False)
    assert "deSolve::" not in code
    assert "simulate" not in code
    output = r("events_without_simulator")
    assert output.strings("ids") == ["E1", "E2"]
    assert output.floats("triggers").tolist() == [-5.0, -3.0]
    assert output.strings("conditions") == ["FALSE", "FALSE"]
    assert output.floats("delay").tolist() == [1.0]
    assert output.floats("priority").tolist() == [2.0]
    assert output.floats("x_new").tolist() == [15.0]
    assert output.floats("p_new").tolist() == [1.0, 0.5, 1.0]
    # the states passed are not changed
    assert output.floats("x").tolist() == [10.0]
    assert output.strings("simulate") == ["FALSE"]
    assert output.strings("no_delay") == ["TRUE"]


# --- shape of the code ----------------------------------------------------------------


@pytest.mark.parametrize("name", list(PARSED))
def test_r_names_are_reserved(name: str, r: Callable[[str], JobOutput]) -> None:
    """Every name the template writes, not an id of the model, is reserved.

    R parses the code and lists its names; the names of arguments, of the entries of
    lists and after `$` never clash with a variable.
    """
    antimony, simulator = PARSED[name]
    system = OdeSystem.from_sbml(model_sbml(antimony))
    ids = [q.symbol.sid for q in system.quantities]
    ids += [r.symbol.sid for r in system.reactions]
    ids += [f.symbol.sid for f in system.functions]
    ids += [e.symbol.sid for e in system.events]
    model_names = set(code_names(ids, "r").values())
    data = context(system, FORMATS["r"], {"simulator": simulator})
    events = data["events"]
    assert isinstance(events, list)
    model_names |= {f for e in events for f in e["functions"].values() if f}
    written = set(r(f"parse_{name}").strings("names"))
    # the arguments of the function definitions
    arguments = {"S", "km", "k", "n"}
    assert written - model_names - arguments <= RESERVED["r"]


def test_r_name_does_not_leave_comment(r: Callable[[str], JobOutput]) -> None:
    """A line break or a quote in a name never becomes code."""
    code = OdeSystem.from_sbml(sbml_with_rate("k*A", name=INJECTED_NAME)).render("r")
    for line in code.splitlines():
        if "INJECTED" in line and "#" in line and '"' not in line:
            assert line.index("#") < line.index("INJECTED"), line
    # the strings are ASCII, whatever the locale R reads the file in
    for line in code.splitlines():
        if not line.isascii():
            assert line[: line.index("#")].isascii(), line
    output = r("injected")
    assert not [n for n in output.strings("names") if "INJECTED" in n]
    name = output.strings("name")[0]
    assert '"); INJECTED_QUOTE <- 1; c("' in name
    assert name.endswith('\\" ä \\u{41} \\')


def test_r_layout() -> None:
    """The code reads as the model: named locals with their name and unit."""
    code = OdeSystem.from_sbml(REPRESSILATOR_SBML).render("r")
    lines = code.splitlines()
    assert lines[0].startswith("# The ODE system of the model `BIOMD0000000012`")
    assert f"sbmlutils {sbmlutils.__version__}" in code
    assert "BIOMD0000000012_urn.xml" in code
    # the states are unpacked one per line, with name and unit
    assert any(line.strip().startswith("PX <- x[[1]]  # ") for line in lines)
    assert "  dx[[1]] <- " in code
    assert "list(dx)" in code
    # no trailing whitespace, no tabs, one newline at the end, no long lines
    assert not [line for line in lines if line != line.rstrip()]
    assert "\t" not in code
    assert code.endswith("\n")
    assert not code.endswith("\n\n")
    assert "\n\n\n" not in code
    assert not [line for line in lines if len(line) > 88 and "#" not in line]


def test_r_needs_base_r_only() -> None:
    """The code loads no package, `simulate` calls `deSolve::lsoda`."""
    rhs = _code(TWO_EVENTS, simulator=False)
    assert "library(" not in rhs
    assert "::" not in rhs
    code = _code(TWO_EVENTS)
    assert "library(" not in code
    assert "require(" not in code
    assert set(re.findall(r"(\w+)::", code)) == {"deSolve", "utils"}


def test_r_function_definitions() -> None:
    """A function definition is an R function, called by the math."""
    code = _code(RULES)
    assert "mm <- function(S, km) S / (km + S)" in code
    assert "mm(A, km)" in code


def test_r_amount_state_is_named() -> None:
    """The amount of a species in a variable compartment reads as its amount."""
    assert "n_A <- x[[2]]  # amount of A" in _code(RULES)


def test_r_format() -> None:
    """The R format is registered with its suffixes, options and 1-based indices."""
    r_format = FORMATS["r"]
    assert r_format.kind == "code"
    assert r_format.suffixes == (".R", ".r")
    assert r_format.options == {"simulator": True}
    assert r_format.first_index == 1


@pytest.mark.parametrize("suffix", [".R", ".r"])
def test_r_write_by_suffix(suffix: str, tmp_path: Path) -> None:
    """`write` takes the R format from the suffix `.R` or `.r`."""
    system = OdeSystem.from_sbml(VDP_SBML)
    path = system.write(tmp_path / f"vdp{suffix}")
    assert path.read_text(encoding="utf-8") == system.render("r")


def test_r_unsupported_raises() -> None:
    """A model with an algebraic rule cannot be written as R."""
    system = OdeSystem.from_sbml(model_sbml("x = 1; y = 2; 0 = x + y - 3"))
    with pytest.raises(NotImplementedError, match="r code"):
        system.render("r")


@pytest.mark.parametrize(
    "sid", [None, "m", "_", "c"], ids=["none", "m", "underscore", "c"]
)
def test_r_model_id_in_header(sid: str | None) -> None:
    """The model id is written into the header, a model without id says so."""

    def set_id(model: libsbml.Model) -> None:
        if sid is None:
            model.unsetId()
        else:
            model.setId(sid)

    sbml = edit_sbml(model_sbml("species A = 1; R1: A -> ; A"), set_id)
    first = OdeSystem.from_sbml(sbml).render("r").splitlines()[0]
    expected = "without id" if sid is None else f"`{sid}`"
    assert first == f"# The ODE system of the model {expected}."


def test_r_script_prints_the_simulation(tmp_path: Path) -> None:
    """The file run as a script prints the head of a simulation."""
    command = rscript_command()
    if command is None:
        toolchain_missing("R", "SBMLUTILS_RSCRIPT")
    path = OdeSystem.from_sbml(VDP_SBML).write(tmp_path / "vdp.R")
    result = subprocess.run(
        [*command, str(path.absolute())],
        capture_output=True,
        text=True,
        check=True,
        timeout=TIMEOUT,
    )
    lines = result.stdout.splitlines()
    assert lines[0].split() == ["time", "x", "y", "J1", "J2"]
    assert len(lines) == 7
    assert not result.stderr


# --- the job runner -------------------------------------------------------------------


def test_r_jobs_stop_at_a_hung_job(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A job which runs longer than `JOB_TIMEOUT` stops all R processes."""
    if rscript_command() is None:
        toolchain_missing("R", "SBMLUTILS_RSCRIPT")
    monkeypatch.setattr(ode_helpers, "JOB_TIMEOUT", 10)
    jobs = {
        "hung": Job("XIDS <- character(0)", "  Sys.sleep(3600)\n"),
        "other": Job("XIDS <- character(0)", "  Sys.sleep(3600)\n"),
    }
    started = time.monotonic()
    with pytest.raises(RuntimeError, match="took more than 10 seconds"):
        run_r_jobs(jobs, tmp_path, processes=2)
    assert time.monotonic() - started < 60


def _processes(tmp_path: Path, script: str, jobs: int = 2) -> None:
    """Run a python script as the process of `jobs` jobs, see `_run_processes`."""
    path = tmp_path / "jobs.py"
    path.write_text(script, encoding="utf-8")
    names = [f"job{k}" for k in range(jobs)]
    ode_helpers._run_processes([sys.executable], [path], [names], tmp_path, ".R")


def test_r_jobs_process_which_does_not_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A process which finished its jobs but does not exit raises after the timeout."""
    monkeypatch.setattr(ode_helpers, "JOB_TIMEOUT", 2)
    script = f"""
import pathlib, time
for k in range(2):
    pathlib.Path({str(tmp_path)!r}, f"job{{k}}.R.time").write_text("0.1")
time.sleep(3600)
"""
    with pytest.raises(RuntimeError, match="finished its jobs but did not exit"):
        _processes(tmp_path, script)


def test_r_jobs_process_which_exits_early(tmp_path: Path) -> None:
    """A process which exits without finishing its jobs raises, naming the job."""
    script = f"""
import pathlib, sys
pathlib.Path({str(tmp_path)!r}, "job0.R.time").write_text("0.1")
print("the end", file=sys.stderr)
"""
    with pytest.raises(RuntimeError, match="without finishing its job job1:\nthe end"):
        _processes(tmp_path, script)
