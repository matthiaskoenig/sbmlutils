"""Driving a model in place with interpolated data."""

from collections.abc import Callable
from pathlib import Path

import libsbml
import pandas as pd
import pytest
from interpolation_models import uptake_model, write_model

from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import (
    AlgebraicRule,
    AssignmentRule,
    Event,
    InitialAssignment,
    Model,
    RateRule,
)

TIMECOURSE = pd.DataFrame(
    {
        "time": [0.0, 2.0, 4.0, 6.0],
        "glc_ext": [5.0, 8.0, 6.0, 5.0],
        "f": [1.0, 2.0, 0.5, 1.0],
        "ext": [2.0, 2.5, 2.0, 1.5],
    }
)


def _interpolation(*columns: str) -> Interpolation:
    """The linear interpolation of the time course, x and the columns."""
    return Interpolation(TIMECOURSE[["time", *columns]], method="linear")


def test_drive_parameter(tmp_path: Path) -> None:
    """A parameter becomes non constant and follows the data."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path)
    model = doc.getModel()
    assert not model.getParameter("f").getConstant()
    assert model.getAssignmentRuleByVariable("f") is not None
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0


def test_drive_species(tmp_path: Path) -> None:
    """A species becomes a boundary species and keeps its reactions."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    model = _interpolation("glc_ext").drive(path).getModel()
    species = model.getSpecies("glc_ext")
    assert species.getBoundaryCondition()
    assert not species.getConstant()
    assert model.getReaction("UPTAKE").getReactant(0).getSpecies() == "glc_ext"


def test_drive_compartment(tmp_path: Path) -> None:
    """A compartment becomes non constant."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    model = _interpolation("ext").drive(path).getModel()
    assert not model.getCompartment("ext").getConstant()


@pytest.mark.parametrize("only_substance", [False, True])
def test_drive_species_simulated(tmp_path: Path, only_substance: bool) -> None:
    """The data is the concentration, or the amount with only substance units."""
    roadrunner = pytest.importorskip("roadrunner")
    model = uptake_model()
    model.species[0].hasOnlySubstanceUnits = only_substance
    path = write_model(model, tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    _interpolation("glc_ext").drive(path, filepath=driven)
    r = roadrunner.RoadRunner(str(driven))
    selection = "glc_ext" if only_substance else "[glc_ext]"
    s = r.simulate(0, 6, 4, selections=["time", selection])
    assert list(s[selection]) == pytest.approx([5.0, 8.0, 6.0, 5.0])


def test_drive_by_mapping_with_model_quantity_as_x(tmp_path: Path) -> None:
    """`targets` maps a column to an id, x is a quantity of the model."""
    roadrunner = pytest.importorskip("roadrunner")
    data = pd.DataFrame({"f": [0.0, 1.0, 2.0], "rate": [0.0, 0.25, 1.0]})
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    Interpolation(data, method="linear").drive(path, {"rate": "k"}, filepath=driven)
    r = roadrunner.RoadRunner(str(driven))
    assert r["k"] == pytest.approx(0.25)
    r["f"] = 1.5
    assert r["k"] == pytest.approx(0.625)


def test_drive_document_in_place(tmp_path: Path) -> None:
    """A document is changed and returned, not copied."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = libsbml.readSBMLFromFile(str(path))
    assert _interpolation("f").drive(doc) is doc
    assert doc.getModel().getAssignmentRuleByVariable("f") is not None


def test_drive_sbml_string(tmp_path: Path) -> None:
    """An SBML string is read."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path.read_text())
    assert doc.getModel().getAssignmentRuleByVariable("f") is not None


def test_drive_level_2(tmp_path: Path) -> None:
    """A Level 2 model is driven and keeps its level."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml", level=2, version=4)
    doc = _interpolation("f").drive(path)
    assert (doc.getLevel(), doc.getVersion()) == (2, 4)
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0


def test_initial_assignment_is_removed(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An initial assignment of a target is removed, with a log line."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k")]
    path = write_model(model, tmp_path / "uptake.xml")
    with caplog.at_level("INFO"):
        driven = _interpolation("f").drive(path).getModel()
    assert driven.getInitialAssignmentBySymbol("f") is None
    assert "initial assignment of 'f'" in caplog.text


def _add_assignment_rule(model: Model) -> None:
    model.rules.append(AssignmentRule("f", "2 * k"))


def _add_rate_rule(model: Model) -> None:
    model.rate_rules.append(RateRule("f", "0.1"))


def _add_algebraic_rule(model: Model) -> None:
    model.algebraic_rules.append(AlgebraicRule(None, "f - 2 * k"))


def _add_event(model: Model) -> None:
    model.events.append(Event("E1", trigger="time > 1", assignments={"f": 3.0}))


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (_add_assignment_rule, "an assignment rule"),
        (_add_rate_rule, "a rate rule"),
        (_add_algebraic_rule, "an algebraic rule"),
        (_add_event, "an event assignment"),
    ],
)
def test_determined_target_raises(
    tmp_path: Path, change: Callable[[Model], None], match: str
) -> None:
    """A target the model determines already is refused."""
    model = uptake_model()
    model.parameters[1].constant = False
    change(model)
    path = write_model(model, tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match=match):
        _interpolation("f").drive(path)


@pytest.mark.parametrize(
    ("data", "targets", "match"),
    [
        (TIMECOURSE[["time", "f"]], {"g": "f"}, "no column 'g'"),
        (TIMECOURSE[["time", "f"]], {"time": "f"}, "is x"),
        (TIMECOURSE[["time", "f"]], {"f": "missing"}, "'missing' is not an element"),
        (TIMECOURSE[["time", "f"]], {"f": "UPTAKE"}, "is a reaction"),
        (
            TIMECOURSE[["time", "f", "glc_ext"]],
            {"f": "k", "glc_ext": "k"},
            "two columns",
        ),
        (TIMECOURSE.rename(columns={"time": "t"})[["t", "f"]], None, "'t'"),
    ],
)
def test_invalid_targets_raise(
    tmp_path: Path, data: pd.DataFrame, targets: dict[str, str] | None, match: str
) -> None:
    """Unknown columns, unknown or undrivable targets, a missing x are refused."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match=match):
        Interpolation(data, method="linear").drive(path, targets)


def test_drive_twice_raises_and_leaves_document(tmp_path: Path) -> None:
    """Driving the driven target again names its rule and changes nothing."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path)
    before = libsbml.writeSBMLToString(doc)
    with pytest.raises(ValueError, match="an assignment rule"):
        _interpolation("glc_ext", "f").drive(doc)
    assert libsbml.writeSBMLToString(doc) == before
