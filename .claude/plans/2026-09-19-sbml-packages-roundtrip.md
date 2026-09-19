# SBML Package Round-Tripping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `SBML -> sbml_to_model -> create_model -> SBML` preserve the fbc, distrib and comp packages, proven by a structural attribute-by-attribute comparison, and fix the section 3 and 4 data model and robustness defects along the way.

**Architecture:** A structural comparison harness comes first and produces a per-construct baseline, because roadrunner and validation are both blind to these packages. The core parser is then refactored so that the parsing of a model body works on any `libsbml.Model`, which lets each comp `ModelDefinition` reuse it. Then the fbc, distrib and comp strands each add their data model fixes and their parser loop into that body parser.

**Tech Stack:** python >= 3.11, `python-libsbml` with the fbc, distrib and comp packages, `libroadrunner` (layer 2) and `cobra` (layer 3) as optional test dependencies, `pytest`, `ruff`, `ty`, `uv`, `tox`.

**Spec:** `.claude/specs/2026-09-19-sbml-packages-roundtrip-design.md`

## Global Constraints

- **VERIFY WITH TOX, NOT `uv run pytest`.** Every task's verification is `uvx --with tox-uv tox -e py3.11` and `uvx --with tox-uv tox -e py3.14`, both green. `uv run pytest` uses an editable install that reads the source tree; CI runs tox, which builds a wheel. On the core branch this hid a failure that would have turned every CI Python version red. A passing `uv run pytest` is not sufficient evidence and must not be reported as if it were.
- **The SBML test suite is resolved from the checkout, never from `sbmlutils.resources`.** The wheel excludes `resources/models/sbml-test-suite-3.4.0` and `resources/models/biomodels`. Use the pattern in `tests/test_roundtrip.py` / `tests/test_parser.py`: `Path(__file__).parent.parent / "src" / "sbmlutils" / "resources" / "models" / ...`.
- **The package fixtures DO ship in the wheel** and are used through their `sbmlutils.resources` constants: `FBC_ECOLI_CORE_SBML`, `FBC_RECON3D_SBML`, `COMP_ICG_BODY`, `COMP_ICG_BODY_FLAT`, and the files under `resources/distrib/` and `resources/examples/`.
- **When measuring against an older version, prove which source is imported** by printing `sbmlutils.__file__`, or read the old source with `git show <commit>:<path>`. An editable install resolving to the wrong tree produced two false conclusions on the core branch.
- **Trust the live code over this plan.** Twelve of fifteen task briefs on the core branch contained a factual error about the code. Line numbers below were measured at the time of writing and will drift. If this plan disagrees with the code, the code wins; report the disagreement.
- **Never use the em dash (U+2014).** Plain hyphen everywhere: code, comments, docstrings, markdown and commit messages.
- **No `Co-Authored-By` trailer on any commit.** The user's CLAUDE.md forbids it. A `Claude-Session` trailer is permitted.
- Never edit `CHANGELOG.md`. Release notes go in `release-notes/`.
- Every module, class and function carries full type annotations and a **google style** docstring (Args/Returns/Raises).
- Log calls use lazy `%s` formatting, never f-strings (ruff `G`).
- libsbml has no type stubs: annotate libsbml objects explicitly and use getters, never SWIG-synthesized attributes.
- Suppress a type diagnostic only with a rule-specific `# ty: ignore[rule-name]`.
- `[tool.ty.terminal] error-on-warning = true`: the tree must stay at zero ty diagnostics.
- Markdown carries no hard line wraps.
- **libsbml objects are SWIG proxies that do not keep their owning `SBMLDocument` alive.** A test helper returning a `libsbml.Model` without holding its document segfaults on the next libsbml call. Hold the document.
- The SBML core results must not regress: `uv run python scripts/roundtrip_report.py --limit 150` stays at **148/148**.
- Branch is `feat/469-packages-roundtrip`, off `develop`.

## Measured baseline (from the survey, before any change)

| Fixture | What a round trip loses today |
| --- | --- |
| `FBC_ECOLI_CORE_SBML` | 137 gene products, 69 GPAs, 95 flux bounds, 72 charges, 72 chemical formulas, the objective, `fbc:strict` |
| `COMP_ICG_BODY` | its submodel, 16 ports, 6 replaced elements, its external model definition |

**Both stripped documents validate with zero errors.** Task 1 turns this into a per-construct table over the whole corpus.

## Corpus

Of the 1690 l3v2 semantic cases, 123 use comp and 34 use fbc (12 v1, 22 v2); none use distrib; all are numbered 01124 or higher. The fbc cases contain no gene products, GPAs, user-defined constraints or key-value pairs. Nested `sBaseRef` occurs only in 01132, 01133 and 01134 (maximum depth 3).

In-repo fixtures fill the gaps: `FBC_ECOLI_CORE_SBML` and `FBC_RECON3D_SBML` (gene products, GPAs), `resources/examples/fbc_user_defined_constraints.xml` (the only user-defined constraint), `resources/distrib/distrib_all.xml`, `distrib_normal.xml`, `uncertainty.xml`, `uncertainty_distribution.xml`, `uncertainty_uncertspan.xml`, `uncertainty_uncertvalue.xml` (distrib).

## File Structure

