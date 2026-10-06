"""Interpolations in a model definition of the factory."""

from pathlib import Path

import pandas as pd
import pytest
from interpolation_models import uptake_model, write_model

from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import AssignmentRule

DATA = pd.DataFrame({"time": [0.0, 2.0, 4.0], "f_data": [1.0, 1.0 / 3.0, 2.0]})


def test_assignment_rules_of_mapping() -> None:
    """One rule per driven element, the formula of its column."""
    interpolation = Interpolation(DATA, method="linear")
    rules = interpolation.assignment_rules({"f_data": "f"})
    assert [type(rule) for rule in rules] == [AssignmentRule]
    assert rules[0].variable == "f"
    assert rules[0].value == interpolation.interpolators[0].formula()
    assert repr(1.0 / 3.0) in str(rules[0].value)


def test_assignment_rules_in_model(tmp_path: Path) -> None:
    """A model definition takes the rules and simulates the data."""
    roadrunner = pytest.importorskip("roadrunner")
    model = uptake_model()
    model.parameters[1].constant = False
    model.rules = Interpolation(DATA, method="linear").assignment_rules({"f_data": "f"})
    path = write_model(model, tmp_path / "uptake.xml")
    r = roadrunner.RoadRunner(str(path))
    s = r.simulate(0, 4, 3, selections=["time", "f"])
    assert list(s["f"]) == pytest.approx([1.0, 1.0 / 3.0, 2.0])


def test_assignment_rules_column_not_sid_raises() -> None:
    """Without targets a column name has to be an SBML id."""
    data = DATA.rename(columns={"f_data": "f [1/min]"})
    with pytest.raises(ValueError, match="not an SBML id"):
        Interpolation(data).assignment_rules()
