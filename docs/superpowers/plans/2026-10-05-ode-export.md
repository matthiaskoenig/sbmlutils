# ODE export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `sbmlutils.converters.odefac` with `sbmlutils.converters.ode`, which exports the ODE system of an SBML model as python, julia, R, typst, LaTeX and markdown from one analysis and one math printer core, with full SBML core semantics including events, verified against roadrunner.

**Architecture:** Three layers. `system.py` resolves the SBML semantics into a frozen `OdeSystem` dataclass tree whose math stays libsbml `ASTNode`. `printers/` turn an `ASTNode` into a string, one dialect per language on a shared precedence engine. `formats.py` and jinja2 templates in `resources/converters/ode/` render an `OdeSystem` into a file; templates see only plain strings and lists.

**Tech Stack:** python >= 3.11, python-libsbml, jinja2, numpy, scipy (generated python only), roadrunner (tests only), typst (python package, tests), julia + DifferentialEquations.jl + DataFrames.jl, R + deSolve, tectonic (LaTeX, CI).

**Spec:** `docs/superpowers/specs/2026-10-05-ode-export-design.md`. Read it before every task; this plan argues from it.

## Global Constraints

- Follow `CLAUDE.md` of the repository and `/home/mkoenig/CLAUDE.md`: no em dash character anywhere, no agent attribution in commits, code or docs, markdown without hard line wraps, google style docstrings, full type annotations, lazy `%s` logging, no `print` in library code.
- ty must stay at zero diagnostics (`uv run ty check`), ruff clean (`uv run ruff check && uv run ruff format --check`). Suppress only with `# ty: ignore[rule]`.
- Annotate libsbml objects explicitly, use getters (`getVariable()`), never SWIG attributes.
- Commit messages: imperative sentence, no prefix convention needed, no `Co-Authored-By`.
- Run tests quiet: `uv run pytest -q -x <path>`.
- Free text (names, notes, units) is never written raw: `single_line` in code comments, format escaping in documents. Every id written into code passes `check_sid`.
- Identifiers in math come only from a symbol mapping; an unmapped identifier raises `NotImplementedError`.
- Numerical tolerances vs roadrunner: point checks `rel=1e-8, abs=1e-12`; trajectories `rtol=1e-6, atol=1e-9` (relax to the `test_roundtrip.py` values `rtol=1e-4, atol=1e-6` only for cases with events, and record that in the test).
- Uniform timecourse for test suite cases: `T_END = 10.0`, `T_STEPS = 51`, as `tests/test_roundtrip.py`.
- Julia and R are executed through a command prefix: env var `SBMLUTILS_JULIA` (default `julia`) and `SBMLUTILS_RSCRIPT` (default `Rscript`), split with `shlex.split`. Tests skip when the command is not runnable. Locally the toolchains are missing; use docker: `SBMLUTILS_JULIA="docker run --rm -v /tmp:/tmp -v $HOME/.julia-docker:/root/.julia julia:1.11 julia"` and `SBMLUTILS_RSCRIPT="docker run --rm -v /tmp:/tmp sbmlutils-r Rscript"` (image built in Task 9). The test writes into pytest `tmp_path`, which is under `/tmp`.

## Review Focus

