"""Testing the factory methods."""
from pathlib import Path
from typing import Any, Dict

import libsbml
import numpy as np
import pytest

from sbmlutils import factory
from sbmlutils.creator import create_model
from sbmlutils.factory import *
from sbmlutils.io import read_sbml


compartment_value_data = [
    (
        1.0,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        1,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        np.NaN,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1.0",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "NaN",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "exp(10)",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 1, "rules": 0},
    ),
    (
        1.0,
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        1,
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1.0",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "exp(10)",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 1},
    ),
]


@pytest.mark.parametrize("value,constant,expected", compartment_value_data)
def test_compartment_value(
    value: Any, constant: bool, expected: Dict, tmp_path: Path
) -> None:
    m1 = {
        "mid": "compartment_value",
        "compartments": [Compartment(sid="C", value=value, constant=constant)],
    }

    result = create_model(
        modules=m1,
        output_dir=tmp_path,
        units_consistency=False,
    )

    doc: libsbml.SBMLDocument = read_sbml(source=result.sbml_path)
    model: libsbml.Model = doc.getModel()
    assert model.getNumCompartments() == expected["compartments"]
    assert model.getNumInitialAssignments() == expected["initial_assignments"]
    assert model.getNumRules() == expected["rules"]


parameter_value_data = [
    (1.0, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (1, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (np.NaN, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1.0", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("NaN", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("exp(10)", True, {"parameters": 1, "initial_assignments": 1, "rules": 0}),
    (1.0, False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (1, False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1.0", False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1", False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("exp(10)", False, {"parameters": 1, "initial_assignments": 0, "rules": 1}),
]


@pytest.mark.parametrize("value,constant,expected", parameter_value_data)
def test_parameter_value(
    value: Any, constant: bool, expected: Dict, tmp_path: Path
) -> None:
    m1 = {
        "mid": "parameter_value",
        "parameters": [Parameter(sid="p", value=value, constant=constant)],
    }

    result = create_model(
        modules=m1,
        output_dir=tmp_path,
        units_consistency=False,
    )

    doc: libsbml.SBMLDocument = read_sbml(source=result.sbml_path)
    model: libsbml.Model = doc.getModel()
    assert model.getNumParameters() == expected["parameters"]
    assert model.getNumInitialAssignments() == expected["initial_assignments"]
    assert model.getNumRules() == expected["rules"]


def test_reaction_creation() -> None:
    """Test Equation.
    bA: A_ext => A; (scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A);
    """
    rt = Reaction(
        sid="bA",
        name="bA (A import)",
        equation="A_ext => A []",
        compartment="membrane",
        pars=[],
        rules=[],
        formula=(
            "scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A",
            "mole_per_s",
        ),
    )
    assert rt


def test_event() -> None:
    objects = [
        Parameter(sid="p1", value=0.0, constant=False),
        Event(sid="e1", trigger="time >= 10", assignments={"p1": 10.0}),
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 1


def test_event2() -> None:
    objects = [
        Compartment("c", value=1.0),
        Species("S1", initialAmount=1.0, compartment="c"),
        Parameter(sid="p1", value=0.0, constant=False),
        Event(
            sid="e1", trigger="time >= 100", assignments={"p1": 10.0, "S1": "p1 + 10"}
        ),
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 2
