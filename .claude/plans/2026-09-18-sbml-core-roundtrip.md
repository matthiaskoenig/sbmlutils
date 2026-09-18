# SBML Core Round-Tripping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `SBML -> sbml_to_model -> create_model -> SBML` preserve SBML core, raising the simulation round-trip pass rate on the SBML test suite from the measured 57.4% to approximately 100%.

**Architecture:** Three layers, in order. First the data model in `factory.py` gains the classes that core SBML needs and that do not exist today (`Unit`, `KineticLaw`, `LocalParameter`, `EventAssignment`) and stops mutating documents it writes. Then `parser.py` gains the branches that read those constructs back. Throughout, a roadrunner-based simulation test in `tests/test_roundtrip.py` is the measuring instrument: it is built first, so every later task is verified by cases moving from failing to passing.

**Tech Stack:** python >= 3.11, `python-libsbml`, `pint`, `pydantic`, `markdown-it-py`, `numpy`; `libroadrunner` (the `examples` extra, which `dev` and the tox test env both pull in) for the simulation tests; `pytest`, `ruff`, `ty`; `uv` for the environment.

**Spec:** `.claude/specs/2026-09-18-sbml-core-roundtrip-design.md`

## Global Constraints

- **Never use the em dash.** Use a plain dash `-`. This applies to code, comments, docstrings, markdown and commit messages.
- **Never add an agent name as commit co-author** beyond the attribution lines already used in this repository.
- **Never edit `CHANGELOG.md`** or any auto-generated file. Release notes go in `release-notes/`.
- Every module, class and function carries full type annotations and a docstring. New docstrings are **google style**.
- Log calls use **lazy `%s` formatting**, never f-strings (ruff `G` enforces this).
- Library code logs, it does not print.
- libsbml has no type stubs: annotate libsbml objects explicitly and use the getters (`getVariable()`), never the SWIG-synthesized attributes.
- Suppress a type diagnostic with a rule-specific `# ty: ignore[rule-name]`, never a blanket `# type: ignore`.
- `[tool.ty.terminal] error-on-warning = true`, so the tree must stay at **zero** ty diagnostics.
- Markdown carries **no hard line wraps**: a paragraph, list item or table row is one line.
- Branch is `feat/469-sbml-core-roundtrip`. `develop` is the default branch and takes changes through a pull request.
- Verification command for every task: `uv run pytest -m "not sbml_testsuite"`, `uv run ruff check`, `uv run ruff format --check`, `uvx ty check`.

## Baseline (measured, do not re-derive)

| Metric | Value |
| --- | --- |
| Element-count-lossless round trips, first 200 l3v2 cases | 0 of 200 |
| Simulation pass rate, first 150 l3v2 cases | 85 of 148 (57.4%) |
| Warning records from re-emitting 194 l3v1 cases | 1512 |
| l3v2 semantic cases in the vendored suite | 1690 |

## Test-suite cases used as fixtures

These were selected by scanning the vendored suite; each exercises the named construct.

| Construct | Cases (`semantic/<NNNNN>/<NNNNN>-sbml-l3v2.xml`) |
| --- | --- |
| unit definitions | `00001`, `00002`, `00003`, `00004` |
| function definitions | `00025`, `00034`, `00035`, `00078` |
| events | `00026`, `00041`, `00071`, `00072` |
| local parameters | `00027`, `00057`, `00058`, `00132` |
| algebraic rules | `00039`, `00040`, `00182`, `00184` |
| modifiers | `00039`, `00063`, `00064`, `00065` |
| constraints | `01247` |
| species conversionFactor | `00976`, `00977`, `01000` |
| variable stoichiometry | `00969`, `00970`, `00971` |

## File Structure

| File | Responsibility |
| --- | --- |
| `tests/test_roundtrip.py` | **new.** The simulation round-trip harness and every round-trip test case. |
| `scripts/roundtrip_report.py` | **new.** Full-sweep reporting script, run locally or nightly, not part of pytest. |
| `src/sbmlutils/factory.py` | The data model. All new classes (`Unit`, `KineticLaw`, `LocalParameter`, `EventAssignment`) live here, next to their peers. |
| `src/sbmlutils/parser.py` | SBML into the data model. Grows one branch per construct. |
| `src/sbmlutils/notes.py` | Notes format detection and normalization. |
| `src/sbmlutils/reaction_equation.py` | `ReactionEquation.modifiers` becomes typed. |
| `pyproject.toml` | The `sbml_testsuite` pytest marker. |
| `tox.ini` | Deselect the full sweep in the default test env. |
| `release-notes/` | The release note for this change. |

`factory.py` is already 3726 lines and this plan adds to it. Splitting it is **out of scope** and must not be attempted here; it would make the diff unreviewable. A follow-up issue is the right home for that.

---

### Task 1: Simulation round-trip harness

Builds the measuring instrument first. It asserts the behaviour that already works, so it is a regression guard from this point on, and every later task adds cases to it.

**Files:**
- Create: `tests/test_roundtrip.py`
- Create: `scripts/roundtrip_report.py`
- Modify: `pyproject.toml` (pytest markers)
- Modify: `tox.ini` (deselect the sweep)

**Interfaces:**
- Consumes: nothing.
- Produces: `assert_roundtrip_simulates_equal(sbml_path: Path, tmp_path: Path) -> None` and `testsuite_case(case: str) -> Path`, used by every later task's tests.

- [ ] **Step 1: Write the harness and the passing-today cases**

Create `tests/test_roundtrip.py`:

```python
"""Round-trip tests.

A round trip is `SBML -> sbml_to_model -> create_model -> SBML`. It must
preserve the simulation behaviour of the model: simulating the original and
simulating the round-tripped document must give the same trajectories.

The models are the semantic cases of the vendored SBML test suite. They are
test data of the repository and are not part of the distribution, so they are
resolved from `sbmlutils.resources.SBML_TESTSUITE_DIR`.

roadrunner is the optional `examples` extra, which `dev` and the tox test
environment pull in. It is `None` when it is not installed, which is what
these tests skip on, following the `cobra` pattern of `sbmlutils.fbc.cobra`.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import SBML_TESTSUITE_DIR
from sbmlutils.validation import ValidationOptions

if TYPE_CHECKING:
    import roadrunner
else:
    try:
        import roadrunner
    except ImportError:
        roadrunner = None

requires_roadrunner = pytest.mark.skipif(
    roadrunner is None, reason="requires libroadrunner"
)

#: the semantic cases of the vendored SBML test suite
SEMANTIC_DIR: Path = Path(SBML_TESTSUITE_DIR) / "semantic"

#: uniform timecourse the round-trip comparison simulates
T_END: float = 10.0
T_STEPS: int = 51

#: tolerances of the trajectory comparison
RTOL: float = 1e-4
ATOL: float = 1e-6


def testsuite_case(case: str, level_version: str = "l3v2") -> Path:
    """Resolve a semantic test suite case to its SBML path.

    Args:
        case: the five digit case id, e.g. `"00001"`
        level_version: the SBML level and version flavour, e.g. `"l3v2"`

    Returns:
        the path of the SBML file of the case
    """
    return SEMANTIC_DIR / case / f"{case}-sbml-{level_version}.xml"


def _simulate(sbml_path: Path) -> tuple[list[str], np.ndarray]:
    """Simulate a uniform timecourse of the given SBML.

    Args:
        sbml_path: path of the SBML file to simulate

    Returns:
        the selection names and the simulation data
    """
    rr = roadrunner.RoadRunner(str(sbml_path))
    rr.timeCourseSelections = (
        ["time"]
        + rr.model.getFloatingSpeciesIds()
        + rr.model.getBoundarySpeciesIds()
        + rr.model.getGlobalParameterIds()
    )
    result = rr.simulate(0.0, T_END, T_STEPS)
    return list(result.colnames), np.array(result)


def assert_roundtrip_simulates_equal(sbml_path: Path, tmp_path: Path) -> None:
    """Assert that a round trip preserves the simulation behaviour.

    Simulates the given SBML, round trips it through the internal model and
    simulates the result, then compares the trajectories selection by
    selection.

    Args:
        sbml_path: path of the SBML file to round trip
        tmp_path: directory the round-tripped SBML is written to

    Raises:
        AssertionError: if the selections or the trajectories differ
    """
    columns_ref, data_ref = _simulate(sbml_path)

    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    columns_rt, data_rt = _simulate(roundtrip_path)

    assert set(columns_ref) == set(columns_rt), (
        f"selections differ after the round trip of '{sbml_path.name}': "
        f"{sorted(set(columns_ref) ^ set(columns_rt))}"
    )
    for k, column in enumerate(columns_ref):
        np.testing.assert_allclose(
            data_rt[:, columns_rt.index(column)],
            data_ref[:, k],
            rtol=RTOL,
            atol=ATOL,
            err_msg=f"'{sbml_path.name}' differs in selection '{column}'",
        )


#: cases which round trip correctly today, they guard against regressions
CASES_BASELINE: list[str] = ["00001", "00002", "00003", "00004", "00005", "00006"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_BASELINE)
def test_roundtrip_baseline(case: str, tmp_path: Path) -> None:
    """Test that cases which round trip today keep round tripping."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 2: Run the baseline tests to verify they pass**

Run: `uv run pytest tests/test_roundtrip.py -v`
Expected: 6 PASS. These cases already round trip; if any fails, stop and report, because the baseline measurement is then wrong.

- [ ] **Step 3: Add the pytest marker**

In `pyproject.toml`, replace the `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
	"sbml_testsuite: full sweep over the vendored SBML test suite, slow; deselect with -m 'not sbml_testsuite'",
]
```

- [ ] **Step 4: Deselect the sweep in the default tox env**

In `tox.ini`, change the `[testenv]` commands:

```ini
commands =
    pytest -m "not sbml_testsuite"
```

- [ ] **Step 5: Add the full-sweep test**

Append to `tests/test_roundtrip.py`:

```python
#: every l3v2 semantic case of the vendored suite
SWEEP_CASES: list[Path] = sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml"))


def sbml_case_idfn(sbml_path: Path) -> str:
    """Inject the case name into the test name."""
    return sbml_path.name


@requires_roadrunner
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_roundtrip_sweep(sbml_path: Path, tmp_path: Path) -> None:
    """Round trip every l3v2 semantic case of the SBML test suite.

    This is the full sweep behind the `sbml_testsuite` marker, it is
    deselected in the default test run.
    """
    assert_roundtrip_simulates_equal(sbml_path, tmp_path)
```

- [ ] **Step 6: Verify the marker deselects the sweep**

Run: `uv run pytest tests/test_roundtrip.py -m "not sbml_testsuite" --collect-only -q | tail -3`
Expected: 6 tests collected, not 1696.

- [ ] **Step 7: Write the reporting script**

Create `scripts/roundtrip_report.py`:

```python
"""Report the round-trip simulation pass rate over the SBML test suite.

Run the full sweep and print a summary, for local runs and for tracking
progress on https://github.com/matthiaskoenig/sbmlutils/issues/469:

    uv run python scripts/roundtrip_report.py
    uv run python scripts/roundtrip_report.py --limit 200
"""

import argparse
import contextlib
import io
import logging
import sys
from collections import Counter
from pathlib import Path

logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from test_roundtrip import (  # noqa: E402
    SEMANTIC_DIR,
    _simulate,
    assert_roundtrip_simulates_equal,
)


