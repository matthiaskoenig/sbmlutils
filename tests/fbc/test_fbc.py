"""Tests for the fbc helpers."""

import libsbml

from sbmlutils.fbc.fbc import add_default_flux_bounds
from sbmlutils.io import read_sbml
from sbmlutils.resources import DEMO_SBML
from sbmlutils.validation import ValidationOptions, validate_doc


def flux_bound_values(doc: libsbml.SBMLDocument) -> set[tuple[float, float]]:
    """Get the values of the flux bounds of every reaction.

    Args:
        doc: SBMLDocument with fbc

    Returns:
        the lower and upper bound value of every reaction
    """
    model: libsbml.Model = doc.getModel()
    values: set[tuple[float, float]] = set()
    for k in range(model.getNumReactions()):
        rfbc = model.getReaction(k).getPlugin("fbc")
        lower = model.getParameter(rfbc.getLowerFluxBound())
        upper = model.getParameter(rfbc.getUpperFluxBound())
        values.add((lower.getValue(), upper.getValue()))
    return values


def test_add_default_flux_bounds() -> None:
    """Every reaction gets the default bounds."""
    doc = read_sbml(DEMO_SBML)

    add_default_flux_bounds(doc, lower=-10.0, upper=20.0)

    assert flux_bound_values(doc) == {(-10.0, 20.0)}
    model: libsbml.Model = doc.getModel()
    assert model.getParameter("lower").getValue() == -10.0
    assert model.getParameter("upper").getValue() == 20.0


def test_add_default_flux_bounds_existing_ids() -> None:
    """Existing `lower` and `upper` ids are neither duplicated nor overwritten."""
    doc = read_sbml(DEMO_SBML)
    model: libsbml.Model = doc.getModel()
    for sid in ["lower", "upper"]:
        p: libsbml.Parameter = model.createParameter()
        p.setId(sid)
        p.setValue(0.0)
        p.setConstant(True)

    add_default_flux_bounds(doc, lower=-10.0, upper=20.0)

    vresult = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert vresult.error_count == 0
    assert model.getParameter("lower").getValue() == 0.0
    assert model.getParameter("upper").getValue() == 0.0
    assert model.getParameter("lower_1").getName() == "lower_1 flux bound"
    assert model.getParameter("upper_1").getName() == "upper_1 flux bound"
    assert flux_bound_values(doc) == {(-10.0, 20.0)}