1. An id that is a keyword or builtin of the target language (`lambda`, `end`, `function`, `T`, `pi`, `t`, `p`, `x`) must produce working code, not a syntax error or a silent shadowing of `t`/`pi`. Pinned in Task 4 (`test_reserved_ids_are_renamed`) and Task 6/8/9 (generated code with such ids runs).
2. A model with no species, no reactions or no parameters (only rate rules on parameters, or only assignment rules) must render in every format, with empty vectors that still type check in each language. Pinned in Task 6 (`test_python_model_without_states`) and Tasks 8, 9, 10.
3. An event firing at t=0 (`initialValue=false` with a trigger true at t=0) and two simultaneous events with priorities must follow roadrunner. Pinned in Task 7 (`test_event_at_t0`, `test_event_priority`).
4. Species in concentration in a compartment whose size changes by a rate rule or an event must keep the amount consistent. Pinned in Task 5 (`test_variable_compartment_ode`) and Task 7 (`test_event_changes_compartment`).
5. Names and notes with markup characters of the target document (`$`, `#`, `_`, `|`, `\`, `<script>`) must appear as text, never as markup. Pinned in Task 10 (`test_markup_in_names_is_text`).

---

## File Structure

```
src/sbmlutils/converters/ode/
    __init__.py         re-exports OdeSystem, FORMATS, NotSupportedError helpers
    text.py             single_line, tex_text, typst_text, markdown_text, check_sid
    printers/
        __init__.py     PRINTERS registry {"python": PythonPrinter, ...}
        base.py         MathPrinter, Precedence, SymbolMap type
        python.py       PythonPrinter
        julia.py        JuliaPrinter
        r.py            RPrinter
        latex.py        LatexPrinter
        typst.py        TypstPrinter
    symbols.py          code_names(system, language) and typeset_symbol(id, dialect)
    system.py           dataclasses + OdeSystem.from_sbml
    dependencies.py     order_assignments(...) with graphlib
    events.py           root function ASTs from trigger ASTs
    formats.py          Format, FORMATS, render, write, render_template
src/sbmlutils/resources/converters/ode/
    python.py.jinja  julia.jl.jinja  r.R.jinja
    typst.typ.jinja  latex.tex.jinja  markdown.md.jinja
tests/converters/ode/
    __init__.py
    conftest.py         helpers: sbml builders, roadrunner reference, toolchain runners
    test_text.py  test_printers.py  test_symbols.py  test_system.py
    test_python.py  test_julia.py  test_r.py  test_presentation.py  test_safety.py
    test_testsuite.py   curated subset + sbml_testsuite sweep
    golden/             expected outputs of the demo model
scripts/ode_report.py
docs/ode.md  docs/api/converters.ode.md
examples/converters/ode.py
```

Removed at the end (Task 12): `src/sbmlutils/converters/odefac.py`, `src/sbmlutils/converters/mathml.py` if unused, `src/sbmlutils/resources/converters/odefac_template.*`, `tests/converters/test_odefac.py`, `examples/converters/odefac.py`, `docs/api/converters.odefac.md`.

---

### Task 1: Text helpers and the printer engine with the python dialect

**Files:**
- Create: `src/sbmlutils/converters/ode/__init__.py`, `text.py`, `printers/__init__.py`, `printers/base.py`, `printers/python.py`
- Test: `tests/converters/ode/__init__.py` (empty), `tests/converters/ode/test_text.py`, `tests/converters/ode/test_printers.py`, `tests/converters/ode/conftest.py`

**Interfaces:**
- Produces:
  - `text.single_line(value: object) -> str`, `text.tex_text(value: object) -> str` (moved verbatim from `odefac.py`), `text.check_sid(sid: str) -> str`, `text.check_math_sids(ast: libsbml.ASTNode) -> None`.
  - `printers.base.SymbolMap = Mapping[str, str]`.
  - `class MathPrinter` with `def print(self, ast: libsbml.ASTNode, symbols: SymbolMap) -> str` and `def print_condition(self, ast, symbols) -> str` (boolean context). Subclasses set class tables and override `_node_*` hooks.
  - `class PythonPrinter(MathPrinter)` whose output equals today's `odefac.python_math` for every formula of `FORMULAS` in `tests/converters/test_odefac.py`, plus: `rateOf`/`delay` raise `NotImplementedError`; a user function call `f(a, b)` prints as `f(a, b)` with `f` looked up in `symbols` (function ids are part of the symbol map).
  - `printers.PRINTERS: dict[str, type[MathPrinter]]`.
  - `conftest.sbml_with_rate(formula: str, name: str = "species A", sid: str = "A") -> str` (port `_sbml` from `test_odefac.py`) and `conftest.import_module(path: Path) -> ModuleType`.

Design of `base.py`: a recursive `_print(ast, ctx) -> tuple[str, int]` returning code and precedence. Precedence constants as an `IntEnum` `Precedence` (CONDITIONAL=1, OR=2, AND=3, NOT=4, COMPARISON=5, XOR=6, SUM=7, PRODUCT=8, UNARY=9, POWER=10, ATOM=11). The engine handles: numbers (`AST_INTEGER`, `AST_REAL`, `AST_REAL_E`, `AST_RATIONAL`, `AST_NAME_AVOGADRO`), constants, names via `symbols`, `AST_FUNCTION` (user function) via `symbols`, n-ary plus/times with 0 and 1 children, unary/binary minus, divide, power (right associative, binds tighter than unary minus on its left), relations with n operands chained as `a < b and b < c`, logic, piecewise, and table driven unary functions. Each dialect supplies: `FUNCTIONS: dict[int, str]` (direct), `CONSTANTS: dict[int, str]`, `number(value: float) -> str`, and hooks `power`, `piecewise`, `rem`, `quotient`, `log`, `root`, `factorial`, `reciprocal` (sec, csc, cot, sech, csch, coth), `of_reciprocal` (arcsec, ...), `minmax`, `logic_and/or/xor/not/implies`, `relation`, `bool_to_number`. Unknown types raise `NotImplementedError(f"The math '{libsbml.formulaToL3String(ast)}' is not supported by the {self.name} printer.")`.

- [ ] **Step 1: Write failing tests**

`tests/converters/ode/test_text.py`: port `single_line`/`tex_text` behaviour (line breaks `\n \r   \u0085 \t` become spaces; `tex_text("a_b$")` is `a\_b\$`), `check_sid("1a")` raises `ValueError`, `check_math_sids(parseL3Formula("a + b"))` passes.

`tests/converters/ode/test_printers.py`:

```python
import libsbml
import pytest

from sbmlutils.converters.ode.printers import PRINTERS
from sbmlutils.converters.ode.printers.python import PythonPrinter

SYMBOLS = {"A": "A", "k": "k", "f": "f"}


def py(formula: str) -> str:
    ast = libsbml.parseL3Formula(formula)
    assert ast is not None, libsbml.getLastParseL3Error()
    return PythonPrinter().print(ast, SYMBOLS)


@pytest.mark.parametrize(
    "formula, expected",
    [
        ("k*A", "k * A"),
        ("-A^2", "-A ** 2"),
        ("(-2)^2", "(-2) ** 2"),
        ("2^3^2", "2 ** 3 ** 2"),
        ("A - (k - 1)", "A - (k - 1)"),
        ("A/(k*2)", "A / (k * 2)"),
        ("log(2, A)", "np.log(A) / np.log(2)"),
        ("rem(A, 2)", "np.fmod(A, 2)"),
        ("piecewise(k, A > 1, 0)", "k if A > 1 else 0"),
        ("A > 1", "float(A > 1)"),
        ("f(A, k)", "f(A, k)"),
        ("time", "t"),
    ],
)
def test_python_golden(formula: str, expected: str) -> None:
    assert py(formula) == expected


def test_unmapped_identifier_raises() -> None:
    with pytest.raises(NotImplementedError, match="'B'"):
        py("B + 1")


@pytest.mark.parametrize("formula", ["rateOf(A)", "delay(A, 1)"])
def test_python_unsupported(formula: str) -> None:
    with pytest.raises(NotImplementedError):
        py(formula)


def test_registry() -> None:
    assert PRINTERS["python"] is PythonPrinter
```

Note: today's `python_math` wraps a relation used as a number in `bool(...)`. Change it to `float(...)` so a boolean is a number in arithmetic (`(A != 2) + 1`); keep `bool(...)` around `and`/`or` used as a number replaced by `float(...)` too. Port the full `FORMULAS` roadrunner comparison into Task 6, not here.

- [ ] **Step 2: Run** `uv run pytest -q -x tests/converters/ode` and see the import errors.
- [ ] **Step 3: Implement** `text.py` (move code from `odefac.py`, do not delete `odefac.py` yet), `printers/base.py`, `printers/python.py` (port tables `_PYTHON_FUNCTIONS`, `_PYTHON_RECIPROCALS`, `_PYTHON_OF_RECIPROCALS`, `_PYTHON_RELATIONALS` and the logic of `_python_math` into the engine plus dialect), `printers/__init__.py`, `ode/__init__.py` (empty `__all__` for now).
- [ ] **Step 4: Run** tests, ruff, ty. All pass.
- [ ] **Step 5: Commit** `Add the math printer engine and its python dialect`.

---

### Task 2: Julia and R dialects

**Files:**
- Create: `src/sbmlutils/converters/ode/printers/julia.py`, `printers/r.py`
- Modify: `printers/__init__.py` (register `"julia"`, `"r"`)
- Test: `tests/converters/ode/test_printers.py` (extend), `tests/converters/ode/conftest.py` (toolchain runners)

**Interfaces:**
- Consumes: `MathPrinter`, `Precedence`, `SymbolMap` from Task 1.
- Produces: `JuliaPrinter`, `RPrinter`; `conftest.julia_command() -> list[str] | None`, `conftest.rscript_command() -> list[str] | None` (from env vars of the Global Constraints, `None` if `[*cmd, "--version"]` fails), `conftest.run_julia(code: str, tmp_path: Path) -> str` and `conftest.run_r(code: str, tmp_path: Path) -> str` (write the script into `tmp_path`, run it, return stdout, raise with stderr on failure).

Dialect rules (from the spec table): julia `^`, `x ? a : b`, `rem`, `div(a, b)` for quotient as float `trunc(a / b)`, `log(b, x)`, `sqrt`, `cbrt` not needed, `x^(1/n)` for root, `gamma(x + 1)` needs SpecialFunctions, so print factorial as `factorial(x)` only for integer literals and `exp(loggamma(x + 1))`... keep it simple: `gamma(x + 1)` and the template imports `SpecialFunctions`; booleans `Float64(c)`; `&&`, `||`, `!`, `xor(a, b)`; `Inf`, `NaN`, `pi`, `exp(1)`; `max`, `min`. R: `^`, `if (c) a else b` (scalar, lazy), rem as `a - b * trunc(a / b)`, `trunc(a / b)`, `log(x, b)`, `sqrt`, `gamma(x + 1)`, `as.numeric(c)`, `&&`, `||`, `!`, `xor(a, b)`, `Inf`, `NaN`, `pi`, `exp(1)`, `max`, `min`. Numbers: julia `1.0e-5` style with `repr(float)` rules (`inf` -> `Inf`), R likewise.

- [ ] **Step 1: Write failing tests**: golden strings per dialect for the same formulas as Task 1 (`-A^2` is `-A ^ 2` in julia and R, `(-2)^2` keeps parentheses, `piecewise(k, A > 1, 0)` is `A > 1 ? k : 0` in julia and `if (A > 1) k else 0` in R, `log(2, A)` is `log(2, A)` julia and `log(A, 2)` R, `rem(-7, 2)` R is `-7 - 2 * trunc(-7 / 2)`). An evaluation test parametrized over the `FORMULAS` list of `tests/converters/test_odefac.py` (copy the list into `conftest.FORMULAS`) which, for each dialect with a runnable toolchain, prints the formula with `A=3.0, k=0.5` bound as variables, runs it and compares with the python value of `PythonPrinter` evaluated by `eval` with `np`, `math` in scope (`pytest.approx(rel=1e-12)`). Skips when the toolchain is missing.
- [ ] **Step 2: Run** and see failures.
- [ ] **Step 3: Implement** both dialects.
- [ ] **Step 4: Run** golden tests locally; run the evaluation tests once with the docker commands of the Global Constraints (pull `julia:1.11`; for R build the image of Task 9 early if needed, `docker build -t sbmlutils-r -f tests/converters/ode/docker/r.Dockerfile tests/converters/ode/docker` with `FROM rocker/r-ver:4.4` and `RUN Rscript -e 'install.packages("deSolve")'`).
- [ ] **Step 5: Commit** `Add the julia and R dialects of the math printer`.

---

### Task 3: LaTeX and typst dialects

**Files:**
- Create: `printers/latex.py`, `printers/typst.py`
- Modify: `printers/__init__.py` (register `"latex"`, `"typst"`)
- Test: `tests/converters/ode/test_printers.py` (extend)

**Interfaces:**
- Produces: `LatexPrinter`, `TypstPrinter` with the same `print(ast, symbols)`; symbols map to already typeset strings (Task 4 builds them). Extra method `print_lines(ast, symbols, width: int = 4) -> list[str]`: for a top level `AST_PLUS`/`AST_MINUS` with more than `width` terms, split into chunks of `width` terms, each line beginning with its sign; otherwise one line.

Rules: LaTeX product `a \cdot b`, division `\frac{a}{b}` (no parentheses needed inside), power `{a}^{b}` with base parenthesized below ATOM, `\sqrt{x}`, `\sqrt[n]{x}`, `\log_{b}\left(x\right)`, `\ln`, `\exp`, functions `\sin`, `\operatorname{rem}\left(a, b\right)`, `\operatorname{quotient}`, `\max`, `\min`, `\left| x \right|`, `\lfloor x \rfloor`, `\lceil x \rceil`, `x!`, relations `<, \leq, >, \geq, =, \neq`, logic `\land \lor \lnot \oplus \Rightarrow`, piecewise `\begin{cases} a & \text{if } c \\ b & \text{otherwise} \end{cases}`, `\pi`, `e`, `\infty`, `\mathrm{NaN}`, `t`, `N_A`, booleans `\mathrm{true}`. Parentheses `\left( \right)`. Typst: product `a dot b`, division `(a)/(b)` (typst fraction, parenthesize operands that are not atoms), power `a^(b)`, `sqrt(x)`, `root(n, x)`, `log_(b) (x)`, `ln(x)`, `exp(x)`, `sin(x)`, `op("rem")(a, b)`, `op("quotient")(a, b)`, `max(...)`, `min(...)`, `abs(x)`, `floor(x)`, `ceil(x)`, `x!`, relations `< <= > >= = !=`, logic `and or not xor` as `" and "` text operators via `space "and" space`, piecewise `cases(a & "if" c, b & "otherwise")`, `pi`, `e`, `infinity`, `"NaN"`, `t`, `N_A`.

- [ ] **Step 1: Write failing tests**: golden strings, e.g. LaTeX `k*A/(1+A)` is `\frac{k \cdot A}{1 + A}`, typst `(k dot A)/(1 + A)`; `log(2, A)` LaTeX `\log_{2}\left(A\right)` typst `log_(2) (A)`; piecewise both; `print_lines` on `a+b+c+d+e+f` with width 4 gives 2 lines. A typst compile test: wrap every typst golden output in `$ ... $` inside one document and compile it with the `typst` python package (`typst.compile(path)`), skip if `typst` is not importable. Add `typst>=0.13` to the `dev` extra in `pyproject.toml` and run `uv lock`.
- [ ] **Step 2: Run** and fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** tests, ruff, ty.
- [ ] **Step 5: Commit** `Add the LaTeX and typst dialects of the math printer`.

---

### Task 4: Symbols and names per format

**Files:**
- Create: `src/sbmlutils/converters/ode/symbols.py`
- Test: `tests/converters/ode/test_symbols.py`

**Interfaces:**
- Produces:
  - `RESERVED: dict[str, frozenset[str]]` for `"python"`, `"julia"`, `"r"`: keywords, builtins and the names the generated code uses (`t`, `x`, `p`, `dx`, `y`, `np`, `pd`, `math`, `scipy`, `float`, `max`, `min`, `abs`, `pi`, `e`, `Inf`, `NaN`, `T`, `F`, `TRUE`, `FALSE`, `c`, `list`, `function`, `end`, `begin`, `module`, `rem`, `div`, `log`, `exp`, `gamma`, `xor`, ...; collect them by reading the dialect tables).
  - `code_names(ids: Iterable[str], language: str) -> dict[str, str]`: identity except for a reserved id or a clash, which gets `_` appended until unique; deterministic in input order.
  - `typeset_symbol(sid: str, dialect: Literal["latex", "typst"]) -> str`: base before the first `_`, subscript after; base of one letter italic, more letters upright (`\mathrm{Glc}` / `upright("Glc")`); subscript upright text with underscores kept (`k_{\mathrm{cat\_glc}}` / `k_("cat_glc")`); digits and letters only, so the id is an SId and needs no further escaping except `_` in LaTeX text.
  - `typeset_names(ids: Iterable[str], dialect, names: Mapping[str, str] | None = None) -> dict[str, str]`: with `names`, use the name when it matches `^[A-Za-z][A-Za-z0-9_]*$`, else the id.

- [ ] **Step 1: Write failing tests**: `test_reserved_ids_are_renamed` (`code_names(["lambda", "t", "lambda_"], "python") == {"lambda": "lambda__", "t": "t_", "lambda_": "lambda_"}`: note the clash with an existing id), julia `end` -> `end_`, R `T` -> `T_`; typeset golden: `k_cat_glc` LaTeX `k_{\mathrm{cat\_glc}}`, typst `k_("cat_glc")`; `Glc` LaTeX `\mathrm{Glc}`, typst `upright("Glc")`; `A` stays `A`.
- [ ] **Step 2: Run** and fail. **Step 3: Implement.** **Step 4: Run.**
- [ ] **Step 5: Commit** `Add the naming of symbols per output format`.

---

### Task 5: Analysis: the OdeSystem

**Files:**
- Create: `src/sbmlutils/converters/ode/system.py`, `dependencies.py`, `events.py`
- Test: `tests/converters/ode/test_system.py`, extend `conftest.py` with `model_sbml(antimony: str) -> str` built with `sbmlutils.parser.antimony_to_sbml` (antimony makes compact test models).

**Interfaces:**
- Produces (all `@dataclass(frozen=True)`; `ast` fields are `libsbml.ASTNode` owned by the system, deep copied from the document so the document can be freed):

```python
Kind = Literal["compartment", "species", "parameter", "reaction", "species_reference"]


@dataclass(frozen=True)
class Symbol:
    sid: str
    name: str | None
    unit: str | None
    sbo: str | None
    kind: Kind


@dataclass(frozen=True)
class Quantity:  # compartment, species, parameter, species reference
    symbol: Symbol
    value: float | None
    constant: bool
    role: Literal["constant", "state", "assigned"]
    compartment: str | None = None  # species only
    amount: bool | None = None  # species: True if hasOnlySubstanceUnits
    boundary: bool | None = None
    conversion_factor: str | None = None


@dataclass(frozen=True)
class FunctionDefinition:
    symbol: Symbol
    arguments: tuple[str, ...]
    body: libsbml.ASTNode


@dataclass(frozen=True)
class Assignment:  # assignment rule, initial assignment, reaction rate
    variable: str
    math: libsbml.ASTNode
    origin: Literal[
        "assignment_rule", "initial_assignment", "reaction", "initial_value"
    ]


@dataclass(frozen=True)
class Participant:
    species: str
    stoichiometry: float | str  # number or species reference id


@dataclass(frozen=True)
class Reaction:
    symbol: Symbol
    reactants: tuple[Participant, ...]
    products: tuple[Participant, ...]
    modifiers: tuple[str, ...]
    reversible: bool
    rate: libsbml.ASTNode  # local parameters already renamed
    local_parameters: tuple[str, ...]  # renamed ids, also in OdeSystem.parameters


@dataclass(frozen=True)
class Ode:
    variable: str
    rhs: libsbml.ASTNode  # complete right hand side of the state
    origin: Literal["reactions", "rate_rule"]
    reaction_terms: (
        libsbml.ASTNode | None
    )  # sum of stoichiometry * conversion factor * rate, before the volume
    volume: str | None  # compartment the terms are divided by
    variable_volume: bool  # the dV/dt correction is part of rhs


@dataclass(frozen=True)
class EventAssignment:
    variable: str
    math: libsbml.ASTNode


@dataclass(frozen=True)
class Event:
    symbol: Symbol
    trigger: libsbml.ASTNode
    root: libsbml.ASTNode  # continuous root function, events.trigger_root
    initial_value: bool
    persistent: bool
    delay: libsbml.ASTNode | None
    priority: libsbml.ASTNode | None
    use_values_from_trigger_time: bool
    assignments: tuple[EventAssignment, ...]


@dataclass(frozen=True)
class ModelInfo:
    sid: str | None
    name: str | None
    level: int
    version: int
    notes: str | None  # plain text
    units: Mapping[str, str | None]  # time, substance, extent, volume, area, length
    source: str | None  # file name if read from a path


@dataclass(frozen=True)
class OdeSystem:
    info: ModelInfo
    compartments: tuple[Quantity, ...]
    species: tuple[Quantity, ...]
    parameters: tuple[Quantity, ...]  # global and renamed local parameters
    species_references: tuple[Quantity, ...]
    functions: tuple[FunctionDefinition, ...]
    assignments: tuple[
        Assignment, ...
    ]  # assignment rules and reaction rates, dependency order
    initial: tuple[
        Assignment, ...
    ]  # t=0 evaluation order: values, initial assignments, rules
    reactions: tuple[Reaction, ...]
    odes: tuple[Ode, ...]  # document order of the states
    events: tuple[Event, ...]
    unsupported: tuple[tuple[str, str], ...]

    @classmethod
    def from_sbml(cls, source: Path | str | libsbml.SBMLDocument) -> OdeSystem: ...
    @property
    def states(self) -> tuple[str, ...]: ...  # ids of the odes, in order
    @property
    def constants(
        self,
    ) -> tuple[
        str, ...
    ]: ...  # role == "constant", document order: compartments, species, parameters, species references
    @property
    def assigned(
        self,
    ) -> tuple[
        str, ...
    ]: ...  # assignment rule variables then reaction ids, dependency order
    def quantity(self, sid: str) -> Quantity: ...
    def symbol(self, sid: str) -> Symbol: ...
```

- `dependencies.order(items: Sequence[tuple[str, libsbml.ASTNode | None]], known: set[str]) -> list[str]`: topological order with `graphlib.TopologicalSorter`, edges to ids not in `items` ignored, ties in input order (use `static_order` on a sorter fed in input order and stable-sort by first ready; simplest: Kahn's algorithm by hand iterating the input list), `ValueError("The assignments of ['a', 'b'] depend on each other in a cycle.")`.
- `events.trigger_root(trigger: libsbml.ASTNode) -> libsbml.ASTNode`: relation `a > b`, `a >= b` -> `a - b`; `a < b`, `a <= b` -> `b - a`; `a == b` -> unsupported (raise `NotImplementedError`), `&&` -> `min(...)`, `||` -> `max(...)`, `!x` -> `-root(x)`, `true` -> `1`, `false` -> `-1`, a relation of more than two operands -> `min` of the pairwise roots; anything else (e.g. a boolean variable) raises `NotImplementedError`, which `from_sbml` turns into an `unsupported` entry `("event trigger", event id)`.

Semantics to implement in `from_sbml` (spec, "Layer 1"): read with `read_sbml`; a document with the comp package and submodels is flattened with `flatten_sbml_doc` first; the fbc and distrib content is ignored with an `unsupported` entry only when it changes the dynamics (distrib uncertainty functions in math: `("distrib function", id)`). Expand nothing: function definitions stay calls. `rateOf(x)`: replace by a copy of the rhs of `x` if `x` is a state, by `0` if constant, else `unsupported ("rateOf of an assigned variable", element id)`. `delay(...)`: `unsupported ("delay", element id)`. Algebraic rules, fast reactions: `unsupported`. Species reference with id and rate rule or initial assignment: a `Quantity` of kind `species_reference`. Species in concentration: ODE `reaction_terms / V`; if `V` is a state, `rhs = (reaction_terms - S * rhs_V) / V` with `variable_volume=True`. Species in concentration with a rate rule: rhs is the rate rule as written. Species reference stoichiometry with an assignment rule or a rate rule: use the id as stoichiometry. Initial values: a species with `initialAmount` and not `hasOnlySubstanceUnits` becomes `Assignment(sid, parse("amount / V"), "initial_value")` so a compartment set by an initial assignment is honoured; numbers stay numbers in `Quantity.value` when no conversion is needed. The `initial` tuple holds every quantity that needs computing at t=0 (states, constants whose value comes from an initial assignment, assigned variables), ordered by `dependencies.order`.

- [ ] **Step 1: Write failing tests** in `test_system.py`, one per rule, built from antimony, e.g.:

```python
from sbmlutils.converters.ode.system import OdeSystem
from tests.converters.ode.conftest import model_sbml


def formula(ast) -> str:
    return libsbml.formulaToL3String(ast)


def test_reaction_ode_in_concentration() -> None:
    system = OdeSystem.from_sbml(
        model_sbml("""
        compartment c = 2; species S1 in c = 10; species S2 in c = 0
        J0: S1 -> 2 S2; k*S1; k = 0.1
    """)
    )
    assert system.states == ("S1", "S2")
    ode = {o.variable: o for o in system.odes}
    assert formula(ode["S2"].rhs) == "2 * J0 / c"
    assert ode["S1"].volume == "c"


def test_variable_compartment_ode() -> None:
    system = OdeSystem.from_sbml(
        model_sbml("""
        compartment c = 2; c' = 0.1; species S in c = 10
        J0: S -> ; k*S; k = 0.1
    """)
    )
    ode = {o.variable: o for o in system.odes}
    assert ode["S"].variable_volume
    assert formula(ode["S"].rhs) == "(-J0 - S * 0.1) / c"


def test_local_parameter_is_renamed() -> None: ...  # J0_k, unique against a global J0_k
def test_conversion_factor() -> None: ...  # species and model factor
def test_stoichiometry_math() -> None: ...  # species reference with assignment rule
def test_rate_rule_on_parameter_and_species() -> None: ...
def test_rateof_of_state_and_constant() -> None: ...
def test_assignment_order_and_cycle() -> None: ...
def test_initial_assignment_depends_on_rule() -> None: ...  # issue 438
def test_initial_amount_with_compartment_from_initial_assignment() -> None: ...
def test_unsupported_constructs_are_collected() -> (
    None
): ...  # algebraic rule, delay, fast
def test_event_fields_and_root() -> None: ...
def test_trigger_root() -> None: ...  # events.trigger_root golden cases
def test_comp_model_is_flattened() -> (
    None
): ...  # COMP_DEX_LIVER from sbmlutils.resources
```

Write each test body fully; the expected formula strings come from `libsbml.formulaToL3String` of the built AST, so build the AST with `libsbml.parseL3Formula` and compare formula strings, not node identity.

- [ ] **Step 2: Run** and fail. **Step 3: Implement** `dependencies.py`, `events.py`, `system.py`. Keep `system.py` below about 700 lines by splitting helpers (`_read_quantities`, `_read_rules`, `_read_reactions`, `_build_odes`, `_build_initial`, `_read_events`).
- [ ] **Step 4: Run** tests, ruff, ty. Run `OdeSystem.from_sbml` over every l3v2 case of the test suite in a quick loop and make sure no case raises anything but `ValueError` for invalid models (record cycles); constructs it does not handle must land in `unsupported`.
- [ ] **Step 5: Commit** `Add the analysis of a model into its ODE system`.

---

### Task 6: Formats and the python code

**Files:**
- Create: `src/sbmlutils/converters/ode/formats.py`, `src/sbmlutils/resources/converters/ode/python.py.jinja`
- Modify: `src/sbmlutils/converters/ode/__init__.py` (export `OdeSystem`, `FORMATS`, `Format`), `system.py` (add `render`, `write`, `render_template` methods delegating to `formats`)
- Test: `tests/converters/ode/test_python.py`, extend `conftest.py` with `roadrunner_reference`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class Format:
    name: str                     # "python", "julia", "r", "typst", "latex", "markdown"
    kind: Literal["code", "document"]
    template: str                 # file name in resources/converters/ode
    suffixes: tuple[str, ...]     # (".py",), (".jl",), (".R", ".r"), (".typ",), (".tex",), (".md",)
    printer: str                  # key of PRINTERS
    options: Mapping[str, object] # defaults: code {"simulator": True}; document {"standalone": True, "symbols": "id", "width": 4}

FORMATS: dict[str, Format]

def render(system: OdeSystem, fmt: str, **options: object) -> str
def write(system: OdeSystem, path: Path | str, fmt: str | None = None, **options: object) -> Path
def render_template(system: OdeSystem, template: Path, fmt: str = "python", **options: object) -> str
def context(system: OdeSystem, fmt: Format, options: Mapping[str, object]) -> dict[str, object]
```

`render` raises `ValueError` for an unknown format or option, `NotImplementedError("The model uses constructs the python code does not support: algebraic rule 'r1', ...")` for a code format with `system.unsupported`. `write` picks the format from the suffix (case sensitive for `.R`/`.r` both map to `r`), raises `ValueError` for an unknown suffix without `fmt`.

`context` returns plain data, never libsbml objects. For code formats: `model` (id, name, level, version, source, units as dict, sbmlutils version from `sbmlutils.__version__`), `states`, `constants`, `assigned` as lists of dicts `{"id", "name": single_line, "unit": single_line, "code": code name, "index": 0- or 1-based, "value": literal or None, "comment": single_line text}`, `functions` (`{"code", "arguments": [...], "body"}`), `initial` (ordered `{"code", "expr"}`), `assignments` (ordered `{"code", "expr", "comment"}`), `rates` (`{"code": "v_" + code, ...}`; reaction rates live in `assignments` with code `v_<id>`? No: keep the reaction id as code name to stay readable and avoid collisions; document `v` only in presentation), `odes` (`{"code", "index", "expr", "comment"}`), `events` (`{"code", "root", "initial_value", "persistent", "delay", "priority", "use_trigger_values", "assignments": [{"index", "kind": "state" | "constant", "expr"}]}`), `options`. Every expression is printed with the format's printer and the code symbol map (states and constants map to their code names, which the template unpacks from `x` and `p`; assigned variables to their code names; functions to their code names).

Python template (`simulator=False` stops after `f_y` and the event functions; `simulator=True` adds `simulate` and `__main__`). Write it with these exact public names: `XIDS`, `PIDS`, `YIDS` (lists of ids), `NAMES`, `UNITS` (dicts), `P0` (numpy array of default constants), `initial_values(p: np.ndarray | None = None) -> np.ndarray`, `f_dxdt(t: float, x: np.ndarray, p: np.ndarray) -> np.ndarray`, `f_y(t, x, p) -> np.ndarray`, `EVENTS` (list, Task 7), `simulate(t_end: float, steps: int = 101, p=None, x0=None, rtol=1e-8, atol=1e-10, method="LSODA") -> pandas.DataFrame`. Unpack at the top of `f_dxdt` and `f_y`: `A, B = x` style one per line `A = x[0]  # name [unit]`, `k = p[0]`. Constants which are set by an initial assignment are computed in `initial_values` too, which then returns `x0` and updates `p`: make it `initial_values(p) -> tuple[np.ndarray, np.ndarray]` returning `(x0, p)`. Write module docstring with the model info and a table of the states.

- [ ] **Step 1: Write failing tests** in `test_python.py`: port `_assert_rates_as_roadrunner` from `tests/converters/test_odefac.py` into `conftest.assert_python_as_roadrunner(sbml: str, tmp_path: Path)` against the new names (`XIDS`, `f_dxdt(t, x, p)`, `initial_values`), checking initial values against roadrunner at t=0 too (states and assigned values). Tests: every formula of `conftest.FORMULAS`; models `DEMO_SBML`, `REPRESSILATOR_SBML`, `VDP_SBML`, `COMP_DEX_LIVER`, `COMP_SPT_LIVER`, `INTERPOLATION_LINEAR_SBML`, `GALACTOSE_SINGLECELL_SBML` (initial assignments, #438); `test_python_model_without_states` (only assignment rules); `test_reserved_ids_run` (ids `lambda`, `t_`, `np`, `p` in one model); `test_simulate_matches_roadrunner` for `REPRESSILATOR_SBML` with `simulator=True` (`T_END`, `T_STEPS`, columns `time`, states, assigned); `test_rhs_only` (`simulator=False` has no `simulate`, imports without scipy/pandas: assert `"scipy" not in code`); `test_unsupported_raises` (algebraic rule); `test_write_by_suffix` and `test_unknown_suffix`.
- [ ] **Step 2: Run** and fail. **Step 3: Implement** `formats.py`, template, methods on `OdeSystem` (`render`, `write`, `render_template` import `formats` lazily to avoid a cycle).
- [ ] **Step 4: Run** tests, ruff, ty; open one generated file (`REPRESSILATOR_SBML`) and read it as a person would: check layout, comments, alignment. Fix anything that looks off.
- [ ] **Step 5: Commit** `Render the ODE system as python code`.

---

### Task 7: Events in the python code

**Files:**
- Modify: `src/sbmlutils/resources/converters/ode/python.py.jinja`, `formats.py` if the context lacks something
- Test: `tests/converters/ode/test_python.py` (events), `tests/converters/ode/test_testsuite.py` (curated subset)

**Interfaces:**
- Consumes: `Event` and its context dict from Task 6.
- Produces: in the generated python, `EVENTS: list[dict]` with keys `id`, `root` (callable `(t, x, p) -> float`), `initial_value`, `persistent`, `delay` (callable or `None`), `priority` (callable or `None`), `use_trigger_values`, `assign` (callable `(t, x, p) -> tuple[np.ndarray, np.ndarray]` returning new `x`, `p`), and `simulate` honouring them.

Algorithm of `simulate` (write it into the template as plain readable python, not as a generic library):
1. `x, p = initial_values(p)`; `trigger_state = [ev["root"](0, x, p) > 0 if ev["initial_value"] else False ...]`: an event whose `initial_value` is false and whose trigger is true at t=0 fires at t=0.
2. Loop: integrate with `solve_ivp(f_dxdt, (t, t_end), x, args=(p,), t_eval=remaining grid, events=[root functions with .direction = 0, .terminal = True], rtol, atol, method)`. On termination by an event, find the events whose trigger changed from false to true (evaluate `root > 0` just after the crossing at `t + eps` by checking the sign at the event state; equality at the root: `>=` relations count as true at the root, track per event via the relation type recorded in the context: `"strict": bool`).
3. Pending queue of `(execution_time, priority, order, event index, values)`: values computed at trigger time when `use_trigger_values`. Execute all due at the current time: highest priority first, ties by document order (roadrunner uses random order for ties; the test suite cases with ties are nondeterministic and excluded), after each execution recompute triggers; a non-persistent pending event whose trigger is now false is dropped; an event triggered by an execution is added.
4. After assignments, recompute assigned values; continue. Output grid rows exactly at `t_eval` points, values right after events at that time (roadrunner reports the post-event value at an event time).

Tests:
- `test_event_at_t0`, `test_event_priority`, `test_event_delay`, `test_event_persistent`, `test_event_use_values_from_trigger_time`, `test_event_changes_compartment` (assignment to a compartment with species in concentration: SBML keeps the concentration as assigned values only; roadrunner reference decides), each a small antimony model compared with roadrunner via `conftest.assert_trajectory_as_roadrunner(sbml, module, rtol=1e-4, atol=1e-6)`.
- `test_testsuite.py`: `CURATED` list of about 60 l3v2 cases covering every feature tag of the test suite (read the `tags` of each case from the comments of the model XML? The XML carries no tags. Choose the cases by grepping the l3v2 XML for the constructs instead: `<event`, `<delay`, `<priority`, `<initialAssignment`, `<algebraicRule` (expected unsupported), `<rateRule`, `conversionFactor`, `<functionDefinition`, `rateOf`, `<localParameter`, `stoichiometryMath`/species reference ids, `constant="false"` compartments, `hasOnlySubstanceUnits="true"`, `boundaryCondition="true"`; take the first three per construct and record why each is in the list as a comment). Each case: if `OdeSystem.from_sbml(case).unsupported`, assert that `render("python")` raises `NotImplementedError` and continue; else generate python, simulate `T_END`, `T_STEPS`, compare all states and assigned values with roadrunner (`timeCourseSelections` as in `tests/test_roundtrip.py` plus compartments). Known failures as a dict `KNOWN_FAILURES: dict[str, str]` with the reason, marked `xfail(strict=True)`. The full sweep `test_python_sweep` behind `@pytest.mark.sbml_testsuite` over all l3v2 cases with the same body, reusing `NONDETERMINISTIC` from `tests/test_roundtrip.py` (import it).
- [ ] **Step 1:** Write the event tests. **Step 2:** Run, fail. **Step 3:** Implement. **Step 4:** Run the curated subset, then the full sweep once (`uv run pytest -q -m sbml_testsuite tests/converters/ode/test_testsuite.py -k python`, run in the background, it may take minutes) and record every failure: fix the cause or add it to `KNOWN_FAILURES` with a precise reason. Target: every case without unsupported constructs and not nondeterministic passes, or has a documented roadrunner disagreement.
- [ ] **Step 5: Commit** `Simulate the events of a model in the python code`.

---

### Task 8: Julia code

**Files:**
- Create: `src/sbmlutils/resources/converters/ode/julia.jl.jinja`
- Modify: `formats.py` (register julia), `tox.ini` (env `julia`), `.github/workflows/ci-cd.yml` (job `julia`)
- Test: `tests/converters/ode/test_julia.py`, `tests/converters/ode/test_testsuite.py` (julia parametrization)

**Interfaces:**
- Consumes: `context` from Task 6, `JuliaPrinter`, `conftest.run_julia`.
- Produces: a julia file defining `module <ModelId>` (model id with first letter upper-cased, `Model` if none, made a valid julia identifier) exporting `XIDS`, `PIDS`, `YIDS`, `P0`, `initial_values(p)` returning `(x0, p)`, `f!(dx, x, p, t)`, `f_y(x, p, t)`, `EVENTS`, and with `simulator=true` `simulate(t_end; steps=101, p=nothing, x0=nothing, reltol=1e-8, abstol=1e-10)` returning `DataFrame`. Imports: `using DifferentialEquations, DataFrames, SpecialFunctions` (simulator), only `SpecialFunctions` when the math needs `gamma`, nothing else for the RHS. Events via `VectorContinuousCallback` with the root functions; priorities, delays and persistence handled in the affect function with a pending queue in the integrator's user data, mirroring the python algorithm of Task 7; `p` is mutable (`Vector{Float64}`) so event assignments to constants work.

- [ ] **Step 1: Write failing tests**: `test_julia.py` with a helper which renders the julia code into `tmp_path`, appends a driver that `include`s it, calls `initial_values`, `f!` at two states and `f_y`, and prints JSON (`using JSON3` is another dependency: print plain `println(join(values, ","))` lines instead), runs it via `conftest.run_julia` and compares with roadrunner as in Task 6. Same models and formula list as Task 6, plus `simulate` of `REPRESSILATOR_SBML` with CSV output (`CSV` package not needed: print rows). Skip without julia.
- [ ] **Step 2:** Run with docker julia (first run installs packages into `$HOME/.julia-docker`; precompile once with `docker run --rm -v $HOME/.julia-docker:/root/.julia julia:1.11 julia -e 'using Pkg; Pkg.add(["DifferentialEquations", "DataFrames", "SpecialFunctions"])'`). Fail.
- [ ] **Step 3: Implement** template. tox env:

```ini
[testenv:julia]
# the generated julia code is run with julia, which this environment needs on the path
basepython = python3.14
passenv = SBMLUTILS_JULIA, JULIA_DEPOT_PATH, HOME
commands =
    pytest -m "not sbml_testsuite" {posargs:tests/converters/ode/test_julia.py tests/converters/ode/test_testsuite.py -k julia}
```

CI job `julia` in `ci-cd.yml` on `ubuntu-latest`: checkout, `astral-sh/setup-uv`, `julia-actions/setup-julia@v2` with `version: "1.11"`, `julia-actions/cache@v2`, `julia -e 'using Pkg; Pkg.add(["DifferentialEquations", "DataFrames", "SpecialFunctions"]); Pkg.precompile()'`, then `uvx --with tox-uv==$TOX_UV_VERSION tox==$TOX_VERSION r -e julia`. Pin action versions as the existing jobs do (read how they pin, by SHA or tag, and do the same). Not added to the rulesets.
- [ ] **Step 4:** Run julia tests via docker; run the curated subset for julia. Record `KNOWN_FAILURES` per format if julia differs from python (the dict is keyed by `(format, case)`).
- [ ] **Step 5: Commit** `Render the ODE system as julia code`.

---

### Task 9: R code

**Files:**
- Create: `src/sbmlutils/resources/converters/ode/r.R.jinja`, `tests/converters/ode/docker/r.Dockerfile` (if not created in Task 2)
- Modify: `formats.py`, `tox.ini` (env `R`), `.github/workflows/ci-cd.yml` (job `R`)
- Test: `tests/converters/ode/test_r.py`, `test_testsuite.py` (R parametrization)

**Interfaces:**
- Produces: an R script defining `XIDS`, `PIDS`, `YIDS`, `P0` (named numeric vector), `initial_values(p = P0)` returning `list(x0 = ..., p = ...)`, `f_dxdt(t, x, p)` returning `list(dx)` (deSolve convention; unpack with `A <- x[[1]]`), `f_y(t, x, p)`, `EVENTS`, and with `simulator=TRUE` `simulate(t_end, steps = 101, p = NULL, x0 = NULL, rtol = 1e-8, atol = 1e-10)` returning a `data.frame`, using `deSolve::lsoda` with `rootfunc` and `events = list(func = ..., root = TRUE)` for the events; delays and priorities via a pending queue in an environment, mirroring Task 7. The file only calls `library(deSolve)` inside `simulate`, so sourcing it for the RHS needs no package.

- [ ] **Step 1: Write failing tests** like Task 8 with `conftest.run_r`.
- [ ] **Step 2:** Build the docker image `sbmlutils-r` and run, fail.
- [ ] **Step 3: Implement** template, tox env `R` (as julia, `passenv = SBMLUTILS_RSCRIPT, R_LIBS_USER, HOME`), CI job `R` with `r-lib/actions/setup-r@v2` (`r-version: "4.4"`) and `Rscript -e 'install.packages("deSolve", repos = "https://cloud.r-project.org")'`. Not added to the rulesets.
- [ ] **Step 4:** Run tests and curated subset via docker.
- [ ] **Step 5: Commit** `Render the ODE system as R code`.

---

### Task 10: Presentation formats: typst, LaTeX, markdown

**Files:**
- Create: `src/sbmlutils/resources/converters/ode/typst.typ.jinja`, `latex.tex.jinja`, `markdown.md.jinja`, `src/sbmlutils/converters/ode/text.py` additions (`typst_text`, `markdown_text`, `latex_document_text` = `tex_text`), `tests/converters/ode/golden/repressilator.{typ,tex,md}`, `tests/converters/ode/golden/demo.{typ,tex,md}`
- Modify: `formats.py` (document context), `.github/workflows/ci-cd.yml` (job `latex` with tectonic)
- Test: `tests/converters/ode/test_presentation.py`, `tests/converters/ode/conftest.py` (`--update-golden` option via `pytest_addoption` in `tests/converters/ode/conftest.py`)

**Interfaces:**
- Consumes: `OdeSystem`, `LatexPrinter`, `TypstPrinter`, `typeset_names`, `print_lines`.
- Produces: `context` for documents: `model` (title, id, level, version, source, version of sbmlutils, notes as escaped text), `units`, `compartments`, `species`, `parameters` (rows of escaped cells: `symbol` math, `id` text, `name` text, `value` text, `unit` text, flags), `functions` (`lhs`, `rhs`), `initial`, `assignments`, `reactions` (`equation` math e.g. `2 A + B -> C`, `rate_lhs` `v_{J0}`, `rate_rhs`, `modifiers`, `local_parameters`), `odes` (`lhs` `\frac{dS}{dt}`/`(d S)/(d t)`, `rhs_lines` list of lines from `print_lines` where the right hand side is written with reaction rate symbols `v_{id}`: print `reaction_terms` with reaction ids mapped to `v_{id}` and then the volume as a fraction, rate rules marked `rate rule`), `events`, `unsupported`, `options`. Markdown uses `LatexPrinter` in `$$ ... $$` and `\begin{aligned}`.

The section order and content of the spec ("Presentation formats") is the contract; every template renders the same sections in the same order, sections without content omitted. LaTeX standalone preamble: `\documentclass{article}`, `\usepackage[utf8]{inputenc}` is not needed with tectonic, use `\usepackage{amsmath, amssymb, booktabs, longtable, hyperref}`, `\usepackage[margin=2cm]{geometry}`. Typst standalone: `#set document(title: ...)`, `#set page(margin: 2cm)`, `#set text(size: 10pt)`, `#set heading(numbering: "1.")`, tables with `#table(columns: 6, stroke: none, table.hline(), ...)`.

- [ ] **Step 1: Write failing tests**:
  - golden comparison for `demo` and `repressilator` in all three formats with `standalone=True`, and fragment checks (`standalone=False`: no `\documentclass`, no `#set page`);
  - typst compile of both models with the `typst` package (`typst.compile(input_path, output=pdf_path)`), standalone and a fragment included from a wrapper document;
  - LaTeX compile with `tectonic` when on `PATH` (`shutil.which("tectonic")`), else skip;
  - markdown: parse with `markdown_it.MarkdownIt("gfm-like")`, assert the tables have the expected number of rows, and `$$` blocks are balanced;
  - `test_markup_in_names_is_text`: names `"a $x$ #b _c_ | d \\ <script>"` in every format; assert the compiled typst PDF builds and the raw output contains the escaped forms (`\$`, `\#` in typst/LaTeX, `\|` and `&lt;script&gt;` in markdown);
  - `test_symbols_name_option` (`symbols="name"`), `test_unsupported_section` (algebraic rule listed), `test_events_section`.
- [ ] **Step 2:** Run, fail. **Step 3: Implement**; generate goldens with `--update-golden`, then read each golden file and the compiled PDF (render the typst PDF to PNG with `typst.compile(..., format="png")` and look at it with the Read tool) and fix every layout problem: alignment, overflowing equations, table widths, headings. Be picky.
- [ ] **Step 4:** Run tests, ruff, ty. CI job `latex`: `ubuntu-latest`, install tectonic (`wtfjoke/setup-tectonic@v3` or download the release binary), run `uvx ... tox r -e py3.14 -- tests/converters/ode/test_presentation.py`. Not required in rulesets.
- [ ] **Step 5: Commit** `Render the ODE system as typst, LaTeX and markdown`.

---

### Task 11: Safety tests and the coverage report

**Files:**
- Create: `tests/converters/ode/test_safety.py`, `scripts/ode_report.py`
- Test: as named

**Interfaces:**
- Consumes: everything above; `run_case_isolated` pattern from `tests/test_roundtrip.py`.
- Produces: `scripts/ode_report.py` with `--format python|julia|r` (repeatable, default python), `--limit`, `--case`, `--timeout`, printing per format: counts of passed, failed, unsupported (by construct), nondeterministic, crashed, timed out; pass rate `passed / (passed + failed)`; table of failures with reason. Worker mode in `tests/converters/ode/test_testsuite.py` (`if __name__ == "__main__": run_worker(...)`) mirroring `tests/test_roundtrip.py`. Output directory `.ode_tmp/` (add to `.gitignore`).

- [ ] **Step 1: Write failing tests** in `test_safety.py`, ported from `tests/converters/test_odefac.py` to all six formats: injected names (`INJECTED_NAME`) never break a line of code or a comment in python, julia, R (assert the injected assignments are not executable lines: parse python with `ast`, for julia and R assert no line starts with `INJECTED`); invalid SIds rejected with `ValueError` in code formats; invalid SId in math rejected in every format; model id with line breaks stays on its line in documents; species without compartment; local parameter collisions.
- [ ] **Step 2:** Run, fail where the port is missing. **Step 3:** Fix. **Step 4:** Run `uv run python scripts/ode_report.py` (background, all l3v2 cases) and keep the summary for the docs (Task 12).
- [ ] **Step 5: Commit** `Test the safety of the generated code and report the test suite coverage`.

---

### Task 12: Migration, documentation and examples

**Files:**
- Delete: `src/sbmlutils/converters/odefac.py`, `src/sbmlutils/resources/converters/odefac_template.*`, `tests/converters/test_odefac.py`, `examples/converters/odefac.py`, `docs/api/converters.odefac.md`; `src/sbmlutils/converters/mathml.py` if nothing uses `evaluableMathML` any more (`rg -l evaluableMathML`).
- Create: `docs/ode.md`, `docs/api/converters.ode.md` (`::: sbmlutils.converters.ode`), `examples/converters/ode.py`, `docs/images/ode/` (rendered typst SVG of the repressilator, generated by the example, committed)
- Modify: `src/sbmlutils/factory/model.py` (`create_markdown` uses `OdeSystem.from_sbml(filepath).write(markdown_path)`), `src/sbmlutils/factory/__init__.py` and `tests/test_factory_facade.py` (drop `SBML2ODE` from the deprecated names), `examples/assignment.py`, `examples/tutorial/linear_chain.py`, `tests/examples/test_example_scripts.py` (`examples.converters.ode`), `zensical.toml` (nav: `ODE export` page under the user guide next to Converters, API entry `ode`), `docs/api/index.md`, `docs/converters.md` (replace the odefac section with a short paragraph linking `ode.md`), `CLAUDE.md` (the converters paragraph: `ode/` package, three layers, formats), `README.md` / `docs/index.md` feature lists if they mention odefac.

`docs/ode.md` content, in this order: what the export is; quick start (`OdeSystem.from_sbml`, `render`, `write`, options table per format); the supported SBML features table (from the spec and the report of Task 11: construct, numerical formats, presentation formats); the numerical formats (shared structure, one subsection per language with the generated code of the repressilator collapsed in a `??? example` block, how to run it: `python model.py`, `julia -e 'include("model.jl"); ...'`, `Rscript -e 'source("model.R"); ...'`, solver notes, events); the presentation formats (typst with the SVG, LaTeX source, markdown rendered inline by including the generated markdown), symbols and naming; safety; custom templates (context keys documented); migration from `odefac` (the table of the spec); verification (test suite pass rates per format from `scripts/ode_report.py`).

- [ ] **Step 1:** Update tests first: `tests/examples/test_example_scripts.py` runs `examples.converters.ode`; `tests/test_factory_facade.py` no longer lists `SBML2ODE`; a test that `create_model(..., create_markdown=True)` writes markdown with `$$`. Run, fail.
- [ ] **Step 2:** Make the changes, delete the old files.
- [ ] **Step 3:** `uv run pytest -q` (whole suite), `uv run ruff check`, `uv run ruff format --check`, `uv run ty check`, `uv run zensical build --clean` and `uv run python scripts/llms_txt.py` if the docs workflow runs it (read `.github/workflows/docs.yml`). Serve the site (`uv run zensical serve`) and look at `ode.md` in the browser with `chrome-devtools-axi`: math renders, code blocks, SVG, tables. Fix anything that looks off. Check that `docs/superpowers/` does not break the build or show up in the nav; exclude it in `zensical.toml` if it does.
- [ ] **Step 4:** `tox run-parallel` (or at least `tox r -e py3.14,ty,lowest`).
- [ ] **Step 5: Commit** `Replace odefac with the ODE export and document it`.

---

## Self-review notes

- Spec coverage: analysis (Task 5), printers (1-3), symbols (4), formats API (6), numerical (6-9), events (7-9), presentation (10), testing incl. sweep and report (7, 11), CI (8-10), docs and migration (12). Release notes are written at release time per `CLAUDE.md`, so the migration table lives in `docs/ode.md` and is copied into the release notes by the release.
- Interface names used across tasks: `OdeSystem.from_sbml`, `render`, `write`, `render_template`, `FORMATS`, `PRINTERS`, `MathPrinter.print`, `print_lines`, `code_names`, `typeset_names`, `initial_values(p) -> (x0, p)`, `f_dxdt(t, x, p)` (python, R), `f!(dx, x, p, t)` (julia), `f_y`, `EVENTS`, `simulate`.
