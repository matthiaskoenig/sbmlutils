"""The units of a model.

`Unit`, `UnitDefinition` and `Units`, which a model definition declares
its units with, `ModelUnits`, the units of the model itself, and
`ValueWithUnit`, the base of the elements which carry a unit.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias

import libsbml
import numpy as np
from pint import UndefinedUnitError, UnitRegistry

from sbmlutils.factory._core import (
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    Value,
    _check_attribute,
)
from sbmlutils.notes import Notes
from sbmlutils.validation import check

if TYPE_CHECKING:
    from sbmlutils.factory.distrib import Uncertainty

logger = logging.getLogger(__name__)

ureg = UnitRegistry()
Q_ = ureg.Quantity
ureg.define("item = 1 dimensionless")


UnitType: TypeAlias = "UnitDefinition | str | None"


class ModelUnits:
    """Class for storing model units information.

    The ModelUnits define globally the units for `time`, `extent`, `substance`,
    `length`, `area` and `volume`.

    The following SBML Level 3 base units can be used.

       ampere         farad  joule     lux     radian     volt
       avogadro       gram   katal     metre   second     watt
       becquerel      gray   kelvin    mole    siemens    weber
       candela        henry  kilogram  newton  sievert
       coulomb        hertz  litre     ohm     steradian
       dimensionless  item   lumen     pascal  tesla
    """

    def __init__(
        self,
        time: UnitType = None,
        extent: UnitType = None,
        substance: UnitType = None,
        length: UnitType = None,
        area: UnitType = None,
        volume: UnitType = None,
    ):
        """Construct ModelUnits."""
        self.time = time
        self.extent = extent
        self.substance = substance
        self.length = length
        self.area = area
        self.volume = volume

    @staticmethod
    def set_model_units(model: libsbml.Model, model_units: ModelUnits) -> None:
        """Set the main units in model from dictionary.

        Setting the model units is important for understanding the model
        dynamics.
        Allowed keys are:
            time
            extent
            substance
            length
            area
            volume

        :param model: SBMLModel
        :param model_units: dict of units
        :return:
        """
        if isinstance(model_units, dict):
            logger.error(
                "Providing model units as dict is deprecated, use 'ModelUnits' instead."
            )
            model_units = ModelUnits(**model_units)

        if not model_units:
            if Sbase._authoring_hints.get():
                logger.warning(
                    "Model units should be set for a model. These can be stored "
                    "using the 'model_units' on a model definition."
                )
        else:
            for key in ("time", "extent", "substance", "length", "area", "volume"):
                if getattr(model_units, key) is None:
                    if Sbase._authoring_hints.get():
                        # strongly recommended fields warn, optional ones inform
                        logger.log(
                            logging.WARNING
                            if key in ["time", "extent", "substance", "volume"]
                            else logging.INFO,
                            "'%s' should be set in 'model_units'.",
                            key,
                        )

                    continue

                unit: str | UnitDefinition = getattr(model_units, key)
                uid = UnitDefinition.get_uid_for_unit(unit=unit)
                # set the values; the six unit attributes of a model are SBML
                # L3 only, and below L3 every one of them answers
                # `LIBSBML_UNEXPECTED_ATTRIBUTE`. The report names the
                # attribute as the document spells it, not as the field of
                # `ModelUnits` is called
                setter, attribute = {
                    "time": (model.setTimeUnits, "timeUnits"),
                    "extent": (model.setExtentUnits, "extentUnits"),
                    "substance": (model.setSubstanceUnits, "substanceUnits"),
                    "length": (model.setLengthUnits, "lengthUnits"),
                    "area": (model.setAreaUnits, "areaUnits"),
                    "volume": (model.setVolumeUnits, "volumeUnits"),
                }[key]
                _check_attribute(
                    setter(uid), model, attribute, uid, f"Model({model.getId()})"
                )


class Unit:
    """A single unit of a `UnitDefinition`.

    Corresponds to the information in a `libsbml.Unit`, i.e. one factor of a
    unit definition. An SBML unit is `(multiplier * 10^scale * kind)^exponent`.
    """

    def __init__(
        self,
        kind: str,
        exponent: float = 1.0,
        scale: int = 0,
        multiplier: float = 1.0,
    ):
        """Construct a Unit.

        Args:
            kind: the SBML unit kind, e.g. `"litre"`
            exponent: the exponent of the unit
            scale: the decimal scale of the unit
            multiplier: the multiplier of the unit
        """
        self.kind = kind
        self.exponent = exponent
        self.scale = scale
        self.multiplier = multiplier

    def __repr__(self) -> str:
        """Get string representation."""
        return (
            f"Unit({self.kind}, exponent={self.exponent}, "
            f"scale={self.scale}, multiplier={self.multiplier})"
        )

    def __eq__(self, other: object) -> bool:
        """Compare two units."""
        if not isinstance(other, Unit):
            return NotImplemented
        return (
            self.kind == other.kind
            and self.exponent == other.exponent
            and self.scale == other.scale
            and self.multiplier == other.multiplier
        )

    def __hash__(self) -> int:
        """Get hash of the unit."""
        return hash((self.kind, self.exponent, self.scale, self.multiplier))

    def create_sbml(self, udef: libsbml.UnitDefinition) -> libsbml.Unit:
        """Create the libsbml.Unit in the given libsbml.UnitDefinition.

        Args:
            udef: the libsbml.UnitDefinition the unit is created in

        Returns:
            the created libsbml.Unit
        """
        unit: libsbml.Unit = udef.createUnit()
        kind: int = libsbml.UnitKind_forName(self.kind)
        if kind == libsbml.UNIT_KIND_INVALID:
            logger.error("'%s' is not a valid SBML unit kind.", self.kind)
        check(unit.setKind(kind), f"Set kind '{self.kind}' on unit")
        check(unit.setExponent(float(self.exponent)), "Set exponent on unit")
        check(unit.setScale(int(self.scale)), "Set scale on unit")
        check(unit.setMultiplier(float(self.multiplier)), "Set multiplier on unit")
        return unit


class UnitDefinition(Sbase):
    """Unit.

    Corresponds to the information in the libsbml.UnitDefinition.
    """

    _hint_sbo_term: ClassVar[bool] = False

    #: the unit definitions of a model live in a namespace of their own, which
    #: comp names by `comp:unitRef`, see `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "unitRef"

    _pint2sbml: ClassVar[dict[str, int]] = {
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
        "henry": libsbml.UNIT_KIND_HENRY,
        "hertz": libsbml.UNIT_KIND_HERTZ,
        "item": libsbml.UNIT_KIND_ITEM,
        "joule": libsbml.UNIT_KIND_JOULE,
        "kelvin": libsbml.UNIT_KIND_KELVIN,
        "kilogram": libsbml.UNIT_KIND_KILOGRAM,
        "liter": libsbml.UNIT_KIND_LITRE,
        "meter": libsbml.UNIT_KIND_METRE,
        "mole": libsbml.UNIT_KIND_MOLE,
        "newton": libsbml.UNIT_KIND_NEWTON,
        "ohm": libsbml.UNIT_KIND_OHM,
        "pascal": libsbml.UNIT_KIND_PASCAL,
        "second": libsbml.UNIT_KIND_SECOND,
        "siemens": libsbml.UNIT_KIND_SIEMENS,
        "sievert": libsbml.UNIT_KIND_SIEVERT,
        "volt": libsbml.UNIT_KIND_VOLT,
        "watt": libsbml.UNIT_KIND_WATT,
    }
    # see https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    _prefixes: ClassVar[dict[str, float]] = {
        "yocto": 1e-24,
        "zepto": 1e-21,
        "atto": 1e-18,
        "femto": 1e-15,
        "pico": 1e-12,
        "nano": 1e-9,
        "micro": 1e-6,
        "milli": 1e-3,
        "centi": 1e-2,
        "deci": 1e-1,
        "deca": 1e1,
        "hecto": 1e2,
        "kilo": 1e3,
        "mega": 1e6,
        "giga": 1e9,
        "tera": 1e12,
        "peta": 1e15,
        "exa": 1e18,
        "zetta": 1e21,
        "yotta": 1e24,
    }

    def __init__(
        self,
        sid: str,
        definition: str | int | None = None,
        units: list[Unit] | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        replacedBy: Any | None = None,
    ):
        """Construct UnitDefinition.

        A unit definition is either written as a pint expression in
        `definition`, which is the authoring style, or as the explicit list of
        `units` it consists of, which is what the parser reads from a file.

        Args:
            sid: the id of the unit definition
            definition: the pint expression, e.g. `"mmole/liter"`, or a
                libsbml unit kind (`libsbml.UNIT_KIND_*`) for a base unit,
                which writes no unit definition; defaults to `sid`
            units: the explicit units of the definition; they take precedence
                over `definition`
            name: the name of the unit definition
            sboTerm: the SBO term of the unit definition
            metaId: the meta id of the unit definition
            annotations: the annotations of the unit definition
            notes: the notes of the unit definition
            keyValuePairs: the key value pairs of the unit definition
            port: the port of the unit definition
            replacedBy: the comp ReplacedBy of the unit definition
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            replacedBy=replacedBy,
        )

        self.units = units
        self.definition: str | int = definition if definition is not None else sid
        if not self.name and units is None and isinstance(self.definition, str):
            # the pint expression is the readable label of the definition; with
            # explicit units the definition is only the id and would make a
            # meaningless name, and a unit kind is a number
            self.name = self.definition

    def create_sbml(self, model: libsbml.Model) -> libsbml.UnitDefinition | None:
        """Create libsbml.UnitDefinition.

        Args:
            model: the libsbml.Model the unit definition is created in

        Returns:
            the created libsbml.UnitDefinition, `None` for a base unit kind
        """
        if self.units is None and isinstance(self.definition, int):
            # libsbml unit kind, the unit definition is a base unit
            return None

        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        units = self.units if self.units is not None else self._units_from_definition()
        for unit in units:
            unit.create_sbml(obj)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _units_from_definition(self) -> list[Unit]:
        """Compile the pint definition string into explicit units.

        Returns:
            the units the pint expression of `definition` resolves to

        Raises:
            UndefinedUnitError: if the expression is not valid pint syntax
            ValueError: if a unit of the expression has no SBML unit kind, or
                the magnitude has no finite, non-zero root under the exponent
                of the first unit
        """
        # parse the string into pint
        try:
            quantity = Q_(self.definition)
        except UndefinedUnitError as err:
            logger.error(
                "Unit definition '%s' is not valid pint syntax, %s.",
                self.definition,
                err,
            )
            raise

        magnitude, units_tuple = quantity.to_tuple()
        # pint types the units as a fixed length tuple, it is empty for a number
        units: list[Sequence[Any]] = list(units_tuple)

        sbml_units: list[Unit] = []
        if units:
            for k, item in enumerate(units):
                prefix, unit_name, _suffix = ureg.parse_unit_name(item[0])[0]
                exponent = float(item[1])
                # An SBML unit is (multiplier * 10^scale * kind)^exponent, so
                # the factors of the unit itself (prefix, conversion to the
                # kind) go into the multiplier as they are, and the magnitude
                # of the expression, which the first unit carries, is rooted
                # by the signed exponent to come out of the power unchanged.
                multiplier = 1.0
                if k == 0:
                    # a magnitude without a real root is checked right below
                    with np.errstate(invalid="ignore", divide="ignore"):
                        multiplier = float(np.power(magnitude, 1.0 / exponent))
                    if not np.isfinite(multiplier) or multiplier == 0.0:
                        msg = (
                            f"The magnitude '{magnitude}' of unit definition "
                            f"'{self.definition}' cannot be carried by the "
                            f"unit '{item[0]}' with exponent '{exponent}'."
                        )
                        logger.error(msg)
                        raise ValueError(msg)

                if prefix:
                    multiplier = multiplier * self.__class__._prefixes[prefix]

                # the pint path cannot resolve a scale, it is part of the
                # multiplier; only a parsed unit definition carries a scale
                scale = 0
                # resolve the kind (this is already a unit known by libsbml)
                kind = self.__class__._pint2sbml.get(unit_name, None)
                if kind is None:
                    # we have to bring the unit to base units, the conversion
                    # factor belongs to one unit and is not rooted either
                    uq = Q_(unit_name).to_base_units()
                    multiplier = multiplier * uq.magnitude
                    kind = self.__class__._pint2sbml.get(str(uq.units), None)
                    if kind is None:
                        msg = (
                            f"Unit '{uq.units}' in definition "
                            f"'{self.definition}' could not be converted to SBML."
                        )
                        logger.error(msg)
                        raise ValueError(msg)

                sbml_units.append(
                    Unit(
                        kind=libsbml.UnitKind_toString(kind),
                        exponent=exponent,
                        scale=scale,
                        multiplier=float(multiplier),
                    )
                )
        else:
            # only magnitude (units canceled)
            kind = self.__class__._pint2sbml["dimensionless"]
            sbml_units.append(
                Unit(
                    kind=libsbml.UnitKind_toString(kind),
                    exponent=1.0,
                    scale=0,
                    multiplier=float(magnitude),
                )
            )

        return sbml_units

    @staticmethod
    def get_uid_for_unit(unit: UnitDefinition | str | None) -> str | None:
        """Get unit id for the given unit.

        Args:
            unit: a UnitDefinition or the id of one

        Returns:
            the unit id, `None` if no unit was given

        Raises:
            ValueError: if the unit is neither a `UnitDefinition` nor a unit
                id; the value would otherwise reach a libsbml setter and
                surface as a SWIG `TypeError` which names neither the value
                nor the element it was set on
        """
        if unit is None:
            return None
        if isinstance(unit, UnitDefinition):
            return unit.sid
        if not isinstance(unit, str):
            raise ValueError(
                f"A unit must be a UnitDefinition or the id of one, but "
                f"'{unit}' is '{type(unit)}'."
            )
        return unit


