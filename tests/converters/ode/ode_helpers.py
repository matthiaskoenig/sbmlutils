"""Helpers shared by the tests of the ODE export.

The helpers are imported as `from ode_helpers import ...`: pytest puts the directory
of a test module on `sys.path` (prepend import mode, no `__init__.py`).
"""

import functools
import importlib.util
import os
import re
import shlex
import shutil
import subprocess
import textwrap
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, NoReturn

import libsbml
import numpy as np
import pandas as pd
import pytest

from sbmlutils.converters.ode import OdeSystem
from sbmlutils.converters.ode.system import Quantity
from sbmlutils.parser import antimony_to_sbml

# the rate laws of `tests/converters/test_odefac.py`, which cover every construct of
# the math the ODE export writes
FORMULAS: list[str] = [
    "k*A",
    "ln(A) + log10(A) + log(2, A) + exp(-k)",
    "piecewise(k, A > 1 && !(A > 10) || xor(true, false), 2*k)",
    "piecewise(k, (A < 1) || (A >= 10), 3*k, A == 3, 0.1)",
    "piecewise(k, A > 1)",
    "rem(A, 2) + rem(-7, A) + quotient(7, A) + root(3, A) + sqrt(A) + A^2 + pow(A, k)",
    "max(A, k, 1) + min(A, k) + abs(-A) + floor(A/2) + ceil(A/2)",
    "factorial(3) + pi + exponentiale",
    "implies(A > 1, k > 1) + (A != 2) + (1 < A <= 5)",
    "piecewise(1, A < INF, 0) + piecewise(1, 5 > -INF, 0)",
    "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)",
    "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)",
    "arcsin(k) + arccos(k) + arctan(k) + arcsinh(k) + arctanh(k)",
    "arcsec(A) + arccsc(A) + arccot(A) + arccosh(A) + arcsech(k) + arccsch(k)",
    "arccoth(A)",
    "piecewise(k*time, true, 0) + 2^-1 + -A^2 + 1/2 + (-2)^2 + 2^3^2",
]


# a model with two events, a delay and a priority, the example of the code
TWO_EVENTS = """
    compartment c = 1
    species S in c = 10
    R1: S -> ; k * S
    k = 0.5; total = 0
    E1: at 1 after S < 5, priority=2: S = S + 5, total = total + 1
    E2: at time > 3, priority=1: k = 2 * k
"""

_AT_T0 = """
    A = 0; A' = 1
    B = 0; C = 0; D = 0
    E1: at time {relation} 0, t0=false: B = B + 1
    E2: at time {relation} 0, t0=true: C = C + 1
    E3: at A > 3, t0=false: D = D + 1, A = 0
"""

EVENT_MODELS: dict[str, str] = {
    "two_events": TWO_EVENTS,
    # a trigger which holds at t = 0, with the initial values false and true
    **{f"at_t0[{r}]": _AT_T0.format(relation=r) for r in (">=", ">")},
    # an event at a time point of the output
    **{
        f"at_time_point[{r}]": f"A = 0; A' = 1; E1: at time {r} 2: A = 10"
        for r in (">=", ">")
    },
    # priorities evaluated before each execution, values at the execution
    "priority": """
        B = 1
        E1: at time > 1, priority=1, fromTrigger=false: B = 2 * B
        E2: at time > 1, priority=2, fromTrigger=false: B = B + 1
        E3: at time > 4, priority=5, fromTrigger=false: B = B + 10
        E4: at time > 4, priority=B, fromTrigger=false: B = B - 1
        E5: at time > 4, priority=7, fromTrigger=false: B = 2 * B
    """,
    # a delay which an event changes
    "delay": """
        compartment c = 1
        species S in c = 10
        R1: S -> ; k * S
        k = 0.5; d = 1.5; n = 0
        E1: at d after S < 5: S = 10, n = n + 1
        E2: at time > 4: d = 0.5
    """,
    # the values of a delayed event from the trigger time and from the execution
    "trigger_values": """
        A = 0; A' = 1
        B = 0; C = 0
        E1: at 2 after time > 1, fromTrigger=true: B = A
        E2: at 2 after time > 1, fromTrigger=false: C = A
    """,
    # events which are and are not persistent
    "persistent": """
        B = 0; C = 0; D = 0; F = 0
        E1: at 1 after (time > 1 && time < 1.5), persistent=false: B = 1
        E2: at 1 after (time > 1 && time < 1.5), persistent=true: C = 1
        E3: at time > 3, priority=2: D = 1
        E4: at time > 3, priority=1, persistent=false: F = 1
    """,
    # events which change the size of a compartment
    "compartment": """
        compartment V = 1
        species S in V = 2; species T in V = 1
        R1: S -> ; k * S * V
        T' = 0.1
        k = 0.1
        E1: at time > 2: V = 2
        E2: at time > 5: V = 0.5, S = 3
    """,
    # an execution which triggers another event
    "cascade": """
        k = 1; B = 0
        E1: at time > 1: k = 5
        E2: at k > 4: B = B + 1
    """,
    # events which set their trigger to its root, a triangle wave
    "threshold": """
        A = 1.5; A' = r; r = 1
        E1: at A >= 2: A = 2, r = -1
        E2: at A <= 1: A = 1, r = 1
    """,
    "turns_true_again": "B = 0; E1: at sin(time) > 0.5: B = B + 1",
    "without_states": "B = 0; y := 2 * B + time; E1: at time > 2: B = 5",
    # events which trigger each other without end
    "infinite_cascade": (
        "x = -1; E0: at time > 1: x = 1; E1: at x > 0: x = -1; E2: at x < 0: x = 1"
    ),
    # a trigger which holds from t = 1 to 1.5
    "window": "B = 0; E1: at time > 1 && time < 1.5: B = B + 1",
    # an event at the time point 3.4 to the rounding of the integration, which
    # finds `A <= 1.88` an error of the time later than t = 2.4 (case 01675)
    "rounding": "A = 2; A' = -0.05; B = 0; E1: at 1 after A <= 1.88: B = 1",
}
"""Models with events in antimony, by their name, which the tests of the numerical
formats simulate."""