def main() -> None:
    """Run the sweep and print the pass rate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="only the first N cases")
    args = parser.parse_args()

    cases = sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml"))
    if args.limit:
        cases = cases[: args.limit]

    tmp_path = Path(__file__).parent.parent / ".roundtrip_tmp"
    tmp_path.mkdir(exist_ok=True)

    outcome: Counter = Counter()
    failures: list[str] = []
    for sbml_path in cases:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _simulate(sbml_path)
        except Exception:  # noqa: BLE001
            outcome["skipped, the original does not simulate"] += 1
            continue
        try:
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                assert_roundtrip_simulates_equal(sbml_path, tmp_path)
            outcome["passed"] += 1
        except Exception as err:  # noqa: BLE001
            outcome["failed"] += 1
            failures.append(f"{sbml_path.name}: {type(err).__name__}")

    comparable = outcome["passed"] + outcome["failed"]
    print(f"cases          : {len(cases)}")
    for key, value in outcome.most_common():
        print(f"  {value:>5}  {key}")
    if comparable:
        rate = 100.0 * outcome["passed"] / comparable
        print(f"\npass rate      : {outcome['passed']}/{comparable} = {rate:.1f}%")
    print("\nfirst failures:")
    for failure in failures[:30]:
        print(f"  {failure}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Record the baseline**

Run: `uv run python scripts/roundtrip_report.py --limit 150`
Expected: a pass rate near `85/148 = 57.4%`. Write the exact number into the commit message. If it differs by more than one or two cases from 57.4%, stop and report, because the environment then differs from the one the spec was measured in.

- [ ] **Step 9: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`
Expected: all clean.

```bash
git add tests/test_roundtrip.py scripts/roundtrip_report.py pyproject.toml tox.ini
git commit -m "test: add simulation round-trip harness for the SBML test suite

The harness simulates a model, round trips it through the internal model
and simulates the result, then compares the trajectories. The full sweep
sits behind the sbml_testsuite marker so the default test run stays fast.

Measured baseline: <N>/<M> = <RATE>%."
```

---

### Task 2: Silence authoring warnings and check `setId`

Foundational noise reduction. 1512 warnings over 194 cases makes every later task's output unreadable, and the unchecked `setId` hides three silent data losses.

**Files:**
- Modify: `src/sbmlutils/factory.py:443-529` (`Sbase._set_fields`)
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: `assert_roundtrip_simulates_equal`, `testsuite_case` from Task 1.
- Produces: `Sbase._set_fields` no longer warns for a model that came from the parser. The mechanism is a module-level flag set by the parser, described below.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
def test_roundtrip_emits_no_authoring_warnings(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that round tripping does not warn about authoring style.

    The `name` and `sboTerm` warnings of `Sbase._set_fields` are hints for
    somebody writing a model definition. A model which came from a file has
    whatever the file had, so the hints are noise, see
    https://github.com/matthiaskoenig/sbmlutils/issues/469
    """
    model = sbml_to_model(testsuite_case("00001"))
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=tmp_path / "roundtrip.xml",
            sbml_level=3,
            sbml_version=2,
            validation_options=ValidationOptions(units_consistency=False),
        )

    authoring = [
        record.getMessage()
        for record in caplog.records
        if "should be set" in record.getMessage()
    ]
    assert authoring == [], f"round trip emitted authoring warnings: {authoring}"
```

Add `import logging` to the imports of `tests/test_roundtrip.py`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_emits_no_authoring_warnings -v`
Expected: FAIL, with five `'sboTerm' should be set` messages.

- [ ] **Step 3: Add the flag to `Sbase`**

In `src/sbmlutils/factory.py`, add to the `Sbase` class body, next to `fields`:

```python
    #: authoring hints are logged for a hand written model definition, they are
    #: noise for a model which was parsed from a file, see `Sbase.no_authoring_hints`
    _authoring_hints: ClassVar[bool] = True

    @staticmethod
    @contextmanager
    def no_authoring_hints() -> Iterator[None]:
        """Suppress the authoring hints of `_set_fields` inside the context.

        The `name` and `sboTerm` hints help somebody writing a model
        definition. They are noise when a model is written back out after it
        was parsed from a file, which is what `sbmlutils.parser` does.

        Yields:
            None
        """
        previous = Sbase._authoring_hints
        Sbase._authoring_hints = False
        try:
            yield
        finally:
            Sbase._authoring_hints = previous
```

Add `from contextlib import contextmanager` and `from collections.abc import Iterator` to the imports (check whether `Iterator` is already imported from `collections.abc`; `Iterable` is).

- [ ] **Step 4: Guard the two warnings**

In `Sbase._set_fields`, change the `name` branch from:

```python
        if self.name is not None:
            sbase.setName(self.name)
        else:
            if not isinstance(
                self, (Document, Port, ReplacedBy, ReplacedElement, AssignmentRule)
            ):
                logger.warning("'name' should be set on '%s'", self)
```

to:

```python
        if self.name is not None:
            sbase.setName(self.name)
        elif Sbase._authoring_hints and not isinstance(
            self, (Document, Port, ReplacedBy, ReplacedElement, AssignmentRule)
        ):
            logger.warning("'name' should be set on '%s'", self)
```

and the `sboTerm` branch's `else:` similarly, so the `logger.warning("'sboTerm' should be set on '%s'", self)` only fires when `Sbase._authoring_hints` is true. Keep the existing exemption tuple exactly as it is.

- [ ] **Step 5: Mark parsed models**

In `src/sbmlutils/parser.py`, at the end of `sbml_to_model`, before `return m`, the model is not written yet, so the flag belongs where writing happens. Instead record on the model that it was parsed. Add to `sbml_to_model`, immediately after `m = Model(**parse_sbase_kwargs(model))`:

```python
    # a parsed model carries whatever the source file had, so the authoring
    # hints of `Sbase._set_fields` are noise when it is written back out
    m.parsed = True
```

and in `factory.py`, in `Model.__init__`, before `self._freeze()`:

```python
        #: `True` when the model was created by `sbmlutils.parser`, which
        #: suppresses the authoring hints when it is written back out
        self.parsed = False
```

Declare `parsed: bool` in the `Model` class-level annotations next to `layouts`, and add `"parsed": None` to the `_keys` ClassVar.

- [ ] **Step 6: Suppress the hints when writing a parsed model**

In `factory.py`, in `Model.create_sbml`, wrap the body:

```python
    def create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create Model.

        To create the complete SBMLDocument with the model use:

          doc = Document(model=model).create_sbml()
        """
        if self.parsed:
            with Sbase.no_authoring_hints():
                return self._create_sbml(doc)
        return self._create_sbml(doc)

    def _create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create the libsbml.Model and all its objects."""
        model: libsbml.Model = doc.createModel()
        ...
```

Move the existing body of `create_sbml` into `_create_sbml` unchanged.

- [ ] **Step 7: Run the test to verify it passes**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_emits_no_authoring_warnings -v`
Expected: PASS.

- [ ] **Step 8: Check the `setId` return code**

In `Sbase._set_fields`, change:

```python
            sbase.setId(self.sid)
```

to:

```python
            check(sbase.setId(self.sid), f"Set id '{self.sid}' on {sbase}")
```

- [ ] **Step 9: Run the full test suite to see what the check surfaces**

Run: `uv run pytest -m "not sbml_testsuite" -q 2>&1 | tail -20`
Expected: the suite still passes. `check()` logs rather than raises, so newly surfaced `setId` failures on `Rule`, `InitialAssignment` and `EventAssignment` appear as log output. Record in the commit message which element types now log. **Do not fix them here**; Task 12 handles rule ids.

- [ ] **Step 10: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/factory.py src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "fix: suppress authoring hints for parsed models and check setId

The 'name' and 'sboTerm' hints of Sbase._set_fields are for somebody
writing a model definition; a parsed model has whatever its source file
had. Re-emitting 194 test suite cases produced 1512 such warnings.

setId was called without checking its return code, which silently
swallowed the ids of rules, initial assignments and event assignments."
```

---

### Task 3: Notes round-trip as XHTML

**Files:**
- Modify: `src/sbmlutils/notes.py`
- Modify: `src/sbmlutils/factory.py` (`Sbase.__init__`, `Sbase._set_fields`, remove `get_notes_xml`)
- Modify: `src/sbmlutils/parser.py:155-156`
- Test: `tests/test_notes.py`, `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces: `sbmlutils.notes.detect_format(notes: str) -> NotesFormat` and `Sbase.__init__(..., notes_format: NotesFormat | None = None)`. `Sbase.notes` holds XHTML after construction.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_notes.py`:

```python
def test_detect_format_markdown() -> None:
    """Test that a markdown string is detected as markdown."""
    assert detect_format("A **glucose** species") == NotesFormat.MARKDOWN


def test_detect_format_html() -> None:
    """Test that an XHTML string is detected as html."""
    notes = '<body xmlns="http://www.w3.org/1999/xhtml"><p>text</p></body>'
    assert detect_format(notes) == NotesFormat.HTML


def test_detect_format_leading_whitespace() -> None:
    """Test that leading whitespace does not hide the markup."""
    notes = '\n  <body xmlns="http://www.w3.org/1999/xhtml"><p>text</p></body>'
    assert detect_format(notes) == NotesFormat.HTML


def test_detect_format_markdown_with_inline_html() -> None:
    """Test that markdown which merely contains a tag stays markdown.

    Only a string which *starts* with markup is html, so a markdown
    paragraph using an inline tag is still rendered as markdown.
    """
    assert detect_format("see <b>this</b> value") == NotesFormat.MARKDOWN


def test_notes_html_is_not_rendered() -> None:
    """Test that html notes are stored verbatim.

    Markdown rendering mutates plain text, `2*3*4` becomes `2<em>3</em>4`,
    which must not happen to notes which came from an SBML file.
    """
    notes = '<body xmlns="http://www.w3.org/1999/xhtml"><p>2*3*4</p></body>'
    assert "2*3*4" in str(Notes(notes, format=NotesFormat.HTML))
    assert "<em>" not in str(Notes(notes, format=NotesFormat.HTML))
```

Add `detect_format` to the import of `tests/test_notes.py`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_notes.py -v -k "detect_format or html_is_not_rendered"`
Expected: FAIL with `ImportError: cannot import name 'detect_format'`.

- [ ] **Step 3: Implement `detect_format`**

In `src/sbmlutils/notes.py`, add:

```python
def detect_format(notes: str) -> NotesFormat:
    """Detect whether notes are markdown or XHTML.

    The rule is deliberately structural rather than a heuristic on the
    content: notes whose first non-whitespace character is `<` and which
    parse as XML are html, everything else is markdown. A markdown
    paragraph which merely contains an inline tag therefore stays markdown.

    Args:
        notes: the notes string

    Returns:
        `NotesFormat.HTML` for notes which are already markup, else
        `NotesFormat.MARKDOWN`
    """
    stripped = notes.strip()
    if not stripped.startswith("<"):
        return NotesFormat.MARKDOWN

    xml: libsbml.XMLNode | None = libsbml.XMLNode.convertStringToXMLNode(
        f'<body xmlns="http://www.w3.org/1999/xhtml">{stripped}</body>'
    )
    return NotesFormat.HTML if xml is not None else NotesFormat.MARKDOWN
```

- [ ] **Step 4: Unwrap a `<notes>` wrapper**

In `Notes.__init__`, before the format branch, add:

```python
        # an SBML `<notes>` element wraps the xhtml body, parsing it back in
        # must not nest a second body inside it
        stripped = notes.strip()
        if stripped.startswith("<notes"):
            start = stripped.find(">") + 1
            end = stripped.rfind("</notes>")
            notes = stripped[start:end] if end > start else stripped
```

and make the body wrapping skip a string which is already a body:

```python
        # insert body text with namespace
        if html.strip().startswith("<body"):
            notes_str = html.strip()
        else:
            notes_str = f'<body xmlns="http://www.w3.org/1999/xhtml">\n{html}\n</body>'
```

- [ ] **Step 5: Run the notes tests**

Run: `uv run pytest tests/test_notes.py -v`
Expected: all PASS.

- [ ] **Step 6: Normalize notes on `Sbase`**

In `factory.py`, in `Sbase.__init__`, add the parameter `notes_format: NotesFormat | None = None` after `notes`, and replace `self.notes = notes` with:

```python
        self.notes_format = notes_format
        self.notes = notes
```

In `Sbase._set_fields`, replace:

```python
        if self.notes is not None and self.notes.strip():
            set_notes(sbase, self.notes)
```

with:

```python
        if self.notes is not None and self.notes.strip():
            notes_format = (
                self.notes_format
                if self.notes_format is not None
                else detect_format(self.notes)
            )
            set_notes(sbase, self.notes, format=notes_format)
