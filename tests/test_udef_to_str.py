"""Test UnitDefinition to string functions."""

import libsbml
import pytest

from sbmlutils.factory import UnitDefinition
from sbmlutils.report.units import udef_to_string

testdata_str = [
    ("pmol", "pmol", "pmol"),
    ("hr", "hr", "hr"),
    ("ml_per_l", "ml/l", "ml/l"),
    ("mmole_per_min", "mmole/min", "mmol/min"),
    ("m3", "meter^3", "m^3"),
    ("m3", "meter^3/second", "m^3/s"),
    ("mM", "mmole/liter", "mmol/l"),
    ("ml_per_s_kg", "ml/s/kg", "ml/s/kg"),
    ("dimensionless", "dimensionless", "-"),
    ("item", "item", "item"),
]


@pytest.mark.parametrize(("uid", "definition", "expected"), testdata_str)
def test_unit_definition_str(uid: str, definition: str, expected: str) -> None:
    """Test unit conversion to string."""
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    unit = UnitDefinition(uid, definition)
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def, model=model, format="str") == expected


testdata_latex = [
    ("pmol", "pmol", "pmol"),
    ("hr", "hr", "hr"),
    ("ml_per_l", "ml/l", "\\frac{ml}{l}"),
    ("mmole_per_min", "mmole/min", "\\frac{mmol}{min}"),
    ("m3", "meter^3", "m^3"),
    ("m3", "meter^3/second", "\\frac{m^3}{s}"),
    ("mM", "mmole/liter", "\\frac{mmol}{l}"),
    ("ml_per_s_kg", "ml/s/kg", "\\frac{ml}{s \\cdot kg}"),
    ("dimensionless", "dimensionless", "-"),
    ("item", "item", "item"),
]


@pytest.mark.parametrize(("uid", "definition", "expected"), testdata_latex)
def test_unit_definition_latex(uid: str, definition: str, expected: str) -> None:
    """Test unit conversion to latex."""
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    unit = UnitDefinition(uid, definition)
    unit_def = unit.create_sbml(model)
    assert udef_to_string(unit_def, model=model, format="latex") == expected


#: units written with a multiplier, scale and exponent of their own, as
#: (kind, multiplier, scale, exponent), with the string they render to
testdata_units = [
    ([(libsbml.UNIT_KIND_SECOND, 160, 0, 1)], "160 s"),
    ([(libsbml.UNIT_KIND_GRAM, 2.1, 0, 1)], "2.1 g"),
    ([(libsbml.UNIT_KIND_SECOND, 11, 0, 1)], "11 s"),
    ([(libsbml.UNIT_KIND_SECOND, 0.5, 0, 1)], "500 ms"),
    ([(libsbml.UNIT_KIND_SECOND, 60, 0, 1)], "min"),
    ([(libsbml.UNIT_KIND_SECOND, 60, 0, -1)], "1/min"),
    ([(libsbml.UNIT_KIND_SECOND, 60, 0, 2)], "min^2"),
    ([(libsbml.UNIT_KIND_SECOND, 3600, 0, 1)], "hr"),
    ([(libsbml.UNIT_KIND_SECOND, 3600, 0, -2)], "1/hr^2"),
    ([(libsbml.UNIT_KIND_SECOND, 86400, 0, 1)], "day"),
    ([(libsbml.UNIT_KIND_METRE, 1, -2, 1)], "cm"),
    ([(libsbml.UNIT_KIND_METRE, 10, -3, 1)], "cm"),
    ([(libsbml.UNIT_KIND_METRE, 1, -2, 3)], "cm^3"),
    ([(libsbml.UNIT_KIND_LITRE, 1, -3, 1)], "ml"),
    ([(libsbml.UNIT_KIND_GRAM, 1, 3, -1), (libsbml.UNIT_KIND_SECOND, 1, 0, 1)], "s/kg"),
    ([(libsbml.UNIT_KIND_GRAM, 2.1, 0, 2)], "(2.1 g)^2"),
    ([(libsbml.UNIT_KIND_DIMENSIONLESS, 1, 0, 1)], "-"),
    ([(libsbml.UNIT_KIND_SECOND, 1, 0, 0.5)], "s^0.5"),
    ([(libsbml.UNIT_KIND_SECOND, 1, 0, -1.5)], "1/s^1.5"),
    (
        [(libsbml.UNIT_KIND_MOLE, 1, -3, 1), (libsbml.UNIT_KIND_SECOND, 160, 0, -1)],
        "mmol/(160 s)",
    ),
    ([(libsbml.UNIT_KIND_SECOND, 160, 0, -1)], "1/(160 s)"),
    (
        [(libsbml.UNIT_KIND_GRAM, 2.1, 0, 1), (libsbml.UNIT_KIND_MOLE, 1, 0, 1)],
        "(2.1 g)*mol",
    ),
    (
        [(libsbml.UNIT_KIND_MOLE, 1, 0, 1), (libsbml.UNIT_KIND_GRAM, 2.1, 0, -2)],
        "mol/(2.1 g)^2",
    ),
]


@pytest.mark.parametrize(("units", "expected"), testdata_units)
def test_unit_multiplier_str(
    units: list[tuple[int, float, int, float]], expected: str
) -> None:
    """A multiplier is rendered as a number, a named unit only for its exact factor."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    unit_def: libsbml.UnitDefinition = model.createUnitDefinition()
    unit_def.setId("u")
    for kind, multiplier, scale, exponent in units:
        unit: libsbml.Unit = unit_def.createUnit()
        unit.setKind(kind)
        unit.setMultiplier(multiplier)
        unit.setScale(scale)
        unit.setExponent(exponent)
    assert udef_to_string(unit_def, model=model, format="str") == expected


testdata_units_latex = [
    (
        [(libsbml.UNIT_KIND_MOLE, 1, -3, 1), (libsbml.UNIT_KIND_SECOND, 160, 0, -1)],
        "\\frac{mmol}{160 s}",
    ),
    (
        [
            (libsbml.UNIT_KIND_MOLE, 1, -3, 1),
            (libsbml.UNIT_KIND_SECOND, 160, 0, -1),
            (libsbml.UNIT_KIND_GRAM, 1, 0, -1),
        ],
        "\\frac{mmol}{\\left(160 s\\right) \\cdot g}",
    ),
    ([(libsbml.UNIT_KIND_SECOND, 1, 0, 0.5)], "s^0.5"),
]


@pytest.mark.parametrize(("units", "expected"), testdata_units_latex)
def test_unit_multiplier_latex(
    units: list[tuple[int, float, int, float]], expected: str
) -> None:
    """A term with a magnitude is grouped in a latex product."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    unit_def: libsbml.UnitDefinition = model.createUnitDefinition()
    unit_def.setId("u")
    for kind, multiplier, scale, exponent in units:
        unit: libsbml.Unit = unit_def.createUnit()
        unit.setKind(kind)
        unit.setMultiplier(multiplier)
        unit.setScale(scale)
        unit.setExponent(exponent)
    assert udef_to_string(unit_def, model=model, format="latex") == expected