| File | Responsibility |
| --- | --- |
| `tests/structural.py` | **new.** The structural comparison: walks the fbc, distrib and comp constructs of two documents attribute by attribute and returns the differences, applying the R5 whitelist. Pure libsbml, no optional dependency. |
| `tests/test_package_roundtrip.py` | **new.** Package round-trip tests built on `tests/structural.py`, plus layers 2 and 3. |
| `scripts/package_report.py` | **new.** Sweeps the corpus with the structural comparison and prints the per-construct baseline table. |
| `src/sbmlutils/parser.py` | The kwargs helpers move to module level and the model-body parsing becomes a reusable function; each strand adds its loop into it. |
| `src/sbmlutils/factory.py` | Data model changes per strand. |
| `release-notes/0.12.0.md` | **new.** Release notes for this work, following the pattern of `release-notes/0.11.0.md`. |

`factory.py` is over 4000 lines. **Splitting it is out of scope by the user's decision** and must not be attempted.

---

### Task 1: The structural comparison harness and the baseline

Gates everything else. Produces the per-construct baseline before any parser code is written, the analogue of the core branch's 57.4%.

**Files:**
- Create: `tests/structural.py`
- Create: `tests/test_package_roundtrip.py`
- Create: `scripts/package_report.py`

**Interfaces:**
- Consumes: `sbml_to_model`, `create_model`, `ValidationOptions` (existing).
- Produces:
  - `Difference`: a dataclass `(construct: str, element_id: str, attribute: str, before: object, after: object)`.
  - `structural_diff(doc_in: libsbml.SBMLDocument, doc_out: libsbml.SBMLDocument) -> list[Difference]`: every difference in fbc, distrib and comp content, after applying the whitelist.
  - `roundtrip_document(sbml_path: Path, tmp_path: Path) -> tuple[libsbml.SBMLDocument, libsbml.SBMLDocument]`: reads, round trips through `sbml_to_model` and `create_model` at L3V2, and returns both documents. **The caller must hold both documents** for as long as it uses any object from them.
  - `WHITELIST`: the R5 normalizations, each with a reason string.

- [ ] **Step 1: Design the comparison policy and write it down as the module docstring of `tests/structural.py`.**

  The policy is a design decision that every later test depends on, so it is written first. It must state:
  - **What is compared, per package:**
    - fbc: the document `fbc:strict`; each gene product's `id`, `name`, `label`, `associatedSpecies`; each objective's `id`, `type`, whether it is the active objective, and each flux objective's `reaction` and `coefficient`; each reaction's `lowerFluxBound`, `upperFluxBound` and GPA as its infix string; each species' `charge` and `chemicalFormula`; each user-defined constraint's `id`, bounds and components; every key-value pair's `key`, `value` and `uri`.
    - distrib: each uncertainty on each element, its uncertainty parameters and spans with `type`, `value`, `var`, `valueLower`/`varLower`/`valueUpper`/`varUpper`, `definitionURL`, math and metadata, **in document order**.
    - comp: each submodel's `id`, `modelRef`, `timeConversionFactor`, `extentConversionFactor` and deletions; each port's `id` and reference; each replaced element and replaced by with its references and **the full nested `sBaseRef` chain**; each model definition **recursively, including its units and all its elements**; each external model definition's `id`, `source`, `modelRef` and `md5`.
    - For every construct above: `metaId`, `sboTerm` and the set of CVTerm resources.
  - **Order:** lists whose SBML order carries no meaning compare as sets keyed by id; `listOfUncertainties` children and the elements of a nested `sBaseRef` chain compare in order.
  - **The whitelist (R5), exactly these three and nothing else:** GPA same-operator flattening, `((a and b) and c)` equal to `(a and b and c)`; `<cn>` gaining `type="integer"`; a `urn:miriam:` annotation URI becoming its `identifiers.org` URL. Each has a reason string.

- [ ] **Step 2: Write failing self-tests that prove the harness sees each KIND of loss, using synthetic mutations.**

  These must not depend on what the current parser happens to lose, because later tasks remove those losses one by one and a test pinned to them would break (pre-flight ruling P1). Instead, take a real fixture, damage one construct in a **copy** of its document, and assert `structural_diff` reports exactly that damage and nothing else. In `tests/test_package_roundtrip.py`:

  ```python
  @pytest.mark.parametrize("mutation", ["drop_gene_product", "change_flux_bound",
      "drop_objective", "flip_strict", "drop_port", "drop_submodel",
      "truncate_sbaseref_chain", "reorder_uncertainty_children"])
  def test_structural_diff_sees_each_kind_of_loss(mutation: str, tmp_path: Path) -> None:
      """A harness that reports nothing on a damaged document is blind.

      Each mutation removes or alters exactly one construct in a copy of a
      real fixture; the harness must report that construct and only that.
      """
      doc_in, doc_damaged = _damaged_copy(mutation, tmp_path)
      diffs = structural_diff(doc_in, doc_damaged)
      assert diffs, f"structural_diff missed a {mutation}"
      assert {d.construct for d in diffs} == {_EXPECTED_CONSTRUCT[mutation]}
  ```

  plus the reverse: `structural_diff(doc, doc)` of an undamaged document returns `[]`, so the harness does not report noise. `_damaged_copy` reads the fixture with libsbml and applies the mutation directly to the libsbml document, and **must hold both documents** for as long as they are used.

  The real-fixture baseline (e_coli_core loses 137 gene products, and so on) is **recorded** in step 7, not asserted as a test.

