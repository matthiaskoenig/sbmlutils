"""Parameter example."""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitsDefinition."""

    hr = UnitDefinition("hr")
    mg = UnitDefinition("mg")
    m2 = UnitDefinition("m2", "meter^2")
    kg = UnitDefinition("kg")
    l_per_hr = UnitDefinition("l_per_hr", "liter/hr")
    l_per_kg = UnitDefinition("l_per_kg", "liter/kg")
    mg_per_l = UnitDefinition("mg_per_l", "mg/liter")
    mg_per_hr = UnitDefinition("mg_per_hr", "mg/hr")


_m = Model(
    "parameter",
    name="model with parameters",
    creators=templates.creators,
    notes="""
    # Example model demonstrating `Parameter`.
    """
    + templates.terms_of_use,
    units=U,
    model_units=ModelUnits(
        time=U.hr,
        extent=U.mg,
        substance=U.mg,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
)

_m.parameters = [
    Parameter(
        "p1",
        1.0,
        U.mg,
        notes="""
        Constant parameter with value.
        """,
    ),
    Parameter(
        "p2",
        2e-5,
        U.mg,
        notes="""
        Constant parameter with value in E notation.
        """,
    ),
    Parameter(
        "p3",
        NaN,
        U.mg,
        notes="""
        Constant parameter with value set via InitialAssignment.
        """,
    ),
    Parameter(
        "p4",
        NaN,
        U.mg,
        constant=False,
        notes="""
        Parameter set via time-dependent AssignmentRule.
        """,
    ),
    Parameter(
        "dose",
        10.0,
        U.mg,
        metaId="meta_dose",
        constant=True,
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C25488"),  # dose
            (BQB.IS, "efo/0000428"),  # dose
        ],
        notes="""
        Parameter with SBOTerm and annotations.
        """,
    ),
]

_m.assignments = [
    InitialAssignment(
        "p3",
        "p1 + p2",
        notes="""
        Sets the initial value of p3 as the sum of p1 and p2.
        """,
    )
]
_m.rules = [
    AssignmentRule(
        "p4",
        "10 mg + 2.0 mg * sin(time/1 hr)",
        notes="""
        Sets p4 as a time dependent parameter via an assignment rule.
        """,
    ),
    AssignmentRule(
        "p5",
        "10 mg + 2.0 mg * sin(time/1 hr)",
        unit=U.mg,
        notes="""
        Creates parameter p5 and sets it via a time dependent assignment rule.
        """,
    ),
]

model = _m


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
    )
