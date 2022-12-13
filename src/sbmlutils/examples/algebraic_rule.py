"""AlgebraicRule example."""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.resources import EXAMPLES_DIR


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
    "algebraic_rule",
    name="model with AlgebraicRule",
    creators=templates.creators,
    notes="""
    # Example model demonstrating `AlgebraicRule`.
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
    Parameter("Atot", 20, U.mg, constant=True, name="total A"),
    Parameter("A1", 15, U.mg, constant=False, name="A1"),
    Parameter("A2", 5, U.mg, constant=False, name="A2"),
]

model.algebraic_rules = [
    AlgebraicRule("Atotal_rule", "Atot - (A1 + A2)", unit=U.mg),
]


if __name__ == "__main__":
    create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
    )