- [ ] **Step 3: Run them to verify they fail** (the harness does not exist yet). `uvx --with tox-uv tox -e py3.14 -- tests/test_package_roundtrip.py -v`

- [ ] **Step 4: Implement `tests/structural.py`** to the policy in step 1. Walk each package through its libsbml plugin (`getPlugin("fbc")`, `getPlugin("distrib")`, `getPlugin("comp")`) on both documents. For comp model definitions, recurse. The function returns differences; it does not assert.

- [ ] **Step 5: Run the tests to verify they pass**: the harness reports each synthetic loss and nothing on an undamaged document.

- [ ] **Step 6: Write `scripts/package_report.py`**, which sweeps the 157 package cases of the test suite (resolved from the checkout) plus every fixture named in the Corpus section, runs `structural_diff` on each, and prints a table of `construct -> (cases exercising it, cases where it is preserved)`. It isolates each case in its own subprocess, as `scripts/roundtrip_report.py` does, so a native crash ends one case, not the sweep.

- [ ] **Step 7: Record the baseline.** Run the report and paste its table into the commit message. **This table is the "57.4%" of this effort.** Expect every package construct at or near zero preserved.

- [ ] **Step 8: Prove the self-tests are load-bearing**, by mutation: temporarily make `structural_diff` return `[]` and confirm the step 2 tests fail. Restore.

- [ ] **Step 9: Verify and commit.** tox on py3.11 and py3.14, `ruff check`, `ruff format --check`, `uvx ty check`, and the 150-case core report at 148/148.

---

### Task 2: Make the model-body parser reusable

A pure refactor with byte-identical output. Prerequisite for comp (Task 12) and the place every later parser loop goes, so that each `ModelDefinition` gets them automatically.

**Files:**
- Modify: `src/sbmlutils/parser.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - Module-level `_parse_sbase_kwargs(sbase: libsbml.SBase) -> dict[str, Any]`, `_parse_udef_kwargs(...)` and `_parse_variable_kwargs(...)`, lifted unchanged from the closures inside `sbml_to_model`. **Verified at writing time that they read only their own argument**, so lifting them changes nothing.
  - `_parse_model_body(model: libsbml.Model, m: Model) -> None`: populates `m` from `model` with everything `sbml_to_model` parses today after constructing `m`: unit definitions, model units, function definitions, compartments, species, parameters, reactions with kinetic laws, initial assignments, rules, events, constraints. It takes any `libsbml.Model`, so it works on a `libsbml.ModelDefinition`, which subclasses `libsbml.Model`.
  - `sbml_to_model` keeps its signature and behaviour, and calls `_parse_model_body`.

- [ ] **Step 1: Capture a byte-for-byte baseline.** Before editing, write the round-tripped SBML of every one of the first 150 l3v2 test-suite cases plus every fixture in the Corpus section to a scratch directory.
- [ ] **Step 2: Lift the three helpers to module level.** Rename with a leading underscore and update the call sites.
- [ ] **Step 3: Extract `_parse_model_body`.** Move the element loops out of `sbml_to_model` into it. `sbml_to_model` keeps reading the document, detecting packages, constructing `m`, setting `m.parsed`, and calls `_parse_model_body(model, m)`.
- [ ] **Step 4: Prove byte-identical output.** Re-run the capture of step 1 and `diff -r` against the baseline. **Expected: no difference.** Any difference is a bug in the refactor.
- [ ] **Step 5: Verify and commit.** tox on py3.11 and py3.14, lint, 150-case report at 148/148.

---

### Task 3: Derive `Model._keys` from the field annotations (ruling R3)

Prerequisite for `fbc:strict` (Task 5), or it becomes a fifth hand-synchronized copy of `Model`'s field set.

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Model._keys`, `Model` field annotations)
- Test: `tests/test_model_merge.py`

**Interfaces:**
- Produces: `Model._keys` computed once at class definition from the `Model` field annotations: any `list[...]` annotation maps to `list`, everything else to `None`, with an explicit override table of two entries, `units -> None` and `creators -> None`, and a comment saying why (`merge_models` collects both in its own deduplicating branch and overwrites them after its loop; a `list` would make it concatenate unit definitions and write duplicate unit ids, and would leave the merged creators empty). The second entry is ruling R3a: the literal already held `"creators": None`, which the plan had missed.

- [ ] **Step 1: Write a test that the derived `_keys` equals the current literal `_keys` exactly**, so the refactor provably changes nothing. Capture the literal dict from the live code into the test first.
- [ ] **Step 2: Run it against the current code**: it passes trivially, which is the point; it pins the current content.
- [ ] **Step 3: Replace the literal with the derivation.** Use `typing.get_type_hints(Model)` or the class `__annotations__`; check which resolves the forward references in this file under `from __future__ import annotations`.
- [ ] **Step 4: Run the test and the existing `tests/test_model_merge.py`**, which pins the units deduplication at its three merge tests. Both must pass unchanged.
- [ ] **Step 5: Verify and commit.** tox on py3.11 and py3.14, lint.

---

### Task 4: Section 3 and 4 robustness fixes

A batch of small, independent fixes from the follow-up issue. Each gets its own test.

