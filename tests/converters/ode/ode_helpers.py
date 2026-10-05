"""Helpers shared by the tests of the ODE export.

The helpers are imported as `from ode_helpers import ...`: pytest puts the directory
of a test module on `sys.path` (prepend import mode, no `__init__.py`).
"""

import functools
import importlib.util
import os
import shlex
import subprocess
from pathlib import Path
from types import ModuleType

import libsbml

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


def _command(variable: str, default: str) -> list[str] | None:
    """Command prefix of a toolchain from an environment variable, if it runs.

    Args:
        variable: the environment variable, e.g. `SBMLUTILS_JULIA`
        default: the command if the variable is not set

    Returns:
        the command split into its arguments, `None` if `--version` fails
    """
    command = shlex.split(os.environ.get(variable) or default)
    try:
        subprocess.run(
            [*command, "--version"], capture_output=True, check=True, timeout=600
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return command


@functools.cache
def julia_command() -> list[str] | None:
    """Command of julia, `SBMLUTILS_JULIA` (default `julia`), `None` if it fails."""
    return _command("SBMLUTILS_JULIA", "julia")


@functools.cache
def rscript_command() -> list[str] | None:
    """Command of Rscript, `SBMLUTILS_RSCRIPT` (default `Rscript`), `None` if it fails."""
    return _command("SBMLUTILS_RSCRIPT", "Rscript")


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
    """
    if command is None:
        raise RuntimeError(f"No toolchain to run {script.name}.")
    script.write_text(code)
    result = subprocess.run(
        [*command, str(script.absolute())], capture_output=True, text=True, check=False
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
