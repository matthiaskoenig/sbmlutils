"""Test the python code of the ODE export against roadrunner."""

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import libsbml
import numpy as np
import pytest
from ode_helpers import (
    FORMULAS,
    assert_python_as_roadrunner,
    edit_sbml,
    import_module,
    model_sbml,
    python_module,
    sbml_with_rate,
    selection,
)

import sbmlutils
from sbmlutils.converters.ode import FORMATS, Format, OdeSystem
from sbmlutils.converters.ode.formats import context, render, render_template
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

# the trajectories of the test suite sweep, as `tests/test_roundtrip.py`
T_END = 10.0
T_STEPS = 51

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


def _code(antimony: str, **options: object) -> str:
    """The python code of a model written in antimony."""
    return OdeSystem.from_sbml(model_sbml(antimony)).render("python", **options)


# --- correctness against roadrunner ---------------------------------------------------


@pytest.mark.parametrize("formula", FORMULAS)
def test_python_formula(formula: str, tmp_path: Path) -> None:
    """The generated python evaluates every construct of the math as roadrunner."""
    assert_python_as_roadrunner(sbml_with_rate(formula), tmp_path)


@pytest.mark.parametrize(
    "sbml_path",
    [
        DEMO_SBML,
        REPRESSILATOR_SBML,
        VDP_SBML,
        COMP_DEX_LIVER,
        COMP_SPT_LIVER,
        INTERPOLATION_LINEAR_SBML,
        GALACTOSE_SINGLECELL_SBML,
    ],
    ids=lambda p: p.stem,
)
def test_python_model(sbml_path: Path, tmp_path: Path) -> None:
    """The generated python of a model computes the values of roadrunner.

    The galactose model has initial assignments (#438).
    """
    assert_python_as_roadrunner(sbml_path, tmp_path)


def test_python_rules_and_functions(tmp_path: Path) -> None:
    """Function definitions, rules, an initial assignment and an amount state."""
    module = assert_python_as_roadrunner(model_sbml(RULES), tmp_path)
    assert module.XIDS == ["c", "n_A", "n_B"]
    x0, p = module.initial_values()
    # the initial assignment of the constant is set in p
    assert p[module.PIDS.index("keff")] == 4.0
    assert x0[module.XIDS.index("n_A")] == pytest.approx(6.0)


def test_python_initial_values_take_constants(tmp_path: Path) -> None:
    """`initial_values` evaluates the initial values with the constants passed."""
    module = python_module(OdeSystem.from_sbml(model_sbml(RULES)), tmp_path / "m.py")
    p = module.P0.copy()
    p[module.PIDS.index("vmax")] = 10.0
    passed = p.copy()
    x0, p_new = module.initial_values(p)
    assert p_new[module.PIDS.index("keff")] == 20.0
    # the constants passed are not changed
    assert np.array_equal(p, passed, equal_nan=True)
    assert np.array_equal(x0, module.initial_values()[0])


def test_python_model_without_states(tmp_path: Path) -> None:
    """A model of assignment rules only has no states and simulates."""
    sbml = model_sbml("""
        k = 2
        y := k * time
        z := y^2
    """)
    module = assert_python_as_roadrunner(sbml, tmp_path)
    assert module.XIDS == []
    simulator = python_module(OdeSystem.from_sbml(sbml), tmp_path / "s.py")
    df = simulator.simulate(4.0, points=5)
    assert list(df.columns) == ["time", "y", "z"]
    assert df["z"].tolist() == pytest.approx([0.0, 4.0, 16.0, 36.0, 64.0])


def test_reserved_ids_run(tmp_path: Path) -> None:
    """Ids which are python keywords or names of the code are renamed and run."""
    sbml = model_sbml("""
        compartment c = 1
        species np in c = 2; species p in c = 1
        lambda = 0.5; t_ = 2; XIDS = 1; f_dxdt = 3; initial_values = 0.1
        R1: np -> p; lambda * np * t_ * XIDS
        R2: p -> ; initial_values * f_dxdt * p
    """)
    module = assert_python_as_roadrunner(sbml, tmp_path)
    assert module.XIDS == ["np", "p"]
    assert {"lambda", "t_", "XIDS", "f_dxdt", "initial_values"} <= set(module.PIDS)