```

Import `detect_format` and `NotesFormat` in `factory.py`.

Add `"notes_format"` to the `Sbase.fields` ClassVar, after `"notes"`.

- [ ] **Step 7: Remove the dead `get_notes_xml`**

Delete `Sbase.get_notes_xml` (`factory.py:435-441`). Verify nothing calls it:

Run: `grep -rn "get_notes_xml" src/ tests/ examples/ docs/`
Expected: no output.

- [ ] **Step 8: Enable notes in the parser**

In `src/sbmlutils/parser.py`, replace the commented-out block:

```python
        # if d["notes"]:
        #     kwargs["notes"] = d["notes"]  # This is an XML string.
```

with:

```python
        # notes are the xhtml of the source document, they are stored verbatim
        if d["notes"]:
            kwargs["notes"] = d["notes"]
            kwargs["notes_format"] = NotesFormat.HTML
```

Import `NotesFormat` from `sbmlutils.notes` in `parser.py`. Remove the `FIXME: no support for notes` line from the module docstring.

- [ ] **Step 9: Write the round-trip notes test**

Append to `tests/test_roundtrip.py`:

```python
def test_roundtrip_preserves_notes(tmp_path: Path) -> None:
    """Test that notes survive a round trip unchanged.

    Notes used to be stored as markdown and rendered on write, so notes read
    from a file came back nested and their text was mutated.
    """
    from sbmlutils.io.sbml import read_sbml
    from sbmlutils.resources import REPRESSILATOR_SBML

    model = sbml_to_model(REPRESSILATOR_SBML)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    doc_rt = read_sbml(roundtrip_path)
    notes_rt = doc_rt.getModel().getNotesString()
    assert notes_rt, "the model lost its notes"
    assert "<notes>" not in notes_rt[7:], "notes were nested on write"
```

- [ ] **Step 10: Run and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/notes.py src/sbmlutils/factory.py src/sbmlutils/parser.py tests/test_notes.py tests/test_roundtrip.py
git commit -m "feat: round trip notes as xhtml

Sbase.notes stored markdown and rendered it through MarkdownIt on write,
so notes read from a file came back as nested <body><notes><body> and
plain text was mutated: '2*3*4' became '2<em>3</em>4'. Notes are now
normalized to xhtml at construction, markdown is still accepted and
rendered once, and the parser reads notes again."
```

---

### Task 4: Stop inventing SBO annotations

**Files:**
- Modify: `src/sbmlutils/factory.py:505-519`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces: writing a model no longer adds a CVTerm for the `sboTerm`, and no longer forces a `metaid`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
def test_roundtrip_invents_no_cvterms(tmp_path: Path) -> None:
    """Test that a round trip adds no annotation which was not in the source.

    `Sbase._set_fields` used to inject an `Annotation(BQB.IS, f"sbo/{sboTerm}")`
    whenever an sboTerm was set, which duplicated the sboTerm attribute as a
    CVTerm and forced a metaid onto elements which had none.
    """
    import libsbml

    from sbmlutils.resources import REPRESSILATOR_SBML

    def cvterm_count(sbml_path: Path) -> int:
        model = libsbml.readSBMLFromFile(str(sbml_path)).getModel()
        total = model.getNumCVTerms()
        for getter, count in (
            (model.getSpecies, model.getNumSpecies()),
            (model.getReaction, model.getNumReactions()),
            (model.getCompartment, model.getNumCompartments()),
            (model.getParameter, model.getNumParameters()),
        ):
            for k in range(count):
                total += getter(k).getNumCVTerms()
        return total

    model = sbml_to_model(REPRESSILATOR_SBML)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert cvterm_count(roundtrip_path) == cvterm_count(Path(REPRESSILATOR_SBML))
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_invents_no_cvterms -v`
Expected: FAIL, the round-tripped count is larger by the number of elements carrying an sboTerm.

- [ ] **Step 3: Remove the injection**

In `factory.py`, in `Sbase._set_fields`, delete the whole block:

```python
        if self.sboTerm is not None:
            sbo_annotation = Annotation(
                qualifier=BQB.IS, resource=f"sbo/{self.sboTerm.replace('_', ':')}"
            )
            # check if SBO annotation exists
            sbo_exists = False
            for annotation in processed_annotations:
                if (
                    annotation.qualifier == sbo_annotation.qualifier
                    and annotation.term == sbo_annotation.term
                ):
                    sbo_exists = True
                    continue
            if not sbo_exists:
                processed_annotations = [sbo_annotation, *processed_annotations]
```

Leave the loop that follows it (`for annotation in processed_annotations: annotator.ModelAnnotator.annotate_sbase(...)`) unchanged.

Remove the now-unused `BQB` import from `factory.py` if ruff reports it as unused; keep `Annotation`, which is still used by `_process_annotations`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_invents_no_cvterms -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -m "not sbml_testsuite" -q`
Expected: PASS. If a test asserted the injected CVTerm, it must be updated to assert the `sboTerm` attribute instead; report which test if so.

- [ ] **Step 6: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check`

```bash
git add src/sbmlutils/factory.py tests/test_roundtrip.py
git commit -m "fix: do not duplicate the sboTerm as a CVTerm

Writing a model injected an Annotation(BQB.IS, 'sbo/<term>') whenever an
sboTerm was set. That invented an annotation which was not in the source,
forced a metaid onto elements which had none, and added 28 CVTerms to the
repressilator in a single round trip. The sboTerm attribute already
carries the term."
```

---

### Task 5: The unit data model

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Unit`, `UnitDefinition`, `UnitType`, `Units`, `ValueWithUnit`, `ModelUnits`, `Model.units`)
- Test: `tests/test_factory.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `Unit(kind: str, exponent: float = 1.0, scale: int = 0, multiplier: float = 1.0)`
  - `UnitDefinition(sid, definition=None, units: list[Unit] | None = None, ...)` with `UnitDefinition.units: list[Unit] | None`
  - `UnitType: TypeAlias = "UnitDefinition | str | None"`
  - `UnitDefinition.get_uid_for_unit` returns the string unchanged for a `str`
  - `Model.units` accepts `type[Units] | list[UnitDefinition] | None` and stores `list[UnitDefinition]`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_factory.py`:

```python
def test_unit_definition_from_units() -> None:
    """Test that a UnitDefinition can be built from explicit units."""
    udef = UnitDefinition(
        "mM",
        units=[Unit("mole", 1.0, -3, 1.0), Unit("litre", -1.0, 0, 1.0)],
        name="millimolar",
    )
    assert udef.units is not None
    assert len(udef.units) == 2
    assert udef.units[0].kind == "mole"
    assert udef.units[0].scale == -3


def test_unit_definition_preserves_scale() -> None:
    """Test that an explicit scale survives writing to SBML.

    `create_sbml` used to hardcode `scale = 0`, so a source using
    `scale="-3" multiplier="1"` came back as `scale="0" multiplier="0.001"`.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = UnitDefinition("mM", units=[Unit("mole", 1.0, -3, 1.0)])
    udef.create_sbml(model)

    sbml_udef = model.getUnitDefinition("mM")
    assert sbml_udef.getUnit(0).getScale() == -3
    assert sbml_udef.getUnit(0).getMultiplier() == 1.0


def test_unit_definition_non_pint_sid() -> None:
    """Test that a unit id which pint cannot parse is representable.

    The SBML test suite uses the ids `substance`, `volume` and `time`, and
    `definition` defaults to `sid`, so these used to raise UndefinedUnitError.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = UnitDefinition("substance", units=[Unit("mole", 1.0, 0, 1.0)])
    udef.create_sbml(model)

    assert model.getUnitDefinition("substance") is not None


def test_model_units_accepts_list() -> None:
    """Test that Model.units accepts a list of UnitDefinitions."""
    model = Model(
        "test",
        units=[UnitDefinition("mM", units=[Unit("mole", 1.0, -3, 1.0)])],
    )
    assert isinstance(model.units, list)
    assert model.units[0].sid == "mM"


def test_model_units_accepts_units_class() -> None:
    """Test that the `class U(Units)` authoring style still works."""

    class U(Units):
        mM = UnitDefinition("mM", "mmole/liter")

    model = Model("test", units=U)
    assert isinstance(model.units, list)
    assert any(udef.sid == "mM" for udef in model.units)


def test_unit_reference_by_id() -> None:
    """Test that a unit can be referenced by its id string."""
    assert UnitDefinition.get_uid_for_unit("mymole") == "mymole"
```

Ensure `Unit`, `UnitDefinition`, `Units`, `Model` and `libsbml` are imported in `tests/test_factory.py`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_factory.py -v -k "unit_definition or model_units or unit_reference"`
Expected: FAIL with `ImportError` / `NameError` for `Unit`.

- [ ] **Step 3: Add the `Unit` class**

In `factory.py`, immediately before `class UnitDefinition(Sbase):`:

```python
class Unit:
    """A single unit of a `UnitDefinition`.

    Corresponds to the information in a `libsbml.Unit`, i.e. one factor of a
    unit definition. An SBML unit is `multiplier * 10^scale * kind^exponent`.
    """

    def __init__(
        self,
        kind: str,
        exponent: float = 1.0,
        scale: int = 0,
        multiplier: float = 1.0,
    ):
        """Construct a Unit.

        Args:
            kind: the SBML unit kind, e.g. `"litre"`
            exponent: the exponent of the unit
            scale: the decimal scale of the unit
            multiplier: the multiplier of the unit
        """
        self.kind = kind
        self.exponent = exponent
        self.scale = scale
        self.multiplier = multiplier

    def __repr__(self) -> str:
        """Get string representation."""
        return (
            f"Unit({self.kind}, exponent={self.exponent}, "
            f"scale={self.scale}, multiplier={self.multiplier})"
        )

    def __eq__(self, other: object) -> bool:
        """Compare two units."""
        if not isinstance(other, Unit):
            return NotImplemented
        return (
            self.kind == other.kind
            and self.exponent == other.exponent
            and self.scale == other.scale
            and self.multiplier == other.multiplier
        )

    def create_sbml(self, udef: libsbml.UnitDefinition) -> libsbml.Unit:
        """Create the libsbml.Unit in the given libsbml.UnitDefinition.

        Args:
            udef: the libsbml.UnitDefinition the unit is created in

        Returns:
            the created libsbml.Unit
        """
        unit: libsbml.Unit = udef.createUnit()
        kind = libsbml.UnitKind_forName(self.kind)
        if kind == libsbml.UNIT_KIND_INVALID:
            logger.error("'%s' is not a valid SBML unit kind.", self.kind)
        check(unit.setKind(kind), f"Set kind '{self.kind}' on unit")
        check(unit.setExponent(float(self.exponent)), "Set exponent on unit")
        check(unit.setScale(int(self.scale)), "Set scale on unit")
        check(unit.setMultiplier(float(self.multiplier)), "Set multiplier on unit")
        return unit
```

- [ ] **Step 4: Give `UnitDefinition` a `units` list**

Change `UnitDefinition.__init__` to accept `units: list[Unit] | None = None` after `definition`, and set:

```python
        self.units = units
        if units is not None:
            # explicit units are authoritative, the definition is only a label
            self.definition = definition if definition is not None else sid
        else:
            self.definition = definition if definition is not None else sid
        if not self.name:
            self.name = self.definition
```

Replace the body of `UnitDefinition.create_sbml` so that it resolves `self.units` first and only falls back to the pint path:

```python
    def create_sbml(self, model: libsbml.Model) -> libsbml.UnitDefinition | None:
        """Create libsbml.UnitDefinition."""
        if self.units is None and isinstance(self.definition, int):
            # libsbml unit kind, the unit definition is a base unit
            return None

        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        units = self.units if self.units is not None else self._units_from_definition()
        for unit in units:
            unit.create_sbml(obj)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _units_from_definition(self) -> list[Unit]:
        """Compile the pint definition string into explicit units.

        Returns:
            the units the pint expression of `definition` resolves to

        Raises:
            ValueError: if a unit of the expression has no SBML unit kind
        """
