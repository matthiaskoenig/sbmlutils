"""Test the SBML report information."""

import libsbml
import pytest

from sbmlutils.report.sbmlinfo import SBMLDocumentInfo
from sbmlutils.resources import EXAMPLES_DIR, REPRESSILATOR_SBML

REACTION_SBML = EXAMPLES_DIR / "reaction.xml"


def test_info_for_repressilator() -> None:
    """The report information is created for a model."""
    info = SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)
    assert info.info["doc"]
    assert info.info["model"]["reactions"]


def test_info_for_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    info = SBMLDocumentInfo.from_sbml(REACTION_SBML)
    equations = {r["id"]: r["equation"] for r in info.info["model"]["reactions"]}
    assert equations["v1"] == "x &#10142; y"
    assert equations["v2"] == "x &#10142; 2.0 y"
    # stoichiometry set by rules via the species reference id
    assert equations["v3"] == "f1 x &#10142; f2 y"
    assert equations["v4"] == "v4_x x &#10142; v4_y y"


@pytest.mark.parametrize(
    "stoichiometry, expected",
    [
        (1.0, "x"),
        (-1.0, "-x"),
        (2.0, "2.0 x"),
        (-2.5, "-2.5 x"),
        (0.0, "0.0 x"),
        (float("nan"), "sr x"),
    ],
)
def test_half_equation(stoichiometry: float, expected: str) -> None:
    """Half equations for the different stoichiometries."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setId("sr")
    sr.setSpecies("x")
    sr.setStoichiometry(stoichiometry)
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == expected


def test_half_equation_nan_without_id() -> None:
    """A variable stoichiometry without species reference id is marked."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setSpecies("x")
    sr.setStoichiometry(float("nan"))
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == "? x"