def sbml_with_rate(formula: str, name: str = "species A", sid: str = "A") -> str:
    """SBML of a model with one species which is consumed by one reaction.

    The model holds the compartment `c` (size 2), the parameter `k` (0.5), the
    species `sid` (initial concentration 3) and the reaction `v` with the rate law
    `formula`.

    Args:
        formula: rate law of the reaction, an L3 infix formula
        name: name of the species, the compartment, the parameter and the reaction,
            in XML syntax, so that a character reference is written as it is
        sid: id of the species

    Returns:
        the SBML string
    """
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("m")
    c: libsbml.Compartment = model.createCompartment()
    c.setId("c")
    c.setName("NAME")
    c.setSize(2.0)
    c.setConstant(True)
    k: libsbml.Parameter = model.createParameter()
    k.setId("k")
    k.setName("NAME")
    k.setValue(0.5)
    k.setConstant(True)
    s: libsbml.Species = model.createSpecies()
    s.setId(sid)
    s.setName("NAME")
    s.setCompartment("c")
    s.setInitialConcentration(3.0)
    s.setHasOnlySubstanceUnits(False)
    s.setBoundaryCondition(False)
    s.setConstant(False)
    r: libsbml.Reaction = model.createReaction()
    r.setId("v")
    r.setName("NAME")
    r.setReversible(False)
    reactant: libsbml.SpeciesReference = r.createReactant()
    reactant.setSpecies(sid)
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    law: libsbml.KineticLaw = r.createKineticLaw()
    math = libsbml.parseL3Formula(formula)
    assert math is not None, libsbml.getLastParseL3Error()
    law.setMath(math)
    sbml = str(libsbml.writeSBMLToString(doc))
    return sbml.replace('name="NAME"', f'name="{name}"')


def model_sbml(antimony: str) -> str:
    """SBML of a model written in antimony.

    Antimony writes SBML L3V2; a species is in concentration unless it is declared
    `substanceOnly`, a compartment without a size has the size 1.

    Args:
        antimony: the body of the model, indented as it is in the test

    Returns:
        the SBML string
    """
    return antimony_to_sbml(textwrap.dedent(antimony))