def test_reserved_id_simulate(tmp_path: Path) -> None:
    """An id `simulate` is renamed, the simulator runs.

    Not compared with roadrunner: a model with the id `simulate` replaces the method
    `RoadRunner.simulate` of every instance.
    """
    pytest.importorskip("scipy")
    sbml = model_sbml("species A = 1; R1: A -> ; simulate * A; simulate = 1")
    module = python_module(OdeSystem.from_sbml(sbml), tmp_path / "m.py")
    df = module.simulate(1.0, 2)
    assert df["A"].tolist() == pytest.approx([1.0, np.exp(-1.0)], rel=1e-6)


def test_negative_base_with_fractional_exponent_is_nan(tmp_path: Path) -> None:
    """A power of a negative state with a fractional exponent is nan, not complex."""
    sbml = model_sbml("""
        compartment c = 1; species A in c = -1
        y := A^0.5 + root(3, A)
        R1: A -> ; k * A^1.5
        k = 1
    """)
    module = python_module(OdeSystem.from_sbml(sbml), tmp_path / "m.py")
    x0, p = module.initial_values()
    with np.errstate(invalid="ignore"):
        assert np.isnan(module.f_dxdt(0.0, x0, p)).all()
        assert np.isnan(module.f_y(0.0, x0, p)).all()


@pytest.mark.filterwarnings("ignore:divide by zero:RuntimeWarning")
def test_time_is_a_numpy_scalar(tmp_path: Path) -> None:
    """Math of the time out of its domain is `inf`, not an error (case 01488).

    A function definition evaluates its arguments before its body, so the guard of
    the piecewise does not protect the division by the time at t = 0.
    """
    sbml = model_sbml("""
        function f(a)
            piecewise(0, a > 1e300, a)
        end
        y := f(1 / time)
    """)
    module = assert_python_as_roadrunner(sbml, tmp_path)
    x0, p = module.initial_values()
    assert module.f_y(0.0, x0, p).tolist() == [0.0]


def test_simulate_matches_roadrunner(tmp_path: Path) -> None:
    """The simulator integrates the repressilator as roadrunner."""
    roadrunner = pytest.importorskip("roadrunner")
    pytest.importorskip("scipy")
    sbml = REPRESSILATOR_SBML.read_text(encoding="utf-8")
    system = OdeSystem.from_sbml(sbml)
    module = python_module(system, tmp_path / "repressilator.py")
    df = module.simulate(T_END, T_STEPS, rtol=1e-10, atol=1e-12)
    assert list(df.columns) == ["time", *system.states, *system.assigned]

    r = roadrunner.RoadRunner(sbml)
    r.integrator.relative_tolerance = 1e-10
    r.integrator.absolute_tolerance = 1e-12
    columns = [*system.states, *system.assigned]
    quantities = {q.symbol.sid: q for q in system.quantities}
    selections = [
        selection(quantities[sid]) if sid in quantities else sid for sid in columns
    ]
    r.timeCourseSelections = ["time", *selections]
    result = r.simulate(0.0, T_END, T_STEPS)
    np.testing.assert_allclose(df["time"], result[:, 0], rtol=1e-12)
    for k, sid in enumerate(columns):
        np.testing.assert_allclose(
            df[sid], result[:, k + 1], rtol=1e-6, atol=1e-9, err_msg=sid
        )