class Units:
    """Base class for unit definitions."""

    # libsbml units
    dimensionless = UnitDefinition(
        "dimensionless", libsbml.UNIT_KIND_DIMENSIONLESS, name="dimensionless"
    )
    ampere = UnitDefinition("ampere", libsbml.UNIT_KIND_AMPERE, name="ampere")
    becquerel = UnitDefinition(
        "becquerel", libsbml.UNIT_KIND_BECQUEREL, name="becquerel"
    )
    candela = UnitDefinition("candela", libsbml.UNIT_KIND_CANDELA, name="candela")
    degree_Celsius = UnitDefinition(
        "degree_Celsius", libsbml.UNIT_KIND_CELSIUS, name="degree_Celsius"
    )
    coulomb = UnitDefinition("coulomb", libsbml.UNIT_KIND_COULOMB, name="coulomb")
    farad = UnitDefinition("farad", libsbml.UNIT_KIND_FARAD, name="farad")
    gram = UnitDefinition("gram", libsbml.UNIT_KIND_GRAM, name="gram")
    gray = UnitDefinition("gray", libsbml.UNIT_KIND_GRAY, name="gray")
    hertz = UnitDefinition("hertz", libsbml.UNIT_KIND_HERTZ, name="hertz")
    item = UnitDefinition("item", libsbml.UNIT_KIND_ITEM, name="item")
    kelvin = UnitDefinition("kelvin", libsbml.UNIT_KIND_KELVIN, name="kelvin")
    kilogram = UnitDefinition("kilogram", libsbml.UNIT_KIND_KILOGRAM, name="kilogram")
    liter = UnitDefinition("litre", libsbml.UNIT_KIND_LITRE, name="liter")
    litre = UnitDefinition("litre", libsbml.UNIT_KIND_LITRE, name="liter")
    meter = UnitDefinition("metre", libsbml.UNIT_KIND_METRE, name="meter")
    metre = UnitDefinition("metre", libsbml.UNIT_KIND_METRE, name="metre")
    mole = UnitDefinition("mole", libsbml.UNIT_KIND_MOLE, name="mole")
    newton = UnitDefinition("newton", libsbml.UNIT_KIND_NEWTON, name="newton")
    ohm = UnitDefinition("ohm", libsbml.UNIT_KIND_OHM, name="ohm")
    second = UnitDefinition("second", libsbml.UNIT_KIND_SECOND, name="second")
    volt = UnitDefinition("volt", libsbml.UNIT_KIND_VOLT, name="volt")

    @classmethod
    def attributes(cls) -> list[tuple[str, str | UnitDefinition]]:
        """Get the attributes list."""
        attributes = inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        return [
            a for a in attributes if not (a[0].startswith("__") and a[0].endswith("__"))
        ]