def edit_sbml(
    sbml: str,
    edit: Callable[[libsbml.Model], object],
    level: tuple[int, int] = (3, 2),
) -> str:
    """SBML of a model changed with libsbml, for what antimony cannot write.

    Args:
        sbml: the SBML of the model
        edit: function which changes the model, e.g. sets a conversion factor
        level: the level and version the document is converted to before the edit,
            e.g. `(3, 1)` for a fast reaction, which L3V2 has no attribute for

    Returns:
        the SBML string of the changed model
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromString(sbml)
    if (doc.getLevel(), doc.getVersion()) != level:
        assert doc.setLevelAndVersion(*level, False)
    edit(doc.getModel())
    return str(libsbml.writeSBMLToString(doc))


def import_module(path: Path) -> ModuleType:
    """Import the python module written to the given path.

    Args:
        path: path of the python file, its stem is the name of the module

    Returns:
        the imported module
    """
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _command(variable: str, default: str, probe: list[str]) -> list[str] | None:
    """Command prefix of a toolchain from an environment variable, if it runs.

    Args:
        variable: the environment variable, e.g. `SBMLUTILS_JULIA`
        default: the command if the variable is not set
        probe: arguments of a run which must succeed, e.g. loading the packages
            the scripts use

    Returns:
        the command split into its arguments, `None` if the probe fails
    """
    command = shlex.split(os.environ.get(variable) or default)
    try:
        subprocess.run(
            [*command, *probe], capture_output=True, check=True, timeout=TIMEOUT
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return command


TIMEOUT = 600
"""Seconds a run of a toolchain may take, a run with docker included."""

JULIA_PACKAGES = ["NaNMath", "SpecialFunctions"]
"""The packages of julia the math of the julia printer uses."""

JULIA_SIMULATOR_PACKAGES = ["OrdinaryDiffEq", "DataFrames"]
"""The packages of julia `simulate` of the julia code uses besides `JULIA_PACKAGES`."""


R_SIMULATOR_PACKAGES = ["deSolve"]
"""The packages of R `simulate` of the R code uses, the rest of it is base R."""


REQUIRE_TOOLCHAINS = "SBMLUTILS_REQUIRE_TOOLCHAINS"
"""The environment variable which makes a test whose toolchain is missing fail
instead of skip, set by the tox environments of the toolchains, so that their tests
never pass without having run."""


def toolchain_missing(name: str, variable: str) -> NoReturn:
    """Skip a test whose toolchain is not runnable, fail it if `REQUIRE_TOOLCHAINS`.

    Args:
        name: the toolchain, e.g. `julia`
        variable: the environment variable of its command, e.g. `SBMLUTILS_JULIA`

    Raises:
        pytest.skip.Exception: if the toolchains are not required
        pytest.fail.Exception: if they are
    """
    message = f"{name} is not runnable, see `{variable}`."
    if os.environ.get(REQUIRE_TOOLCHAINS):
        pytest.fail(f"{message} {REQUIRE_TOOLCHAINS} requires it.")
    pytest.skip(message)


@functools.cache
def julia_command() -> list[str] | None:
    """Command of julia, `SBMLUTILS_JULIA` (default `julia`).

    The packages are those of the environment `tests/converters/ode/julia`, which is
    instantiated and made active with `JULIA_PROJECT`, or with `--project` in the
    command, e.g. a docker run with the environment copied into its depot as
    `@sbmlutils-ode`: `docker run --rm -v /tmp:/tmp -v $HOME/.julia-docker:/root/.julia
    -e JULIA_LOAD_PATH=@:@stdlib julia:1.11 julia --project=@sbmlutils-ode`.

    Returns:
        the command, `None` if it fails to load `JULIA_PACKAGES` and
        `JULIA_SIMULATOR_PACKAGES`, which the generated code uses
    """
    packages = ", ".join([*JULIA_PACKAGES, *JULIA_SIMULATOR_PACKAGES])
    return _command("SBMLUTILS_JULIA", "julia", ["-e", f"using {packages}"])


@functools.cache
def rscript_command() -> list[str] | None:
    """Command of Rscript, `SBMLUTILS_RSCRIPT` (default `Rscript`).

    The math of the R printer uses base R only, `simulate` of the R code the
    packages `R_SIMULATOR_PACKAGES`, e.g. a docker run of the image of
    `tests/converters/ode/docker/r.Dockerfile`: `docker run --rm -v /tmp:/tmp
    sbmlutils-r Rscript`.

    Returns:
        the command, `None` if it fails to load `R_SIMULATOR_PACKAGES`
    """
    load = "; ".join(f"library({package})" for package in R_SIMULATOR_PACKAGES)
    return _command("SBMLUTILS_RSCRIPT", "Rscript", ["-e", load])


def _run(command: list[str] | None, script: Path, code: str) -> str:
    """Write a script and run it with a toolchain.

    Args:
        command: the command of the toolchain, `None` if it is not runnable
        script: path of the script
        code: the code of the script

    Returns:
        the standard output

    Raises:
        RuntimeError: if the toolchain is not runnable or the script fails
        subprocess.TimeoutExpired: if the script runs longer than `TIMEOUT`
    """
    if command is None:
        raise RuntimeError(f"No toolchain to run {script.name}.")
    script.write_text(code)
    result = subprocess.run(
        [*command, str(script.absolute())],
        capture_output=True,
        text=True,
        check=False,
        timeout=TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed with exit code {result.returncode}:\n{result.stderr}"
        )
    return result.stdout


def run_julia(code: str, tmp_path: Path) -> str:
    """Run julia code with `julia_command`.

    Args:
        code: the julia code
        tmp_path: directory of the script, below `/tmp` for the docker command

    Returns:
        the standard output
    """
    return _run(julia_command(), tmp_path / "script.jl", code)


@dataclass(frozen=True)
class Job:
    """Generated julia or R code and the code of its language which runs it.

    Attributes:
        code: the generated code, a julia module or an R file
        run: the body of a function of the module or environment `m` of the code and
            the output stream `io`, which writes its results with `emit(io, key,
            values)`, a line of the key and the values, and `emit_table(io, df)`, a
            line of the names of the columns and a line per column; `quietly(f)`
            calls the function `f` without logging its warnings
    """

    code: str
    run: str


BENIGN_WARNINGS: dict[str, tuple[str, ...]] = {
    "julia": (
        # a state of almost 0 at the start of an integration, e.g. `trig` of case
        # 01531 after an event, makes the estimate of the first step of
        # OrdinaryDiffEq tiny, which then starts with the step 1e-6 and adapts it
        "Initial timestep too small (near machine epsilon), using default",
    ),
    "r": (
        # math out of its domain is NaN as in roadrunner, e.g. `acos(t)` of case
        # 00955 for t > 1, which base R warns about as numpy does (the python sweep
        # ignores these warnings with `np.errstate`), and julia's NaNMath does not
        "NaNs produced",
    ),
}
"""The warnings which a language logs about what it handles itself, by language."""


@dataclass(frozen=True)
class JobOutput:
    """The results of a `Job`.

    Attributes:
        language: the language of the job, `julia` or `r`
        lines: the values of each key the job emitted, as text
        error: the error the job threw, with its stack trace, `None` if it ran
        log: the warnings and errors the job logged, e.g. of the integrator, which a
            job that expects them suppresses with `quietly`
        seconds: the time the job took, its compilation included
    """

    language: str
    lines: dict[str, list[str]]
    error: str | None
    log: str
    seconds: float

    def warnings(self) -> list[str]:
        """The messages of the log, without those of `BENIGN_WARNINGS`.

        A message of julia starts with `┌` and is benign if it holds a benign
        message; a message of R is a line `Warning: <message>` and is benign if its
        message is a benign one, so that a benign message never hides another one.
        """
        benign = BENIGN_WARNINGS[self.language]
        if self.language == "julia":
            messages = re.split(r"(?m)^(?=┌)", self.log)
            return [
                m for m in messages if m.strip() and not any(b in m for b in benign)
            ]
        return [
            m
            for m in self.log.splitlines(keepends=True)
            if m.strip() and m.strip().removeprefix("Warning: ") not in benign
        ]

    def check(self) -> None:
        """Fail if the job threw an error or logged a warning."""
        name = LANGUAGES[self.language].title
        if self.error is not None:
            pytest.fail(f"The {name} code failed:\n{self.error}")
        warnings = self.warnings()
        if warnings:
            pytest.fail(f"The {name} code logged warnings:\n" + "".join(warnings))

    def strings(self, key: str) -> list[str]:
        """The values of a key as text."""
        self.check()
        return self.lines[key]

    def floats(self, key: str) -> np.ndarray:
        """The values of a key as numbers."""
        return np.array([float(v) for v in self.strings(key)], dtype=float)

    def table(self) -> pd.DataFrame:
        """The table which the job emitted with `emit_table`."""
        columns = self.strings("columns")
        return pd.DataFrame({c: self.floats(f"column {c}") for c in columns})

    def point_values(self) -> "PointValues":
        """The values of `PointValues`, emitted by a job of `*_POINT_VALUES_JOB`."""
        return PointValues(
            xids=self.strings("XIDS"),
            pids=self.strings("PIDS"),
            yids=self.strings("YIDS"),
            x0=self.floats("x0"),
            p=self.floats("p"),
            y0=self.floats("y0"),
            points=[
                (
                    float(self.floats(f"t{k}")[0]),
                    self.floats(f"x{k}"),
                    self.floats(f"dx{k}"),
                    self.floats(f"y{k}"),
                )
                for k in range(1, 4)
            ],
        )


# the prelude of a script of julia jobs: the functions which write the results and
# the function which runs a job, writing its results or its error into files next
# to its code
_JULIA_PRELUDE = r"""
import Logging

