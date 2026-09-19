"""Test model merging."""

from pathlib import Path

import libsbml

from sbmlutils.factory import *


def test_model_keys_pinned() -> None:
    """Pin `Model._keys`.

    `Model._keys` is the map `merge_models` reads to decide whether a field
    is concatenated (`list`) or overwritten (`None`). It used to be a
    hand-written literal; this pins its exact content (every key and its
    `list`/`None` value) so that deriving it from the `Model` field
    annotations provably changes nothing. `units` and
    `creators` are `list`-typed fields on `Model` but are pinned to `None`
    here because `merge_models` merges them itself, deduplicated (units by
    unit id, creators by equality), in dedicated branches; marking either one
    `list` would make `merge_models`'s generic list-extend branch run
    instead, which for `units` writes duplicate unit ids into the merged
    model, and for `creators` is worse: `merge_models` unconditionally
    overwrites `model.creators` with `list(creators)` after its main loop, so
    a `creators` list populated by the generic branch is silently discarded,
    leaving the merged model with no creators at all.
    """
    assert Model._keys == {
        "sid": None,
        "name": None,
        "sboTerm": None,
        "metaId": None,
        "annotations": list,
        "notes": None,
        "keyValuePairs": list,
        "port": None,
        "packages": list,
        "creators": None,
        "model_units": None,
        "conversionFactor": None,
        "units": None,
        "functions": list,
        "compartments": list,
        "species": list,
        "parameters": list,
        "assignments": list,
        "rules": list,
        "rate_rules": list,
        "algebraic_rules": list,
        "reactions": list,
        "events": list,
        "constraints": list,
        "external_model_definitions": list,
        "model_definitions": list,
        "submodels": list,
        "ports": list,
        "replaced_elements": list,
        "deletions": list,
        "user_defined_constraints": list,
        "objectives": list,
        "gene_products": list,
        "layouts": list,
        "parsed": None,
    }


def test_creator_merge() -> None:
    """Test merging of models with creators."""
    c = Creator(
        givenName="Matthias",
        familyName="König",
        organization="Humboldt-University Berlin",
        email="konigmatt@googlemail.com",
    )

    m1 = Model(
        "m1",
        creators=[c],
    )
    assert m1.creators
    assert len(m1.creators) == 1

    m2 = Model("m2", creators=[c])
    assert m2.creators
    assert len(m2.creators) == 1

    m_merged = Model.merge_models(models=[m1, m2])

    print("CREATORS:", m_merged.creators)

    assert m_merged.creators
    assert len(m_merged.creators) == 1
    # models without units merge into a model without units
    assert m_merged.units == []


def test_units_merge() -> None:
    """Test that the units of merged models are collected and deduplicated.

    Two models which declare the same unit id must contribute a single
    UnitDefinition, otherwise the merged model writes two `unitDefinition`
    elements with the same id, which is an invalid SBML document.
    """

    class U1(Units):
        mM = UnitDefinition("mM", "mmole/liter")
        min = UnitDefinition("min", "min")

    class U2(Units):
        mM = UnitDefinition("mM", "mmole/liter")
        mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")

    m_merged = Model.merge_models(models=[Model("m1", units=U1), Model("m2", units=U2)])

    sids = [udef.sid for udef in m_merged.units]
    assert sids.count("mM") == 1
    assert sids.count("min") == 1
    assert sids.count("mmole_per_min") == 1

    # the base unit kinds write nothing, so the merged model has exactly the
    # three definitions of the two models
    doc = libsbml.readSBMLFromString(m_merged.get_sbml())
    model: libsbml.Model = doc.getModel()
    written = [
        model.getUnitDefinition(k).getId() for k in range(model.getNumUnitDefinitions())
    ]
    assert sorted(written) == ["mM", "min", "mmole_per_min"]


def test_units_merge_same_sid_different_attribute() -> None:
    """Test that the same unit id under different attribute names is merged once.

    The units used to be merged by the attribute name of the `Units` class, so
    two models which named the same unit id differently each contributed a
    UnitDefinition and the merged model had a duplicate SBML id.
    """

    class U1(Units):
        mM = UnitDefinition("mM", "mmole/liter")

    class U2(Units):
        millimolar = UnitDefinition("mM", "mmole/liter")

    m_merged = Model.merge_models(models=[Model("m1", units=U1), Model("m2", units=U2)])

    assert [udef.sid for udef in m_merged.units].count("mM") == 1

    doc = libsbml.readSBMLFromString(m_merged.get_sbml())
    model: libsbml.Model = doc.getModel()
    assert model.getNumUnitDefinitions() == 1


def test_units_merge_same_attribute_different_sid() -> None:
    """Test that different unit ids under the same attribute name are both kept.

    The units used to be merged by the attribute name of the `Units` class, so
    two models which used the same attribute name for different unit ids
    silently lost one of the two definitions.
    """

    class U1(Units):
        u = UnitDefinition("mM", "mmole/liter")

    class U2(Units):
        u = UnitDefinition("mmole_per_min", "mmole/min")

    m_merged = Model.merge_models(models=[Model("m1", units=U1), Model("m2", units=U2)])

    sids = [udef.sid for udef in m_merged.units]
    assert "mM" in sids
    assert "mmole_per_min" in sids


def test_units_merge_copies_unit_definitions(tmp_path: Path) -> None:
    """Test that a merged model does not share its unit definitions.

    Every other merged list is extended by `deepcopy`, the units were
    collected by reference. The merged model and the model it was merged from
    then shared one `UnitDefinition` object, so changing the unit of the
    merged model silently changed the SBML the source model writes.
    """

    class U1(Units):
        mM = UnitDefinition("mM", "mmole/liter", name="millimolar")

    m1 = Model("m1", units=U1)
    m_merged = Model.merge_models(models=[m1, Model("m2")])

    (udef,) = [udef for udef in m_merged.units if udef.sid == "mM"]
    udef.name = "changed in the merged model"

    sbml_path = tmp_path / "m1.xml"
    create_model(model=m1, filepath=sbml_path)
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    assert doc.getModel().getUnitDefinition("mM").getName() == "millimolar"