**Files:**
- Modify: `src/sbmlutils/factory.py`, `src/sbmlutils/metadata/annotator.py`, and wherever the `spatialDimensions` loss turns out to be
- Test: `tests/test_factory.py`, `tests/metadata/` or the closest existing annotation test file

**Interfaces:** internal only.

The fixes, each with a failing test first:

- [ ] **`get_uid_for_unit` regains its type guard.** A unit that is neither a `str` nor a `UnitDefinition` raises `ValueError` naming the offending type and pointing at `UnitDefinition` or a unit id, instead of surfacing as a SWIG `TypeError` from `setUnits`. Test: `Parameter("p", value=1.0, unit=1.0)` written to a model raises `ValueError`. `SbaseRef.unitRef` and `Species.substanceUnits` log the same warning `ValueWithUnit` does for a bad type.
- [ ] **`Model.units` is deep-copied in `merge_models`**, like every other merged list. Test: merge two models, mutate a unit definition in the merged model, and assert the source model's unit definition is unchanged.
- [ ] **`Sbase._authoring_hints` becomes a `contextvars.ContextVar[bool]`.** `no_authoring_hints()` sets and resets it with the token. Test: two threads, one inside `no_authoring_hints()` writing a model and one outside writing a model with an unnamed element; the outside thread still logs its hint.
- [ ] **(Ruling T4a: already fixed before this branch, in the core round-tripping work of 0.11.0. `factory.py` has four call sites and each checks for `None` and logs. The task pins that with a test and changes no code; the checked sites keep their site-specific messages.)** ~~The six `parseL3FormulaWithModel` call sites that skip the `None` check are routed through `ast_node_from_formula`~~, so an unparsable formula logs an error instead of passing `None` on silently. Find them with `grep -n "parseL3FormulaWithModel" src/sbmlutils/factory.py`; exclude `ast_node_from_formula` itself and call sites that already check. Test: one unparsable formula per call site logs an ERROR (`caplog`).
- [ ] **(Ruling T4a: already fixed before this branch; pinned with a test.)** `ModelUnits.set_model_units` uses lazy `%s` instead of an f-string passed to `logger.warning`.
- [ ] **An annotation resource never loses its collection (ruling C1b).** `metadata/annotator.py` writes `annotation.resource_normalized`, and pymetadata returns the bare term for a collection it does not know: `http://identifiers.org/sabiork/1406` is written as `1406`, `urn:miriam:foo:bar` as `bar`. The normalized resource is written only when it is an `http(s)://` URL **and** parsing it again yields the same collection and term as the resource given (ruling C1d); otherwise write the resource as given. The warning is per collection, not per resource (ruling C1e): inside a document-scoped collector (a `ContextVar`, entered by the code which writes a whole document) each resource is logged at `DEBUG` and one `WARNING` per collection is logged when the scope ends, with the count and an example; a single `annotate_sbase` call outside a collector warns directly. Per resource, Recon3D logged 19853 warnings and e_coli_core 1426. A test for "no URI scheme" is NOT enough: `http://identifiers.org/unit/UO:0000040` becomes the bare `UO:0000040`, which reads like a URI with the scheme `UO`, and `http://identifiers.org/slm/000000035` becomes `https://identifiers.org/000000035`, a URL which has lost its collection (measured with pymetadata 0.6.2; 281 and 319 uses in the corpus). Known collections stay normalized. Failing tests first: a species annotated `(BQB.IS, "http://identifiers.org/sabiork/1406")`, `"http://identifiers.org/unit/UO:0000040"`, `"https://identifiers.org/CMO:0000012"` or `"http://identifiers.org/slm/000000035"` is written with exactly that resource, and `(BQB.IS, "chebi/CHEBI:12965")` still as `https://identifiers.org/CHEBI:12965`. Re-run `scripts/package_report.py` afterwards: no `cvterms` difference may remain which is a lost collection or a bare term. This is a loss in released 0.11.0: release note.
- [ ] **A non-integral `spatialDimensions` round trips (ruling C7).** Test-suite case 01310 writes a compartment's `spatialDimensions` 2.7 back as 0.0, a core loss the simulation sweep cannot see. Reproduce it end to end on case 01310 first, find where the value is lost (the parser, the `Compartment` field type, or the factory), fix it there. Failing test first: a compartment with `spatialDimensions=2.7` round trips as 2.7.

- [ ] **Verify and commit** after each fix or as one commit per fix. tox on py3.11 and py3.14, lint, 150-case report at 148/148.

---

### Task 5: `fbc:strict` on `Model`

**Files:**
- Modify: `src/sbmlutils/factory.py` (`Model`, `Document.create_sbml`), `src/sbmlutils/parser.py`
- Test: `tests/test_package_roundtrip.py`

**Interfaces:**
- Consumes: Task 3's derived `_keys`, Task 2's `_parse_model_body`.
- Produces: `Model.strict: bool | None`. `None` keeps today's behaviour of writing `fbc:strict="false"` when fbc is declared. The parser sets it from the document.