```

Move the existing pint parsing body into `_units_from_definition`, changing it to build and return `list[Unit]` rather than calling `_create_unit`. Keep the existing multiplier and prefix arithmetic exactly as it is, including `multiplier = np.power(multiplier, 1 / abs(exponent))`, so the pint path produces byte-identical output to today. Map the libsbml integer kind back to its name with `libsbml.UnitKind_toString(kind)`. Delete the now-unused `_create_unit` static method.

- [ ] **Step 5: Widen `UnitType` and `get_uid_for_unit`**

Change the alias:

```python
UnitType: TypeAlias = "UnitDefinition | str | None"
```

and `get_uid_for_unit`:

```python
    @staticmethod
    def get_uid_for_unit(unit: UnitDefinition | str | None) -> str | None:
        """Get unit id for the given unit.

        Args:
            unit: a UnitDefinition or the id of one

        Returns:
            the unit id, `None` if no unit was given
        """
        if unit is None:
            return None
        if isinstance(unit, UnitDefinition):
            return unit.sid
        return unit
```

In `ValueWithUnit.__init__`, the warning `"'unit' must be of type UnitDefinition"` must no longer fire for a `str`:

```python
        self.unit = unit
        if self.unit is not None and not isinstance(self.unit, (UnitDefinition, str)):
            logger.warning(
                "'unit' must be a UnitDefinition or a unit id, but '%s' in '%s' is '%s'.",
                self.unit,
                self,
                type(self.unit),
            )
```

- [ ] **Step 6: Normalize `Model.units` to a list**

In `Model.__init__`, replace `self.units = units if units else Units` with:

```python
        self.units = Model._normalize_units(units)
```

and add the static method to `Model`:

```python
    @staticmethod
    def _normalize_units(
        units: type[Units] | list[UnitDefinition] | None,
    ) -> list[UnitDefinition]:
        """Normalize the units of a model to a list of UnitDefinitions.

        A model definition declares its units as a `class U(Units)`, which is
        the documented authoring style; the parser passes a list. Both are
        stored as a list.

        Args:
            units: a `Units` subclass, a list of UnitDefinitions, or None

        Returns:
            the unit definitions of the model
        """
        if units is None:
            return []
        if isinstance(units, list):
            return units

        udefs: list[UnitDefinition] = []
        for uid, definition in units.attributes():
            if isinstance(definition, str):
                udefs.append(UnitDefinition(sid=uid, definition=definition))
            elif isinstance(definition, UnitDefinition):
                udefs.append(definition)
            else:
                raise ValueError(
                    f"Units attributes must be a unit string or UnitDefinition, "
                    f"but '{type(definition)}' for '{definition}'."
                )
        return udefs
```

Change the declared field type to `units: list[UnitDefinition]` and the constructor parameter to `units: type[Units] | list[UnitDefinition] | None = None`.

In `Model.create_sbml` (now `_create_sbml` after Task 2), replace:

```python
        # units
        if self.units:
            self.units.create_unit_definitions(model=model)
```

with:

```python
        # units
        for udef in self.units:
            udef.create_sbml(model=model)
```

Keep `Units.create_unit_definitions` in place for backward compatibility, but have it delegate:

```python
    @classmethod
    def create_unit_definitions(cls, model: libsbml.Model) -> None:
        """Create the libsbml.UnitDefinitions in the model.

        Deprecated, `Model` normalizes its units to a list of
        `UnitDefinition` and creates them directly.
        """
        for udef in Model._normalize_units(cls):
            udef.create_sbml(model=model)
```

- [ ] **Step 7: Let `ModelUnits` take unit ids**

In `ModelUnits.set_model_units`, the six attributes go through `UnitDefinition.get_uid_for_unit`, which now accepts a string, so no change is needed beyond confirming the annotations are `UnitType`. Verify by reading `factory.py:242-297` and widen any annotation still typed `UnitDefinition | None`.

- [ ] **Step 8: Run the tests**

Run: `uv run pytest tests/test_factory.py -v -k "unit_definition or model_units or unit_reference"`
Expected: all PASS.

- [ ] **Step 9: Run the full suite and the unit tests specifically**

Run: `uv run pytest -m "not sbml_testsuite" -q && uv run pytest tests/test_udef_to_str.py -q`
Expected: PASS. The pint path must produce identical output to before; if `test_udef_to_str.py` fails, the refactor of `_units_from_definition` changed behaviour and must be corrected.

- [ ] **Step 10: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check`

```bash
git add src/sbmlutils/factory.py tests/test_factory.py
git commit -m "feat: represent unit definitions as explicit units

A UnitDefinition stored only a pint expression which was parsed at write
time, with scale hardcoded to 0, so an arbitrary SBML unitDefinition was
not representable and ids like 'substance' raised. UnitDefinition now
holds a list of Unit(kind, exponent, scale, multiplier); the pint string
stays the authoring style and compiles into that list. Model.units
accepts a list as well as a Units subclass, and a unit can be referenced
by id."
```

---

### Task 6: Parse units

**Files:**
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: `Unit`, `UnitDefinition`, `Model.units` as a list, `UnitType` accepting `str` (Task 5).
- Produces: a parsed `Model` carries `units`, `model_units`, and the `unit` of every parameter, compartment and species.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
#: cases whose round trip depends on unit definitions being preserved
CASES_UNITS: list[str] = ["00001", "00002", "00003", "00004"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_UNITS)
def test_roundtrip_units(case: str, tmp_path: Path) -> None:
    """Test that unit definitions and unit references survive a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)


def test_roundtrip_preserves_unit_definitions(tmp_path: Path) -> None:
    """Test that the listOfUnitDefinitions and the model units are preserved."""
    import libsbml

    sbml_path = testsuite_case("00038")
    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    m_in = libsbml.readSBMLFromFile(str(sbml_path)).getModel()
    m_out = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()

    assert {
        m_out.getUnitDefinition(k).getId() for k in range(m_out.getNumUnitDefinitions())
    } == {
        m_in.getUnitDefinition(k).getId() for k in range(m_in.getNumUnitDefinitions())
    }
    assert m_out.getTimeUnits() == m_in.getTimeUnits()
    assert m_out.getCompartment(0).getUnits() == m_in.getCompartment(0).getUnits()
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py -v -k "units"`
Expected: FAIL, the round-tripped model has no unit definitions.

- [ ] **Step 3: Parse the unit definitions**

In `parser.py`, in `sbml_to_model`, after the model is constructed and before the parameters loop:

```python
    # unit definitions
    udef: libsbml.UnitDefinition
    for udef in model.getListOfUnitDefinitions():
        units: list[Unit] = []
        u: libsbml.Unit
        for u in udef.getListOfUnits():
            units.append(
                Unit(
                    kind=libsbml.UnitKind_toString(u.getKind()),
                    exponent=u.getExponent() if u.isSetExponent() else 1.0,
                    scale=u.getScale() if u.isSetScale() else 0,
                    multiplier=u.getMultiplier() if u.isSetMultiplier() else 1.0,
                )
            )
        m.units.append(UnitDefinition(units=units, **parse_sbase_kwargs(udef)))
```

`parse_sbase_kwargs` returns `sid`, so `UnitDefinition(units=..., **kwargs)` supplies `sid` positionally by keyword. `UnitDefinition.__init__` does not accept `uncertainties`, so strip that key:

```python
    def parse_udef_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
        """Parse SBase information of a UnitDefinition.

        A UnitDefinition has no uncertainties, so that key is removed.
        """
        kwargs = parse_sbase_kwargs(sbase)
        kwargs.pop("uncertainties", None)
        return kwargs
```

and use `parse_udef_kwargs(udef)`.

Import `Unit` and `UnitDefinition` from `sbmlutils.factory` in `parser.py`.

- [ ] **Step 4: Parse the model units**

After the unit definitions loop:

```python
    # model units
    m.model_units = ModelUnits(
        time=model.getTimeUnits() if model.isSetTimeUnits() else None,
        extent=model.getExtentUnits() if model.isSetExtentUnits() else None,
        substance=model.getSubstanceUnits() if model.isSetSubstanceUnits() else None,
        length=model.getLengthUnits() if model.isSetLengthUnits() else None,
        area=model.getAreaUnits() if model.isSetAreaUnits() else None,
        volume=model.getVolumeUnits() if model.isSetVolumeUnits() else None,
    )
```

Import `ModelUnits`. Confirm the `ModelUnits.__init__` parameter names by reading `factory.py:224-241` and match them exactly.

- [ ] **Step 5: Parse the unit of each element**

In the parameters loop, replace `# unit=p.getUnits(),` with:

```python
                unit=p.getUnits() if p.isSetUnits() else None,
```

In the compartments loop, replace `# unit=p.getUnits(),` with:

```python
                unit=c.getUnits() if c.isSetUnits() else None,
```

In the species loop, replace `# unit=p.getUnits(),` with:

```python
                substanceUnit=(
                    s.getSubstanceUnits() if s.isSetSubstanceUnits() else None
                ),
```

Note the `Species` constructor parameter is `substanceUnit`, singular, while the attribute is `substanceUnits`. Confirm against `factory.py:1221`.

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_roundtrip.py -v -k "units"`
Expected: PASS.

- [ ] **Step 7: Measure progress**

Run: `uv run python scripts/roundtrip_report.py --limit 150`
Expected: the pass rate has risen above the 57.4% baseline. Record it in the commit message.

- [ ] **Step 8: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "feat: parse unit definitions and unit references

Every one of the first 200 test suite cases lost its unit definitions,
523 species lost their substanceUnits and 173 compartments their units.
The parser now reads the listOfUnitDefinitions, the model unit
attributes and the unit of every parameter, compartment and species.

Round-trip pass rate: <RATE>%."
```

---

### Task 7: Parse function definitions

**Files:**
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers. `Function` already exists in `factory.py:1013-1063` and needs no change.
- Produces: a parsed `Model` carries `functions`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
#: cases which use a functionDefinition
CASES_FUNCTIONS: list[str] = ["00025", "00034", "00035", "00078"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_FUNCTIONS)
def test_roundtrip_function_definitions(case: str, tmp_path: Path) -> None:
    """Test that function definitions survive a round trip.

    Dropping them produced libsbml error 10214, `a <ci> element in this
    context must refer to a function definition`, in 48 of 150 cases.
    """
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py -v -k "function_definitions"`
Expected: FAIL, roadrunner cannot load the round-tripped model.

- [ ] **Step 3: Parse the function definitions**

In `parser.py`, after the unit definitions and before the parameters loop:

```python
    # function definitions
    fd: libsbml.FunctionDefinition
    for fd in model.getListOfFunctionDefinitions():
        ast = fd.getMath() if fd.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        if formula:
            m.functions.append(Function(value=formula, **parse_sbase_kwargs(fd)))
```

Import `Function` from `sbmlutils.factory`. Confirm the `Function` constructor parameter name by reading `factory.py:1021-1049`; it is `value`, and `Function` derives from `Sbase`, so it does not accept `uncertainties`. If it does not, reuse the `parse_udef_kwargs` helper from Task 6 and rename it to something neutral such as `parse_sbase_kwargs_no_uncertainties`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_roundtrip.py -v -k "function_definitions"`
Expected: PASS.

- [ ] **Step 5: Measure and commit**

Run: `uv run python scripts/roundtrip_report.py --limit 150`

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "feat: parse function definitions

The parser never read the listOfFunctionDefinitions, so every model using
a user defined function round tripped into SBML which libsbml rejects
with error 10214.

Round-trip pass rate: <RATE>%."
```

---

### Task 8: `KineticLaw` and `LocalParameter`

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Formula`, `Reaction`, new `LocalParameter` and `KineticLaw`)
- Test: `tests/test_factory.py`

**Interfaces:**
- Consumes: `UnitType` accepting `str` (Task 5).
- Produces:
  - `LocalParameter(sid, value, unit=None, ...)`, an `Sbase` subclass
  - `KineticLaw(math: str, unit: UnitType = None, local_parameters: list[LocalParameter] | None = None, ...)`, an `Sbase` subclass
  - `Reaction.formula` is a `KineticLaw | None`; `Reaction._process_formula` normalizes `str`, `tuple[str, UnitType]`, `Formula` and `KineticLaw`
  - `Formula` stays as a deprecated alias accepted by `_process_formula`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_factory.py`:

```python
def test_reaction_formula_string_is_a_kinetic_law() -> None:
    """Test that a formula string is normalized into a KineticLaw."""
    reaction = Reaction("r1", "S1 -> S2", formula="k1 * S1")
    assert isinstance(reaction.formula, KineticLaw)
    assert reaction.formula.math == "k1 * S1"
    assert reaction.formula.local_parameters == []


def test_reaction_formula_tuple_keeps_the_unit() -> None:
    """Test that the unit of a `(math, unit)` tuple is kept.

    `Formula` parsed the unit and `create_sbml` then used only the math, so
    the unit was silently dropped.
    """
    reaction = Reaction("r1", "S1 -> S2", formula=("k1 * S1", "mole_per_s"))
    assert isinstance(reaction.formula, KineticLaw)
    assert reaction.formula.unit == "mole_per_s"


def test_local_parameters_are_local() -> None:
    """Test that local parameters are written into the kinetic law.

    `Reaction.pars` creates global model parameters, which collide when two
    reactions use the same local parameter id.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for sid in ("S1", "S2"):
        species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")

    reaction = Reaction(
        "r1",
        "S1 -> S2",
        formula=KineticLaw(
            math="k * S1", local_parameters=[LocalParameter("k", 0.5)]
        ),
    )
    reaction.create_sbml(model)

    assert model.getNumParameters() == 0, "a local parameter leaked into the model"
    klaw = model.getReaction("r1").getKineticLaw()
    assert klaw.getNumLocalParameters() == 1
    assert klaw.getLocalParameter(0).getId() == "k"
    assert klaw.getLocalParameter(0).getValue() == 0.5
