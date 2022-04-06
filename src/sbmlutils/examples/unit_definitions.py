"""Example model with UnitDefinitions."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitDefinitions."""

    mmole = UnitDefinition("mmole")
    min = UnitDefinition("min")
    kg = UnitDefinition("kg")
    per_kg = UnitDefinition("per_kg", "1/kg")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    mmole_per_min_l = UnitDefinition("mmole_per_min_l", "mmole/min/l")
    l_per_min = UnitDefinition("l_per_min", "l/min")
    per_min = UnitDefinition("per_min", "1/min")
    s = UnitDefinition("s", "second")
    mg = UnitDefinition("mg", "mg")
    ml = UnitDefinition("ml", "ml")
    hr = UnitDefinition("hr", "hr")
    per_hr = UnitDefinition("per_hr", "1/hr")
    cm = UnitDefinition("cm", "cm")
    mg_per_l = UnitDefinition("mg_per_l", "mg/l")
    mg_per_g = UnitDefinition("mg_per_g", "mg/g")
    mg_per_hr = UnitDefinition("mg_per_hr", "mg/hr")
    l_per_hr = UnitDefinition("l_per_hr", "l/hr")
    l_per_kg = UnitDefinition("l_per_kg", "l/kg")
    l_per_ml = UnitDefinition("l_per_ml", "l/ml")
    g_per_mole = UnitDefinition("g_per_mole", "g/mole")
    m2_per_kg = UnitDefinition("m2_per_kg", "meter^2/kg")
    mg_per_min = UnitDefinition("mg_per_min", "mg/min")
    mmole_per_hr = UnitDefinition("mmole_per_hr", "mmole/hr")
    mmole_per_min_kg = UnitDefinition("mmole_per_min_kg", "mmole/min/kg")
    mmole_per_hr_ml = UnitDefinition("mmole_per_hr_ml", "mmole/hr/ml")
    ml_per_s = UnitDefinition("ml_per_s", "ml/s")
    ml_per_s_kg = UnitDefinition("ml_per_s_kg", "ml/s/kg")
    ml_per_l = UnitDefinition("ml_per_l", "ml/l")
    mul_per_g = UnitDefinition("mul_per_g", "microliter/g")
    mul_per_min_mg = UnitDefinition("mul_per_min_mg", "microliter/min/mg")
    min_per_day = UnitDefinition("min_per_day", "min/day")
    min_per_hr = UnitDefinition("min_per_hr", "min/hr")
    s_per_min = UnitDefinition("s_per_min", "s/min")
    s_per_hr = UnitDefinition("s_per_hr", "s/hr")
    mg_per_day = UnitDefinition("mg_per_day", "mg/day")


_m = Model(
    "unit_definitions",
    name="model with UnitDefinitions",
    notes="""
    # Model with UnitDefinitions
    This example demonstrates how to create UnitDefinitions.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.second,
        volume=U.liter,
        substance=U.mole,
        extent=U.mole,
        length=U.meter,
        area=U.m2,
    ),
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(models=_m, output_dir=EXAMPLES_DIR, tmp=tmp, units_consistency=False)


if __name__ == "__main__":
    create()