def test_initial_values_keep_the_constants_passed(tmp_path: Path) -> None:
    """A constant with a default is not recomputed, a scan of it simulates."""
    roadrunner = pytest.importorskip("roadrunner")
    pytest.importorskip("scipy")
    sbml = model_sbml("compartment c; species A in c = 2; R1: A -> ; k*A; k = 1")
    module = python_module(OdeSystem.from_sbml(sbml), tmp_path / "scan.py")
    assert module.P0.tolist() == [1.0, 1.0]
    p = module.P0.copy()
    p[module.PIDS.index("c")] = 3.0
    assert module.initial_values(p)[1].tolist() == [3.0, 1.0]
    assert (
        "Every constant keeps the value passed." in (tmp_path / "scan.py").read_text()
    )
    df = module.simulate(T_END, T_STEPS, p=p, rtol=1e-10, atol=1e-12)

    r = roadrunner.RoadRunner(sbml)
    r.integrator.relative_tolerance = 1e-10
    r.integrator.absolute_tolerance = 1e-12
    r["init(c)"] = 3.0
    r.timeCourseSelections = ["time", "[A]"]
    result = r.simulate(0.0, T_END, T_STEPS)
    np.testing.assert_allclose(df["A"], result[:, 1], rtol=1e-6, atol=1e-9)
    # the concentration decays with k / c
    assert df["A"].iloc[-1] == pytest.approx(2.0 * np.exp(-T_END / 3.0), rel=1e-6)


def test_initial_values_list_the_computed_constants() -> None:
    """The docstring of `initial_values` names the constants it computes."""

    def initial_amount(model: libsbml.Model) -> None:
        species: libsbml.Species = model.getSpecies("B")
        species.setInitialAmount(4.0)

    sbml = edit_sbml(
        model_sbml("""
            compartment c = 2; species B in c = 1
            k = 2 * c; q = 1
        """),
        initial_amount,
    )
    code = OdeSystem.from_sbml(sbml).render("python", simulator=False)
    docstring = code.split("def initial_values")[1].split('"""')[1]
    assert "a value passed for them is replaced" in docstring
    lines = [line.split() for line in docstring.splitlines()]
    assert ["p[1]", "B", "converted", "with", "its", "compartment"] in lines
    assert ["p[2]", "k", "initial", "assignment"] in lines
    assert not [line for line in lines if "q" in line]


def test_simulate_from_x0_and_p(tmp_path: Path) -> None:
    """The simulator starts from the states and the constants passed."""
    pytest.importorskip("scipy")
    module = python_module(
        OdeSystem.from_sbml(model_sbml("species A = 2; R1: A -> ; k * A; k = 1")),
        tmp_path / "m.py",
    )
    p = module.P0.copy()
    p[module.PIDS.index("k")] = 2.0
    df = module.simulate(1.0, 3, p=p, x0=np.array([4.0]))
    assert list(df.columns) == ["time", "A", "R1"]
    assert df["A"].tolist() == pytest.approx(4.0 * np.exp(-2.0 * df["time"]), rel=1e-6)


def test_script_prints_the_simulation(tmp_path: Path) -> None:
    """The python file runs as a script and prints the head of the simulation."""
    pytest.importorskip("scipy")
    path = tmp_path / "model.py"
    OdeSystem.from_sbml(VDP_SBML).write(path)
    result = subprocess.run(
        [sys.executable, str(path)], capture_output=True, text=True, check=True
    )
    assert result.stdout.split()[:3] == ["time", "x", "y"]


# --- shape of the code ----------------------------------------------------------------


def test_rhs_only(tmp_path: Path) -> None:
    """`simulator=False` writes the right hand side without scipy and pandas."""
    code = OdeSystem.from_sbml(REPRESSILATOR_SBML).render("python", simulator=False)
    assert "scipy" not in code
    assert "pandas" not in code
    path = tmp_path / "rhs.py"
    path.write_text(code)
    module = import_module(path)
    assert not hasattr(module, "simulate")
    assert {"f_dxdt", "f_y", "initial_values", "P0", "XIDS"} <= set(vars(module))