# a line of the key and the values, separated by tabs, a line break in a value a space
emit(io, key, values) = println(
    io, key, "\t", join([replace(string(v), r"\R" => " ") for v in values], "\t")
)

function emit_table(io, df)
    emit(io, "columns", names(df))
    for column in names(df)
        emit(io, "column " * column, df[!, column])
    end
end

# the code which logs warnings it expects, e.g. a job of an integration which fails
quietly(f) = Logging.with_logger(f, Logging.NullLogger())

# run a job: its results, its error and the warnings it logs into files next to it
function run_job(path, job)
    started = time()
    open(path * ".log", "w") do log
        Logging.with_logger(Logging.ConsoleLogger(log, Logging.Warn)) do
            try
                m = Base.include(Module(), path)
                open(path * ".out", "w") do io
                    Base.invokelatest(job, m, io)
                end
            catch error
                open(path * ".err", "w") do io
                    showerror(io, error, catch_backtrace())
                end
            end
        end
    end
    open(io -> print(io, time() - started), path * ".time", "w")
end
"""

# the prelude of a script of R jobs, as `_JULIA_PRELUDE`: the code of a job is
# sourced into an environment of its own whose parent is the base environment, so
# that it can use base R and the packages it names (`deSolve::lsoda`) only
_R_PRELUDE = r"""
# a line of the key and the values, separated by tabs, a line break in a value a space
emit <- function(io, key, values) {
  texts <- vapply(as.list(values), function(value) {
    text <- if (is.numeric(value)) {
      sprintf("%.17g", as.double(value))
    } else {
      as.character(value)
    }
    gsub("[\r\n]", " ", text)
  }, character(1))
  cat(paste(c(key, texts), collapse = "\t"), "\n", file = io, sep = "")
}

emit_table <- function(io, df) {
  emit(io, "columns", names(df))
  for (k in seq_along(df)) {
    emit(io, paste("column", names(df)[[k]]), df[[k]])
  }
}

# the code which signals warnings it expects, e.g. a job of an integration which fails
quietly <- function(f) suppressWarnings(f())

# run a job: its results, its error and the warnings it signals into files next to it
run_job <- function(path, job) {
  started <- proc.time()[["elapsed"]]
  log <- file(paste0(path, ".log"), "w")
  tryCatch(
    withCallingHandlers(
      {
        m <- new.env(parent = baseenv())
        sys.source(path, envir = m)
        io <- file(paste0(path, ".out"), "w")
        tryCatch(job(m, io), finally = close(io))
      },
      warning = function(w) {
        writeLines(paste("Warning:", gsub("[\r\n]", " ", conditionMessage(w))), log)
        invokeRestart("muffleWarning")
      },
      error = function(e) {
        calls <- vapply(
          sys.calls(), function(call) paste(deparse(call, nlines = 1), collapse = " "),
          character(1)
        )
        writeLines(c(conditionMessage(e), "", calls), paste0(path, ".err"))
      }
    ),
    error = function(e) NULL
  )
  close(log)
  writeLines(format(proc.time()[["elapsed"]] - started), paste0(path, ".time"))
}
"""


def _julia_job(k: int, run: str, path: Path) -> list[str]:
    """The lines of a julia script which define and run the job `k`."""
    return [f"function job_{k}(m, io)", run, "end", f'run_job(raw"{path}", job_{k})']


def _r_job(k: int, run: str, path: Path) -> list[str]:
    """The lines of an R script which define and run the job `k`."""
    return [
        f"job_{k} <- function(m, io) {{",
        run,
        "}",
        f'run_job(r"({path})", job_{k})',
    ]


@dataclass(frozen=True)
class _Language:
    """How the jobs of a language are run, see `run_jobs`.

    Attributes:
        title: the name of the language in a message
        suffix: the suffix of a file of code
        command: the command of the toolchain, `None` if it is not runnable
        prelude: the code of a script before its jobs
        job: the lines of a script which define and run a job, of its number, its
            body and the path of its code
    """

    title: str
    suffix: str
    command: Callable[[], list[str] | None]
    prelude: str
    job: Callable[[int, str, Path], list[str]]


OTHER_STATES: list[tuple[float, float, float]] = [
    (0.0, 1.0, 0.0),
    (0.0, 1.5, 0.1),
    (1.5, 0.5, 0.2),
]
"""The time, the factor and the offset of each state at which the rates of change are
compared: the initial states times the factor plus the offset, see `other_states`."""

_JULIA_STATES = ", ".join(
    f"({t!r}, x0 .* {factor!r} .+ {offset!r})" for t, factor, offset in OTHER_STATES
)

JULIA_POINT_VALUES_JOB = f"""
    x0, p = m.initial_values()
    emit(io, "XIDS", m.XIDS)
    emit(io, "PIDS", m.PIDS)
    emit(io, "YIDS", m.YIDS)
    emit(io, "x0", x0)
    emit(io, "p", p)
    emit(io, "y0", m.f_y(x0, p, 0.0))
    for (k, (t, x)) in enumerate([{_JULIA_STATES}])
        dx = zeros(length(x))
        m.f!(dx, x, p, t)
        emit(io, "t$k", [t])
        emit(io, "x$k", x)
        emit(io, "dx$k", dx)
        emit(io, "y$k", m.f_y(x, p, t))
    end
