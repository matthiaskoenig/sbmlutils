"""AssignmentRule and InitialAssignment example."""
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *


class U(Units):
    """UnitsDefinition."""

    hr = UnitDefinition("hr")
    mg = UnitDefinition("mg")
    m2 = UnitDefinition("m2", "meter^2")
    kg = UnitDefinition("kg")
    l_per_hr = UnitDefinition("l_per_hr", "liter/hr")
    l_per_kg = UnitDefinition("l_per_hr", "liter/kg")


_m = Model("assignment_example")
_m.creators = templates.creators
_m.notes = """
Example model for testing InitialAssignments in roadrunner.
""" + templates.terms_of_use
_m.units = U
_m.model_units = ModelUnits(
    time=U.hr,
    extent=U.mg,
    substance=U.mg,
    length=U.meter,
    area=U.m2,
    volume=U.liter,
)

_m.parameters = [
    # dosing
    Parameter("Ave", 0, U.mg, constant=False),
    Parameter("D", 0, U.mg, constant=False),
    Parameter("IVDOSE", 0, U.mg, constant=True),
    Parameter("PODOSE", 100, U.mg, constant=True),
    Parameter("k1", 0.1, "litre_per_hr", constant=True),
    # whole body data
    Parameter("BW", 70, "kg", True),
    Parameter("FVve", 0.0514, "litre_per_kg", True),
]

_m.assignments = [
    InitialAssignment("Ave", "IVDOSE", U.mg),
    InitialAssignment("D", "PODOSE", U.mg),
]

_m.rules = [
    # concentrations
    AssignmentRule("Cve", "Ave/Vve", "mg_per_litre"),
    # volumes
    AssignmentRule("Vve", "BW*FVve", U.liter),
]

_m.rate_rules = [
    RateRule("Ave", "- k1*Cve", "mg_per_h"),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