def _check_unit_type(unit: Any, attribute: str, owner: object) -> None:
    """Warn if a unit attribute is neither a `UnitDefinition` nor a unit id.

    The value is passed on either way, `UnitDefinition.get_uid_for_unit`
    refuses it when the element is written. The warning is the early hint
    which names the attribute and the element it was given on.

    Args:
        unit: the value given for the unit attribute
        attribute: the name of the attribute, e.g. `substanceUnit`
        owner: the element the attribute belongs to, which the warning names
    """
    if unit is not None and not isinstance(unit, (UnitDefinition, str)):
        logger.warning(
            "'%s' must be a UnitDefinition or a unit id, but '%s' in '%s' is '%s'.",
            attribute,
            unit,
            owner,
            type(unit),
        )


class ValueWithUnit(Value):
    """Helper class.

    The value field is a helper storage field which is used differently by different
    subclasses.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.sid} = {self.value} [{self.unit}]"

    def __init__(
        self,
        sid: str | None,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct the value with its unit.

        Args:
            sid: the id of the element
            value: the value, a number or a formula
            unit: the unit of the value, a `UnitDefinition` or a unit id
            name: the name of the element
            sboTerm: the SBO term of the element
            metaId: the metaid of the element
            annotations: the annotations of the element
            notes: the notes of the element
            keyValuePairs: the fbc key-value pairs of the element
            port: the comp port of the element, see `Sbase.create_port`
            uncertainties: the distrib uncertainties of the element
            replacedBy: the comp replacement of the element
        """
        super().__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            port=port,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.unit = unit
        _check_unit_type(self.unit, "unit", self)

    def _set_fields(self, sbase: Any, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)
        if self.unit is not None:
            if sbase.getTypeCode() in [
                libsbml.SBML_ASSIGNMENT_RULE,
                libsbml.SBML_RATE_RULE,
                libsbml.SBML_ALGEBRAIC_RULE,
            ]:
                # AssignmentRules, RateRules and AlgebraicRules have no units
                pass
            else:
                uid = UnitDefinition.get_uid_for_unit(unit=self.unit)
                check(sbase.setUnits(uid), f"Set unit '{uid}' on {sbase}")
