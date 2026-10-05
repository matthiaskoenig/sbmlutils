"""Helpers shared by the tests of the ODE export.

The helpers are imported as `from ode_helpers import ...`: pytest puts the directory
of a test module on `sys.path` (prepend import mode, no `__init__.py`).
"""

import functools
import importlib.util
import os
import shlex
import shutil
import subprocess
import textwrap
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import libsbml
import numpy as np
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


@functools.cache
def julia_command() -> list[str] | None:
    """Command of julia, `SBMLUTILS_JULIA` (default `julia`).

    Returns:
        the command, `None` if it fails to load `JULIA_PACKAGES`
    """
    return _command(
        "SBMLUTILS_JULIA", "julia", ["-e", f"using {', '.join(JULIA_PACKAGES)}"]
    )


@functools.cache
def rscript_command() -> list[str] | None:
    """Command of Rscript, `SBMLUTILS_RSCRIPT` (default `Rscript`).

    The math of the R printer uses base R only.

    Returns:
        the command, `None` if `--version` fails
    """
    return _command("SBMLUTILS_RSCRIPT", "Rscript", ["--version"])


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


def run_r(code: str, tmp_path: Path) -> str:
    """Run R code with `rscript_command`.

    Args:
        code: the R code
        tmp_path: directory of the script, below `/tmp` for the docker command

    Returns:
        the standard output
    """
    return _run(rscript_command(), tmp_path / "script.R", code)


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


def assert_python_as_roadrunner(sbml: str | Path, tmp_path: Path) -> ModuleType:
    """Assert that the generated python computes the values of roadrunner.

    The initial values (states, constants and assigned values at t=0) are compared,
    then the rates of change and the assigned values at the initial state and at two
    other states, in which every state is changed, so that no value is zero by
    chance, the last one at t=1.5, so that math of the time is covered.

    Args:
        sbml: the SBML of the model or the path of its file; a comp model is read
            from its file, roadrunner flattens a model only if it reads the file
        tmp_path: directory of the python file

    Returns:
        the module of the generated python
    """
    roadrunner = pytest.importorskip("roadrunner")
    system = OdeSystem.from_sbml(sbml)
    module = python_module(system, tmp_path / "model.py", simulator=False)
    assert list(module.XIDS) == list(system.states)
    assert list(module.YIDS) == list(system.assigned)
    r = roadrunner.RoadRunner(str(sbml))

    x0, p = module.initial_values()
    initial = roadrunner_reference(r, system)
    assert_values(dict(zip(module.XIDS, x0, strict=True)), initial.states, "x0")
    assert_values(dict(zip(module.PIDS, p, strict=True)), initial.constants, "p")
    y0 = module.f_y(0.0, x0, p)
    assert_values(dict(zip(module.YIDS, y0, strict=True)), initial.assigned, "y0")

    for t, x in [(0.0, x0), (0.0, x0 * 1.5 + 0.1), (1.5, x0 * 0.5 + 0.2)]:
        r.model.setTime(t)
        reference = roadrunner_reference(
            r, system, dict(zip(module.XIDS, x, strict=True))
        )
        dxdt = module.f_dxdt(t, x, p)
        assert isinstance(dxdt, np.ndarray)
        rates = dict(zip(module.XIDS, dxdt, strict=True))
        assert_values(rates, reference.rates, f"dx/dt at t={t}")
        y = dict(zip(module.YIDS, module.f_y(t, x, p), strict=True))
        assert_values(y, reference.assigned, f"y at t={t}")
    return module
