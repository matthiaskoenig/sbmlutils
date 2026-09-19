# SBML package round-tripping: fbc, distrib, comp

Design for the second half of issue [#469](https://github.com/matthiaskoenig/sbmlutils/issues/469), "Full support of core, fbc, distrib roundtrip". SBML core was completed in #473 and released in 0.11.0. This effort covers sections 1, 3 and 4 of `.claude/issues/followup-after-core-roundtrip.md`.

Date: 2026-09-19
Status: approved for implementation. The user directed that the pull request be opened once the final review is clean.

## Problem

`sbml_to_model` reads SBML core faithfully since 0.11.0, but it reads essentially nothing of the fbc, distrib and comp packages, although `factory.py` can write most of it. Measured on the current tree:

- Round-tripping `resources/models/fbc/e_coli_core.xml.gz` discards **137 gene products, 69 gene product associations, 95 flux bounds, 72 charges, 72 chemical formulas, the objective and `fbc:strict`**.
- Round-tripping `resources/models/comp/icg_body.xml` discards **its submodel, all 16 ports, 6 replaced elements and its external model definition**.
- **Both stripped documents validate with zero errors.**

## The central risk

The core branch measured progress with two instruments: roadrunner trajectories and libsbml validation. **Both are blind to all three packages:**

| Package | What roadrunner does | What validation does |
| --- | --- | --- |
| fbc | loads the model, `simulate()` raises "FBC model discovered, but not simulatable" | passes on a fully stripped document |
| distrib | simulates normally, ignores distrib entirely | passes on a fully stripped document |
| comp | flattens the hierarchy, then simulates | passes on a fully stripped document |

So the failure mode is **a green test suite over a lossy round trip**: a distrib test that simulates and passes while dropping every uncertainty, a comp test that passes because flattening hid the dropped hierarchy, an fbc test that only validates. The design is built around not declaring success on evidence that cannot see the failure.

## Goal

A round trip preserves the fbc, distrib and comp content of a document, **proven by a structural comparison that checks attributes, not element counts**, over the SBML test suite and the in-repo fixtures. Along the way it fixes the data model and robustness defects in sections 3 and 4 of the follow-up issue.

## Scope

**In scope:** fbc, distrib and comp round-tripping; section 3 data model cleanups; section 4 robustness fixes.

**Out of scope, by the user's decision:**
- **Splitting `factory.py`.** Deferred to its own pure-refactor change, after this behaviour is settled and tested.
- **A structured `GeneProductAssociation` tree.** `Reaction.geneProductAssociation` stays an infix string.

**Out of scope, by ruling (below):**
- Making `Model` a real dataclass or pydantic model (option C.1(c) in the survey).
- Resolving and inlining external model definitions.
- `groups`, `layout`, `render`, `qual`, `multi`, `spatial`, `arrays`, and arbitrary non-RDF `<annotation>` content.

## Decisions already taken by the user

- The package work lands as its own branch and pull request, off `develop`.
- `Reaction.geneProductAssociation` stays an infix string. The survey measured the cost: on `e_coli_core` (69 GPAs, 174 `geneProductRef`) and `Recon3D` (5938 GPAs, 22559 refs), **zero** GPA or `geneProductRef` nodes carry an `id`, `name`, `metaid` or `sboTerm`, so the string loses no metadata on any model in the repository. Re-parsing each GPA's infix gives back the identical string for 67 of 69 on `e_coli_core`; the two exceptions, `R_PFL` and `R_ATPS4r`, are libsbml flattening nested same-operator groups, `((a and b) and c)` to `(a and b and c)`, which is the same boolean rule.
- The `factory.py` split is deferred.
- The pull request is opened once the final review is clean, without asking.

## Rulings

Each is a decision taken on the user's behalf. The cost of being wrong is stated so it can be reversed.

**R1. `ModelDefinition` subclasses `Model`.** `ModelDefinition` today is a stub: its constructor takes only `id`, `name`, `compartments` and `species`, and its `_set_fields` walks eighteen attribute names behind `hasattr`, sixteen of which the constructor never sets, using camelCase names (`externalModelDefinitions`) that do not match `Model`'s snake_case (`external_model_definitions`), and missing `algebraic_rules`, `gene_products` and `user_defined_constraints`. Its `units` are commented out, so a comp model's inline definitions would lose the unit preservation #469 just fixed, one level down. Completing its constructor by hand would add a fifth hand-synchronized copy of `Model`'s field set. Making it a `Model` subclass reuses the one field set, and `libsbml.ModelDefinition` already subclasses `libsbml.Model`, so `create_objects` works for every element type. The code's own `# FIXME: handle as model` says the same. It also lets the comp parser recurse into the core parser for each model definition, about 60 lines rather than 300. *Cost if wrong: a later change to holding a `Model` instead of being one; the parser recursion is the same either way.*

**R2. External model definitions are preserved as references, not resolved.** A faithful round trip reproduces `<externalModelDefinition id= source= modelRef= md5=>` exactly as it was read. Loading the external model and inlining it would itself be a mutation of the document. Resolution is a separate concern, which `comp.flatten_sbml` already handles for simulation. This removes the survey's "C4 external model resolution" from this effort. *Cost if wrong: resolution becomes a follow-up if someone needs `sbml_to_model` to load referenced files.*

**R3. `Model`'s field set: derive `_keys` from the annotations, and go no further.** The survey found four hand-synchronized copies of `Model`'s field set (the field annotations, `_keys`, `ModelDict`, the constructor signature). Deriving `_keys` from the annotations removes one copy in about 30 lines, keeps the deliberate `units` exception visible in an explicit override table, and changes no behaviour. `ModelDict` stays, because `tests/test_distrib.py` and several `examples/` use it. Making `Model` a dataclass or pydantic model is not attempted: #473 just removed a half-finished pydantic base, which is a strong argument against another casual attempt, and it interacts with `FrozenClass`, the `objects` fan-out and `ModelDefinition`. *Cost if wrong: the remaining copies stay until a dedicated design change.*

**R4. `Objective.active` keeps its default of `True`.** Changing it would change how every existing model definition with several objectives is written. Instead the parser reads `activeObjectiveId` and sets `active` explicitly on each parsed objective, so a round trip preserves which objective is active. *Cost if wrong: authored models with several objectives still get the last one active, which is the current, documented behaviour.*

**R5. Known, semantics-preserving normalizations are whitelisted explicitly in the structural comparison, each with a written reason.** They are: GPA same-operator flattening (above); `<cn>` gaining `type="integer"` (MathML round trips as an L3 infix string); `urn:miriam:` annotation URIs becoming `identifiers.org` URLs (pymetadata canonicalization, idempotent). Nothing else may differ. *Cost if wrong: a real loss hidden behind a whitelist entry; each entry therefore needs a test showing the normalized form means the same thing.*

## Verification strategy

**Layer 1, the structural harness, is the first task and gates everything.** It compares the document read against the document written, **attribute by attribute** on every fbc, distrib and comp construct, not by counting elements. It is swept over all 1690 l3v2 test-suite cases and the in-repo fixtures, and it produces a per-construct baseline table **before any parser code is written**, the analogue of the core branch's 57.4%.

Its comparison policy is part of the design and must be settled in that first task, because later tests depend on it:
- lists whose SBML order carries no meaning compare as sets; lists whose order is meaningful compare in order;
- `listOfUncertainties` child order must be preserved (the survey found it is currently lost);
- a `Deletion`'s ownership is compared where SBML places it;
- the R5 normalizations are the only permitted differences.

**Layer 2, comp semantics:** flatten both the original and the round-tripped document with `flatten_sbml`, simulate both, and compare trajectories. This catches a hierarchy that round trips structurally but changes the flattened model.

**Layer 3, fbc semantics:** load both documents through the existing `fbc/cobra.py` bridge and compare the stoichiometric matrix, flux bounds, objective, `gene_reaction_rule` and the FBA solution. This catches an fbc model that round trips structurally but solves differently.

**Layers 2 and 3 are skipped when roadrunner or cobra is not installed**, following the existing optional-dependency pattern. Layer 1 has no optional dependency and always runs.

**Every task verifies with tox, not `uv run pytest`.** `uv run` uses an editable install that reads the source tree; CI runs tox, which builds a wheel that excludes the SBML test suite. On the core branch this hid a failure that would have turned every CI Python version red. Every test that reads `resources/models/` resolves the path from the checkout, as `tests/test_parser.py` does.

**Windows CI is part of the verification, not a formality.** The core branch hit a Windows-only failure that no Linux run could show.

**When a measurement is taken against an older version, prove which source is imported** by printing `sbmlutils.__file__`, or read the old source with `git show`. An editable install resolving to the wrong tree produced two false conclusions on the core branch.

### Corpus

Of the 1690 l3v2 semantic cases, **123 use comp and 34 use fbc; none use distrib**. All are numbered 01124 or higher, so the core branch's 150-case window touched none of them. The 34 fbc cases contain no gene products, GPAs, user-defined constraints or key-value pairs. Nested `sBaseRef` occurs in exactly three cases, 01132 to 01134, maximum depth 3. The vendored `models/distrib/testsuite/` holds 50 cases containing no `<distrib:>` element at all.

So gene products, GPAs, user-defined constraints, key-value pairs and **all of distrib** are verified on in-repo fixtures: `fbc/e_coli_core.xml.gz`, `Recon3D.xml.gz`, `resources/distrib/uncertainty*.xml`, and `resources/examples/fbc_user_defined_constraints.xml`. Where a construct has no fixture at all, one is authored, and the spec records that such a fixture tests what its author already believed.

## Design by strand

### [V] Structural harness

As above. It lives in the test suite, is reusable by every later task, and also feeds a reporting script, as `scripts/roundtrip_report.py` does for simulation.

### [F] fbc

- **F1. `fbc:strict` on `Model`.** A new field, written from the model and read by the parser. It is currently hardcoded to `False` at document creation. With R3 in place, adding the field touches the annotations, the constructor and `ModelDict`, and `_keys` follows automatically.
- **F2. The parser loop.** It reads gene products (id, name, label, `associatedSpecies`), objectives and flux objectives, flux bounds (`lowerFluxBound`, `upperFluxBound`), the GPA as an infix string from the **id** side (`setAssociation` uses ids, so reading labels would change the model), species `charge` and `chemicalFormula`, user-defined constraints and their components, and key-value pairs on every element.
- **F3. `Objective.active` per R4.**
- **Fix: the gene pre-check mangles labels.** It strips `and`, `AND`, `or`, `OR` and parentheses from the association string with `str.replace`, so any gene label containing those letters as a substring is mangled (`ORF1` becomes `F1`) and a spurious `GeneProduct missing in model` is logged. Tokenize the association instead.
- **Fix: `EquationPart.keyValuePairs` is declared but never written.** Key-value pairs on a species reference are dropped.
- **Pin the GPA normalization** with a test on `R_PFL` and `R_ATPS4r`, so the R5 whitelist entry is visible and cannot hide anything else.

### [D] distrib

- **D1. `UncertParameter` and `UncertSpan` become `Sbase` subclasses.** Both constructors keep their positional `type` first, and the `Sbase` parameters go at the end, so every existing positional call in `examples/` and `tests/test_distrib.py` keeps working. `UncertParameter`'s check that `value` or `var` is set survives. Attribute writing moves out of `Uncertainty.create_sbml` into each class's `_set_fields`, called with `model=None` to avoid uncertainty-on-uncertainty recursion (the pattern `LocalParameter` already uses). Both classes join the authoring-hint exemptions, or every existing `UncertParameter(type=..., value=...)` starts warning. In libsbml, `UncertSpan` subclasses `UncertParameter` and there is no `getUncertSpan()` getter: spans come back from `getUncertParameter(index)`.
- **D2. The parser loop**, reading uncertainties, their parameters and spans with their metadata, `definitionURL`, and math.
- **Preserve `listOfUncertainties` child order.** It is currently lost.

### [C] comp

- **C1. Nested `sBaseRef`.** An optional recursive `sBaseRef: SbaseRef | None` field on `SbaseRef`, written through `createSBaseRef()` and read by walking `getSBaseRef()` until it returns `None`. The SBML spec allows arbitrary depth.
- **C2. `ModelDefinition` per R1**, including its unit definitions.
- **C3. The parser loop**: submodels (with `timeConversionFactor`, `extentConversionFactor`), ports, replaced elements, replaced by, deletions, model definitions (recursing into the core parser, per R1), and external model definitions (preserved, per R2).
- **Fix: `SbaseRef._set_fields` sets the id twice.** The checked second call returns `-2`, so **every `ReplacedElement` and `ReplacedBy` ever created logs two ERROR lines**.
- **Fix: `Submodel.setModelRef(None)` raises `TypeError`**, and `modelRef` defaults to `None`.
- **Layer 2 verification** on the 123 comp cases. Every one of the 103 comp cases that failed the core sweep passes once the original is flattened, which is the evidence layer 2 builds on.

### [X] Section 3 cleanups

- `_keys` derived from the annotations, per R3.
- `get_uid_for_unit` regains its type guard: a unit that is neither a `str` nor a `UnitDefinition` fails with a `ValueError` and guidance, instead of a SWIG `TypeError` from `setUnits`. `SbaseRef.unitRef` and `Species.substanceUnits` warn on a bad type the way `ValueWithUnit` does.
- `Model.units` is deep-copied in `merge_models`, like every other merged list.
- `Sbase._authoring_hints` becomes a `contextvars.ContextVar`, so concurrent model creation on several threads cannot race.
- **A port that is accepted but never written no longer declares an empty comp namespace.** `KineticLaw`, `LocalParameter`, `EventAssignment`, `Trigger`, `Priority`, `Delay`, `Event` and `Constraint` accept a `port` that is never written, yet it makes the model declare comp. Either write the port or stop declaring comp for it; the task decides on evidence.

### [X] Section 4 robustness

- **The six `parseL3FormulaWithModel` call sites that skip the `None` check** that `ast_node_from_formula` performs, so a formula that fails to parse passes on as `None` without an error. Route them through `ast_node_from_formula`.
- **Targeted `check()` wraps** on the `set*` calls in `factory.py` that can actually fail. The survey measured which of the 136 `set*` calls can fail and which cannot; wrapping only the ones that can fail is the goal, because wrapping all of them adds noise without value. Note that `setMath`, `setPersistent` and `setInitialValue` cannot fail and are not wrapped.
- The `ModelUnits.set_model_units` f-string log message becomes lazy `%s`.

## Sequencing

Hard dependencies, from the survey:

1. **[V] comes before everything**, and produces the baseline.
2. **D1 before D2.** A distrib parser cannot preserve metadata on an `UncertParameter` that has nowhere to put it.
3. **C1 before C3.** Cheap, about 20 lines.
4. **C2 before C3 finishes.** If `ModelDefinition` is a `Model`, the comp parser recurses; deciding late means writing the parser twice.
5. **R3's `_keys` derivation before F1**, or `fbc:strict` becomes a fifth hand-synchronized copy.
6. Section 3 and 4 items are independent and can land anywhere, but the `_authoring_hints` and authoring-hint exemption changes interact with D1 and should precede it.

## Success criteria

- The structural harness produces a baseline, and at the end reports **every fbc, distrib and comp construct preserved** on every test-suite case and fixture that exercises it, with any residual difference either an R5 normalization or an individually understood, documented known failure.
- On `e_coli_core`: 137 gene products, 69 GPAs, 95 flux bounds, 72 charges, 72 chemical formulas, the objective and `fbc:strict` all survive.
- On `icg_body.xml`: the submodel, 16 ports, 6 replaced elements and the external model definition all survive.
- Layer 2: every comp case whose flattened original simulates also simulates identically after a flattened round trip.
- Layer 3: every fbc fixture solves to the same FBA objective value, with the same bounds, stoichiometry and gene rules.
- The SBML core results are not regressed: the 150-case simulation window stays at 148/148, and the full sweep stays at or above 1372 of 1482.
- `tox -e py3.11` and `tox -e py3.14`, `ruff check`, `ruff format --check` and `ty check` are clean, and CI is green on Linux, macOS and Windows.

## Backward compatibility

The authoring styles stay: `UncertParameter(type, value=...)` positionally, `Reaction(..., geneProductAssociation="a and b")`, `Model(**model_dict)`, `Objective(...)` with its current default, `ModelDefinition(...)` for the fields it takes today.

Behaviour changes to record in the release notes:
- `ModelDefinition` is a `Model`, so it accepts and writes every element a model does.
- `UncertParameter` and `UncertSpan` are `Sbase`, so `str()` of one changes, and they carry metadata.
- `Model` gains `strict` (fbc).
- A model no longer declares an empty comp namespace for a port that is not written.

## Rejected alternatives

- **Completing `ModelDefinition`'s constructor by hand.** Adds a fifth copy of `Model`'s field set.
- **Making `Model` a dataclass or pydantic model now.** The honest single-source-of-truth answer, but the largest change here, entangled with `FrozenClass` and `ModelDefinition`, and #473 just removed a half-finished attempt.
- **A structured `GeneProductAssociation`.** Decided against by the user; measured to lose no metadata on any model in the repository.
- **Resolving external model definitions in the parser.** Inlining an external model changes the document; it is not a round trip.
- **Verifying by simulation or validation alone.** Both are blind to these packages, measured.
- **Splitting `factory.py` first.** Every later change would land as a cross-file diff against a layout nobody has exercised; splitting last draws the seams where the code ends up.
