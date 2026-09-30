"""Testing ODE factory."""

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

import libsbml
import pytest

from sbmlutils.converters.odefac import SBML2ODE
from sbmlutils.io import read_sbml
from sbmlutils.resources import (
    COMP_DEX_LIVER,
    COMP_SPT_LIVER,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    MODELS_DIR,
    REPRESSILATOR_SBML,
    VDP_SBML,
)

test_models = [
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
]

INTERPOLATION_LINEAR_SBML = MODELS_DIR / "interpolation" / "data1_linear.xml"

# a name which leaves a single-line comment if a line break is written into it,
# as character references in the SBML file (a literal line break in an attribute
# is read as a space)
INJECTED_NAME = (
    "A&#10;INJECTED_LF = 1&#13;INJECTED_CR = 1&#13;&#10;INJECTED_CRLF = 1"
    "&#x2028;INJECTED_LS = 1&#x85;INJECTED_NEL = 1&#9;tab"
)


@pytest.mark.parametrize("sbml_path", test_models)
def test_odefac_to_R(sbml_path: Path, tmp_path: Path) -> None:
    """Create R code for given model."""
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    sbml2ode = SBML2ODE(doc=doc)
    out_path = tmp_path / "model.R"
    sbml2ode.to_R(out_path)
    assert out_path.exists()


@pytest.mark.parametrize("sbml_path", test_models)
def test_odefac_to_python(sbml_path: Path, tmp_path: Path) -> None:
    """Create python code for given model."""
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    sbml2ode = SBML2ODE(doc=doc)
    out_path = tmp_path / "dallaman.py"
    sbml2ode.to_python(out_path)
    assert out_path.exists()


def _sbml(formula: str, name: str = "species A", sid: str = "A") -> str:
    """SBML of a model with one species which is consumed by one reaction.

    Args:
        formula: rate law of the reaction, an L3 infix formula
        name: name of the species, the compartment, the parameter and the reaction,
            in XML syntax
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
    law.setMath(libsbml.parseL3Formula(formula))
    sbml = str(libsbml.writeSBMLToString(doc))
    return sbml.replace('name="NAME"', f'name="{name}"')


def _import(path: Path) -> ModuleType:
    """Import the python module written to the given path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_python_name_does_not_leave_comment(tmp_path: Path) -> None:
    """A line break in a name is written into a comment, never into the code."""
    doc = read_sbml(_sbml("k*A", name=INJECTED_NAME))
    code = SBML2ODE(doc).to_python()

    # every line with injected text is a comment line
    for line in code.splitlines():
        if "INJECTED" in line:
            assert "#" in line and line.index("#") < line.index("INJECTED"), line

    # the module holds only the statements of the template
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
    module = _import(path)
    assert not [name for name in vars(module) if name.startswith("INJECTED")]


@pytest.mark.parametrize("language", ["R", "julia", "markdown", "tex"])
def test_name_does_not_leave_line(language: str) -> None:
    """A line break in a name is removed from the output of every language."""
    doc = read_sbml(_sbml("k*A", name=INJECTED_NAME))
    sbml2ode = SBML2ODE(doc)
    code = {
        "R": sbml2ode.to_R,
        "julia": sbml2ode.to_julia,
        "markdown": sbml2ode.to_markdown,
        "tex": sbml2ode.to_tex,
    }[language]()
    for line in code.splitlines():
        # the injected text never starts a line of its own
        assert not line.lstrip().startswith("INJECTED"), line
    for separator in ("\r", "\x85", "\u2028"):
        assert separator not in code


@pytest.mark.parametrize("language", ["python", "R", "julia"])
def test_invalid_sid_is_rejected(language: str) -> None:
    """An id which is no SId is never written into code."""
    doc = read_sbml(_sbml("k", sid="A = 1\nimport os\nB"))
    sbml2ode = SBML2ODE(doc)
    convert = {
        "python": sbml2ode.to_python,
        "R": sbml2ode.to_R,
        "julia": sbml2ode.to_julia,
    }[language]
    with pytest.raises(ValueError, match="SId"):
        convert()


