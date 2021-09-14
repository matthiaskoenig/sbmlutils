"""Module for unit information.

Definition of units via simple unit strings parsed by Pint.
Within models subclasses of `Units`.
"""
from sbmlutils.factory import Units


class CoreUnits(Units):
    """Reusable core units."""

    ampere = "ampere"
    avogadro = "avogadro"
    # bequerel = "bequerel"
    candela = "candela"
    celsius = "celsius"
    coulomb = "coulomb"
    dimensionless = "dimensionless"
    farad = "farad"
    gram = "gram"
    g = "gram"
    gray = "gray"
    hertz = "hertz"
    item = ""
    kelvin = "kelvin"
    kilogram = "kg"
    kg = "kg"
    litre = "liter"
    liter = "liter"
    meter = "meter"
    metre = "metre"
    m = "meter"
    mole = "mole"
    min = "min"
    hr = "hr"
    newton = "newton"
    ohm = "ohm"
    second = "second"
    s = "second"
    volt = "volt"

    m2 = "meter^2"
    m3 = "meter^3"
    mmole = "mmole"
    mM = "mmole/liter"
    g_per_mole = "g/mole"

    # amount/time
    mole_per_min = "mole/min"
    mmole_per_min = "mmole/min"
    mole_per_s = "mole/second"
    mmole_per_s = "mmole/second"

    mmole_per_min_l = "mmole/min/litre"
    mmole_per_min_kg = "mmole/min/kg"

    per_s = "1/second"
    per_min = "1/min"
    per_hr = "1/hr"
    per_kg = "1/kg"
    per_l = "1/liter"
    per_mmole = "1/mmole"

    mg_per_hr = "mg/hr"
    mg_per_day = "mg/day"

    ml = "ml"
    l_per_min = "liter/min"
    l_per_mmole = "liter/mmole"


if __name__ == "__main__":

    definitions = [
        "ampere",
        # "avogadro",
        # "becquerel",
        "candela",
        "celsius",
        "coulomb",
        "farad",
        "gram",
        "gray",
        "hertz",
        "dimensionless",
        "kelvin",
        "kg",
        "kg",
        "liter",
        "litre",
        "l",
        "meter",
        "metre",
        "m",
        "mole",
        "min",
        "hr",
        "newton",
        "ohm",
        "second",
        "second",
        "volt",
        "meter^2",
        "meter^3",
        "mmole",
        "mmole/liter",
        "g/mole",
        "mole/min",
        "mmole/min",
        "mole/second",
        "mmole/second",
        "mmole/min/l",
        "mmole/min/kg",
        "1/second",
        "1/min",
        "1/hr",
        "1/kg",
        "1/liter",
        "1/mmole",
        "mg/hr",
        "mg/day",
        "ml",
        "liter/min",
        "liter/mmole",
    ]

    # for definition in definitions:
    #     print("---", definition, "---")
    #     udef = Pint2SBML.create_unit_definition(
    #         model=model, definition=definition,
    #     )
    #     print(libsbml.UnitDefinition_printUnits(udef, compact=True))
    #
    # print(CoreUnits.uid("mg/hr"))

    # quantity = Q_(self.definition).to_compact().to_reduced_units().to_base_units()
    from pint import Quantity as Q_

    quantity = Q_(1.0, "mliter")
    # quantity = Q_(1.0, "mliter").to_base_units()
    # print(quantity)
    # quantity = Q_(1.0, "mliter").to_root_units()
    # print(quantity)
    # quantity = Q_(1.0, "mliter").to_compact()
    # print(quantity)
    # quantity = Q_(1.0, "mliter").to_reduced_units()
    # print(quantity)