- [ ] **Step 1: Failing test:** round trip a model whose source has `fbc:strict="true"` and assert the output has `fbc:strict="true"`. The current code hardcodes `setStrict(False)` in `Document.create_sbml` (measured near `factory.py:4979`).
- [ ] **Step 2 (moved):** `Objective.active` is set from the document in **Task 6**, where objectives are first parsed (pre-flight ruling P2). This task does `fbc:strict` only.
- [ ] **Step 3: Add `Model.strict`**, write it in `Document.create_sbml`, and add it to the annotations, the constructor and `ModelDict`. `_keys` follows automatically from Task 3; confirm that.
- [ ] **Step 4: In the parser, read `fbc:strict`** from the fbc plugin of the model inside `_parse_model_body` and set `m.strict` (ruling T5a: the plugin attaches to a comp `ModelDefinition` too, and Task 12 recurses into `_parse_model_body`), only when `isSetStrict()` is true. **An fbc v1 model is NOT read as strict (ruling T5c):** libsbml's v1-to-v2 converter invents `fbc:strict="true"`, which turned 11 of the 12 valid fbc v1 test-suite cases into documents with 54 errors of id 2020714 each. The parser unsets it after converting, `strict` stays `None` and is written as `false`; the structural comparison does not compare `fbc.strict` for an fbc v1 source, which has no such attribute.
- [ ] **Step 5: Verify and commit.** tox, lint, 148/148.

---

### Task 6: The fbc parser loop

**Files:**
- Modify: `src/sbmlutils/parser.py` (`_parse_model_body`)
- Test: `tests/test_package_roundtrip.py`

**Interfaces:**
- Consumes: Tasks 1, 2, 5. The factory classes `GeneProduct`, `Objective`, `FluxObjective`, `UserDefinedConstraint`, `UserDefinedConstraintComponent`, `KeyValuePair`, and `Reaction`'s `lowerFluxBound`, `upperFluxBound`, `geneProductAssociation`, and `Species`' `charge`, `chemicalFormula`. The survey found these attribute-complete for writing; **read each live constructor before building one**.

- [ ] **Step 1: Add a test that `structural_diff` reports no fbc difference on `FBC_ECOLI_CORE_SBML`** after a round trip. Run it to confirm it fails today (per the recorded baseline, 137 gene products and the rest are lost).
- [ ] **Step 2: Parse gene products** (`id`, `name`, `label`, `associatedSpecies`) into `m.gene_products`.
- [ ] **Step 3: Parse the GPA of each reaction as an infix string from the ID side.** `Reaction.geneProductAssociation` is written with `setAssociation(infix, usingId=True, addMissingGP=False)`, so the parser must produce an infix of gene product **ids**, not labels; reading labels would change the model. Check which libsbml accessor gives the id-side infix.
- [ ] **Step 3b: `Objective.active` from the document (ruling R4, moved here from Task 5 by pre-flight ruling P2).** Read the model's `activeObjectiveId` and pass `active=True` only to the matching objective and `active=False` to every other. The authoring default of `Objective.active` stays `True`. Failing test first: a model with two objectives whose `activeObjectiveId` names the **first** round trips with the first still active. Today the last-written objective wins.
- [ ] **Step 4: Parse flux bounds, objectives and flux objectives, species charge and chemical formula, user-defined constraints and their components, and key-value pairs on every element** that carries them.
- [ ] **Step 5: Run the test to verify it passes** on `FBC_ECOLI_CORE_SBML`, and add the same structural assertion on `FBC_RECON3D_SBML` and `resources/examples/fbc_user_defined_constraints.xml`. The packaged `fbc_user_defined_constraints.xml` was invalid fbc v3 (13 errors, component coefficients spelled as numbers, which libsbml refuses to write) and is regenerated from its example (ruling T6a, release note).
- [ ] **Step 6: Re-run `scripts/package_report.py`** and record the fbc rows against the Task 1 baseline in the commit message.
- [ ] **Step 7: Verify and commit.** tox, lint, 148/148.

---

### Task 7: fbc fixes: gene label mangling, species-reference key-value pairs, the GPA normalization pin

**Files:**
- Modify: `src/sbmlutils/factory.py`
- Test: `tests/test_factory.py`, `tests/test_package_roundtrip.py`