@pytest.mark.parametrize("language", ["python", "R", "julia"])
def test_invalid_sid_in_math_is_rejected(language: str) -> None:
    """A MathML identifier which is no SId is never written into code."""
    sbml = _sbml("k*A").replace("<ci> k </ci>", "<ci> k + __import__('os') </ci>")
    sbml2ode = SBML2ODE(read_sbml(sbml))
    convert = {
        "python": sbml2ode.to_python,
        "R": sbml2ode.to_R,
        "julia": sbml2ode.to_julia,
    }[language]
    with pytest.raises(ValueError, match="SId"):
        convert()


# rate laws of the reaction of `_sbml` in L3 infix syntax
FORMULAS = [
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


def _assert_rates_as_roadrunner(sbml: str, path: Path) -> None:
    """Assert that the generated python returns the rates of roadrunner.

    The rates of change and the assigned variables are compared at the initial
    state and at a second state, in which every state variable is changed, so that
    no value is zero by chance.
    """
    roadrunner = pytest.importorskip("roadrunner")
    SBML2ODE(read_sbml(sbml)).to_python(py_file=path)
    module = _import(path)
    assert len(module.f_y(module.x0, 0.0, module.p)) == len(module.yids)

    r = roadrunner.RoadRunner(sbml)
    model: libsbml.Model = libsbml.readSBMLFromString(sbml).getModel()
    floating = set(r.model.getFloatingSpeciesIds())
    rate_rules = set(r.model.getRateRuleSymbols())

    def selection(sid: str) -> str:
        """Roadrunner selection of the state variable as the python holds it."""
        species: libsbml.Species | None = model.getSpecies(sid)
        if species and not species.getHasOnlySubstanceUnits():
            return f"[{sid}]"
        return sid

    xids = [sid for sid in module.xids if sid in floating | rate_rules]
    assert xids or module.yids
    for x in [module.x0, module.x0 * 1.5 + 0.1]:
        # boundary species are state variables of the python as well
        for k, sid in enumerate(module.xids):
            r[selection(sid)] = x[k]
        rates = dict(zip(module.xids, module.f_dxdt(x, 0.0, module.p), strict=True))
        for sid in xids:
            expected = r[f"{selection(sid)}'"]
            assert rates[sid] == pytest.approx(expected, rel=1e-8, abs=1e-12), sid
        y = dict(zip(module.yids, module.f_y(x, 0.0, module.p), strict=True))
        for sid, value in y.items():
            expected = r[selection(sid)]
            assert value == pytest.approx(expected, rel=1e-8, abs=1e-12), sid


@pytest.mark.parametrize("formula", FORMULAS)
def test_python_formula(formula: str, tmp_path: Path) -> None:
    """The generated python evaluates every construct of the math as roadrunner."""
    _assert_rates_as_roadrunner(_sbml(formula), tmp_path / "formula.py")


@pytest.mark.parametrize(
    "sbml_path",
    [
        DEMO_SBML,
        REPRESSILATOR_SBML,
        VDP_SBML,
        COMP_DEX_LIVER,
        COMP_SPT_LIVER,
        INTERPOLATION_LINEAR_SBML,
    ],
    ids=lambda p: p.stem,
)
def test_python_model(sbml_path: Path, tmp_path: Path) -> None:
    """The generated python of a model runs and returns the rates of roadrunner."""
    sbml = sbml_path.read_text(encoding="utf-8")
    _assert_rates_as_roadrunner(sbml, tmp_path / "model.py")


def test_python_model_with_initial_assignments(tmp_path: Path) -> None:
    """The generated python of a model with initial assignments imports and runs."""
    path = tmp_path / "model.py"
    SBML2ODE.from_file(GALACTOSE_SINGLECELL_SBML).to_python(py_file=path)
    module = _import(path)
    dxdt = module.f_dxdt(module.x0, 0.0, module.p)
    assert len(dxdt) == len(module.xids)
