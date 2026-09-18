# Follow-up after SBML core round-tripping (#469)

Companion issue to [#469](https://github.com/matthiaskoenig/sbmlutils/issues/469). Everything below was found while making SBML core round trip, and was deliberately deferred rather than folded into that branch. Each item records where it came from and why it was left.

## Context

#469 took the round-trip simulation pass rate over the SBML test suite from 85/148 (57.4%) to 148/148 (100%) on the first 150 l3v2 semantic cases, and unit preservation from 0/200 to 200/200. Scope was SBML core plus the annotation and notes defects the round trip introduced. The items here are what that scope excluded.

## 1. Package round-tripping: fbc, distrib, comp

The largest remaining gap, and the reason #469 was scoped to core.

- **fbc.** `GeneProduct`, `Objective`, `FluxObjective`, `UserDefinedConstraint` and `UserDefinedConstraintComponent` are attribute-complete in `factory.py` but `parser.py` reads none of them. Reaction flux bounds and `geneProductAssociation` are likewise unread. Note the `GeneProductAssociation` itself cannot carry its own `id`, `name`, `metaId` or `sboTerm`, nor can the nested `And`/`Or`/`GeneProductRef` nodes.
- **distrib.** `Uncertainty` is parsed nowhere. `UncertParameter` and `UncertSpan` are plain objects rather than `Sbase` subclasses, carrying an explicit `FIXME: This is an SBase!`, so they cannot hold `id`, `name`, `metaId`, `sboTerm`, notes or annotations. Nested `UncertParameter` children, `definitionURL` outside the distribution case, and the `DrawFromDistribution`/`Distribution` elements are not representable at all.
- **comp.** `Submodel`, `Port`, `ReplacedElement`, `ReplacedBy` and `Deletion` are supported except for the nested `<sBaseRef>` child, so deep comp references (`port -> sBaseRef -> sBaseRef`) cannot be expressed. `ModelDefinition` is a stub: its constructor accepts only `id`, `name`, `compartments` and `species`, so a hierarchical model's inline model definitions cannot survive a round trip. comp also needs external model resolution, which is why it was excluded.
- **Not modelled at all:** `groups`, `layout` (a `Layout` class exists but `Model.layouts` is untyped and the parser ignores it), `render`, `qual`, `multi`, `spatial`, `arrays`. Arbitrary non-RDF `<annotation>` content is dropped: only MIRIAM CVTerms are read and written.

## 2. Upstream libsbml defect: `SimpleSpeciesReference::setName`

Worth reporting to libsbml.

`libsbml.SpeciesReference.setName` and `libsbml.ModifierSpeciesReference.setName` apply SId syntax validation to the `name` attribute, which in SBML is type `string`, not `SId`. Measured against python-libsbml 5.21.1:

```
SpeciesReference.setName('reactant name')          -> rc=-4 (LIBSBML_INVALID_ATTRIBUTE_VALUE), getName() == ''
SpeciesReference.setName('reactantname')           -> rc=0,  getName() == 'reactantname'
ModifierSpeciesReference.setName('modifier name')  -> rc=-4, getName() == ''
Species.setName('a species name')   [control]      -> rc=0,  getName() == 'a species name'
```

`Species.setName` and `Reaction.setName` have no such restriction, so the behaviour is inconsistent within libsbml itself. Both classes inherit the implementation from `SimpleSpeciesReference`.

#469 handles this by checking the return code and logging a warning naming the value, the species and the code, so the loss is visible rather than silent. It deliberately does not mangle the name as a workaround. A test pins the current behaviour, so if libsbml fixes it the test will fail and someone will notice.

## 3. Data model cleanups

- **Three hand-synchronized copies of the same field set.** `Model` carries the pydantic-style field annotations, the `_keys` ClassVar used by `merge_models`, the `ModelDict` TypedDict, and the constructor signature. All four must be kept in sync by hand. Collapsing them to one source of truth was left out of #469 to keep the diff reviewable.
- **`Model._keys["units"]` is deliberately out of sync** with the declared field type, and the mismatch is load-bearing: correcting it to `list` would flip `merge_models` to extend-with-deepcopy and emit duplicate unit ids. There is a comment saying so, but the underlying design is fragile.
- **`Model.units_dict` is dead.** Set to `None` in `__init__` and read nowhere.
- **`ModelDefinition` still takes `type[Units]`** and never creates unit definitions. Pre-existing FIXME.
- **`get_uid_for_unit` lost its type guard** during #469, so a value that is neither a `str` nor a `UnitDefinition` now surfaces as a SWIG `TypeError` from `setUnits` rather than a `ValueError` with guidance. `SbaseRef.unitRef` and `Species.substanceUnits` do not warn on a bad type the way `ValueWithUnit` does.
- **`Model.units` merge is by reference, not deepcopy**, unlike every other merged list in `merge_models`. Pre-existing pattern, noted for completeness.
- **`Sbase._authoring_hints` is a bare class-level mutable**, not thread-local, so concurrent model creation across threads could race. The package is single-threaded in documented use.
- **`Model._has_comp_content()` does not descend into nested `Sbase` objects**, so a `KineticLaw`, `LocalParameter` or `EquationPart` carrying a `port` would not be detected. It also skips `Model.layouts`. Neither is currently exploitable, because `Layout.create_sbml` never calls `create_port` and no nested construct emits a comp element, but both are latent.
- **`factory.py` is now over 3700 lines.** Splitting it was explicitly out of scope for #469 and needs its own change.

## 4. Robustness and consistency

- **Unchecked libsbml return codes.** `delay.setMath()`, `priority.setMath()`, and the trigger's `setMath`/`setInitialValue`/`setPersistent` are not wrapped in `check()`, inconsistent with the surrounding code. A math expression that fails to set would do so silently.
- **Silent drop on degenerate math.** `parser.py` discards a function definition whose `formulaToL3String` returns a falsy string, with no log line, asymmetric with `ast_node_from_formula` which logs. Not reachable from any current test-suite case.
- **`ModelUnits.set_model_units` builds its message with an f-string** then passes it to `logger.warning`, rather than lazy `%s`. Pre-existing.
- **`LocalParameter.sid` is typed as a required `str`** but the parser supplies it from `parse_sbase_kwargs`, which yields `None` for a spec-noncompliant document omitting the mandatory id. This matches how `Species` and `Compartment` are already handled, so it is a convention question rather than a bug.
- **Model history is never parsed.** `sbmlutils.parser` reads no `ModelHistory`, so creators and timestamps do not round trip. `SBMLDocumentInfo.sbase_dict` already extracts the history, so the data is available. #469 reverted a `set_timestamps=False` change that had been intended to help here, because it wrote a fake `1900-01-01` rather than preserving anything, and because with no parser support there was nothing to preserve.

## 5. Test coverage gaps

- **No regression test for the `include_sbo_cvterm=True` default path** in `tests/report/test_sbmlinfo.py`. #469 added that flag so `sbmlutils.parser` could opt out of the synthesized SBO CVTerm while the sbml4humans report keeps it. Behaviour preservation for that downstream consumer currently rests on code inspection alone, so a future change to the default could break the frontend with no failing test in this repository.
- **`test_assignment_rule_keeps_its_id` covers only `SBML_ASSIGNMENT_RULE`**, not the other four typecodes in `_ID_ATTRIBUTE_TYPECODES`.
- **The four function-definition test cases all use the same two-argument `multiply` construct.** No zero-argument case, no unset-math case.
- **`test_roundtrip_preserves_unit_definitions` asserts unit definition ids, `timeUnits` and compartment units, but not parameter `units` or species `substanceUnits`.** The 200/200 unit preservation result is currently demonstrated by a manual measurement rather than pinned by pytest.

## 6. Infrastructure

- **The full sweep segfaults.** Running the unrestricted 1690-case round-trip sweep crashes inside libroadrunner's LLVM JIT at varying positions. It never fires within the first 150 cases, so it does not affect the reported numbers, but a native crash cannot be caught by Python, so the sweep needs subprocess isolation (`pytest-forked` or equivalent) before it can run unattended.
- **`scripts/roundtrip_report.py` imports the private `_simulate`** from the test module.
- **`assert_roundtrip_simulates_equal`'s docstring documents only `AssertionError`** in its `Raises` section, though `sbml_to_model`, `create_model` and roadrunner can all raise.

## 7. Documentation

- **`docs/units.md` documents only the pint authoring style.** #469 added an explicit `Unit(kind, exponent, scale, multiplier)` list as the faithful representation, which the docs do not mention.
- **The `spatialDimensions` default changed from `3` to `None`.** This is valid SBML, but it changes unit inheritance, because a compartment's inheritance of the model-level `volumeUnits` is keyed on `spatialDimensions == 3`. Most sbmlutils models set `unit` explicitly so the impact is small, but it is not documented.
- **An orphaned `# FIXME: support merging of notes, see` comment** remains in `parser.py` with a dangling reference, now doubly stale since the module-level notes FIXME was removed.
