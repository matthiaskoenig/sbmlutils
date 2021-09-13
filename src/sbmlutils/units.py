"""Module for unit information.

Definition of units via simple unit strings parsed by Pint.
Within models subclasses of `Units`.

"""
import logging
from dataclasses import dataclass
from typing import Dict, Type, Tuple, List

import libsbml
import inspect
from pint import Quantity as Q_

logger = logging.getLogger(__file__)

__all__ = [
    "Units",
    "CoreUnits"
]


class Pint2SBML:
    """Conversion of pint unit strings to libsbml UnitDefinitions."""

    pint2sbml = {
        "dimensionless": libsbml.UNIT_KIND_DIMENSIONLESS,
        "ampere": libsbml.UNIT_KIND_AMPERE,
        # None: libsbml.UNIT_KIND_BECQUEREL,
        # "becquerel": libsbml.UNIT_KIND_BECQUEREL,
        "candela": libsbml.UNIT_KIND_CANDELA,
        "degree_Celsius": libsbml.UNIT_KIND_CELSIUS,
        "coulomb": libsbml.UNIT_KIND_COULOMB,
        "farad": libsbml.UNIT_KIND_FARAD,
        "gram": libsbml.UNIT_KIND_GRAM,
        "gray": libsbml.UNIT_KIND_GRAY,
        "hertz": libsbml.UNIT_KIND_HERTZ,
        "kelvin": libsbml.UNIT_KIND_KELVIN,
        "kilogram": libsbml.UNIT_KIND_KILOGRAM,
        "liter": libsbml.UNIT_KIND_LITRE,
        "meter": libsbml.UNIT_KIND_METRE,
        "mole": libsbml.UNIT_KIND_MOLE,
        "newton": libsbml.UNIT_KIND_NEWTON,
        "ohm": libsbml.UNIT_KIND_OHM,
        "second": libsbml.UNIT_KIND_SECOND,
        "volt": libsbml.UNIT_KIND_VOLT,
    }

    @staticmethod
    def create_unit_definition(
        model: libsbml.Model,
        definition: str) -> libsbml.UnitDefinition:
        """Parses string definition and returns SBML unit definition.

        :param definition:
        :return:
        """
        logger.warning(f"Create UnitDefinition for: '{definition}'")
        udef: libsbml.UnitDefinition = model.createUnitDefinition()

        # parse the string into pint
        quantity = Q_(definition).to_compact().to_reduced_units().to_base_units()

        m, units = quantity.to_tuple()
        for k, item in enumerate(units):
            print(k, item)

            if k == 0:
                multiplier = quantity.magnitude
            else:
                multiplier = 1.0

                # FIXME: get exponent from

            base_unit = item[0]
            kind = Pint2SBML.pint2sbml[base_unit]
            exponent = item[1]
            scale = 0

            Pint2SBML._create_unit(udef, kind, exponent, scale, multiplier)

        return udef

    @staticmethod
    def _create_unit(
        udef: libsbml.UnitDefinition,
        kind: str,
        exponent: float,
        scale: int = 0,
        multiplier: float = 1.0,
    ) -> libsbml.Unit:
        """Create libsbml.Unit."""
        unit: libsbml.Unit = udef.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
        return unit


class Units:
    """Base class for unit definitions."""

    @classmethod
    def attributes(cls) -> List[Tuple[str]]:

        attributes = inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        return [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]



@dataclass
class UnitsEntry:
    uid: str
    definition: str
    unit_definition: libsbml.UnitDefinition


class UnitsDict:

    def __init__(self, units_class: Type[Units], model: libsbml.Model):
        self.units: Dict[str, UnitsEntry] = {}
        for definition, uid in units_class.attributes():

            udef = Pint2SBML.create_unit_definition(model=model, definition=definition)

            self.units[definition] = UnitsEntry(
                uid=uid,
                definition=definition,
                unit_definition=udef
            )




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
    l = "liter"
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
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    udef: libsbml.UnitDefinition = Pint2SBML.create_unit_definition(
        model=model, definition="meter/second"
    )
    print(udef)
    print(libsbml.UnitDefinition_printUnits(udef, compact=True))

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

    for definition in definitions:
        print("---", definition, "---")
        udef = Pint2SBML.create_unit_definition(
            model=model, definition=definition,
        )
        print(libsbml.UnitDefinition_printUnits(udef, compact=True))

    print(CoreUnits.uid("mg/hr"))