def test_python_code_parses_and_names_are_reserved() -> None:
    """Every name the template writes, not an id of the model, is reserved."""
    system = OdeSystem.from_sbml(model_sbml(RULES))
    ids = [q.symbol.sid for q in system.quantities]
    ids += [r.symbol.sid for r in system.reactions]
    ids += [f.symbol.sid for f in system.functions]
    model_names = set(code_names(ids, "python").values())
    for simulator in (True, False):
        tree = ast.parse(system.render("python", simulator=simulator))
        written: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                written.add(node.id)
            elif isinstance(node, ast.arg):
                written.add(node.arg)
            elif isinstance(node, ast.FunctionDef):
                written.add(node.name)
            elif isinstance(node, ast.alias):
                written.add((node.asname or node.name).split(".")[0])
        # the names of the code, apart from the ids and the function arguments
        arguments = {"S", "km", "k", "n"}
        assert written - model_names - arguments <= RESERVED["python"]


@pytest.mark.skipif(
    importlib.util.find_spec("ruff") is None, reason="ruff is not installed"
)
@pytest.mark.parametrize("simulator", [True, False])
@pytest.mark.parametrize("model", ["repressilator", "rules"])
def test_python_code_passes_ruff(model: str, simulator: bool) -> None:
    """The generated python passes `ruff check` with the default rules."""
    if model == "repressilator":
        code = OdeSystem.from_sbml(REPRESSILATOR_SBML).render(
            "python", simulator=simulator
        )
    else:
        code = _code(RULES, simulator=simulator)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--no-cache",
            "--stdin-filename",
            "model.py",
            "-",
        ],
        input=code,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_python_layout() -> None:
    """The code reads as the model: named locals with their name and unit."""
    code = OdeSystem.from_sbml(REPRESSILATOR_SBML).render("python")
    lines = code.splitlines()
    assert lines[0].startswith('"""')
    assert f"sbmlutils {sbmlutils.__version__}" in code
    assert "BIOMD0000000012_urn.xml" in code
    # the states are unpacked one per line, with name and unit
    assert any(line.strip().startswith("PX = x[0]  # ") for line in lines)
    # one statement per line
    statements = [
        n.lineno for n in ast.walk(ast.parse(code)) if isinstance(n, ast.stmt)
    ]
    assert len(statements) == len(set(statements))
    # no trailing whitespace, no tabs, one newline at the end
    assert not [line for line in lines if line != line.rstrip()]
    assert "\t" not in code
    assert code.endswith("\n")
    assert not code.endswith("\n\n")
    assert "\n\n\n\n" not in code


def test_python_amount_state_is_named() -> None:
    """The amount of a species in a variable compartment reads as its amount."""
    code = _code(RULES)
    assert "n_A = x[1]  # amount of A" in code


def test_python_function_definitions() -> None:
    """A function definition is a python function, called by the math."""
    code = _code(RULES)
    assert "def mm(S, km):" in code
    assert "return S / (km + S)" in code
    assert "mm(A, km)" in code


def test_python_function_argument_reserved() -> None:
    """An argument of a function definition is renamed like an id."""
    code = _code("""
        function f(x, lambda)
            x * lambda
        end
        species A = 1; R1: A -> ; f(A, 2)
    """)
    assert "def f(x_, lambda_):" in code
    assert "return x_ * lambda_" in code


INJECTED_NAME = (
    "A&#10;INJECTED_LF = 1&#13;INJECTED_CR = 1&#13;&#10;INJECTED_CRLF = 1"
    "&#x2028;INJECTED_LS = 1&#x85;INJECTED_NEL = 1&#9;tab"
    " &quot;&quot;&quot; INJECTED_DOC = 1 \\ end\\"
)


def test_python_name_does_not_leave_comment(tmp_path: Path) -> None:
    """A line break or quotes in a name never leave the comment or the string."""
    sbml = sbml_with_rate("k*A", name=INJECTED_NAME)
    system = OdeSystem.from_sbml(sbml)
    code = system.render("python")
    for line in code.splitlines():
        if "INJECTED" in line and "#" in line:
            assert line.index("#") < line.index("INJECTED"), line
    tree = ast.parse(code)
    assigned = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert not {name for name in assigned if name.startswith("INJECTED")}
    path = tmp_path / "injected.py"
    path.write_text(code, encoding="utf-8")
    module = import_module(path)
    assert not [name for name in vars(module) if name.startswith("INJECTED")]
    name = module.NAMES["A"]
    assert '"""' in name
    assert name.endswith("\\")
    assert "\n" not in name