"""
"""The body of a julia `Job` which emits the values of `PointValues`, at the states
of `other_states`, of julia code rendered with `simulator=False`."""

_R_STATES = ", ".join(
    f"list({t!r}, x0 * {factor!r} + {offset!r})" for t, factor, offset in OTHER_STATES
)

R_POINT_VALUES_JOB = f"""
  initial <- m$initial_values()
  x0 <- initial$x0
  p <- initial$p
  emit(io, "XIDS", m$XIDS)
  emit(io, "PIDS", m$PIDS)
  emit(io, "YIDS", m$YIDS)
  emit(io, "x0", x0)
  emit(io, "p", p)
  emit(io, "y0", m$f_y(0, x0, p))
  states <- list({_R_STATES})
  for (k in seq_along(states)) {{
    t <- states[[k]][[1]]
    x <- states[[k]][[2]]
    emit(io, paste0("t", k), t)
    emit(io, paste0("x", k), x)
    emit(io, paste0("dx", k), m$f_dxdt(t, x, p)[[1]])
    emit(io, paste0("y", k), m$f_y(t, x, p))
  }}
"""
"""The body of an R `Job` which emits the values of `PointValues`, at the states of
`other_states`, of R code rendered with `simulator=False`."""


def julia_simulate_job(
    t_end: float = 10.0, points: int = 51, arguments: str = ""
) -> str:
    """The body of a julia `Job` which emits the table of `simulate`.

    Args:
        t_end: the end time
        points: the number of time points
        arguments: further keyword arguments of `simulate`, e.g. `"dtmax=1.0"`

    Returns:
        the body, which integrates with the tolerances of `assert_table_as_roadrunner`
    """
    extra = f", {arguments}" if arguments else ""
    return (
        f"    df = m.simulate({t_end!r}; points={points}, reltol=1e-10, "
        f"abstol=1e-12{extra})\n    emit_table(io, df)\n"
    )


def r_simulate_job(t_end: float = 10.0, points: int = 51, arguments: str = "") -> str:
    """The body of an R `Job` which emits the table of `simulate`.

    Args:
        t_end: the end time
        points: the number of time points
        arguments: further arguments of `simulate`, e.g. `"hmax = 1"`

    Returns:
        the body, which integrates with the tolerances of `assert_table_as_roadrunner`
    """
    extra = f", {arguments}" if arguments else ""
    return (
        f"  df <- m$simulate({t_end!r}, points = {points}, rtol = 1e-10, "
        f"atol = 1e-12{extra})\n  emit_table(io, df)\n"
    )


JOB_TIMEOUT = 600
"""Seconds a job may take, its compilation included, and a process may take to exit
after its last job."""


def _stderr(path: Path) -> str:
    """The end of the standard error of a process."""
    return path.read_text(encoding="utf-8", errors="replace")[-5000:]


def _run_processes(
    command: list[str],
    scripts: list[Path],
    parts: list[list[str]],
    directory: Path,
    suffix: str,
) -> None:
    """Run the scripts of jobs in parallel processes, see `run_jobs`.

    A process which has not finished a job for `JOB_TIMEOUT` seconds (or has not
    exited that long after its last job) and a process which fails stop all of them:
    a process is terminated (`docker run` passes the signal on to its container),
    and killed if it does not end.

    Args:
        command: the command of the toolchain
        scripts: the script of each process
        parts: the names of the jobs of each process, in their order
        directory: the directory of the files of the jobs
        suffix: the suffix of the files of code, e.g. `.jl`

    Raises:
        RuntimeError: if a process fails, exits before it finished its jobs, or a
            job or the exit takes longer than `JOB_TIMEOUT`
    """
    stderr_paths = [script.with_suffix(".stderr") for script in scripts]
    running = []
    for script, stderr_path in zip(scripts, stderr_paths, strict=True):
        with stderr_path.open("w") as stderr:
            running.append(
                subprocess.Popen(
                    [*command, str(script.absolute())],
                    stdout=subprocess.DEVNULL,
                    stderr=stderr,
                )
            )

    def finished(k: int) -> int:
        """The number of jobs the process k finished."""
        return sum((directory / f"{n}{suffix}.time").exists() for n in parts[k])

    done = [0] * len(running)
    progress = [time.monotonic()] * len(running)
    try:
        while any(process.poll() is None for process in running):
            for k, process in enumerate(running):
                count = finished(k)
                if count > done[k]:
                    done[k], progress[k] = count, time.monotonic()
                if process.poll() is not None and process.returncode != 0:
                    raise RuntimeError(
                        f"{scripts[k].name} failed with exit code "
                        f"{process.returncode}:\n{_stderr(stderr_paths[k])}"
                    )
                if process.poll() is None and (
                    time.monotonic() - progress[k] > JOB_TIMEOUT
                ):
                    if done[k] < len(parts[k]):
                        raise RuntimeError(
                            f"The job {parts[k][done[k]]} of {scripts[k].name} "
                            f"took more than {JOB_TIMEOUT} seconds."
                        )
                    raise RuntimeError(
                        f"{scripts[k].name} finished its jobs but did not exit "
                        f"within {JOB_TIMEOUT} seconds."
                    )
            time.sleep(0.2)
        for k, process in enumerate(running):
            if process.returncode != 0:
                raise RuntimeError(
                    f"{scripts[k].name} failed with exit code {process.returncode}:"
                    f"\n{_stderr(stderr_paths[k])}"
                )
            count = finished(k)
            if count < len(parts[k]):
                unfinished = parts[k][count]
                raise RuntimeError(
                    f"{scripts[k].name} exited without finishing its job "
                    f"{unfinished}:\n{_stderr(stderr_paths[k])}"
                )
    finally:
        for process in running:
            if process.poll() is None:
                process.terminate()
        for process in running:
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def run_jobs(
    language: str, jobs: Mapping[str, Job], directory: Path, processes: int = 1
) -> dict[str, JobOutput]:
    """Run jobs of julia or R code, many jobs in one process of the toolchain.

    The code of each job is loaded into a module (julia) or an environment (R) of its
    own, so that the code of two jobs never clashes; a job which throws an error does
    not stop the others. A process loads the packages and compiles the code which
    they share (the integrators of julia) once for all of its jobs, which makes many
    jobs in one process fast.

    Args:
        language: `julia` or `r`, see `LANGUAGES`
        jobs: the jobs by their name, a name is a file name
        directory: directory of the files of the jobs, below `/tmp` for the docker
            command
        processes: the number of processes, which run in parallel, each with a part
            of the jobs

    Returns:
        the output of each job

    Raises:
        RuntimeError: if the toolchain is not runnable or a process fails
    """
    spec = LANGUAGES[language]
    command = spec.command()
    if command is None:
        raise RuntimeError(f"{spec.title} is not runnable.")
    names = list(jobs)
    parts = [names[part::processes] for part in range(processes)]
    scripts = []
    for part, part_names in enumerate(parts):
        lines = [spec.prelude]
        for k, name in enumerate(part_names):
            path = (directory / f"{name}{spec.suffix}").absolute()
            path.write_text(jobs[name].code, encoding="utf-8")
            lines += spec.job(k, jobs[name].run.rstrip(), path)
        script = directory / f"jobs_{part}{spec.suffix}"
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")
        scripts.append(script)
    _run_processes(command, scripts, parts, directory, spec.suffix)
    outputs = {}
    for name in names:
        path = directory / f"{name}{spec.suffix}"

        def read(extension: str, path: Path = path) -> str | None:
            """The text of the file of the job with the extension, if it exists."""
            file = path.with_name(f"{path.name}.{extension}")
            return file.read_text(encoding="utf-8") if file.exists() else None

        lines: dict[str, list[str]] = {}
        for line in (read("out") or "").splitlines():
            key, _, values = line.partition("\t")
            lines[key] = values.split("\t") if values else []
        outputs[name] = JobOutput(
            language=language,
            lines=lines,
            error=read("err"),
            log=read("log") or "",
            seconds=float(read("time") or "nan"),
        )
    return outputs


def run_julia_jobs(
    jobs: Mapping[str, Job], directory: Path, processes: int = 1
) -> dict[str, JobOutput]:
    """Run julia jobs with `julia_command`, see `run_jobs`."""
    return run_jobs("julia", jobs, directory, processes)


def run_r_jobs(
    jobs: Mapping[str, Job], directory: Path, processes: int = 1
) -> dict[str, JobOutput]:
    """Run R jobs with `rscript_command`, see `run_jobs`."""
    return run_jobs("r", jobs, directory, processes)


def run_r(code: str, tmp_path: Path) -> str:
    """Run R code with `rscript_command`.

    Args:
        code: the R code
        tmp_path: directory of the script, below `/tmp` for the docker command

    Returns:
        the standard output
    """
    return _run(rscript_command(), tmp_path / "script.R", code)


LANGUAGES: dict[str, _Language] = {
    "julia": _Language("julia", ".jl", julia_command, _JULIA_PRELUDE, _julia_job),
    "r": _Language("R", ".R", rscript_command, _R_PRELUDE, _r_job),
}
"""How the jobs of julia and R are run, by language."""


def compile_typst(source: str, tmp_path: Path) -> bytes:
    """Compile a typst document with the `typst` python package.

    The test which calls it is skipped if the package is not installed (it is part
    of the `dev` extra).

    Args:
        source: the typst document
        tmp_path: directory of the document

    Returns:
        the PDF

    Raises:
        RuntimeError: if the document does not compile or compiles with a warning,
            with the messages of typst
    """
    typst = pytest.importorskip("typst")
    path = tmp_path / "document.typ"
    path.write_text(source)
    try:
        pdf, warnings = typst.compile_with_warnings(str(path))
    except typst.TypstError as error:
        raise RuntimeError(f"{path.name} failed to compile:\n{error}") from error
    if warnings:
        raise RuntimeError(f"{path.name} compiled with warnings:\n{warnings}")
    return pdf


def tectonic_command() -> list[str] | None:
    """Command of tectonic, the LaTeX engine, if it is on the path.

    Returns:
        the command, `None` if `tectonic` is not on the path
    """
    tectonic = shutil.which("tectonic")
    return [tectonic] if tectonic else None


def compile_latex(source: str, tmp_path: Path) -> Path:
    """Compile a LaTeX document with tectonic.

    Args:
        source: the LaTeX document
        tmp_path: directory of the document and of the PDF

    Returns:
        the path of the PDF

    Raises:
        RuntimeError: if tectonic is not on the path or the document fails
    """
    command = tectonic_command()
    if command is None:
        raise RuntimeError("tectonic is not on the path.")
    path = tmp_path / "document.tex"
    path.write_text(source)
    result = subprocess.run(
        [*command, "--chatter", "minimal", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{path.name} failed with exit code {result.returncode}:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return path.with_suffix(".pdf")


# --- comparison with roadrunner -------------------------------------------------------

POINT = {"rel": 1e-8, "abs": 1e-12}
"""Tolerance of a value of the generated code at a point against roadrunner."""


def selection(quantity: Quantity) -> str:
    """The roadrunner selection of a quantity in the representation of the system.

    An amount of a species is the amount of the species, a species in concentration
    its concentration, everything else its id.

    Args:
        quantity: the quantity of the system

    Returns:
        the selection, e.g. `[S]` for the concentration of `S`
    """
    if quantity.amount_of is not None:
        return quantity.amount_of
    if quantity.symbol.kind == "species" and not quantity.amount:
        return f"[{quantity.symbol.sid}]"
    return quantity.symbol.sid


@dataclass(frozen=True)
class Reference:
    """The values of a roadrunner in the representation of an ODE system.

    Attributes:
        states: the value of each state
        rates: the rate of change of each state
        constants: the value of each constant roadrunner knows, i.e. without the
            renamed local parameters
        assigned: the value of each assigned variable and reaction rate
    """

    states: dict[str, float]
    rates: dict[str, float]
    constants: dict[str, float]
    assigned: dict[str, float]


def roadrunner_reference(
    r: Any, system: OdeSystem, states: Mapping[str, float] | None = None
) -> Reference:
    """The values of a roadrunner, at its current state or at the given states.

    The states are set in the order compartments and parameters first, then the
    species, so that a concentration is set with the size of its compartment.

    Args:
        r: the `roadrunner.RoadRunner` of the model
        system: the ODE system of the model
        states: the value of each state to set before the values are read

    Returns:
        the values in the representation of the system
    """
    quantities = {q.symbol.sid: q for q in system.quantities}
    if states is not None:
        ordered = sorted(
            states, key=lambda sid: quantities[sid].symbol.kind == "species"
        )
        for sid in ordered:
            r[selection(quantities[sid])] = states[sid]
    constants = {}
    for sid in system.constants:
        try:
            constants[sid] = r[selection(quantities[sid])]
        except RuntimeError:
            # a local parameter, which roadrunner holds under the id of its reaction
            continue
    assigned = {}
    for sid in system.assigned:
        quantity = quantities.get(sid)
        assigned[sid] = r[sid if quantity is None else selection(quantity)]
    return Reference(
        states={sid: r[selection(quantities[sid])] for sid in system.states},
        rates=_rates(r, system),
        constants=constants,
        assigned=assigned,
    )


def _rates(r: Any, system: OdeSystem) -> dict[str, float]:
    """The rate of change of each state of the system in roadrunner.

    Roadrunner has no selection of the rate of a boundary species or a species
    reference with a rate rule, these are read from its rates of change, the rates of
    its state vector, which holds every species as its amount.
    """
    vector = r.getRatesOfChange()
    by_id = {r.model.getStateVectorId(k): v for k, v in enumerate(vector)}
    result = {}
    for sid in system.states:
        quantity = system.quantity(sid)
        try:
            result[sid] = r[f"{selection(quantity)}'"]
        except RuntimeError:
            rate = by_id[quantity.amount_of or sid]
            concentration = quantity.symbol.kind == "species" and not quantity.amount
            if concentration and quantity.amount_of is None:
                rate /= r[str(quantity.compartment)]
            result[sid] = rate
    return result


def assert_values(
    values: Mapping[str, float], expected: Mapping[str, float], what: str
) -> None:
    """Assert that values equal the values of roadrunner at a point.

    Args:
        values: the values of the generated code by id
        expected: the values of roadrunner by id
        what: the kind of the values, for the message
    """
    for sid, value in expected.items():
        assert values[sid] == pytest.approx(value, nan_ok=True, **POINT), (
            f"{what} {sid}: {values[sid]} != {value}"
        )


def python_module(system: OdeSystem, path: Path, **options: object) -> ModuleType:
    """Write the python code of a system and import it.

    Args:
        system: the ODE system
        path: path of the python file
        **options: the options of the python format

    Returns:
        the imported module
    """
    system.write(path, None, **options)
    return import_module(path)


@dataclass(frozen=True)
class PointValues:
    """The values of generated code at the initial state and at other states.

    Attributes:
        xids: the ids of the states
        pids: the ids of the constants
        yids: the ids of the assigned values
        x0: the initial states, of `initial_values`
        p: the constants, of `initial_values`
        y0: the assigned values at t = 0 and x0
        points: the time, the states, their rates of change and the assigned
            values at each further state
    """

    xids: list[str]
    pids: list[str]
    yids: list[str]
    x0: np.ndarray
    p: np.ndarray
    y0: np.ndarray
    points: list[tuple[float, np.ndarray, np.ndarray, np.ndarray]]


def other_states(x0: np.ndarray) -> list[tuple[float, np.ndarray]]:
    """The states at which the rates of change are compared, with their time.

    The initial state and two other states, in which every state is changed, so that
    no value is zero by chance, the last one at t=1.5, so that math of the time is
    covered.

    Args:
        x0: the initial states

    Returns:
        the time and the states of each point
    """
    return [(t, x0 * factor + offset) for t, factor, offset in OTHER_STATES]


def assert_values_as_roadrunner(sbml: str | Path, values: PointValues) -> None:
    """Assert that the values of generated code are those of roadrunner.

    The initial values (states, constants and assigned values at t=0) are compared,
    then the rates of change and the assigned values at each point.

    Args:
        sbml: the SBML of the model or the path of its file; a comp model is read
            from its file, roadrunner flattens a model only if it reads the file
        values: the values of the generated code
    """
    roadrunner = pytest.importorskip("roadrunner")
    system = OdeSystem.from_sbml(sbml)
    assert values.xids == list(system.states)
    assert values.yids == list(system.assigned)
    r = roadrunner.RoadRunner(str(sbml))

    initial = roadrunner_reference(r, system)
    assert_values(dict(zip(values.xids, values.x0, strict=True)), initial.states, "x0")
    assert_values(dict(zip(values.pids, values.p, strict=True)), initial.constants, "p")
    assert_values(
        dict(zip(values.yids, values.y0, strict=True)), initial.assigned, "y0"
    )
    for t, x, dxdt, y in values.points:
        r.model.setTime(t)
        reference = roadrunner_reference(
            r, system, dict(zip(values.xids, x, strict=True))
        )
        rates = dict(zip(values.xids, dxdt, strict=True))
        assert_values(rates, reference.rates, f"dx/dt at t={t}")
        assigned = dict(zip(values.yids, y, strict=True))
        assert_values(assigned, reference.assigned, f"y at t={t}")


def assert_python_as_roadrunner(sbml: str | Path, tmp_path: Path) -> ModuleType:
    """Assert that the generated python computes the values of roadrunner.

    See `assert_values_as_roadrunner`, the points are those of `other_states`.

    Args:
        sbml: the SBML of the model or the path of its file
        tmp_path: directory of the python file

    Returns:
        the module of the generated python
    """
    pytest.importorskip("roadrunner")
    system = OdeSystem.from_sbml(sbml)
    module = python_module(system, tmp_path / "model.py", simulator=False)
    x0, p = module.initial_values()
    points = []
    for t, x in other_states(x0):
        dxdt = module.f_dxdt(t, x, p)
        assert isinstance(dxdt, np.ndarray)
        points.append((t, x, dxdt, module.f_y(t, x, p)))
    values = PointValues(
        xids=list(module.XIDS),
        pids=list(module.PIDS),
        yids=list(module.YIDS),
        x0=x0,
        p=p,
        y0=module.f_y(0.0, x0, p),
        points=points,
    )
    assert_values_as_roadrunner(sbml, values)
    return module


T_END = 10.0
"""The end time of a trajectory, as the test suite sweep of `tests/test_roundtrip.py`."""

T_STEPS = 51
"""The number of time points of a trajectory, 0 and `T_END` included."""


def assert_table_as_roadrunner(
    sbml: str | Path,
    df: pd.DataFrame,
    rtol: float = 1e-6,
    atol: float = 1e-9,
    t_end: float = T_END,
    points: int = T_STEPS,
) -> None:
    """Assert that a simulation of generated code integrates as roadrunner.

    The simulation integrated with the relative tolerance 1e-10 and the absolute
    tolerance 1e-12, as roadrunner does here; every column of the table (the states,
    the assigned values and the constants which events change) is compared with its
    roadrunner selection, at every time point.

    Args:
        sbml: the SBML of the model or the path of its file
        df: the table of the simulation, the time and a column per id
        rtol: the relative tolerance of the comparison
        atol: the absolute tolerance of the comparison
        t_end: the end time
        points: the number of time points
    """
    roadrunner = pytest.importorskip("roadrunner")
    system = OdeSystem.from_sbml(sbml)
    r = roadrunner.RoadRunner(str(sbml))
    r.integrator.relative_tolerance = 1e-10
    r.integrator.absolute_tolerance = 1e-12
    quantities = {q.symbol.sid: q for q in system.quantities}
    columns = list(df.columns[1:])
    selections = [
        selection(quantities[sid]) if sid in quantities else sid for sid in columns
    ]
    r.timeCourseSelections = ["time", *selections]
    result = r.simulate(0.0, t_end, points)
    np.testing.assert_allclose(df["time"], result[:, 0], rtol=1e-12)
    for k, sid in enumerate(columns):
        np.testing.assert_allclose(
            df[sid], result[:, k + 1], rtol=rtol, atol=atol, err_msg=sid
        )


def assert_trajectory_as_roadrunner(
    sbml: str | Path,
    module: ModuleType,
    rtol: float = 1e-6,
    atol: float = 1e-9,
    t_end: float = T_END,
    points: int = T_STEPS,
) -> None:
    """Assert that `simulate` of the generated python integrates as roadrunner.

    See `assert_table_as_roadrunner`.

    Args:
        sbml: the SBML of the model or the path of its file
        module: the module of the generated python, with `simulate`
        rtol: the relative tolerance of the comparison
        atol: the absolute tolerance of the comparison
        t_end: the end time
        points: the number of time points
    """
    pytest.importorskip("roadrunner")
    pytest.importorskip("scipy")
    df = module.simulate(t_end, points, rtol=1e-10, atol=1e-12)
    assert_table_as_roadrunner(sbml, df, rtol, atol, t_end, points)
