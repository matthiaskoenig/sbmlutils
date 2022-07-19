"""AssignmentRule and InitialAssignment example."""
from sbmlutils.examples import templates
from sbmlutils.factory import *


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


model = Model(
    "assignment",
    name="model with assignments",
    creators=templates.creators,
    notes="""
    # Example model demonstrating `InitialAssignment` and `AssignmentRule`.

    InitalAssignments allow to set values at the initial timepoint of simulation.
    AssignmentRules are evaluated at every time point.
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

model.parameters = [
    # dosing
    Parameter(
        "D",
        NaN,
        U.mg,
        name="total dose",
        constant=False,
        notes="""The parameter does not have an initial value set.
        An InitialAssignment is used to set the parameter.
        """,
    ),
    Parameter("A", 0, U.mg, name="amount in blood"),
    Parameter("IVDOSE", 0, U.mg, name="intravenous dose"),
    Parameter("PODOSE", 100, U.mg, name="oral dose"),
    Parameter("k1", 0.1, U.l_per_hr, name="rate constant for dose"),
    # whole body data
    Parameter("BW", 70, U.kg, name="body weight"),
    Parameter("FVblood", 0.05, U.l_per_kg, name="fractional volume of the blood"),
]

model.assignments = [
    InitialAssignment(
        "D",
        "PODOSE +  IVDOSE",
        U.mg,
        name="total dose",
        notes="""Using an InitialAssignment to set the total dose at the beginning
        of the simulation as sum from iv and oral dose.
        The target parameter `D` of the initial assignment exists in the model.
        """,
    ),
    InitialAssignment(
        "Vblood",
        "BW*FVblood",
        U.liter,
        name="blood volume",
        sid="init_Vblood",
        notes="""Calculating the blood volume via an Initial assignment.
        The target of the initial assignment `Vblood` does not exist in the model
        so a corresponding parameter for the assignment is generated.

        The `sid` can be used to set the id of the assignment.
        """,
    ),
]

model.rules = [
    AssignmentRule(
        "Cve",
        "A/Vblood",
        U.mg_per_l,
        name="rule to calulate concentration",
        notes="""
        Assignment rule to calculate the concentration `Cve` in [mg/l] from the
        species `A` and the volume `Vblood`.
        """,
    ),
]

model.rate_rules = [
    RateRule("D", "-k1*Cve", U.mg_per_hr, name="rule for the change of D"),
]


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(model=model, filepath=EXAMPLES_DIR / f"{model.sid}.xml")