- [ ] **Gene labels are mangled by the pre-check.** The check strips `(`, `)`, `and`, `AND`, `or`, `OR` from the association string with a `str.replace` chain (measured near `factory.py:2366-2371`), so any label containing those letters is mangled and a spurious `GeneProduct missing in model` is logged. The chain is also inconsistent: `"and"` becomes a space while `"AND"`, `"or"` and `"OR"` become nothing. **Replace it with a tokenizer** that splits on whitespace and parentheses and drops only the whole tokens `and`, `AND`, `or`, `OR`. Failing test first: a gene product with label or id `ORF1` in an association `ORF1 and b0001`, where both exist, logs **no** missing-gene-product error.
- [ ] **`EquationPart.keyValuePairs` is declared but never written.** Write them in `set_speciesref_fields`. Failing test first: a reactant with a key-value pair round trips with it.
- [ ] **Pin the GPA normalization.** A test on `R_PFL` and `R_ATPS4r` of `FBC_ECOLI_CORE_SBML` asserts the round-tripped infix is the same-operator-flattened form, and that `structural_diff` whitelists exactly that and reports nothing else for those reactions. This makes the R5 entry visible and ensures it cannot hide anything else.
- [ ] **Pin the GPA node metadata (ruling C5).** Every `and` and `or` node of `resources/distrib/e_coli_core.xml` and `e_coli_core_expression.xml` (22 and 32 in each) carries `sboTerm` SBO:0000173 (and) or SBO:0000174 (or) and nothing else; the term restates the node's own operator, so the infix string loses nothing that is not derivable. It is NOT whitelisted. A test asserts on both files that the only fbc difference is `fbc.geneProductAssociation.nodes`, and that every lost node metadata is exactly SBO:0000173 on an `and` or SBO:0000174 on an `or`. Any other node metadata must fail this test.
- [ ] **The fbc charge is written for the document's fbc version (ruling C6).** libsbml keeps the fbc v2 integer charge and the fbc v3 double charge apart and writes only the one of the document's version, so today `Species(charge=-2.0)` in an fbc v2 model and `Species(charge=1)` in an fbc v3 model are both written `fbc:charge="0"`. The factory sets the charge the document's fbc version writes (v2: the integer, a non-integral charge logged as an error; v3: the double); the parser reads it by version. Failing tests first: both cases write the charge given.
- [ ] **Regenerate the key-value-pair fixture (ruling C4).** `resources/examples/fbc/fbc_key_value_pair.xml` predates the key-value-pair writer and holds three empty `keyValuePair` elements. Regenerate it from `examples/fbc/fbc_key_value_pair.py` and point the key-value-pair fixture of `tests/test_package_roundtrip.py` at the resource instead of building it from the example.
- [ ] **Verify and commit.** tox, lint, 148/148.

---

### Task 8: `UncertParameter` and `UncertSpan` become `Sbase`

**Files:**
- Modify: `src/sbmlutils/factory.py` (`UncertParameter`, `UncertSpan`, `Uncertainty.create_sbml`, the authoring-hint exemptions)
- Test: `tests/test_distrib.py`

**Interfaces:**
- Produces: `UncertParameter` and `UncertSpan` as `Sbase` subclasses carrying `sid`, `name`, `sboTerm`, `metaId`, `annotations`, `notes` and `keyValuePairs`, each writing its own attributes in `_set_fields`.

Measured at writing time: `class UncertParameter:` and `class UncertSpan:` have no base class (near `factory.py:3246` and `3270`).

- [ ] **Step 1: Failing test:** an `UncertParameter` carrying a `metaId` and `sboTerm` writes both onto the libsbml `UncertParameter`.
- [ ] **Step 2: Keep every existing call working.** Both constructors keep `type` as the first positional parameter; the `Sbase` parameters go at the end. `tests/test_distrib.py` constructs these positionally across the full `DISTRIB_UNCERTTYPE_*` matrix and must pass **unchanged**. `UncertParameter`'s check that `value` or `var` is set must survive.
- [ ] **Step 3: Move attribute writing out of `Uncertainty.create_sbml`** into each class's `_set_fields`, called with `model=None` so that `Sbase._set_fields` does not recurse into uncertainties on the uncertainty (the pattern `LocalParameter` already uses).
- [ ] **Step 4: Add both classes to the authoring-hint exemptions** in `Sbase._set_fields`, or every existing `UncertParameter(type=..., value=...)` starts logging `'name' should be set`. Test: building the existing distrib examples logs no authoring hint.
- [ ] **Step 5: Note for the implementer:** in libsbml, `UncertSpan` subclasses `UncertParameter` and there is **no** `getUncertSpan()` getter. A span is created with `createUncertSpan()` and read back through `getUncertParameter(index)`.
- [ ] **Step 6: Verify and commit.** tox, lint, 148/148, and `tests/test_distrib.py` unchanged and green.

---

### Task 9: The distrib parser loop

**Files:**
- Modify: `src/sbmlutils/parser.py` (`_parse_model_body`, and the kwargs so that every element can carry its uncertainties)
- Test: `tests/test_package_roundtrip.py`

- [ ] **Step 0: Delete the three draft-syntax fixtures (ruling C2).** `resources/distrib/uncertainty_distribution.xml`, `uncertainty_uncertspan.xml` and `uncertainty_uncertvalue.xml` use a pre-release distrib syntax (`<distrib:uncertainty>` directly under the parameter, `<distrib:confidenceInterval>`, `<distrib:mean>`) which libsbml drops silently on read, so they look like coverage and contain none. Nothing references them; confirm with grep before deleting, and name the removal in the release notes.
- [ ] **Step 1: Failing test:** `structural_diff` reports no distrib difference on each file that carries uncertainties: `distrib/uncertainty.xml`, `distrib/e_coli_core_expression.xml`, `examples/distrib_uncertainties.xml`, `examples/distrib_comp.xml`, `examples/distrib_comp_flat.xml`, `examples/model.xml` (verify the list against the resources). **The test asserts first that libsbml reads at least one uncertainty from each file**, so it cannot pass vacuously.
- [ ] **Step 2: Parse each element's uncertainties**, with their uncertainty parameters and spans, `definitionURL`, math and metadata. Every `Sbase` can carry uncertainties, so the natural place is the shared kwargs.
- [ ] **Step 3: Preserve `listOfUncertainties` child order.** The survey found it is currently lost. Test: a source whose uncertainty lists a span before a parameter round trips in that order.
- [ ] **Step 4: Run the tests to verify they pass**, re-run the package report, and record the distrib rows against the baseline.
- [ ] **Step 5: Verify and commit.** tox, lint, 148/148.