```

Import `KineticLaw` and `LocalParameter` in `tests/test_factory.py`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_factory.py -v -k "formula or local_parameters"`
Expected: FAIL with `ImportError` for `KineticLaw`.

- [ ] **Step 3: Add `LocalParameter`**

In `factory.py`, immediately after `class Parameter(ValueWithUnit):`:

```python
class LocalParameter(ValueWithUnit):
    """LocalParameter of a KineticLaw.

    A local parameter is scoped to the kinetic law it is defined in, unlike a
    `Parameter`, which is global to the model.
    """

    def create_sbml(self, klaw: libsbml.KineticLaw) -> libsbml.LocalParameter:
        """Create the libsbml.LocalParameter in the given kinetic law.

        Args:
            klaw: the libsbml.KineticLaw the local parameter is created in

        Returns:
            the created libsbml.LocalParameter
        """
        lp: libsbml.LocalParameter = klaw.createLocalParameter()
        self._set_fields(lp, None)
        if self.value is not None:
            check(lp.setValue(float(self.value)), f"Set value on '{self.sid}'")
        return lp

    def _set_fields(self, sbase: libsbml.LocalParameter, model: Any) -> None:
        """Set fields on libsbml.LocalParameter."""
        super()._set_fields(sbase, model)
```

`ValueWithUnit._set_fields` calls `sbase.setUnits(uid)`, which a `libsbml.LocalParameter` supports, so the unit is handled by the base class.

- [ ] **Step 4: Add `KineticLaw`**

In `factory.py`, immediately before `class Reaction(Sbase):`:

```python
class KineticLaw(Sbase):
    """KineticLaw of a Reaction.

    Corresponds to the information in a `libsbml.KineticLaw`: the rate math,
    and the local parameters which are scoped to it.
    """

    def __init__(
        self,
        math: str,
        unit: UnitType = None,
        local_parameters: list[LocalParameter] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        notes_format: NotesFormat | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct a KineticLaw.

        Args:
            math: the rate expression, as an SBML L3 formula string
            unit: the unit of the rate, deprecated in SBML L3
            local_parameters: the parameters scoped to this kinetic law
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            notes_format=notes_format,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math
        self.unit = unit
        self.local_parameters = local_parameters if local_parameters else []

    def __repr__(self) -> str:
        """Get string representation."""
        return f"KineticLaw({self.math})"

    def create_sbml(self, reaction: libsbml.Reaction) -> libsbml.KineticLaw:
        """Create the libsbml.KineticLaw on the given reaction.

        Args:
            reaction: the libsbml.Reaction the kinetic law belongs to

        Returns:
            the created libsbml.KineticLaw
        """
        klaw: libsbml.KineticLaw = reaction.createKineticLaw()
        self._set_fields(klaw, None)

        # local parameters must exist before the math is parsed, so that the
        # formula parser resolves their ids
        for local_parameter in self.local_parameters:
            local_parameter.create_sbml(klaw)

        model: libsbml.Model = reaction.getModel()
        ast_node = libsbml.parseL3FormulaWithModel(self.math, model)
        if ast_node is None:
            logger.error(
                "Kinetic law math could not be parsed: '%s', %s",
                self.math,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(klaw.setMath(ast_node), f"Set math on kinetic law '{self.math}'")
        return klaw
```

- [ ] **Step 5: Normalize `Reaction.formula`**

Keep `Formula = namedtuple("Formula", "value unit")` where it is, for backward compatibility, and add a deprecation note to it:

```python
#: deprecated, a kinetic law is a `KineticLaw`; still accepted by
#: `Reaction._process_formula`
Formula = namedtuple("Formula", "value unit")
```

Replace `Reaction._process_formula`:

```python
    @staticmethod
    def _process_formula(
        formula: KineticLaw | Formula | tuple[str, UnitType] | str | None,
    ) -> KineticLaw | None:
        """Process the reaction formula into a KineticLaw.

        Args:
            formula: a KineticLaw, a `(math, unit)` tuple, a math string, or
                None

        Returns:
            the kinetic law of the reaction, None if no formula was given

        Raises:
            ValueError: if the formula is of an unsupported type
        """
        if formula is None:
            return None
        if isinstance(formula, KineticLaw):
            return formula
        if isinstance(formula, str):
            return KineticLaw(math=formula)
        if isinstance(formula, (tuple, list)):
            math, unit = formula
            return KineticLaw(math=math, unit=unit)
        raise ValueError(f"Unsupported formula: '{formula}'")
```

A `Formula` is a `tuple` subclass, so the tuple branch handles it.

Change the `Reaction.__init__` annotation of `formula` to `KineticLaw | Formula | tuple[str, UnitType] | str | None = None`.

- [ ] **Step 6: Write the kinetic law from `create_sbml`**

In `Reaction.create_sbml`, replace the call to `set_kinetic_law` with:

```python
        if self.formula is not None:
            self.formula.create_sbml(r)
```

Read `factory.py:1751-1816` first and remove `Reaction.set_kinetic_law` along with the now-dead code path. If `set_kinetic_law` is referenced elsewhere, keep it as a thin wrapper delegating to `KineticLaw`:

Run: `grep -rn "set_kinetic_law" src/ tests/ examples/ docs/`

Decide based on the result and note it in the commit message.

- [ ] **Step 7: Run the tests**

Run: `uv run pytest tests/test_factory.py -v -k "formula or local_parameters"`
Expected: PASS.

- [ ] **Step 8: Run the full suite**

Run: `uv run pytest -m "not sbml_testsuite" -q`
Expected: PASS. The examples build many reactions with `formula=`, so this is the real check that normalization is backward compatible.

- [ ] **Step 9: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check`

```bash
git add src/sbmlutils/factory.py tests/test_factory.py
git commit -m "feat: model kinetic laws and local parameters

A kinetic law was an untyped namedtuple holding math and a unit, the unit
was silently dropped on write, and local parameters had no representation
at all: Reaction.pars creates global model parameters, which collide when
two reactions use the same local id. KineticLaw and LocalParameter now
mirror the SBML elements; Reaction(formula='k1*S1') is unchanged."
```

---

### Task 9: Parse kinetic laws and local parameters

**Files:**
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: `KineticLaw`, `LocalParameter` (Task 8).
- Produces: a parsed `Reaction.formula` is a `KineticLaw` carrying its local parameters.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
#: cases whose kinetic laws carry local parameters
CASES_LOCAL_PARAMETERS: list[str] = ["00027", "00057", "00058", "00132"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_LOCAL_PARAMETERS)
def test_roundtrip_local_parameters(case: str, tmp_path: Path) -> None:
    """Test that local parameters of a kinetic law survive a round trip.

    Dropping them produced libsbml error 10215, `a <ci> element in this
    context must refer to a model component`.
    """
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py -v -k "local_parameters"`
Expected: FAIL.

- [ ] **Step 3: Parse the kinetic law**

In `parser.py`, in the reactions loop, replace:

```python
        # formula
        ast = None
        if r.isSetKineticLaw():
            klaw: libsbml.KineticLaw = r.getKineticLaw()
            ast = klaw.getMath() if klaw.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
```

with:

```python
        # kinetic law
        kinetic_law: KineticLaw | None = None
        if r.isSetKineticLaw():
            klaw: libsbml.KineticLaw = r.getKineticLaw()
            ast = klaw.getMath() if klaw.isSetMath() else None
            math = libsbml.formulaToL3String(ast) if ast else None
            if math:
                local_parameters: list[LocalParameter] = []
                lp: libsbml.LocalParameter
                for lp in klaw.getListOfLocalParameters():
                    local_parameters.append(
                        LocalParameter(
                            value=lp.getValue() if lp.isSetValue() else None,
                            unit=lp.getUnits() if lp.isSetUnits() else None,
                            **parse_sbase_kwargs(lp),
                        )
                    )
                kinetic_law = KineticLaw(
                    math=math,
                    local_parameters=local_parameters,
                    **parse_sbase_kwargs(klaw),
                )
```

and change the `Reaction(...)` construction to pass `formula=kinetic_law`.

`parse_sbase_kwargs` supplies `sid`, which `KineticLaw` accepts as an optional keyword. A `libsbml.KineticLaw` has no id in L3V2; `parse_sbase_kwargs` returns `d["id"]` which will be an empty string or `None`, so confirm `SBMLDocumentInfo.sbase_dict` returns `None` rather than `""` for an unset id, and if it returns `""`, normalize it:

```python
            "sid": d["id"] if d["id"] else None,
```

in `parse_sbase_kwargs`.

Import `KineticLaw` and `LocalParameter` in `parser.py`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_roundtrip.py -v -k "local_parameters"`
Expected: PASS.

- [ ] **Step 5: Measure and commit**

Run: `uv run python scripts/roundtrip_report.py --limit 150`

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "feat: parse kinetic laws with their local parameters

Round-trip pass rate: <RATE>%."
```

---

### Task 10: Events

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Event`, new `EventAssignment`)
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_factory.py`, `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces:
  - `EventAssignment(variable: str, value: str | float, ...)`, an `Sbase` subclass
  - `Event.assignments` is `list[EventAssignment]`; the constructor accepts `dict[str, str | float] | list[EventAssignment]`
  - `Event.useValuesFromTriggerTime` is honoured

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_factory.py`:

```python
def test_event_use_values_from_trigger_time_is_honoured() -> None:
    """Test that useValuesFromTriggerTime is written.

    `_set_fields` called `setUseValuesFromTriggerTime(True)` unconditionally,
    discarding the constructor argument, which changes simulation results.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    event = Event(
        "e1",
        trigger="time >= 10",
        assignments={"S1": 5.0},
        useValuesFromTriggerTime=False,
    )
    event.create_sbml(model)

    assert model.getEvent("e1").getUseValuesFromTriggerTime() is False


def test_event_assignments_accept_a_dict() -> None:
    """Test that the dict authoring style still works."""
    event = Event("e1", trigger="time >= 10", assignments={"S1": 5.0})
    assert len(event.assignments) == 1
    assert event.assignments[0].variable == "S1"
    assert event.assignments[0].value == 5.0


def test_event_assignments_keep_sbase_fields() -> None:
    """Test that an EventAssignment carries its own metaId and sboTerm."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    event = Event(
        "e1",
        trigger="time >= 10",
        assignments=[EventAssignment("S1", 5.0, metaId="ea1", sboTerm="SBO:0000064")],
    )
    event.create_sbml(model)

    ea = model.getEvent("e1").getEventAssignment(0)
    assert ea.getVariable() == "S1"
    assert ea.getMetaId() == "ea1"
    assert ea.getSBOTermID() == "SBO:0000064"
```

