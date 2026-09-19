# SBML core round-tripping

Design for issue [#469](https://github.com/matthiaskoenig/sbmlutils/issues/469).

Date: 2026-09-18
Status: approved, ready for implementation planning

## Problem

`sbmlutils` can write SBML from a `Model` definition (`factory.py`) and read SBML back into a `Model` (`parser.py`), but the two directions do not compose. Round-tripping a model through `sbml_to_model` and `create_model` silently loses most of its content, and the result is frequently not valid SBML.

### Measured baseline

All numbers below were measured on the vendored SBML test suite (`resources/models/sbml-test-suite-3.4.0`), level 3 version 2 semantic cases, `SBML -> sbml_to_model -> create_model -> SBML`.

Structural loss, first 200 cases:

| Outcome | Cases |
| --- | --- |
| Crashes | 0 |
| Round trips preserving all element counts | 0 (0.0%) |

| Content lost | Cases affected |
| --- | --- |
| `unitDefinition` | 200 of 200 |
| `functionDefinition` | 50 of 50 that have them |
| `event` and event assignments | 7 of 7 |
| local parameters of a kinetic law | 5 of 5 |
| `species.substanceUnits` | 523 elements |
| `compartment.units` | 173 elements |

The output is not merely lossy. Dropping function definitions makes libsbml reject the result with error `10214` ("a `<ci>` element in this context must refer to a function definition") in 48 of 150 cases, and dropping local parameters produces error `10215` in 3 more.

Simulation loss, first 150 cases, roadrunner uniform timecourse before and after the round trip:

| Outcome | Cases |
| --- | --- |
| Trajectories match | 85 |
| Round-tripped model does not load in roadrunner | 56 |
| Trajectories differ | 7 |
| Original does not simulate (excluded) | 2 |

**Pass rate over simulatable cases: 85/148 = 57.4%.** This is the acceptance metric of the issue.

A third measurement, three consecutive cycles on the repressilator (`BIOMD0000000012_urn.xml`), shows the damage is a one-shot mutation rather than unbounded drift:

| | elements | CVTerms | metaIds | unitDefinitions | model notes |
| --- | --- | --- | --- | --- | --- |
| source | 108 | 27 | 81 | 3 | yes |
| cycle 1 | 98 | 55 | 57 | 0 | no |
| cycle 2 | 98 | 55 | 57 | 0 | no |
| cycle 3 | 98 | 55 | 57 | 0 | no |

## Goal

Raise the simulation round-trip pass rate for SBML core to approximately 100%, and fix the data-model defects that cause the gap.

## Scope

In scope: SBML core, and the annotation and notes defects that a round trip introduces.

Out of scope, tracked separately: the `fbc`, `distrib` and `comp` packages, and a structural document differ. `comp` in particular requires resolving external model definitions and is a substantially larger problem.

## Root causes

The gap is not a single missing loop in the parser. Several core SBML constructs have no faithful representation in the data model, so the parser could not preserve them even if it read them.

### 1. Unit definitions cannot be represented

Three independent problems.

`UnitDefinition` stores a pint expression string (`"mmole/min/l"`) that is parsed at write time (`factory.py:787-840`). An SBML `<unitDefinition>` is a list of `<unit kind exponent scale multiplier>` elements. The pint path cannot express an arbitrary such list: `create_sbml` hardcodes `scale = 0` (`factory.py:815`), so a source using `scale="-3" multiplier="1"` comes back as `scale="0" multiplier="0.001"`. A unit id that is not pint-parseable raises outright - and `UnitDefinition("substance")` is exactly that shape, because `definition` defaults to `sid` (`factory.py:783`). The test-suite ids `substance`, `volume` and `time` all fail this way.

A unit cannot be referenced by id at all. `UnitType` is `"UnitDefinition | None"` (`factory.py:185`) with no `str` member, and `get_uid_for_unit` raises for a string (`factory.py:862-876`).

`Model.units` is typed `type[Units]` - a Python *class* whose class attributes are the unit definitions (`factory.py:879-948`, `factory.py:3160`). A parser can synthesize one (`merge_models` already does, `factory.py:3518`), but the catalogue and the references are decoupled: the `unit=` on an element contributes only `unit.sid`, while the `listOfUnitDefinitions` comes solely from `Model.units`, so an unregistered unit produces a dangling reference and invalid SBML.

### 2. Local parameters are written as global parameters

`Reaction.pars` is emitted with `create_objects(model, self.pars, key="parameters")` (`factory.py:1714`), which creates *global* model parameters. SBML local parameters are scoped to their kinetic law, so this both changes semantics and makes identically named local parameters in different reactions collide. There is no `LocalParameter` class anywhere in the package.

`Formula` is an untyped `namedtuple("Formula", "value unit")` (`factory.py:1608`). `_process_formula` parses the unit and `create_sbml` then uses only `.value`, so the unit is silently dropped. A `KineticLaw` also cannot carry its own `id`, `name`, `metaId`, `sboTerm`, notes or annotations.

### 3. Notes are not round-trippable

`Sbase.notes` is a **markdown** string rendered through MarkdownIt on write (`factory.py:496-497`, `notes.py:28-51`). There is no way to select `NotesFormat.HTML` through an `Sbase`. Feeding a real SBML notes string back in produces nested `<body><notes><body>`, which is why `parser.py:155-156` has the notes assignment commented out. Markdown is mutating even for plain text: `"2*3*4"` renders to `2<em>3</em>4`.

### 4. Events are lossy and one attribute is ignored

`Event._set_fields` calls `sbase.setUseValuesFromTriggerTime(True)` unconditionally (`factory.py:1888`), discarding the constructor argument stored at `factory.py:1872`. This is a plain bug and changes simulation results.

`Event.assignments` is a `dict[str, str | float]`, so an event assignment cannot carry its own `id`, `name`, `sboTerm`, `metaId` or annotations, and `trigger`/`priority`/`delay` being plain strings carry nothing for `Trigger`/`Priority`/`Delay`.

### 5. Ids are silently swallowed

`Sbase._set_fields` calls `sbase.setId()` without checking the return code (`factory.py:460`). For `Rule`, `InitialAssignment` and `EventAssignment`, libsbml aliases `setId` to the `variable`/`symbol` attribute and returns an error that is discarded. `AssignmentRule.__init__` synthesizes `sid = f"AssignmentRule_{variable}"` (`factory.py:1481`) which is then thrown away. Round-trip output contains no rule ids at all.

### 6. Modifiers are strings

`ReactionEquation.modifiers` is `list[str]` (`reaction_equation.py:106`), so a `ModifierSpeciesReference` loses its `id`, `name`, `metaId`, `sboTerm`, notes and annotations.

Separately, `set_speciesref_fields` (`factory.py:1722-1737`) ignores the `name`, `annotations`, `notes` and `keyValuePairs` that `EquationPart` already stores and that `parser.py:241,255` already fills.

### 7. A round trip mutates the document

Changes introduced that were never in the source:

- **An SBO term is duplicated as a CVTerm.** When `sboTerm` is set, `_set_fields` injects `Annotation(BQB.IS, f"sbo/{sboTerm}")` (`factory.py:505-519`). This also forces a `metaid` onto the element and adds an `<annotation>` block to elements that had none. On the repressilator this is +28 CVTerms in one cycle. No test depends on it.
- **The fbc package is force-injected.** `parser.py:165` hardcodes `m.packages = [Package.FBC_V3]`, so a core-only model comes back declaring `xmlns:fbc` and `fbc:strict="false"`.
- **Model history dates are clobbered.** `set_model_history` is called without `set_timestamps=False` (`factory.py:3376-3377`), so created and modified dates are rewritten to now.
- **Unset values become NaN.** An unset `Compartment.size` is written as `size="NaN"` (`factory.py:1184`) and an unset `Parameter.value` as `value="NaN"` (`factory.py:1109`). `spatialDimensions` is written unconditionally (`factory.py:1209`).
- **Best-practice warnings fire on parsed models.** `_set_fields` warns whenever `name` or `sboTerm` is unset. Measured: re-emitting the first 194 l3v1 test-suite cases produced **1512 warning records**. Round-tripping is not authoring and must not warn about authoring style.

### 8. `Reaction.reversible` is a dead field

Stored at `factory.py:1680` and never read; `_set_fields` uses `self.equation.reversible` (`factory.py:1803`). `Reaction(equation="A => B", reversible=True)` silently emits `reversible="false"`. This changes simulation results.

### 9. The pydantic layer on `Model` is inert

`class Model(Sbase, FrozenClass, BaseModel)` never reaches `BaseModel.__init__`, because `Model.__init__` calls `super().__init__(...)` which resolves to `Sbase.__init__` and stops. `FrozenClass.__setattr__` shadows pydantic's. Verified consequences: `Model(sid=12345)` is accepted with an `int` sid, `m.species = "not a list"` is accepted, and `deepcopy(m)`, `m == m2`, `m.model_dump()` and `m.model_copy()` all raise `AttributeError`. The 33 declared field annotations are documentation only and `extra="allow"` is meaningless.

There are four hand-synchronized sources of truth for the same field set: the pydantic fields (`3149-3184`), the `_keys` ClassVar (`3186-3220`), the `ModelDict` TypedDict (`3089-3137`) and the constructor signature (`3239-3273`). `units_dict` (`3291`) appears in none of them.

### 10. Attributes with no home, and small bugs

`Species.conversionFactor`, `Compartment.units`, `Parameter.units` (commented out at `parser.py:173,188,214`), the model-level unit attributes, `Reaction.compartment`, `Reaction.fast`, `Constraint.message`, function definitions, constraints and events are all supported by `factory.py` but never read by `parser.py`.

`parser.py:173` calls `p.isSetValue` without `()`, so the bound method is always truthy and every parameter receives a value.

## Design

### Part 1: core data model (`factory.py`)

**Units.** Introduce a first-class `Unit`, and let `UnitDefinition` hold a list of them. The pint string stays the documented authoring style and *compiles into* that list, so `create_sbml` only ever writes a `list[Unit]` and there is one representation at write time.

```python
class Unit:
    kind: str            # "litre"
    exponent: float = 1.0
    scale: int = 0
    multiplier: float = 1.0

class UnitDefinition(Sbase):
    def __init__(self, sid, definition=None, units: list[Unit] | None = None, ...)
```

```python
UnitDefinition("mM", "mmole/liter")                    # authoring, unchanged
UnitDefinition("mM", units=[Unit("mole", 1, -3, 1.0),  # parsed, exact
                           Unit("litre", -1, 0, 1.0)])
```

This also fixes the hardcoded `scale = 0`, and a `UnitDefinition` whose `sid` is not pint-parseable becomes representable.

`UnitType` gains a `str` member so a unit can be referenced by id, and `get_uid_for_unit` resolves a string to itself instead of raising.

**`Model.units`** accepts `type[Units] | list[UnitDefinition]` and normalizes to `list[UnitDefinition]` at construction, reusing `Units.attributes()`. The `class U(Units)` style is untouched; the parser passes a list. `ModelUnits` entries accept a unit id string.

**Kinetic laws.** Replace the `Formula` namedtuple with real classes mirroring SBML:

```python
class LocalParameter(Sbase):
    value: float | None
    unit: UnitType

class KineticLaw(Sbase):
    math: str
    unit: UnitType = None
    local_parameters: list[LocalParameter]
```

`Reaction.formula` keeps accepting a plain string or a `(math, unit)` tuple and normalizes into a `KineticLaw`, so `Reaction("r1", "S1 -> S2", formula="k1*S1")` is unchanged. Local parameters are written inside the kinetic law. `Reaction.pars` keeps creating global parameters.

**Notes.** `Sbase.notes` normalizes to XHTML at construction and `_set_fields` writes it verbatim, so writing is no longer a rendering step.

The detection rule is explicit rather than a heuristic on content: a string whose first non-whitespace character is `<` and which parses as XML is stored verbatim, with a wrapping `<notes>` element unwrapped to its body if present. Anything else is treated as markdown and rendered once through the existing `Notes` path. A `NotesFormat` argument on `Sbase` lets an author override the detection in either direction.

This makes a round trip a fixed point: parsed XHTML is stored and written unchanged, so `"2*3*4"` in a source document stays `2*3*4` instead of becoming `2<em>3</em>4`.

`Sbase.get_notes_xml` is dead code (no callers) and is removed.

**Events.** Add `EventAssignment(variable, value)` as an `Sbase` subclass. `Event.assignments` accepts `list[EventAssignment]` or the existing dict, normalizing the dict into the list. Fix `setUseValuesFromTriggerTime` to honour its argument.

**Ids.** Wrap `setId` in `check()` (`factory.py:460`) so the three silent losses become loud, and set ids on `Rule`, `InitialAssignment` and `EventAssignment` through libsbml's `setIdAttribute`.

**Modifiers.** `ReactionEquation.modifiers` becomes a list of `EquationPart` rather than `list[str]`, accepting bare strings and normalizing them. `set_speciesref_fields` is extended to write the `name`, `notes`, `annotations` and `keyValuePairs` that `EquationPart` already carries.

**`Model`.** Drop the inert `BaseModel` base. The field annotations stay as plain class-level type hints, `FrozenClass` keeps rejecting unknown attributes, and `deepcopy` and equality start working - which the round-trip tests need. `units_dict` is declared. `ModelDict` and `_keys` stay, but the spec records that they duplicate the constructor signature; collapsing them is a follow-up, not part of this change.

**Faithful defaults.** Stop writing `NaN` for an unset `Compartment.size` or `Parameter.value`, and stop writing `spatialDimensions` when it was not set. Plumb `set_timestamps=False` so model history dates are not clobbered.

**Missing attributes.** `Species.conversionFactor`, `Compartment.units`, `Parameter.units`, the model-level unit attributes, `Reaction.compartment`, `Reaction.fast`, and `Constraint.message`.

**`Reaction.reversible`** is made live: it overrides `equation.reversible` when explicitly set.

**Warnings.** Move the `name`/`sboTerm` best-practice warnings behind a flag so they do not fire for a parsed model.

### Part 2: parser (`parser.py`)

Add the missing branches: unit definitions, model units, function definitions, events, constraints, local parameters, notes, model history, units on every element, `conversionFactor`, `Reaction.compartment` and `Reaction.fast`.

Fix `p.isSetValue` to `p.isSetValue()` (`parser.py:173`).

Replace the hardcoded `m.packages = [Package.FBC_V3]` with detection of the packages the source document actually declares.

### Part 3: annotations

Remove the automatic SBO-term-to-CVTerm injection in `_set_fields`. An `sboTerm` is already written as the `sboTerm` attribute; duplicating it as an annotation invents data on every write, and forces a `metaid` onto elements that had none. No test depends on it.

Keep pymetadata's URI canonicalization (`urn:miriam:uniprot:P03023` becomes `https://identifiers.org/uniprot:P03023`). It lives in `pymetadata.core.annotation.RDFAnnotation`, not in this repo; it is the documented purpose of that library, it leaves arbitrary URLs untouched, and it is idempotent, so a second round trip is a fixed point. This is recorded as intentional normalization rather than loss.

### Part 4: verification (`tests/test_roundtrip.py`)

Simulation equivalence, which is what the issue asks for:

1. roadrunner simulates the original over a uniform timecourse.
2. The model round trips through `sbml_to_model` and `create_model`.
3. roadrunner simulates the result.
4. Trajectories are compared with `numpy.allclose`.

A curated subset covering every core construct runs in CI. The full 10032-file sweep sits behind a pytest marker for local and nightly runs, so the required `tests` check stays fast. The test skips when roadrunner is absent, following the existing `cobra` pattern - roadrunner is in the `examples` extra, which `dev` pulls in, and is not a runtime dependency.

## Drive-by bug fixes

Three one-line bugs found during the audit. They are outside the round-trip scope but are unambiguous defects, so they are fixed here rather than left in place:

- `factory.py:651-652` - `KeyValuePair.uri` calls `setValue` instead of `setUri`, so the uri is never written.
- `factory.py:2153` - `up_p.setValue(uncertParameter.var)` should be `setVar`.
- `factory.py:2122` - `up_span.setValueLower(uncertSpan.varUpper)` should be `setVarUpper`.

## Success criteria

- Simulation round-trip pass rate for l3v2 semantic core cases rises from 57.4% to approximately 100%; any remaining failure is individually understood and documented.
- No round trip produces a document libsbml rejects.
- A round trip of a core-only model does not declare the fbc package.
- A round trip adds no CVTerm and no metaId that was not in the source.
- Notes survive a round trip unchanged, and a second round trip is a fixed point.
- Round-tripping the test suite emits no best-practice warnings.
- `ruff check`, `ruff format` and `uvx ty check` are clean; the existing test suite still passes.

## Backward compatibility

Every change is additive at the call site. `UnitDefinition("mM", "mmole/liter")`, `class U(Units)`, `Reaction(..., formula="k1*S1")`, `Event(..., assignments={"S1": 5.0})` and `ReactionEquation(modifiers=["M1"])` all keep working.

Behavioural changes to call out in the release notes:

- Writing a model no longer emits an SBO CVTerm alongside the `sboTerm` attribute, and no longer forces a `metaid` onto elements that lacked one.
- An unset compartment size or parameter value is no longer written as `NaN`.
- `Reaction(..., reversible=...)` now takes effect instead of being ignored.
- `Model` is no longer a pydantic `BaseModel`. It was never validated as one, but `model_validate` did resolve, so the removal is technically breaking.
- `Reaction.pars` continues to create global parameters; local parameters are new and separate. Reinterpreting `pars` as local was considered and rejected as a silent breaking change.

## Rejected alternatives

- **Round-trip units through a pint string.** Scale and multiplier do not survive a string faithfully, and kinds pint cannot express have no path back.
- **Replace pint with raw units entirely.** Cleanest data model, but breaks every existing model definition and all documentation.
- **Synthesize a `Units` subclass in the parser.** Possible (`merge_models` does it), but opaque to type checkers and cannot represent unit ids that are not Python identifiers.
- **Reinterpret `Reaction.pars` as local parameters.** Silently changes the SBML output of every existing model that uses it.
- **Make `Model` a real pydantic model.** Would give genuine validation, but is a large rewrite of construction touching every caller; deferred.
- **A structural document differ.** Useful as a development tool, but the issue asks for simulation equivalence and two verification harnesses is one too many.
