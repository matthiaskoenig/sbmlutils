# Follow-up after SBML core round-tripping (#469)

Companion issue to [#469](https://github.com/matthiaskoenig/sbmlutils/issues/469). Everything below was found while making SBML core round trip and was deliberately left out of that branch. Each item says where it came from and why it was left.

## Context

The core branch made `SBML -> sbml_to_model -> create_model -> SBML` faithful for SBML core. Measured:

| Metric | Before | After |
| --- | --- | --- |
| Round-trip simulation, first 150 l3v2 cases | 85/148 (57.4%) | 148/148 (100%) |
| Round-trip simulation, all 1690 l3v2 cases | not measurable | 1372/1482 (92.6%), 99.5% on core-only cases |
| Unit preservation, first 200 cases | 0/200 | 200/200 |
| Second round trip reproduces the first byte for byte | not measured | 1823/1823 files |

The 110 remaining full-sweep failures are 103 comp cases, every one of which passes once the original is flattened, and 7 cases where an id shadows a MathML constant (`pi`, `INF`, `NaN`, `time`, `avogadro`) and is lost in the L3 infix math.

## Decisions already taken

- **Package work lands as its own branch and pull request**, off `develop`, after the core pull request merges. It is roughly two and a half to three times the size of the core effort.
- **`Reaction.geneProductAssociation` stays an infix string.** Structured `GeneProductAssociation`, `And`, `Or` and `GeneProductRef` objects would roughly double the fbc work and change the `Reaction` API. The association's logical structure round trips through the string; metadata on nested association nodes is not preserved, and that is documented.
- **The `factory.py` split is deferred to its own pure-refactor change**, after the behaviour is settled and tested. A split touches every line and would make every package diff unreviewable.
- **The `SimpleSpeciesReference::setName` defect is reported upstream to libsbml.** It rejects a species reference or modifier name containing a space with `-4`, applying SId validation to an attribute of type `string`. The core branch logs a warning and pins the behaviour with a test that will fail if libsbml fixes it.

## Verification strategy: the lesson of the core branch

**Simulation is blind to all three packages, and so is validation.** Measured on the current tree:

| Package | What roadrunner does | Consequence |
| --- | --- | --- |
| fbc | loads the model but `simulate()` raises "FBC model discovered, but not simulatable" | no signal |
| distrib | simulates normally | passes with 100% of distrib dropped |
| comp | flattens, then simulates | hides structural loss |

Round-tripping `e_coli_core` today loses 137 gene products, 69 GPAs, 95 flux bounds, 72 charges and chemical formulas, and the objective. Round-tripping `icg_body.xml` loses its submodel, 16 ports, 6 replacedElements and its externalModelDefinition. **Every one of those stripped documents validates with zero errors.**

So the package work must start with a **structural harness**: an attribute-by-attribute comparison over every package construct, swept over the test suite and the in-repo fixtures. It gates everything else and must be the first task, not the last. Two further layers are worth having: comp semantics by flattening both sides with `flatten_sbml` and comparing trajectories, and fbc semantics through the existing `fbc/cobra.py` bridge, comparing the stoichiometric matrix, bounds, objective, `gene_reaction_rule` and the FBA solution.

**Verify with tox, not `uv run pytest`.** `uv run` uses an editable install that reads the source tree, while CI runs tox, which builds a wheel, and the wheel excludes the SBML test suite and the biomodels archives. On the core branch this hid a failure that would have turned every CI Python version red. Any test that reads `resources/models/` must resolve the path from the checkout, the way `tests/test_parser.py` does.

### Test corpus

Of the 1690 l3v2 semantic cases, **123 use comp, 34 use fbc (12 v1, 22 v2), and none use distrib**. All of them are numbered 01124 or higher. The fbc cases are uniform and contain no gene products, GPAs, user-defined constraints or key-value pairs. Nested `sBaseRef` occurs in exactly three cases (01132, 01133, 01134), with a maximum depth of 3 anywhere in the repository. The vendored `models/distrib/testsuite/` holds 50 cases that contain no `<distrib:>` element at all.

So gene products, GPAs, user-defined constraints, key-value pairs and all of distrib need in-repo fixtures: `fbc/e_coli_core.xml.gz`, `Recon3D.xml.gz`, `resources/distrib/uncertainty*.xml`, and `examples/fbc_user_defined_constraints.xml`, which is the only file with a user-defined constraint.

## 1. Package round-tripping: fbc, distrib, comp

Sizing below is relative to the 14-task core effort.

### fbc, about 0.5

`GeneProduct`, `Objective`, `FluxObjective`, `UserDefinedConstraint` and `UserDefinedConstraintComponent` can be written by `factory.py` but none is read by `parser.py`. Reaction flux bounds and `geneProductAssociation` are also unread, and so are species `charge` and `chemicalFormula`. Found by the survey in addition:

- **`fbc:strict` is hardcoded to `False`** and has no `Model` field, so a strict source model comes back non-strict.
- **`Objective.active` defaults to `True`**, so when a model has several objectives the last one written always wins `activeObjectiveId`, whichever one the source marked active.
- **`EquationPart.keyValuePairs` is declared but never written**, so key-value pairs on a species reference are dropped.

The three fbc and distrib write bugs found during the core work are already fixed on that branch: `KeyValuePair.uri` wrote `value` twice, `UncertParameter` called `setValue` instead of `setVar`, and `UncertSpan` called `setValueLower` instead of `setVarUpper`.

### distrib, about 0.4

`Uncertainty` is parsed nowhere. `UncertParameter` and `UncertSpan` are plain objects rather than `Sbase` subclasses, marked with an explicit `FIXME: This is an SBase!`, so they cannot hold `id`, `name`, `metaId`, `sboTerm`, notes or annotations. Making them `Sbase` is a large but mechanical diff. `Uncertainty` also **loses the order of its children**. Nested `UncertParameter` children, `definitionURL` outside the distribution case, and the `DrawFromDistribution` and `Distribution` elements cannot be represented at all. In libsbml, `UncertSpan` subclasses `UncertParameter` and there is no `getUncertSpan()` getter; spans come back from `getUncertParameter(index)`.

### comp, about 1.0

`Submodel`, `Port`, `ReplacedElement`, `ReplacedBy` and `Deletion` are supported except for the nested `<sBaseRef>` child, so deep references (`port -> sBaseRef -> sBaseRef`) cannot be expressed. `ModelDefinition` is a stub: its constructor accepts only `id`, `name`, `compartments` and `species`, and its `_set_fields` walks attribute names behind `hasattr` checks with `units` commented out. So a hierarchical model's inline model definitions cannot round trip; completing it is the main design decision in this section. comp also needs external model resolution. Found by the survey in addition:

- **`SbaseRef._set_fields` sets the id twice**, and because the checked call returns `-2`, **every `ReplacedElement` and `ReplacedBy` ever created logs two ERROR lines**.
- **`Submodel.setModelRef(None)` raises `TypeError`**, and `modelRef` defaults to `None`.

### Not modelled at all

`groups`, `layout` (a `Layout` class exists, but `Model.layouts` is untyped and the parser ignores it), `render`, `qual`, `multi`, `spatial` and `arrays`. Arbitrary non-RDF `<annotation>` content is dropped: only MIRIAM CVTerms are read and written.

## 2. Upstream libsbml defect

Reported upstream to libsbml; see "Decisions already taken". Numbering is kept so that sections 1, 3 and 4, which are in scope for the package work, keep their references.

## 3. Data model cleanups

- **Three hand-synchronized copies of `Model`'s field set.** The class-level field annotations, the `_keys` ClassVar used by `merge_models`, the `ModelDict` TypedDict and the constructor signature must all be kept in sync by hand. `Model` is no longer a pydantic `BaseModel` since the core branch, so the annotations are plain type hints, but the duplication remains.
- **`_keys["units"]` is deliberately `None`** while the declared field is `list[UnitDefinition]`, and the mismatch carries weight: correcting it to `list` would switch `merge_models` to extend-with-deepcopy and write duplicate unit ids. A comment says so, but the design is fragile and a single source of truth would remove the trap.
- **`ModelDefinition` still takes `type[Units]`** and never creates unit definitions. See comp above.
- **`get_uid_for_unit` lost its type guard** in the core branch, so a unit that is neither a `str` nor a `UnitDefinition` now fails as a SWIG `TypeError` from `setUnits` instead of a `ValueError` with guidance. `SbaseRef.unitRef` and `Species.substanceUnits` do not warn on a bad type the way `ValueWithUnit` does.
- **`Model.units` is merged by reference, not deep copied**, unlike every other merged list. This predates the core branch.
- **`Sbase._authoring_hints` is a class-level mutable, not thread-local**, so concurrent model creation on several threads could race. The package is single-threaded in its documented use.
- **An empty comp namespace for ports that are never written.** `Event`, `Constraint`, `KineticLaw`, `LocalParameter`, `EventAssignment`, `Trigger`, `Priority` and `Delay` accept a `port` that is never written (only the elements which call `Sbase.create_port` write one), and `KineticLaw` and `LocalParameter` accept a `replacedBy` that is never written, yet either now makes the model declare comp. The document is valid, but a port the user asked for is silently not created.

## 4. Robustness and consistency

The original version of this section said that `delay.setMath()`, `priority.setMath()` and the trigger's `setMath`, `setInitialValue` and `setPersistent` should be wrapped in `check()`. **That diagnosis was wrong.** Measured, those calls cannot fail: they return success even when given `None`. The real defects are:

- **Six `parseL3FormulaWithModel` call sites skipped the `None` check** that `ast_node_from_formula` does, so a formula that failed to parse was passed on as `None` without an error. Resolved: the core branch added the check to `KineticLaw.create_sbml` and `EventAssignment.create_sbml`, and `fix/event-trigger-priority-delay` routes the trigger, priority and delay of an event and the math of a `Constraint` through `ast_node_from_formula`, which logs the error.
- **105 of the 136 `set*` calls in `factory.py` are unchecked.** The survey lists exactly which of them can fail and which cannot. Wrapping only the ones that can fail is worth doing; wrapping all of them adds noise without value.
- **An unparsable function definition is dropped without a log line** in `parser.py`, unlike `ast_node_from_formula`, which logs. No current test-suite case reaches it.
- **The port-without-id error message** reads `'AssignmentRule(True)'` instead of naming the variable.
- **`LocalParameter.sid` is typed as a required `str`**, but the parser passes `None` for a non-compliant document that leaves out the mandatory id. `Species` and `Compartment` are handled the same way, so this is a question of convention rather than a bug.
- **Model history is never parsed.** `sbmlutils.parser` reads no `ModelHistory`, so creators and timestamps do not round trip. `SBMLDocumentInfo.sbase_dict` already extracts the history. The core branch reverted a `set_timestamps=False` change that was meant to help here, because it wrote a fake `1900-01-01` instead of preserving anything, and with no parser support there was nothing to preserve.

## 5. Decided before the 0.11.0 tag: resolved

**The empty-string sentinel on event children.** The core branch held an event's `trigger`, `priority` and `delay` as formula strings, with `None` meaning "no element" and `""` meaning "an element without math". That was inconsistent with every other element type, where `None` means "no math" and `""` is math which does not parse, and the strings had no place for the metadata of the element, which was lost on a round trip.

Resolved before 0.11.0 was tagged, on the branch `fix/event-trigger-priority-delay`, following the pattern of `KineticLaw`:

- `Trigger`, `Priority` and `Delay` are `Sbase` subclasses with `math: str | None` and the full `Sbase` parameter set; `Trigger` also carries `initialValue` and `persistent`. On an `Event`, `None` writes no element, an object whose `math` is `None` writes the element without math. The `""` sentinel is gone, `""` is math which does not parse like any other.
- Math which does not parse is logged as an error through `ast_node_from_formula`, the element is written without math. The claim above that an unparsable trigger "before logged an error" was wrong: measured on `e2944176`, before the core branch, it became a trigger without math just as silently; it is logged for the first time now.
- `Event(trigger="time >= 10", priority="1", delay="2")` is still accepted, the strings, and numbers, are normalized into the objects and write the same SBML as before. `trigger`, `priority` and `delay` are properties which normalize an assignment after construction the same way; a trigger string assigned later keeps the flags of the trigger it replaces. `trigger_persistent` and `trigger_initialValue` configure the `Trigger` created from a string, and as properties they read and set `event.trigger.persistent` and `event.trigger.initialValue`, so code which set them after construction, as in 0.10, still takes effect; set on an event without a trigger, they log a warning. Passed together with a `Trigger`, the object's own values win and a differing flag is logged as a warning.
- `sbml_to_model` reads the id, name, metaid, sboTerm, notes and annotations of the trigger, priority and delay with `parse_sbase_kwargs`, so they round trip. Their id is a real id attribute from SBML L3V2 on, `setId` aliases nothing, so they are not in `_ID_ATTRIBUTE_TYPECODES`; below L3V2 `setId` returns "unexpected attribute" and the generic level guard in `Sbase._set_fields` drops the id, as for a `KineticLaw`.
- A `port` on a `Trigger`, `Priority` or `Delay` is found by `Model._has_comp_content`, but is not written, see "An empty comp namespace for ports that are never written" in section 3.

## 6. Test coverage gaps

- **No regression test for the `include_sbo_cvterm=True` default path** in `tests/report/test_sbmlinfo.py`. The core branch added that flag so the parser could opt out of the synthesized SBO CVTerm while the sbml4humans report keeps it. That the downstream frontend still gets the same data is currently checked only by reading the code.
- **`test_assignment_rule_keeps_its_id` covers only `SBML_ASSIGNMENT_RULE`**, not the other four typecodes in `_ID_ATTRIBUTE_TYPECODES`.
- **The four function-definition cases all use the same two-argument `multiply` construct**, with no zero-argument or unset-math case.
- **`CASES_UNITS` is redundant** with `test_roundtrip_preserves_unit_definitions`: unit definitions do not change a roadrunner trajectory, so those parametrized cases pass whether or not units are preserved.
- **The `01760` entry in `KNOWN_FAILURES` gives a stale reason.**

## 7. Infrastructure

- **Plain `pytest` runs the slow sweep.** Without `-m "not sbml_testsuite"` it runs all 1690 cases, about 28 minutes, because each case starts a fresh interpreter for isolation. tox passes the marker, but running `pytest` by hand does not.
- **The dev-only `__main__` block in `parser.py` still reads `resources/models/` from the installed package.** It predates the core branch and runs only by hand.
- **`scripts/roundtrip_report.py` imports the private `_simulate`** from the test module.
- **The libroadrunner segfault** that was seen once on the unrestricted sweep could not be reproduced in four isolated and two in-process runs. Each case now runs in its own subprocess, and that isolation is tested with a real `SIGSEGV`, so a recurrence would be recorded rather than kill the sweep.

## 8. Documentation

- **`docs/units.md`** now documents the explicit `Unit(kind, exponent, scale, multiplier)` form alongside the pint style.
- **An id that shadows a MathML constant** (`pi`, `INF`, `NaN`, `time`, `avogadro`) is lost when math round trips as an L3 infix string. This is the cause of 7 of the remaining full-sweep failures and should be documented as a known limitation, or fixed by round-tripping the MathML itself rather than its infix form.

## 9. Core MathML fidelity, found by the structural harness of the package work

Measured by comparing the math of the main model of all 1690 test-suite cases before and after the core round trip (package branch, Task 1). None of these changes a simulation, which is why the core sweep never saw them. All come from round-tripping math as an L3 infix string instead of as MathML, like the constant shadowing in section 8.

- 658 maths: a negative constant `<cn> -2 </cn>` comes back as the unary minus of an integer, `<apply><minus/><cn type="integer"> 2 </cn></apply>`.
- 59 maths: a csymbol loses its display name, e.g. a time csymbol written as `t` comes back as `time`.
- 11 maths: a nested n-ary `and`/`or` of the same operator is flattened.

Round-tripping the MathML itself would remove all three and the constant shadowing at once.

## 10. pymetadata: `resource_normalized` loses information, found by the structural harness of the package work

Measured with pymetadata 0.6.2 (package branch, Task 1 fix round). sbmlutils guards against all of these from 0.12.0 on by writing the resource as given, so the fix belongs in pymetadata.

- **An unknown collection is reduced to the bare term:** `http://identifiers.org/sabiork/1406` becomes `1406`, `urn:miriam:foo:bar` becomes `bar`, `http://identifiers.org/unit/UO:0000040` becomes `UO:0000040`, `http://identifiers.org/ncbigi/gi:16128336` becomes `gi:16128336` (281 uses in the corpus, 138 distinct in `distrib/e_coli_core.xml` alone).
- **A compact URL of a collection it does not know is reduced to the bare term:** `https://identifiers.org/CMO:0000012` becomes `CMO:0000012` (`icg_body.xml`).
- **The collection is dropped from the URL:** `http://identifiers.org/slm/000000035` becomes `https://identifiers.org/000000035`, which resolves to nothing; parsing that result again gives collection `None` (319 uses).

- **A hyphenated prefix cannot be read back:** `urn:miriam:ec-code:1.1.1.1` becomes `https://identifiers.org/ec-code:1.1.1.1`, which keeps collection and term, but the compact pattern of pymetadata does not match a hyphen in the prefix, so parsing the result again fails and sbmlutils writes the URN as given (0 uses in the corpus).

The invariant which separates a canonicalization from a loss: `resource_normalized` is an `http(s)://` URL and parsing it again yields the same collection and term.

## 11. libsbml: the key-value pairs of a species reference are written and never read back

Measured with python-libsbml 5.21.2 alone, no sbmlutils involved (package branch, fbc fixes). The fbc version 3 `listOfKeyValuePairs` of a `<speciesReference>` is written into the document, and reading that document again gives a species reference without any key-value pair; on a `<modifierSpeciesReference>` the same round trip works. sbmlutils writes the pairs of reactants, products and modifiers from 0.12.0 on, so a reactant or product pair is write-only for every libsbml reader, and the structural comparison cannot see it. A test pins the behaviour so that a fixed libsbml is noticed. To report upstream at [sbmlteam/libsbml](https://github.com/sbmlteam/libsbml).

## 12. libsbml: the core id and name of a comp reference are not written

Measured with python-libsbml 5.21.2 alone (package branch, comp data model). The SBML Level 3 Version 2 core `id` and `name` set on a `ReplacedElement`, a `ReplacedBy`, a `Deletion` or a nested `sBaseRef` do not survive a write and re-read, nested or not; `metaid`, `sboTerm`, notes, annotation and the four reference attributes do. A `Port` is not affected, its `id` is a comp attribute. sbmlutils sets them, libsbml does not write them, and the structural comparison reads both sides through libsbml and cannot see it. Documented on the `SbaseRef` docstring.