Import `Event` and `EventAssignment` in `tests/test_factory.py`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_factory.py -v -k "event"`
Expected: FAIL.

- [ ] **Step 3: Add `EventAssignment`**

In `factory.py`, immediately before `class Event(Sbase):`:

```python
class EventAssignment(Value):
    """EventAssignment of an Event.

    Assigns the value of the expression to the variable when the event fires.
    """

    def __init__(
        self,
        variable: str,
        value: str | float,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        notes_format: NotesFormat | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct an EventAssignment.

        Args:
            variable: the id of the element the assignment applies to
            value: the assigned expression, as an SBML L3 formula string
        """
        super().__init__(
            sid=sid,
            value=value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            notes_format=notes_format,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable = variable

    def __repr__(self) -> str:
        """Get string representation."""
        return f"EventAssignment({self.variable} = {self.value})"

    def create_sbml(self, event: libsbml.Event, model: libsbml.Model) -> libsbml.EventAssignment:
        """Create the libsbml.EventAssignment on the given event.

        Args:
            event: the libsbml.Event the assignment belongs to
            model: the libsbml.Model, used to resolve ids in the expression

        Returns:
            the created libsbml.EventAssignment
        """
        ea: libsbml.EventAssignment = event.createEventAssignment()
        self._set_fields(ea, model)
        check(ea.setVariable(self.variable), f"Set variable '{self.variable}'")
        ast_node = libsbml.parseL3FormulaWithModel(str(self.value), model)
        if ast_node is None:
            logger.error(
                "Event assignment math could not be parsed: '%s', %s",
                self.value,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(ea.setMath(ast_node), f"Set math on '{self.variable}'")
        return ea
```

`Sbase._set_fields` calls `setId`, which for an `EventAssignment` aliases `variable`. Because Task 2 wrapped `setId` in `check()`, an `EventAssignment` with a `sid` will log. Guard it: in `EventAssignment.create_sbml`, set `self.sid = None` is wrong because it mutates; instead override `_set_fields` to skip the id:

```python
    def _set_fields(self, sbase: libsbml.EventAssignment, model: libsbml.Model) -> None:
        """Set fields on libsbml.EventAssignment.

        The id is not set: `libsbml.EventAssignment.setId` aliases the
        `variable` attribute, so setting it here would overwrite the variable.
        """
        sid = self.sid
        self.sid = None
        try:
            super()._set_fields(sbase, model)
        finally:
            self.sid = sid
```

- [ ] **Step 4: Normalize `Event.assignments`**

In `Event.__init__`, change the `assignments` parameter to `dict[str, str | float] | list[EventAssignment] | None = None` and replace the assignment and its warning with:

```python
        self.assignments = Event._process_assignments(assignments)
```

and add:

```python
    @staticmethod
    def _process_assignments(
        assignments: dict[str, str | float] | list[EventAssignment] | None,
    ) -> list[EventAssignment]:
        """Normalize the event assignments to a list.

        A model definition writes the assignments as a
        `{variable: expression}` dict, which is the documented authoring
        style; the parser passes a list of `EventAssignment`.

        Args:
            assignments: the assignments as a dict or a list

        Returns:
            the event assignments
        """
        if assignments is None:
            return []
        if isinstance(assignments, dict):
            return [
                EventAssignment(variable=variable, value=value)
                for variable, value in assignments.items()
            ]
        return list(assignments)
```

- [ ] **Step 5: Fix `useValuesFromTriggerTime` and write the assignments**

In `Event._set_fields`, replace:

```python
        sbase.setUseValuesFromTriggerTime(True)
```

with:

```python
        check(
            sbase.setUseValuesFromTriggerTime(self.useValuesFromTriggerTime),
            f"Set useValuesFromTriggerTime on '{self.sid}'",
        )
```

and replace the assignment loop:

```python
        for key, math in self.assignments.items():
            ast_assign = libsbml.parseL3FormulaWithModel(str(math), model)
            ea = sbase.createEventAssignment()
            ea.setVariable(key)
            ea.setMath(ast_assign)
```

with:

```python
        for assignment in self.assignments:
            assignment.create_sbml(sbase, model)
```

- [ ] **Step 6: Run the factory tests**

Run: `uv run pytest tests/test_factory.py -v -k "event"`
Expected: PASS.

- [ ] **Step 7: Write the round-trip test**

Append to `tests/test_roundtrip.py`:

```python
#: cases which use events
CASES_EVENTS: list[str] = ["00026", "00041", "00071", "00072"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_EVENTS)
def test_roundtrip_events(case: str, tmp_path: Path) -> None:
    """Test that events survive a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 8: Parse the events**

In `parser.py`, replace the `# events` comment with:

```python
    # events
    e: libsbml.Event
    for e in model.getListOfEvents():
        trigger: libsbml.Trigger | None = e.getTrigger() if e.isSetTrigger() else None
        if trigger is None or not trigger.isSetMath():
            logger.error("Event '%s' has no trigger, it is skipped.", e.getId())
            continue

        assignments: list[EventAssignment] = []
        ea: libsbml.EventAssignment
        for ea in e.getListOfEventAssignments():
            ast = ea.getMath() if ea.isSetMath() else None
            value = libsbml.formulaToL3String(ast) if ast else None
            if value is not None:
                kwargs = parse_sbase_kwargs(ea)
                # the id of an EventAssignment aliases its variable
                kwargs["sid"] = None
                assignments.append(
                    EventAssignment(variable=ea.getVariable(), value=value, **kwargs)
                )

        priority_ast = (
            e.getPriority().getMath()
            if e.isSetPriority() and e.getPriority().isSetMath()
            else None
        )
        delay_ast = (
            e.getDelay().getMath()
            if e.isSetDelay() and e.getDelay().isSetMath()
            else None
        )

        m.events.append(
            Event(
                trigger=libsbml.formulaToL3String(trigger.getMath()),
                assignments=assignments,
                trigger_persistent=(
                    trigger.getPersistent() if trigger.isSetPersistent() else True
                ),
                trigger_initialValue=(
                    trigger.getInitialValue() if trigger.isSetInitialValue() else True
                ),
                useValuesFromTriggerTime=(
                    e.getUseValuesFromTriggerTime()
                    if e.isSetUseValuesFromTriggerTime()
                    else True
                ),
                priority=(
                    libsbml.formulaToL3String(priority_ast) if priority_ast else None
                ),
                delay=libsbml.formulaToL3String(delay_ast) if delay_ast else None,
                **parse_sbase_kwargs(e),
            )
        )
```

Import `Event` and `EventAssignment` in `parser.py`.

Note: `Event.__init__` requires `sid` to be a `str`, while `parse_sbase_kwargs` may return `None` for an event without an id. Confirm by reading `factory.py:1829-1831`; if `sid` is required, generate a fallback `f"event{k}"` using `enumerate`.

- [ ] **Step 9: Run the round-trip events test**

Run: `uv run pytest tests/test_roundtrip.py -v -k "events"`
Expected: PASS.

- [ ] **Step 10: Measure and commit**

Run: `uv run python scripts/roundtrip_report.py --limit 150`

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/factory.py src/sbmlutils/parser.py tests/test_factory.py tests/test_roundtrip.py
git commit -m "feat: round trip events

Event._set_fields called setUseValuesFromTriggerTime(True) unconditionally,
discarding the constructor argument and changing simulation results. Event
assignments were a plain dict and could not carry their own metaId or
sboTerm; they are now EventAssignment objects, and the dict authoring
style is normalized into them. The parser reads events.

Round-trip pass rate: <RATE>%."
```

---

### Task 11: Parse constraints

**Files:**
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers. `Constraint` already exists at `factory.py:1925-1983` and is attribute-complete.
- Produces: a parsed `Model` carries `constraints`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_roundtrip.py`:

```python
def test_roundtrip_constraints(tmp_path: Path) -> None:
    """Test that constraints survive a round trip."""
    import libsbml

    sbml_path = testsuite_case("01247")
    model = sbml_to_model(sbml_path)
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    m_in = libsbml.readSBMLFromFile(str(sbml_path)).getModel()
    m_out = libsbml.readSBMLFromFile(str(roundtrip_path)).getModel()
    assert m_out.getNumConstraints() == m_in.getNumConstraints()
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_constraints -v`
Expected: FAIL, `0 != 1`.

- [ ] **Step 3: Parse the constraints**

In `parser.py`, replace the `# constraints` comment with:

```python
    # constraints
    constraint: libsbml.Constraint
    for constraint in model.getListOfConstraints():
        ast = constraint.getMath() if constraint.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        if formula:
            m.constraints.append(
                Constraint(
                    value=formula,
                    message=(
                        constraint.getMessageString()
                        if constraint.isSetMessage()
                        else None
                    ),
                    **parse_sbase_kwargs(constraint),
                )
            )
```

Import `Constraint`. Confirm the constructor parameter names by reading `factory.py:1935-1965`; the math parameter is `value` and the message parameter is `message`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_roundtrip.py::test_roundtrip_constraints -v`
Expected: PASS.

- [ ] **Step 5: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "feat: parse constraints"
```

---

### Task 12: Reaction and species reference fidelity

**Files:**
- Modify: `src/sbmlutils/reaction_equation.py` (`modifiers`)
- Modify: `src/sbmlutils/factory.py` (`set_speciesref_fields`, `Reaction.reversible`, rule ids)
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_reaction_equation.py`, `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces: `ReactionEquation.modifiers` is `list[EquationPart]`, accepting `list[str]`; `Reaction.reversible` overrides `equation.reversible` when set.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_reaction_equation.py`:

```python
def test_modifiers_accept_strings() -> None:
    """Test that the `modifiers=["M1"]` authoring style still works."""
    equation = ReactionEquation.from_str("S1 -> S2 [M1]")
    assert len(equation.modifiers) == 1
    assert equation.modifiers[0].species == "M1"


def test_modifiers_keep_sbase_fields() -> None:
    """Test that a modifier carries its own metaId and sboTerm."""
    equation = ReactionEquation(
        reactants=[EquationPart(species="S1")],
        products=[EquationPart(species="S2")],
        modifiers=[EquationPart(species="M1", metaId="mod1", sboTerm="SBO:0000019")],
    )
    assert equation.modifiers[0].metaId == "mod1"
```

Append to `tests/test_factory.py`:

```python
def test_reaction_reversible_overrides_the_equation() -> None:
    """Test that an explicit `reversible` is honoured.

    `Reaction.reversible` was stored and never read; `_set_fields` used
    `equation.reversible`, so `Reaction(equation='A => B', reversible=True)`
    silently emitted `reversible="false"`.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for sid in ("A", "B"):
        species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")

    reaction = Reaction("r1", "A => B", reversible=True)
    reaction.create_sbml(model)

    assert model.getReaction("r1").getReversible() is True
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_reaction_equation.py tests/test_factory.py -v -k "modifiers or reversible"`
Expected: FAIL.

- [ ] **Step 3: Type the modifiers**

In `reaction_equation.py`, change the `modifiers` field of `ReactionEquation` from `list[str]` to `list[EquationPart]`, and normalize in `__post_init__` (add one if the dataclass has none):

```python
    def __post_init__(self) -> None:
        """Normalize the modifiers to EquationParts.

        A modifier may be given as a bare species id, which is the documented
        string syntax, or as a full `EquationPart` carrying its own SBase
        fields.
        """
        self.modifiers = [
            EquationPart(species=modifier) if isinstance(modifier, str) else modifier
            for modifier in self.modifiers
        ]
```

Update `_parse_modifiers` (or wherever `from_str` fills modifiers) to keep producing strings; `__post_init__` converts them.

Find every consumer:

Run: `grep -rn "\.modifiers" src/ tests/ examples/`

Update each: `reaction_equation.py`'s `to_string`, `factory.py:1748-1750`, `report/sbmlinfo.py` and the converters. A consumer reading `modifier` as a string becomes `modifier.species`.

- [ ] **Step 4: Write the modifier SBase fields**

In `factory.py`, in `Reaction.create_sbml`, replace the modifier loop:

```python
        for modifier in self.equation.modifiers:
            msref: libsbml.ModifierSpeciesReference = r.createModifier()
            msref.setSpecies(modifier)
```

with:

```python
        for modifier in self.equation.modifiers:
            msref: libsbml.ModifierSpeciesReference = r.createModifier()
            set_speciesref_fields(msref, modifier)
```

Read `factory.py:1744-1752` first and match the existing variable names.

- [ ] **Step 5: Write the remaining species reference fields**

In `set_speciesref_fields`, after the existing `metaId`/`sboTerm` handling, add:

```python
            if part.name is not None:
                sref.setName(part.name)
            if part.notes is not None and part.notes.strip():
                notes_format = (
                    part.notes_format
                    if getattr(part, "notes_format", None) is not None
                    else detect_format(part.notes)
                )
                set_notes(sref, part.notes, format=notes_format)
            for annotation in Sbase._process_annotations(part.annotations or []):
                annotator.ModelAnnotator.annotate_sbase(
                    sbase=sref, annotation=annotation
                )
```

Read `factory.py:1722-1742` first; `set_speciesref_fields` is a closure inside `Reaction.create_sbml` and `stoichiometry`/`constant` are already handled. Confirm `EquationPart` has `notes_format`; if not, add it to the dataclass in `reaction_equation.py` for symmetry with `Sbase`.

- [ ] **Step 6: Make `Reaction.reversible` live**

In `Reaction._set_fields`, replace:

```python
        sbase.setReversible(self.equation.reversible)
```

with:

```python
        reversible = (
            self.reversible if self.reversible is not None else self.equation.reversible
        )
        check(sbase.setReversible(reversible), f"Set reversible on '{self.sid}'")
```

Read `factory.py:1795-1805` first and match the surrounding code.

- [ ] **Step 7: Parse `compartment` and `fast`**

In `parser.py`, in the `Reaction(...)` construction, add:

```python
                compartment=r.getCompartment() if r.isSetCompartment() else None,
                fast=r.getFast() if r.isSetFast() else False,
```

`fast` was removed in SBML L3V2, so guard with `r.isSetFast()` and note that `setFast` is only called when the level/version supports it. Read `factory.py:1799-1804`; if `setFast` is called unconditionally, guard it:

```python
        if sbase.getLevel() < 3 or (
            sbase.getLevel() == 3 and sbase.getVersion() < 2
        ):
            sbase.setFast(self.fast)
```

- [ ] **Step 8: Parse modifier SBase fields**

In `parser.py`, replace the modifier loop:

```python
        modifier: libsbml.SpeciesReference
        for modifier in r.getListOfModifiers():
            if modifier.isSetSpecies():
                equation.modifiers.append(modifier.getSpecies())
```

with:

```python
        modifier: libsbml.ModifierSpeciesReference
        for modifier in r.getListOfModifiers():
            if modifier.isSetSpecies():
                equation.modifiers.append(
                    EquationPart(
                        species=modifier.getSpecies(),
                        **parse_sbase_kwargs(modifier),
                    )
                )
```

`EquationPart` does not accept `uncertainties` or `keyValuePairs`; strip whatever it does not accept, reusing the helper from Task 6.

- [ ] **Step 9: Write the round-trip tests**

Append to `tests/test_roundtrip.py`:

```python
#: cases which use modifiers in a reaction
CASES_MODIFIERS: list[str] = ["00039", "00063", "00064", "00065"]

#: cases whose reactions have a variable stoichiometry
CASES_VARIABLE_STOICHIOMETRY: list[str] = ["00969", "00970", "00971"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_MODIFIERS + CASES_VARIABLE_STOICHIOMETRY)
def test_roundtrip_species_references(case: str, tmp_path: Path) -> None:
    """Test that modifiers and variable stoichiometry survive a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 10: Run everything and commit**

Run: `uv run pytest -m "not sbml_testsuite" -q`
Expected: PASS. The modifier type change touches several consumers, so this is the real check.

Run: `uv run python scripts/roundtrip_report.py --limit 150`

Run: `uv run ruff check && uv run ruff format --check && uvx ty check`

```bash
git add src/sbmlutils/reaction_equation.py src/sbmlutils/factory.py src/sbmlutils/parser.py tests/test_reaction_equation.py tests/test_factory.py tests/test_roundtrip.py
git commit -m "feat: preserve species reference and modifier metadata

Modifiers were a list of species ids, so a ModifierSpeciesReference lost
its id, name, metaId, sboTerm, notes and annotations. They are now
EquationParts and a bare string is still accepted. set_speciesref_fields
now writes the name, notes and annotations which EquationPart already
carried and the parser already filled. Reaction.reversible was a dead
field and now overrides the equation.

Round-trip pass rate: <RATE>%."
```

---

### Task 13: Faithful defaults, package detection and the `isSetValue` bug

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Compartment`, `Parameter`, `Model.create_sbml` history)
- Modify: `src/sbmlutils/parser.py` (packages, `isSetValue`, conversionFactor, creators)
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces: a round trip of a core-only model declares no fbc namespace, writes no invented `NaN`, and preserves model history timestamps.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_roundtrip.py`:

```python
def test_roundtrip_core_model_declares_no_fbc(tmp_path: Path) -> None:
    """Test that a core only model does not gain the fbc package.

    `parser.py` hardcoded `m.packages = [Package.FBC_V3]`, so every parsed
    model came back declaring xmlns:fbc and fbc:strict.
    """
    model = sbml_to_model(testsuite_case("00001"))
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert "fbc" not in roundtrip_path.read_text()


def test_roundtrip_invents_no_nan(tmp_path: Path) -> None:
    """Test that an unset size or value is not written as NaN."""
    model = sbml_to_model(testsuite_case("00001"))
    roundtrip_path = tmp_path / "roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert "NaN" not in roundtrip_path.read_text()


#: cases whose species carry a conversionFactor
CASES_CONVERSION_FACTOR: list[str] = ["00976", "00977", "01000"]


@requires_roadrunner
@pytest.mark.parametrize("case", CASES_CONVERSION_FACTOR)
def test_roundtrip_conversion_factor(case: str, tmp_path: Path) -> None:
    """Test that a species conversionFactor survives a round trip."""
    assert_roundtrip_simulates_equal(testsuite_case(case), tmp_path)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_roundtrip.py -v -k "fbc or nan or conversion_factor"`
Expected: FAIL.

- [ ] **Step 3: Detect the packages**

In `parser.py`, replace:

```python
    m = Model(**parse_sbase_kwargs(model))
    # FIXME: parse packages
    m.packages = [Package.FBC_V3]
```

with:

```python
    m = Model(**parse_sbase_kwargs(model))
    m.packages = _packages_of_document(doc)
```

and add the module-level helper:

```python
#: the package prefix of a document mapped to the `Package` of sbmlutils
_PACKAGE_FOR_PREFIX: dict[str, Package] = {
    "comp": Package.COMP_V1,
    "distrib": Package.DISTRIB_V1,
}


def _packages_of_document(doc: libsbml.SBMLDocument) -> list[Package]:
    """Determine the SBML packages a document declares.

    Args:
        doc: the SBMLDocument to inspect

    Returns:
        the packages of the document which sbmlutils supports
    """
    packages: list[Package] = []
    for k in range(doc.getNumPlugins()):
        prefix: str = doc.getPlugin(k).getPrefix()
        if prefix == "fbc":
            version: int = doc.getPkgVersion(prefix)
            packages.append(Package.FBC_V3 if version >= 3 else Package.FBC_V2)
        elif prefix in _PACKAGE_FOR_PREFIX:
            packages.append(_PACKAGE_FOR_PREFIX[prefix])
    return packages
```

`Model.check_packages` unconditionally adds `Package.COMP_V1`, so a core-only model still declares comp. Read `factory.py:3466-3467` and remove the unconditional `packages_set.add(Package.COMP_V1)`, then run the comp tests:

Run: `uv run pytest tests/test_comp.py tests/test_model_merge.py -q`

If they fail, comp is required by those paths; in that case add comp only when the model has comp content:

```python
        if (
            self.submodels
            or self.ports
            or self.replaced_elements
            or self.deletions
            or self.model_definitions
            or self.external_model_definitions
        ):
            packages_set.add(Package.COMP_V1)
```

Place this in `Model.create_sbml`, not `check_packages`, because the lists are not populated when `check_packages` runs from `__init__`. Reading `Model.__init__` confirms `check_packages` is called before the lists are set.

Verify `doc.getPkgVersion` exists in this libsbml version:

Run: `uv run python -c "import libsbml; print(hasattr(libsbml.SBMLDocument(3,2), 'getPkgVersion'))"`

If it does not, use `doc.getPlugin(k).getPackageVersion()`.

- [ ] **Step 4: Fix the `isSetValue` bug**

In `parser.py`, change:

```python
                value=p.getValue() if p.isSetValue else None,
```

to:

```python
                value=p.getValue() if p.isSetValue() else None,
```

- [ ] **Step 5: Stop writing NaN**

In `factory.py`, in `Compartment.create_sbml`, read `factory.py:1179-1204` and replace the unconditional size assignment so that an unset value writes nothing:

```python
        if self.value is not None and not (
            isinstance(self.value, float) and math.isnan(self.value)
        ):
            check(c.setSize(float(self.value)), f"Set size on '{self.sid}'")
```

Do the same for `Parameter.create_sbml` (`factory.py:1105-1131`) and its `setValue`.

Make `spatialDimensions` conditional in `Compartment._set_fields`:

```python
        if self.spatialDimensions is not None:
            check(
                sbase.setSpatialDimensions(self.spatialDimensions),
                f"Set spatialDimensions on '{self.sid}'",
            )
```

and change the `Compartment.__init__` default of `spatialDimensions` from `3` to `None`. Then in `parser.py`, pass through what the source had:

```python
                spatialDimensions=(
                    c.getSpatialDimensions() if c.isSetSpatialDimensions() else None
                ),
```

Import `math` in `factory.py` if it is not already imported. Check: `grep -n "^import math" src/sbmlutils/factory.py`.

- [ ] **Step 6: Parse the conversionFactor**

In `parser.py`, in the species loop, add:

```python
                conversionFactor=(
                    s.getConversionFactor() if s.isSetConversionFactor() else None
                ),
```

Confirm the parameter name by reading `factory.py:1272`.

- [ ] **Step 7: Preserve the model history timestamps**

In `factory.py`, in `Model._create_sbml`, change:

```python
        if self.creators:
            set_model_history(model, self.creators)
```

to:

```python
        if self.creators:
            set_model_history(model, self.creators, set_timestamps=False)
```

Read `factory.py:300-350` to confirm the parameter name of `set_model_history`.

- [ ] **Step 8: Run the tests**

Run: `uv run pytest tests/test_roundtrip.py -v -k "fbc or nan or conversion_factor"`
Expected: PASS.

- [ ] **Step 9: Run the full suite**

Run: `uv run pytest -m "not sbml_testsuite" -q`
Expected: PASS. The `spatialDimensions` default change touches model creation broadly; if examples now omit it where they relied on the implicit `3`, that is correct SBML, but check that `tests/examples/test_examples.py` still passes.

- [ ] **Step 10: Measure and commit**

Run: `uv run python scripts/roundtrip_report.py --limit 150`

Run: `uv run ruff check && uv run ruff format --check && uvx ty check`

```bash
git add src/sbmlutils/factory.py src/sbmlutils/parser.py tests/test_roundtrip.py
git commit -m "fix: stop mutating documents on a round trip

The parser hardcoded the fbc package onto every model, an unset
compartment size or parameter value was written as NaN, spatialDimensions
was written even when the source omitted it, and model history timestamps
were rewritten to now. isSetValue was called without parentheses, so the
bound method was always truthy and every parameter received a value.

Round-trip pass rate: <RATE>%."
```

---

### Task 14: Drop the inert pydantic base and fix three write bugs

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Model` bases, `KeyValuePair.create_sbml`, `Uncertainty.create_sbml`)
- Test: `tests/test_model.py`, `tests/test_distrib.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Model` is `class Model(Sbase, FrozenClass)`; `copy.deepcopy(model)` and `model_a == model_b` work.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_model.py`:

```python
def test_model_is_deepcopyable() -> None:
    """Test that a Model can be deep copied.

    `Model` declared `BaseModel` as a base but never reached
    `BaseModel.__init__`, so `__pydantic_extra__` was never initialized and
    deepcopy raised AttributeError. A round trip wants to snapshot a parsed
    model before mutating it.
    """
    import copy

    model = Model("test", compartments=[Compartment("c", value=1.0)])
    clone = copy.deepcopy(model)

    assert clone.sid == "test"
    assert clone.compartments[0].sid == "c"
    assert clone.compartments[0] is not model.compartments[0]
```

Append to `tests/test_distrib.py`:

```python
def test_uncert_parameter_writes_var() -> None:
    """Test that an UncertParameter with a var writes it.

    `create_sbml` called `setValue(uncertParameter.var)` instead of `setVar`.
    """
    doc = libsbml.SBMLDocument(3, 1)
    doc.enablePackage(
        "http://www.sbml.org/sbml/level3/version1/distrib/version1", "distrib", True
    )
    model = doc.createModel()
    parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setConstant(True)

    uncertainty = Uncertainty(
        uncertParameters=[UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, var="p2")]
    )
    uncertainty.create_sbml(parameter, model)

    up = parameter.getPlugin("distrib").getUncertainty(0).getUncertParameter(0)
    assert up.getVar() == "p2"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_model.py::test_model_is_deepcopyable tests/test_distrib.py::test_uncert_parameter_writes_var -v`
Expected: FAIL.

- [ ] **Step 3: Drop `BaseModel`**

In `factory.py`, change:

```python
class Model(Sbase, FrozenClass, BaseModel):
    """Model."""

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        protected_namespaces=(),
    )
```

to:

```python
class Model(Sbase, FrozenClass):
    """Model.

    The field annotations below document the model structure. `Model` used to
    declare `pydantic.BaseModel` as a base, but `Model.__init__` never reached
    `BaseModel.__init__` and `FrozenClass.__setattr__` shadowed pydantic's, so
    no validation ever ran and `deepcopy`, `==` and `model_dump` raised.
    `FrozenClass` rejects unknown attributes, which is what the freeze was for.
    """
```

Keep the 33 field annotations exactly as they are; they are now plain class-level type hints.

Remove the now-unused `BaseModel` and `ConfigDict` imports if ruff reports them.

- [ ] **Step 4: Declare `parsed` and `units_dict`**

Add to the field annotations, next to `layouts`:

```python
    layouts: list | None
    parsed: bool
    units_dict: dict[str, UnitDefinition] | None
```

and add `"parsed": None` and `"units_dict": None` to the `_keys` ClassVar so `merge_models` keeps working.

- [ ] **Step 5: Find what relied on pydantic**

Run: `grep -rn "model_dump\|model_validate\|model_copy\|__pydantic" src/ tests/ examples/`
Expected: `Document.get_json` may use `model_dump`. Read `factory.py:3611-3616`; if it calls a pydantic method, reimplement it without pydantic or report the finding and stop.

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_model.py::test_model_is_deepcopyable -v && uv run pytest -m "not sbml_testsuite" -q`
Expected: PASS.

- [ ] **Step 7: Fix the three write bugs**

In `factory.py`, in `KeyValuePair.create_sbml`, change:

```python
        if self.uri is not None:
            check(kvp.setValue(self.value), f"Set `uri={self.uri}` on KeyValuePair")
```

to:

```python
        if self.uri is not None:
            check(kvp.setUri(self.uri), f"Set `uri={self.uri}` on KeyValuePair")
```

In `Uncertainty.create_sbml`, change `up_p.setValue(uncertParameter.var)` to `up_p.setVar(uncertParameter.var)` and `up_span.setValueLower(uncertSpan.varUpper)` to `up_span.setVarUpper(uncertSpan.varUpper)`. Read `factory.py:2110-2160` first and confirm the surrounding branches, because the `setValueLower` line sits in a branch which also handles `valueLower`.

- [ ] **Step 8: Run the distrib tests**

Run: `uv run pytest tests/test_distrib.py -v`
Expected: PASS.

- [ ] **Step 9: Verify and commit**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`

```bash
git add src/sbmlutils/factory.py tests/test_model.py tests/test_distrib.py
git commit -m "refactor: drop the inert pydantic base from Model

Model declared BaseModel as a base, but Model.__init__ never reached
BaseModel.__init__ and FrozenClass.__setattr__ shadowed pydantic's, so no
validation ever ran, the declared field types were documentation only, and
deepcopy, equality and model_dump all raised AttributeError. The
annotations stay as type hints and FrozenClass keeps rejecting unknown
attributes.

Also fixes three write bugs found while reading: KeyValuePair.uri called
setValue instead of setUri, UncertParameter called setValue instead of
setVar, and UncertSpan called setValueLower instead of setVarUpper."
```

---

### Task 15: Full sweep, documentation and release notes

**Files:**
- Modify: `docs/io.md` or `docs/creation.md` (round-trip section)
- Create: `release-notes/<version>.md` entry
- Modify: `tests/test_roundtrip.py` (record known failures)
- Modify: `src/sbmlutils/parser.py` (module docstring FIXMEs)

**Interfaces:**
- Consumes: everything.
- Produces: the final measured pass rate and a documented list of remaining failures.

- [ ] **Step 1: Run the full sweep**

Run: `uv run python scripts/roundtrip_report.py 2>&1 | tail -40`
Expected: a pass rate near 100%. This takes a while; it simulates 1690 cases twice.

- [ ] **Step 2: Triage the remaining failures**

For each failing case, determine the cause. Group them. Expected residual categories, from the spec:

- MathML normalization: math round trips as an L3 infix string, so `<cn>2</cn>` comes back as `<cn type="integer">2</cn>`.
- csymbol definitionURLs beyond the standard ones.
- Constructs the spec put out of scope (fbc, distrib, comp content in a semantic case).

Write the list into `tests/test_roundtrip.py` as an explicit, documented xfail set:

```python
#: cases which do not round trip yet, with the reason, see
#: https://github.com/matthiaskoenig/sbmlutils/issues/469
KNOWN_FAILURES: dict[str, str] = {
    # "01234": "csymbol definitionURL is not preserved",
}
```

and apply it in `test_roundtrip_sweep`:

```python
@requires_roadrunner
@pytest.mark.sbml_testsuite
@pytest.mark.parametrize("sbml_path", SWEEP_CASES, ids=sbml_case_idfn)
def test_roundtrip_sweep(sbml_path: Path, tmp_path: Path, request: pytest.FixtureRequest) -> None:
    """Round trip every l3v2 semantic case of the SBML test suite."""
    case = sbml_path.name[:5]
    if case in KNOWN_FAILURES:
        request.node.add_marker(pytest.mark.xfail(reason=KNOWN_FAILURES[case], strict=True))
    assert_roundtrip_simulates_equal(sbml_path, tmp_path)
```

`strict=True` means a case which starts passing fails the test, so the list cannot rot.

- [ ] **Step 3: Note the level and version caveat**

Add to the module docstring of `tests/test_roundtrip.py`:

```python
"""...

Only the l3v2 flavour of each case is round tripped. `create_model` writes
SBML L3V2, so round tripping an L1 or L2 file is a conversion rather than a
round trip and its trajectories are not expected to match attribute for
attribute.
"""
```

- [ ] **Step 4: Clean up the parser docstring**

In `parser.py`, the module docstring still says:

```python
"""Parse Models in internal model format.

FIXME: no support for notes
FIXME: no support for modelHistory

"""
```

Replace it with an accurate description of what is and is not supported, naming the remaining gaps (fbc, distrib, comp) and linking issue #469.

- [ ] **Step 5: Document round-tripping**

Add a section to `docs/io.md` describing `sbml_to_model` and the round-trip guarantee, the measured coverage, and what is not preserved (annotation URI canonicalization, MathML normalization, the packages which are out of scope). Remember: markdown carries no hard line wraps.

- [ ] **Step 6: Write the release note**

Read `release-notes/` to match the existing format and file naming, then add an entry describing the feature and, in a separate list, the behaviour changes from the spec's backward compatibility section:

- writing a model no longer emits an SBO CVTerm alongside the sboTerm attribute, and no longer forces a metaid
- an unset compartment size or parameter value is no longer written as NaN
- `Reaction(..., reversible=...)` now takes effect
- `Model` is no longer a pydantic `BaseModel`
- `ReactionEquation.modifiers` is a list of `EquationPart`, a list of strings is still accepted

- [ ] **Step 7: Full verification**

Run: `uv run ruff check && uv run ruff format --check && uvx ty check && uv run pytest -m "not sbml_testsuite" -q`
Expected: all clean.

Run: `uv run pytest -m sbml_testsuite -q 2>&1 | tail -5`
Expected: passes, with only the documented xfails.

- [ ] **Step 8: Commit**

```bash
git add tests/test_roundtrip.py src/sbmlutils/parser.py docs/io.md release-notes/
git commit -m "docs: document SBML core round-tripping

Final round-trip pass rate over the l3v2 semantic cases: <RATE>%.
Remaining failures are recorded as strict xfails with their cause."
```

- [ ] **Step 9: Open the pull request**

```bash
git push -u origin feat/469-sbml-core-roundtrip
gh pr create --base develop --title "Full support of SBML core round-tripping (#469)" --body "$(cat <<'BODY'
Closes #469 for SBML core.

`SBML -> sbml_to_model -> create_model -> SBML` now preserves SBML core.
The round-trip simulation pass rate over the l3v2 semantic cases of the
SBML test suite went from 57.4% to <RATE>%.

## What was broken

Unit definitions, function definitions, events, constraints, local
parameters and notes were dropped; the fbc package, an SBO CVTerm and a
forced metaid were injected; and a round trip emitted 1512 authoring
warnings over 194 cases.

## Data model changes

- `Unit` and `UnitDefinition.units` make an arbitrary SBML unitDefinition
  representable; the pint string stays the authoring style
- `KineticLaw` and `LocalParameter` replace the untyped `Formula` namedtuple
- `EventAssignment` replaces the plain assignment dict
- `Sbase.notes` is normalized to xhtml, so notes round trip
- `ReactionEquation.modifiers` is a list of `EquationPart`
- `Model` no longer declares the inert `pydantic.BaseModel` base

## Behaviour changes

See `release-notes/`.

## Verification

Simulation equivalence: roadrunner simulates the original, the model round
trips, roadrunner simulates the result, trajectories are compared. A
curated subset runs in CI; the full sweep is behind the `sbml_testsuite`
marker.

Design: `.claude/specs/2026-09-18-sbml-core-roundtrip-design.md`
Plan: `.claude/plans/2026-09-18-sbml-core-roundtrip.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_011pXSSqAtx3gFq732VkFeUV
BODY
)"
```

---

## Self-review notes

**Spec coverage.** Every section of the spec maps to a task: units to Tasks 5 and 6, local parameters to Tasks 8 and 9, notes to Task 3, events to Task 10, ids to Tasks 2 and 12, modifiers to Task 12, document mutations to Tasks 4 and 13, `Reaction.reversible` to Task 12, the pydantic hybrid to Task 14, the missing attributes to Tasks 6, 11, 12 and 13, the drive-by bugs to Task 14, and the verification harness to Tasks 1 and 15.

**Ordering.** Task 2 comes early because 1512 warnings per sweep make every later task's output unreadable. Task 1 comes first because it is the instrument every later task is measured with.

**Known risk.** Task 12 changes the type of `ReactionEquation.modifiers`, which has consumers in `factory.py`, `report/sbmlinfo.py` and the converters. Step 3 of that task greps for them explicitly. If the blast radius is larger than expected, stop and report rather than fixing consumers blindly.

**Not attempted.** Splitting `factory.py`, collapsing `ModelDict` / `_keys` / the constructor signature into one source of truth, and fbc / distrib / comp round-tripping. Each is a follow-up issue.