# --- the format layer -----------------------------------------------------------------


def test_formats() -> None:
    """The python format is registered with its suffix and options."""
    python = FORMATS["python"]
    assert isinstance(python, Format)
    assert python.kind == "code"
    assert python.suffixes == (".py",)
    assert python.options == {"simulator": True}


def test_unknown_format_and_option() -> None:
    """An unknown format, option or option value raises a `ValueError`."""
    system = OdeSystem.from_sbml(VDP_SBML)
    with pytest.raises(ValueError, match="format 'fortran'"):
        system.render("fortran")
    with pytest.raises(ValueError, match="option 'standalone'"):
        system.render("python", standalone=True)
    with pytest.raises(ValueError, match="simulator"):
        system.render("python", simulator="yes")


def test_unsupported_raises() -> None:
    """A model with an algebraic rule cannot be written as code."""
    sbml = model_sbml("x = 1; y = 2; 0 = x + y - 3")
    system = OdeSystem.from_sbml(sbml)
    assert system.unsupported
    with pytest.raises(NotImplementedError, match="algebraic rule"):
        system.render("python")


def test_events_raise() -> None:
    """The python code of events is written by a later version of the export."""
    system = OdeSystem.from_sbml(
        model_sbml("species A = 1; R1: A -> ; A; E1: at time > 1: A = 2")
    )
    for simulator in (True, False):
        with pytest.raises(NotImplementedError, match="event 'E1'"):
            system.render("python", simulator=simulator)
    # the rendering context holds the events already
    events = context(system, FORMATS["python"], {"simulator": True})["events"]
    assert isinstance(events, list)
    assert events[0]["id"] == "E1"
    assert events[0]["root"] == "t - 1"


def test_write_by_suffix(tmp_path: Path) -> None:
    """`write` takes the format from the suffix and returns the path."""
    system = OdeSystem.from_sbml(VDP_SBML)
    path = system.write(tmp_path / "vdp.py")
    assert path == tmp_path / "vdp.py"
    assert path.read_text(encoding="utf-8") == system.render("python")
    path = system.write(str(tmp_path / "vdp.txt"), fmt="python", simulator=False)
    assert path.read_text(encoding="utf-8") == render(system, "python", simulator=False)


def test_unknown_suffix(tmp_path: Path) -> None:
    """A suffix of no format raises without `fmt`."""
    system = OdeSystem.from_sbml(VDP_SBML)
    with pytest.raises(ValueError, match=r"\.txt"):
        system.write(tmp_path / "vdp.txt")
    with pytest.raises(ValueError, match=r"\.PY"):
        system.write(tmp_path / "vdp.PY")


def test_render_template(tmp_path: Path) -> None:
    """A template of the user is rendered with the context of a format."""
    template = tmp_path / "states.jinja"
    template.write_text(
        "{% for x in states %}{{ x.index }} {{ x.code }} {{ x.unit }}\n{% endfor %}"
    )
    system = OdeSystem.from_sbml(VDP_SBML)
    text = system.render_template(template)
    assert text.splitlines()[0].split()[:2] == ["0", "x_"]
    assert render_template(system, template) == text
    with pytest.raises(ValueError, match="option"):
        system.render_template(template, simulator=1)


def test_context_is_plain_data() -> None:
    """The context holds strings, numbers, booleans, lists and dicts only."""
    system = OdeSystem.from_sbml(model_sbml(RULES))
    data = context(system, FORMATS["python"], {"simulator": True})

    def check(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                check(item)
        elif isinstance(value, list | tuple):
            for item in value:
                check(item)
        else:
            assert value is None or isinstance(value, str | int | float | bool), value

    check(data)
    model = data["model"]
    assert isinstance(model, dict)
    assert model["sbmlutils"] == sbmlutils.__version__
    states = data["states"]
    assert isinstance(states, list)
    assert [x["index"] for x in states] == [0, 1, 2]