**Corpus caveat, to record in the commit message:** the SBML test suite has no distrib case at all, so distrib is verified only on in-repo fixtures, which test what their authors already believed.

---

### Task 10: comp: nested `sBaseRef`, and two `SbaseRef`/`Submodel` bugs

**Files:**
- Modify: `src/sbmlutils/factory.py` (`SbaseRef`, `Submodel`)
- Test: `tests/test_comp.py`

- [ ] **Nested `sBaseRef`.** Add an optional recursive `sBaseRef: SbaseRef | None` field on `SbaseRef`, written with `createSBaseRef()` in `_set_fields`. The SBML spec allows arbitrary depth. Failing test first: a port with a three-deep `sBaseRef` chain writes all three levels.
- [ ] **`SbaseRef._set_fields` sets the id twice**, and the checked second call returns `-2`, so every `ReplacedElement` and `ReplacedBy` ever created logs two ERROR lines. Failing test first: creating a `ReplacedElement` logs no ERROR.
- [ ] **`Submodel.setModelRef(None)` raises `TypeError`**, and `modelRef` defaults to `None`. Guard the call. Failing test first: a `Submodel` without a `modelRef` is written without raising.
- [ ] **Verify and commit.** tox, lint, 148/148, `tests/test_comp.py` green.

---

### Task 11: `ModelDefinition` subclasses `Model` (ruling R1)

**Files:**
- Modify: `src/sbmlutils/factory.py` (`ModelDefinition`)
- Test: `tests/test_comp.py`

**Interfaces:**
- Consumes: `Model`, and `Model._create_sbml` which creates every list of elements.
- Produces: `class ModelDefinition(Model)`. Its `create_sbml` creates a `libsbml.ModelDefinition` through the comp plugin of the document's model and fills it with `Model`'s element creation. Every element type a `Model` accepts, including its `units`, is now accepted and written.

Measured at writing time: `class ModelDefinition(Sbase):` near `factory.py:3872`. Its current `_set_fields` walks attribute names behind `hasattr`, uses camelCase names that do not match `Model`'s snake_case, and leaves `units` commented out.

- [ ] **Step 1: Failing test:** a `ModelDefinition` with parameters, reactions, rules, events, a unit definition, gene products and algebraic rules writes all of them into the `libsbml.ModelDefinition`. Today only compartments and species can be passed at all.
- [ ] **Step 2: Keep every existing `ModelDefinition(...)` call working.** Grep `src/`, `tests/`, `examples/` and `docs/` for them first. The constructor must still accept the arguments it takes today.
- [ ] **Step 3: Decide what `ModelDefinition` must NOT inherit from `Model`** and document it: the document-level `packages`, and whatever else only makes sense on the top-level model. Test that a `ModelDefinition` does not try to set them.
- [ ] **Step 4: Confirm the `units` of a model definition are written**, since unit preservation is what #469 fixed at the top level.
- [ ] **Step 5: Verify and commit.** tox, lint, 148/148, `tests/test_comp.py` and `tests/examples/` green.

---

### Task 12: The comp parser loop

**Files:**
- Modify: `src/sbmlutils/parser.py`
- Test: `tests/test_package_roundtrip.py`

**Interfaces:**
- Consumes: Tasks 2, 10, 11.

- [ ] **Step 1: Add a test that `structural_diff` reports no comp difference on `COMP_ICG_BODY`** after a round trip. Run it to confirm it fails today (per the recorded baseline, the submodel, 16 ports, 6 replaced elements and the external model definition are lost).
- [ ] **Step 2: Parse submodels** (`id`, `modelRef`, `timeConversionFactor`, `extentConversionFactor`), **ports, replaced elements, replaced by and deletions**, each with the full nested `sBaseRef` chain from Task 10.
- [ ] **Step 3: Parse each model definition by recursing into `_parse_model_body`** (Task 2) with a `ModelDefinition` (Task 11) as the target. This is why the refactor and R1 come first: the recursion gets every core, fbc and distrib element of the model definition for free.
- [ ] **Step 4: Preserve external model definitions exactly, and do NOT resolve them** (ruling R2): `id`, `source`, `modelRef`, `md5`. Test: the output's `<externalModelDefinition>` attributes equal the input's, and no external file is opened.
- [ ] **Step 5: Run the test to verify it passes** on `COMP_ICG_BODY`, and on the three nested-`sBaseRef` cases 01132, 01133 and 01134 (resolved from the checkout).
- [ ] **Step 6: Re-run the package report** over all 123 comp cases and record the comp rows against the baseline.
- [ ] **Step 7: Verify and commit.** tox, lint, 148/148.

---

### Task 13: No empty comp namespace for a port that is never written

**Files:**
- Modify: `src/sbmlutils/factory.py`
- Test: `tests/test_comp.py`

`KineticLaw`, `LocalParameter`, `EventAssignment`, `Trigger`, `Priority`, `Delay`, `Event` and `Constraint` accept a `port` that is never written, yet it makes `Model._has_comp_content()` declare the comp package, so the document gets an empty comp namespace.

- [ ] **Decide on evidence, then implement one of two options, and record the choice in the commit message.**
  - **Write the port** for each element type whose SBML element can be the target of a comp port. A port references an element by id, so an element without an id attribute at the target level cannot have one.
  - **Or stop declaring comp for a port that will not be written**, and log a warning that the port is ignored.
  - Check each element type against libsbml: can a `comp:port` reference it?
