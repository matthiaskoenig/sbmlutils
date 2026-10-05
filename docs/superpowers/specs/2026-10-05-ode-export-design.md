# ODE export: design

Status: approved in conversation on 2026-10-05, replaces `sbmlutils.converters.odefac`.

Closes [#481](https://github.com/matthiaskoenig/sbmlutils/issues/481) (an updated code generator with complete coverage, run against the test suite) and [#438](https://github.com/matthiaskoenig/sbmlutils/issues/438) (initial assignments not supported).

## Goal

An SBML model is exported as its system of ordinary differential equations in six formats which share one analysis and one math printer core:

- numerical formats, which are code that simulates the model: **python** (numpy, scipy `solve_ivp`), **julia** (DifferentialEquations.jl), **R** (deSolve);
- presentation formats, which are documents that describe the model: **typst**, **LaTeX**, **markdown**.

The numerical code is correct, meaning it reproduces roadrunner over the SBML semantic test suite, and readable, meaning a person can read the equations in it. The presentation formats render the same content in the same order, so a model reads the same in every one of them. This is first class functionality of sbmlutils with its own documentation page.

## Decisions

| Question | Decision |
|---|---|
| Math engine | Own printers on the libsbml AST, one per dialect. `sbmlmath` is not used, see below. |
| Semantic coverage | Full, events included. Algebraic rules, `delay()` and fast reactions are reported as unsupported. |
| API | Clean break: new package `sbmlutils.converters.ode`, `odefac` is removed. |
| Code shape | Option `simulator`: `True` writes a self contained simulator, `False` the right hand side and its helpers only. |
| Document shape | Option `standalone`: `True` writes a compilable document, `False` a fragment to include. |
| Verification | Every format is executed or compiled: python in the default test run, julia and R in tox environments and CI jobs of their own, typst through the `typst` python package, LaTeX with tectonic. |

### Why not sbmlmath

Issue #481 suggests [sbmlmath](https://github.com/dweindl/sbmlmath) (MathML to sympy) with the sympy code printers. A probe with sbmlmath 0.4.1 and sympy 1.14.0 showed:

- parsing fails for a `piecewise` whose condition holds `&&`;
- `rem` becomes sympy `Mod`, which is the floored modulo, while SBML `rem` has the sign of the dividend;
- `log(2, A)` is printed by the numpy printer as `numpy.log(A, 2)`, whose second argument is the `out` array, and by the LaTeX printer as `\log(A)`, dropping the base;
- sympy has no typst printer, and `delay` has no printer at all;
- sympy evaluates and reorders the expression, so the printed equation is no longer the equation of the model.

Each of these needs an override, so the sympy route ends in custom printers on top of two extra dependencies. A printer on the libsbml AST with a dialect table per language keeps the exact SBML semantics, preserves the structure of the math as written, covers typst, and generalizes `python_math`, which is already verified against roadrunner.

## Architecture

```
sbmlutils/converters/ode/
    __init__.py        public API: OdeSystem, FORMATS, render, write
    system.py          analysis: SBML document to OdeSystem
    dependencies.py    ordering of assignments, cycle detection
    printers/
        base.py        MathPrinter: precedence, associativity, dispatch on AST type
        python.py      PythonPrinter
        julia.py       JuliaPrinter
        r.py           RPrinter
        latex.py       LatexPrinter (markdown uses it inside $$)
        typst.py       TypstPrinter
    symbols.py         naming: code identifiers and typeset symbols
    formats.py         Format registry, jinja2 environment, filters, escaping
sbmlutils/resources/converters/ode/
    python.py.jinja    julia.jl.jinja    r.R.jinja
    typst.typ.jinja    latex.tex.jinja   markdown.md.jinja
    _sections/         shared partials of the presentation templates
```

The three layers are independent: the analysis knows no format, a printer knows no model, a template knows no libsbml.

### Layer 1: analysis (`system.py`)

`OdeSystem.from_sbml(source)` takes a path, an SBML string or an `SBMLDocument` (read with `read_sbml`) and returns a frozen dataclass tree:

- `ModelInfo`: id, name, SBML level and version, notes as plain text, model units (time, substance, extent, volume, area, length) as strings from `udef_to_string`.
- `Symbol`: id, name, unit string, SBO term, `kind` (`compartment`, `species`, `parameter`, `reaction`, `species_reference`).
- `Compartment`, `Species`, `Parameter`: the symbol plus value, `constant`, and for a species its compartment, `hasOnlySubstanceUnits`, `boundaryCondition`, conversion factor.
- `FunctionDefinition`: id, arguments, body AST.
- `InitialAssignment`, `Assignment` (assignment rule): variable, AST.
- `Reaction`: id, reactants, products, modifiers with their stoichiometry (a number, or the AST of a stoichiometry given by a rule or an initial assignment of a species reference), reversible flag, rate AST, local parameters. Local parameters are renamed to `<reaction id>_<local id>` (made unique against all ids) and become constant parameters; the rate AST is rewritten accordingly.
- `Ode`: state variable, right hand side AST, `origin` (`reactions` or `rate_rule`), and for species in concentration the volume term.
- `Event`: id, trigger AST, `initialValue`, `persistent`, delay AST, priority AST, `useValuesFromTriggerTime`, assignments (variable, AST).
- `unsupported`: list of `(construct, element id)`, e.g. `("algebraic rule", "rule3")`.

The following SBML semantics are resolved once, here:

- **State variables** are the species which are neither constant nor boundary nor assigned and take part in a reaction or a rate rule, plus every parameter, compartment and species reference with a rate rule. A boundary species with a rate rule is a state as well. Every other species, parameter and compartment is constant or assigned.
- **Species** are stored as roadrunner holds them: in amount if `hasOnlySubstanceUnits`, else in concentration. The reaction terms of the ODE of a species in concentration are divided by its compartment. A species in concentration whose compartment is not constant (a rate rule, an assignment rule or an event assignment changes its size) is integrated as its amount `n_S` instead, with the concentration `S = n_S / V` as an assignment: the amount is what SBML conserves when the size changes, so a rate rule, an assignment rule and an event on the compartment are all exact without a `dV/dt` term.
- **Conversion factors**: a species conversion factor, else the model conversion factor, multiplies the reaction terms of the species.
- **Stoichiometry**: a number, or the id of a species reference with an assignment rule, rate rule or initial assignment, which is then a symbol of the system.
- **Rate rules** on species in concentration apply to the concentration as written (SBML semantics), no volume term.
- **`rateOf(x)`** is replaced by the right hand side of `x` for a state, by `0` for a constant, and is unsupported for an assigned variable whose derivative would need symbolic differentiation.
- **Assignments** (assignment rules and the reaction rates) are ordered by their dependencies with `graphlib.TopologicalSorter`; a cycle raises `ValueError` naming the variables. Ties keep the order of the document.
- **Initial values** at t=0: the order of evaluation is the topological order over initial assignments, assignment rules and the initial values of the elements together, so that an initial assignment which depends on an assignment rule (and the reverse) is evaluated right. Initial amounts and concentrations are converted to the representation of the state with the initial size of the compartment, which itself may come from an initial assignment.
- **Function definitions** are kept as functions, called by the math.
- **Unsupported**: algebraic rules, `delay()`, fast reactions, an event assignment to a constant, the comp, fbc and distrib packages (a comp model is flattened with `flatten_sbml` first). They are collected, never silently dropped.

### Layer 2: math printers (`printers/`)

`MathPrinter.print(ast, symbols)` returns a string. The base class implements the traversal: dispatch on `ASTNode.getType()`, parentheses from a precedence and associativity table, n-ary operators, unary minus, and the structure of `piecewise`, `log` with base, `root` with degree, relations with more than two operands. A dialect overrides tables and a few node handlers:

| Construct | python | julia | R | LaTeX | typst |
|---|---|---|---|---|---|
| power | `a ** b` | `a ^ b` | `a ^ b` | `a^{b}` | `a^(b)` |
| `piecewise` | `x if c else y` (lazy) | `c ? x : y` (lazy) | `if (c) x else y` (lazy, scalar) | `cases` environment | `cases(...)` |
| `rem` | `np.fmod` | `rem` | sign of dividend via `trunc` | `\operatorname{rem}` | `op("rem")` |
| `quotient` | `np.trunc(a / b)` | `div` | `trunc(a / b)` | `\operatorname{quotient}` | `op("quotient")` |
| `log(b, x)` | `np.log(x) / np.log(b)` | `log(b, x)` | `log(x, b)` | `\log_{b} x` | `log_(b) x` |
| `and`, `or`, `xor`, `not` | `and`, `or`, `^`, `not` on `bool` | `&&`, `\|\|`, `xor`, `!` | `&&`, `\|\|`, `xor`, `!` | `\land`, `\lor`, `\oplus`, `\lnot` | `and`, `or`, `xor`, `not` |
| `time`, `avogadro` | `t`, literal | `t`, literal | `t`, literal | `t`, `N_A` | `t`, `N_A` |
| `INF`, `NaN` | `np.inf`, `np.nan` | `Inf`, `NaN` | `Inf`, `NaN` | `\infty`, `\mathrm{NaN}` | `infinity`, `"NaN"` |

Booleans are numbers in SBML: a relation used as a number becomes `float(...)` in python, `Float64(...)` in julia, `as.numeric(...)` in R. Every construct the dialect cannot express raises `NotImplementedError` naming the construct. Identifiers come only from the `symbols` mapping; an identifier without a mapping raises, so an id is never written raw.

Presentation printers break long equations: the top level sum of a right hand side is split into lines of at most `width` terms (default 4) inside an `align`/aligned block.

### Layer 3: formats (`formats.py`, templates)

`FORMATS` maps a name to a `Format`: template, printer, file suffixes, kind (`code` or `document`) and the options it accepts. The API:

```python
from sbmlutils.converters.ode import OdeSystem

system = OdeSystem.from_sbml("model.xml")
code: str = system.render("python", simulator=True)
system.write("model.py")  # format from the suffix
system.write("model.typ", standalone=False)
system.render_template(Path("my_template.jinja"))
```

`render` checks the options against the format, builds the symbol mapping of the format (`symbols.py`), prints every AST once with the printer of the format and renders the template with a context of plain strings and lists, so a template never touches libsbml. A numerical format raises `NotImplementedError` listing `system.unsupported` if it is not empty; a document lists them in a section of their own.

Safety is kept from `odefac`: every free text goes through `single_line` in code comments and through the escaping of the format in documents; every id written into code is checked to be an SId; generated python names avoid keywords and the names the code uses itself (`t`, `x`, `p`, `np`, ...), likewise for julia and R.

## Numerical formats

The three files have the same structure; python is 0-indexed, julia and R are 1-indexed, and the indices are hidden behind named locals.

1. Header: model id and name, source, sbmlutils version, units of the model, the unsupported constructs (empty for a file that is written at all).
2. Id tables `xids`, `pids`, `yids`, one entry per line with name and unit as a comment.
3. `p`: default values of the constant parameters, constant compartments and constant species.
4. `initial_values(p)`: returns `(x0, p)`, the constants set by an initial assignment updated in `p`, evaluating initial values, initial assignments and assignment rules at t=0 in their order. This fixes #438.
5. Right hand side: `f_dxdt(t, x, p)` in python (the order of `solve_ivp`), `f!(dx, x, p, t)` in julia, `f_dxdt(t, x, p)` returning `list(dx)` in R. The body unpacks named locals from `x` and `p`, calls the function definitions (emitted as functions before it), evaluates the assignments in order, the reaction rates as `v_<reaction id>`, then one line per state, each with the name and unit as a comment. `f_y(t, x, p)` returns all assigned values and reaction rates.
6. Events (`simulator=True` and `False`): `event_triggers(t, x, p)` returns one continuous root function value per event, `event_assign_<id>(t, x, p)` returns the new state. A single relation `a > b` becomes `a - b`, `&&` the minimum, `||` the maximum and `!` the negation of its operands' root functions, so that the sign of the root function is the truth value of the trigger. Strict and non-strict relations differ only at the root, which the event handling resolves by the direction of the crossing.
7. `simulate(t_end, steps, p=None, x0=None)` (only `simulator=True`): integrates, stops at every root crossing from false to true, evaluates triggers with `initialValue`, orders simultaneous events by priority, schedules delayed events, drops non-persistent events whose trigger turned false before execution, applies assignments with the values of trigger or execution time, re-evaluates the initial values of assigned variables, restarts the integration, and returns a table with `time`, the states and the assigned values (pandas `DataFrame`, `DataFrames.DataFrame`, `data.frame`). Python uses `scipy.integrate.solve_ivp` (LSODA, `rtol=1e-8`, `atol=1e-10` as defaults, overridable), julia `DifferentialEquations.solve` with `Rodas5P` and a `VectorContinuousCallback`, R `deSolve::lsoda` with `rootfunc` and `events = list(func=..., root=TRUE)`. The python file runs as a script (`if __name__ == "__main__"`) and prints the head of the table.

The correctness contract: `initial_values`, `f_dxdt`, `f_y` and `simulate` match roadrunner (`rtol=1e-6`, `atol=1e-9`) for every case of the SBML semantic test suite without an unsupported construct.

## Presentation formats

One section order for all three formats, the sections without content are omitted:

1. Title (model name, else id), a metadata line (id, SBML level and version, source, sbmlutils version), the notes of the model as plain text.
2. Units of the model.
3. Compartments, species and parameters: tables with symbol, id, name, value, unit and the constant flag; species add compartment, amount or concentration and boundary condition.
4. Function definitions as `f(x, y) = ...`.
5. Initial assignments and assignment rules, in their order.
6. Reactions: the reaction equation (`2 A + B -> C`, `<->` if reversible, modifiers after it), the rate `v_r = ...` and the local parameters.
7. ODE system: `d x / d t = ...` per state, written with the reaction rates (`v_1 - 2 v_2`), conversion factors and volumes explicit, rate rules marked.
8. Events: trigger, delay, priority, flags and assignments.
9. Unsupported constructs.

Symbols: an id is typeset as a math symbol. The part before the first `_` is the base, the rest the subscript (`k_cat_glc` is `k` with subscript `cat_glc`); a base of more than one letter is upright. The option `symbols="id" | "name"` selects ids or element names (a name which is no valid symbol falls back to the id).

Format specifics:

- **typst**: `standalone=True` writes `#set document`, page and text settings, headings and the content; `False` the content only. Math in `$ ... $`, tables with `#table`. Escaped characters in text: backslash, `#`, `$`, `*`, `_`, `@`, `<`, `>`, `[`, `]` and the backtick.
- **LaTeX**: `standalone=True` writes an `article` with `amsmath`, `booktabs`, `longtable`, `hyperref`; `False` the body only and a comment listing the packages it needs. Escaping by `tex_text`.
- **markdown**: GitHub flavored tables, display math in `$$ ... $$` with the LaTeX printer (rendered by GitHub and by Zensical with MathJax), ids in code spans. Escaped: `|`, `*`, `_`, backtick, `<`, `>` and the HTML entities. This replaces the markdown which `create_model(create_markdown=True)` writes.

## Testing

Tests live in `tests/converters/ode/`:

- `test_system.py`: the analysis, one test per semantic rule above (conversion factors, variable compartments, local parameter renaming, stoichiometry math, rate rules on every kind, `rateOf`, ordering, cycles, initial values, unsupported collection).
- `test_printers.py`: every AST node type in every dialect against golden strings, the precedence table, and the evaluation of the numerical dialects against roadrunner for the formula set of the current `test_odefac.py`.
- `test_numerical.py`: python always (skips without roadrunner); julia and R skip when `julia` or `Rscript` with its packages is missing. Compares `initial_values`, `f_dxdt` and `f_y` at two states and the trajectory of `simulate` at the time points of the test suite case.
- `test_presentation.py`: typst compiled with the `typst` python package (added to the `dev` extra), LaTeX compiled when `tectonic` is on the path, markdown parsed with `markdown-it-py`; golden files for the demo model in `tests/converters/ode/golden/`, regenerated with `pytest --update-golden`.
- `test_safety.py`: the injection and SId tests of `test_odefac.py`, ported to every format.
- A curated subset of the SBML semantic test suite (every feature tag at least once, about 60 cases) runs in the default test run; the full sweep runs behind the `sbml_testsuite` marker. `scripts/ode_report.py` runs the sweep, one process per case, and reports the pass rate per numerical format with the known failures and their reasons, as `scripts/roundtrip_report.py` does.

Continuous integration: tox environments `julia` and `R` (python 3.14 plus the toolchain), jobs in `ci-cd.yml` with `julia-actions/setup-julia` (DifferentialEquations, DataFrames) and `r-lib/actions/setup-r` (deSolve), and a `latex` job with tectonic. They are not required checks of the ruleset at first, so a toolchain outage does not block a merge; the decision to make them required is left to the maintainer.

## Documentation

- `docs/ode.md`, "ODE export": the API, the options, one section per format with the output of the repressilator (code listings for the numerical formats, the typst output compiled to SVG, the LaTeX source, the markdown rendered), how to run the generated code with its solver, and the table of supported SBML features.
- `docs/api/converters.ode.md` replaces `docs/api/converters.odefac.md`; `docs/converters.md` links to the new page.
- `examples/converters/ode.py` writes all six formats of a packaged model.

## Migration

`sbmlutils.converters.odefac` and its templates are removed. `create_model(create_markdown=True)`, `examples/assignment.py` and `examples/tutorial/linear_chain.py` use the new API. The release notes of the next release map the old calls to the new ones:

| 0.13 | new |
|---|---|
| `SBML2ODE.from_file(path)` | `OdeSystem.from_sbml(path)` |
| `SBML2ODE(doc)` | `OdeSystem.from_sbml(doc)` |
| `to_python(path)` | `write(path)` or `render("python")` |
| `to_R`, `to_julia`, `to_markdown`, `to_tex` | `render("r" \| "julia" \| "markdown" \| "latex")` |
| `to_custom_template(path)` | `render_template(path)` |
