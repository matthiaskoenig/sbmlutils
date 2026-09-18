"""Test model merging."""

import libsbml

from sbmlutils.factory import *


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