- [ ] **Failing test first** for the chosen behaviour.
- [ ] **Verify and commit.** tox, lint, 148/148.

---

### Task 14: Targeted `check()` wraps

**Files:**
- Modify: `src/sbmlutils/factory.py`
- Test: `tests/test_factory.py`

The survey measured which `set*` calls in `factory.py` can fail and which cannot. `setMath`, `setPersistent` and `setInitialValue` **cannot fail**: they return success even given `None`. They are **not** wrapped.

- [ ] **Step 1: Enumerate the unwrapped `set*` calls** with `grep -nE "\.set[A-Z][A-Za-z]*\(" src/sbmlutils/factory.py`, excluding those already inside `check(`.
- [ ] **Step 2: For each, determine by execution whether it can fail** on the inputs `factory.py` can pass it. Record the list in the commit message.
- [ ] **Step 3: Wrap only the ones that can fail** in `check(...)` with a message naming the element. Wrapping calls that cannot fail adds noise without value.
- [ ] **Step 4: For a representative sample of the wrapped calls, a failing test** that passes a value libsbml rejects and asserts an ERROR is logged.
- [ ] **Step 4b: Two swallowed failures found by the fbc work (ruling T7a), each reproduced end to end and with a failing test first.** (1) `create_model` reports `valid: TRUE` for a file it never wrote when the parent directory of `filepath` is missing: a write which fails must surface as an error (decide from the live `write_sbml`/`create_model` code whether the directory is created or the failure raised, and keep 'validation reports, it never blocks' intact: that sentence is about validation, not about a file which does not exist). (2) A key-value pair in an fbc v2 document writes an empty `<keyValuePair/>` plus two `check()` errors, which is how the old key-value-pair fixture got its three empty elements: key-value pairs are fbc v3, so in a v2 document one clear error names the element and the version and no element is written.
- [ ] **Step 5: Verify and commit.** tox, lint, 148/148.

---

### Task 15: Semantic verification layers 2 and 3

**Files:**
- Modify: `tests/test_package_roundtrip.py`

- [ ] **Layer 2, comp semantics.** For each comp case and `COMP_ICG_BODY`: flatten the original and the round-tripped document with `sbmlutils.comp.flatten_sbml`, simulate both with roadrunner, and compare trajectories with the tolerances of `tests/test_roundtrip.py`. Skip when roadrunner is not installed, following the existing pattern. Note that `flatten_sbml` changes the working directory to resolve external model definitions relative to the file; restore it in a `finally`.
- [ ] **Layer 3, fbc semantics.** For `FBC_ECOLI_CORE_SBML` and `FBC_RECON3D_SBML`: load both documents through `sbmlutils.fbc.cobra` and compare the stoichiometric matrix, flux bounds, objective, `gene_reaction_rule` and the FBA objective value. Skip when `cobra` is not installed; `cobra` is deliberately not in the tox `ty` environment, and its import already carries a `# ty: ignore[unresolved-import]`.
- [ ] **Prove each layer can fail**, by mutation: drop a submodel from the round-tripped comp document and confirm layer 2 fails; change a flux bound and confirm layer 3 fails. Restore.
- [ ] **Verify and commit.** tox, lint, 148/148.

---

### Task 16: Final measurement, documentation and release notes

**Files:**
- Modify: `docs/io.md`, `docs/fbc.md`, `docs/distrib.md`, `docs/comp.md`
- Create: `release-notes/0.12.0.md`
- Modify: `.claude/issues/followup-after-core-roundtrip.md`

- [ ] **Step 1: Run `scripts/package_report.py` over the whole corpus** and record the final per-construct table next to the Task 1 baseline. Any construct not fully preserved is either an R5 normalization or an individually understood, documented known failure.
- [ ] **Step 2: Confirm the success criteria of the spec**, each with its evidence: the `e_coli_core` and `icg_body` losses are all gone; layer 2 passes on every comp case whose flattened original simulates; layer 3 solves every fbc fixture to the same objective; the core 150-case report is 148/148 and the full core sweep is at or above 1372 of 1482.
- [ ] **Step 3: Document round-tripping of the packages** in `docs/io.md`, and in the package pages, what is and is not preserved. State the corpus caveat: distrib is verified only on in-repo fixtures.
- [ ] **Step 4: Write `release-notes/0.12.0.md`** following the exact format of `release-notes/0.11.0.md`: breaking changes, behaviour changes, features, fixes, documentation, development. The breaking and behaviour changes come from the spec's Backward compatibility section. **Every factual claim in the release notes must be one this branch measured.** On the core branch, two false claims reached the release notes.
- [ ] **Step 5: Update the follow-up issue:** mark sections 1, 3 and 4 done with a pointer to this work, and record what remains (the `factory.py` split, the `Model` single-source question, a structured GPA, external model resolution).
- [ ] **Step 6: Verify and commit.** tox on py3.11 and py3.14, `ruff check`, `ruff format --check`, `uvx ty check`, the docs build (`uv run zensical build --clean`), and the 150-case core report at 148/148.
- [ ] **Do NOT push and do NOT open a pull request.** The final whole-branch review comes first. The user has directed that the pull request be opened once that review is clean.
