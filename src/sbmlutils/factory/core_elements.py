"""The elements of SBML core.

Function definitions, parameters, compartments, species, initial
assignments, rules, reactions with their kinetic laws, events and
constraints.
"""

from __future__ import annotations

import logging
import numbers
import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar, Generic, Literal, NamedTuple, TypeVar

import libsbml

from sbmlutils.factory._core import (
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    Value,
    _check_attribute,
    _fbc_plugin,
    _no_plugin_reason,
    _set_math,
    create_objects,
)
from sbmlutils.factory.distrib import Uncertainty
from sbmlutils.factory.units import (
    UnitDefinition,
    Units,
    UnitType,
    ValueWithUnit,
    _check_unit_type,
)
from sbmlutils.notes import Notes
from sbmlutils.reaction_equation import EquationPart, ReactionEquation
from sbmlutils.validation import check

logger = logging.getLogger(__name__)


class Function(Sbase):
    """SBML FunctionDefinitions.

    FunctionDefinitions consist of a lambda expression in the value field, e.g.,
        lambda(x,y, piecewise(x,gt(x,y),y) )  #  definition of minimum function
        lambda(x, sin(x) )

    A value of `None` is a function definition without math, which SBML
    allows from L3V2 on.
    """

    def __init__(
        self,
        sid: str,
        value: str | None,
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
        """Construct Function."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.formula = value

    def create_sbml(self, model: libsbml.Model) -> libsbml.FunctionDefinition:
        """Create FunctionDefinition SBML in model."""
        fd: libsbml.FunctionDefinition = model.createFunctionDefinition()
        self._set_fields(fd, model)

        self.create_port(model)
        return fd

    def _set_fields(
        self, sbase: libsbml.FunctionDefinition, model: libsbml.Model
    ) -> None:
        super()._set_fields(sbase, model)
        _set_math(sbase, self.formula, model)


class Parameter(ValueWithUnit):
    """Parameter."""

    #: the identifier is required, unlike on `Sbase`
    sid: str

    def __init__(
        self,
        sid: str,
        value: str | float | None = None,
        unit: UnitType = None,
        constant: bool = True,
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
        """Construct Parameter."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.constant = constant

    def create_sbml(self, model: libsbml.Model) -> libsbml.Parameter:
        """Create Parameter SBML in model."""
        obj: libsbml.Parameter = model.createParameter()
        self._set_fields(obj, model)
        if self.value is None:
            # an unset value stays unset, it is not invented as NaN
            pass
        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    "When setting a numeric value use float not str: '%s'.", self
                )
                obj.setValue(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)
        else:
            # numerical value
            obj.setValue(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, sbase: libsbml.Parameter, model: libsbml.Model) -> None:
        """Set fields."""
        super()._set_fields(sbase, model)
        _check_attribute(
            sbase.setConstant(self.constant), sbase, "constant", self.constant, self
        )


class LocalParameter(ValueWithUnit):
    """LocalParameter of a KineticLaw.

    A local parameter is scoped to the kinetic law it is defined in, unlike a
    `Parameter`, which is global to the model. Its id is scoped with it:
    `libsbml.Model.getElementBySId`, which comp resolves a `comp:idRef` with,
    does not answer with a local parameter, so a `<comp:port>` names one by
    its metaid, see `Sbase._port_reference`.

    A `<comp:replacedBy>` is not offered. libsbml writes one on a
    `<localParameter>` and reads it back, but no such replacement is valid,
    whichever way it names the element it is replaced by (measured with
    libsbml 5.21.2): naming the local parameter of the submodel, by
    `comp:metaIdRef` or through a `<comp:port>` of the submodel, makes the
    flattened model invalid (libsbml 10216, "Cannot use a KineticLaw local
    parameter outside of its local scope"), `comp:idRef` cannot name a local
    parameter at all (1020702), and naming anything else is a class mismatch
    (1021201, 1021203).
    """

    #: the identifier is required, unlike on `Sbase`
    sid: str

    #: the id of a local parameter is scoped to its kinetic law, see the
    #: class docstring
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __init__(
        self,
        sid: str,
        value: str | float | None = None,
        unit: UnitType = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Construct LocalParameter.

        Args:
            sid: the SId of the local parameter, which is required
            value: the value of the local parameter
            unit: the unit of the value
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid, which a `<comp:port>` of the local
                parameter references it by
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port, which names the local parameter by its
                metaid
            uncertainties: optional distrib uncertainties
        """
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
        )

    def create_sbml(
        self, klaw: libsbml.KineticLaw, model: libsbml.Model
    ) -> libsbml.LocalParameter:
        """Create the libsbml.LocalParameter in the given kinetic law.

        Args:
            klaw: the libsbml.KineticLaw the local parameter is created in
            model: the libsbml.Model the kinetic law is created in, which
                the port and the uncertainties of the local parameter are
                created in; handed down, never looked up, see
                `Model._fill_sbml`

        Returns:
            the created libsbml.LocalParameter
        """
        lp: libsbml.LocalParameter = klaw.createLocalParameter()
        self._set_fields(lp, model)
        self.create_port(model)
        if self.value is not None:
            check(lp.setValue(float(self.value)), f"Set value on '{self.sid}'")
        return lp


class Compartment(ValueWithUnit):
    """Compartment."""

    #: the identifier is required, unlike on `Sbase`
    sid: str

    def __init__(
        self,
        sid: str,
        value: str | float | None,
        unit: UnitType = None,
        constant: bool = True,
        spatialDimensions: float | None = None,
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
        """Construct Compartment."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.constant = constant
        self.spatialDimensions = spatialDimensions

    def create_sbml(self, model: libsbml.Model) -> libsbml.Compartment:
        """Create Compartment SBML in model."""
        obj: libsbml.Compartment = model.createCompartment()
        self._set_fields(obj, model)

        if self.value is None:
            # an unset size stays unset, it is not invented as NaN
            pass
        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    "When setting a numeric value use float not str: '%s'.", self
                )
                obj.setSize(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)
        else:
            obj.setSize(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, sbase: libsbml.Compartment, model: libsbml.Model) -> None:
        """Set fields on Compartment."""
        super()._set_fields(sbase, model)
        _check_attribute(
            sbase.setConstant(self.constant), sbase, "constant", self.constant, self
        )
        if self.spatialDimensions is not None:
            check(
                sbase.setSpatialDimensions(self.spatialDimensions),
                f"Set spatialDimensions on '{self.sid}'",
            )


class Species(Sbase):
    """Species."""

    def __init__(
        self,
        sid: str,
        compartment: str,
        initialAmount: float | None = None,
        initialConcentration: float | None = None,
        substanceUnit: UnitType = None,
        hasOnlySubstanceUnits: bool = False,  # default: concentrations
        constant: bool = False,
        boundaryCondition: bool = False,
        charge: float | None = None,
        chemicalFormula: str | None = None,
        conversionFactor: str | None = None,
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
        """Construct Species."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        if initialAmount and initialConcentration:
            raise ValueError(
                f"Either initialAmount or initialConcentration can be set on "
                f"species, but not both: `{sid}`."
            )
        self.substanceUnits = substanceUnit
        _check_unit_type(self.substanceUnits, "substanceUnit", self)
        self.initialAmount = initialAmount
        self.initialConcentration = initialConcentration
        self.compartment = compartment
        self.constant = constant
        self.boundaryCondition = boundaryCondition
        self.hasOnlySubstanceUnits = hasOnlySubstanceUnits
        self.charge = charge
        self.chemicalFormula = chemicalFormula
        self.conversionFactor = conversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.Species:
        """Create Species SBML in model."""
        s: libsbml.Species = model.createSpecies()
        self._set_fields(s, model)
        self.create_port(model)
        return s

    def _set_fields(self, sbase: libsbml.Species, model: libsbml.Model) -> None:
        """Set fields on libsbml.Species."""
        super()._set_fields(sbase, model)
        _check_attribute(
            sbase.setConstant(self.constant), sbase, "constant", self.constant, self
        )
        if self.compartment is None:
            raise ValueError(f"Compartment cannot be None on Species: '{self}'")
        _check_attribute(
            sbase.setCompartment(self.compartment),
            sbase,
            "compartment",
            self.compartment,
            self,
        )
        # `boundaryCondition` is a plain boolean which every SBML level and
        # version has, measured to answer success for every input
        sbase.setBoundaryCondition(self.boundaryCondition)
        _check_attribute(
            sbase.setHasOnlySubstanceUnits(self.hasOnlySubstanceUnits),
            sbase,
            "hasOnlySubstanceUnits",
            self.hasOnlySubstanceUnits,
            self,
        )

        # the substance unit of the species, which falls back to the one of
        # the model; the model's is set only here, not first and then again,
        # which would report the same loss twice
        substance_units: str | None = (
            UnitDefinition.get_uid_for_unit(unit=self.substanceUnits)
            if self.substanceUnits is not None
            else model.getSubstanceUnits()
        )
        _check_attribute(
            sbase.setSubstanceUnits(substance_units),
            sbase,
            "substanceUnits",
            substance_units,
            self,
        )

        if self.initialAmount is not None:
            # a plain double which every SBML level and version has, measured
            # to answer success for every input
            sbase.setInitialAmount(self.initialAmount)
        if self.initialConcentration is not None:
            _check_attribute(
                sbase.setInitialConcentration(self.initialConcentration),
                sbase,
                "initialConcentration",
                self.initialConcentration,
                self,
            )
        if self.conversionFactor is not None:
            _check_attribute(
                sbase.setConversionFactor(self.conversionFactor),
                sbase,
                "conversionFactor",
                self.conversionFactor,
                self,
            )

        # fbc
        if (self.charge is not None) or (self.chemicalFormula is not None):
            obj_fbc: libsbml.FbcSpeciesPlugin | None = sbase.getPlugin("fbc")
            if obj_fbc is None:
                # reported rather than raised, unlike every other element
                # whose fbc content needs the plugin: the rest of the species
                # is written and only the two fbc attributes are lost. A
                # model with a charge declares fbc itself, so the only
                # document which gets here is one whose level cannot declare
                # a package at all, see `_no_plugin_reason`
                logger.error(
                    "The fbc charge and chemical formula of '%s' are not written: %s.",
                    self,
                    _no_plugin_reason(sbase, "fbc"),
                )
            else:
                if self.charge is not None:
                    self._set_charge(obj_fbc)
                if self.chemicalFormula is not None:
                    _check_attribute(
                        obj_fbc.setChemicalFormula(self.chemicalFormula),
                        obj_fbc,
                        "chemicalFormula",
                        self.chemicalFormula,
                        self,
                    )

    def _set_charge(self, species_fbc: libsbml.FbcSpeciesPlugin) -> None:
        """Set the fbc charge as the fbc version of the document writes it.

        libsbml keeps the integer `fbc:charge` of fbc version 2 and the double
        `fbc:charge` of fbc version 3 apart: it writes only the one of the
        version of the document, and the getter of the other one returns 0.
        `FbcSpeciesPlugin.setCharge` picks which of the two it sets from the
        python type of its argument, an `int` the fbc version 2 charge and a
        `float` the fbc version 3 one, so the charge is passed as the type the
        version of the plugin writes. The version is read from the plugin of
        the created species, which is the version of the document being
        written, rather than from the packages of the `Model`.

        fbc version 2 has no charge which is not a whole number, so such a
        charge cannot be written into a document of that version at all. It is
        reported and left unset rather than rounded, which would write a
        charge the model never stated.

        Args:
            species_fbc: the fbc plugin of the created libsbml.Species
        """
        if self.charge is None:
            return
        if species_fbc.getPackageVersion() >= 3:
            check(
                species_fbc.setCharge(float(self.charge)),
                f"Set charge '{self.charge}' on species '{self.sid}'",
            )
        elif float(self.charge).is_integer():
            check(
                species_fbc.setCharge(int(self.charge)),
                f"Set charge '{self.charge}' on species '{self.sid}'",
            )
        else:
            logger.error(
                "Species '%s' has the charge %s, which fbc version 2 cannot "
                "express: its 'fbc:charge' is an integer. The charge is not "
                "written; use `Package.FBC_V3` for a model with such a charge.",
                self.sid,
                self.charge,
            )


class _ModelSymbols:
    """The ids the rules and initial assignments of a model are checked against.

    A rule or an initial assignment checks that its variable has no rule or
    initial assignment yet and creates a parameter for a variable which is
    no symbol of the model. libsbml answers each of these lookups by walking
    a list of the model, which makes writing the rules of a model quadratic
    in its size. While `Model._fill_sbml` writes the rules and the initial
    assignments, `indexed` therefore keeps the ids in sets which are built
    once and kept up to date by the writers; outside of it, e.g. for the
    rule of a `Parameter` with a math value or for an element written into a
    libsbml model by a caller of its own, `for_model` answers with the
    libsbml lookups, which is what an index is equal to.

    The sets answer exactly what the libsbml lookups answer:
    `getParameter`, `getSpecies`, `getCompartment` and `getSpeciesReference`
    (the reactants and products of every reaction, not the modifiers) for a
    symbol, `getRuleByVariable` for a rule, which also finds an algebraic
    rule by the empty variable, and `getInitialAssignmentBySymbol`.
    """

    #: the index of the model which is being filled, see `indexed`
    _active: ClassVar[ContextVar[_ModelSymbols | None]] = ContextVar(
        "sbmlutils_model_symbols", default=None
    )

    def __init__(self, model: libsbml.Model, indexed: bool) -> None:
        """Answer the lookups for a model, from sets or from libsbml.

        Args:
            model: the libsbml.Model the lookups are made in
            indexed: whether the ids are collected into sets now, which the
                writers must keep up to date, or looked up with libsbml
        """
        self.model = model
        self._is_index = indexed
        self._parameters: dict[str, libsbml.Parameter] = {}
        self._symbols: set[str] = set()
        self._rule_variables: set[str] = set()
        self._assignment_symbols: set[str] = set()
        if not indexed:
            return
        for parameter in model.getListOfParameters():
            self._parameters.setdefault(parameter.getId(), parameter)
        self._symbols.update(s.getId() for s in model.getListOfSpecies())
        self._symbols.update(c.getId() for c in model.getListOfCompartments())
        for reaction in model.getListOfReactions():
            self._symbols.update(sr.getId() for sr in reaction.getListOfReactants())
            self._symbols.update(sr.getId() for sr in reaction.getListOfProducts())
        self._rule_variables.update(r.getVariable() for r in model.getListOfRules())
        self._assignment_symbols.update(
            a.getSymbol() for a in model.getListOfInitialAssignments()
        )

    @classmethod
    @contextmanager
    def indexed(cls, model: libsbml.Model) -> Iterator[None]:
        """Index the ids of the model for the writers inside the context.

        Only the rules, initial assignments and the parameters they create
        may be written inside the context, since only those keep the index
        up to date.

        Args:
            model: the libsbml.Model whose rules and initial assignments are
                written inside the context

        Yields:
            None
        """
        token = cls._active.set(cls(model, indexed=True))
        try:
            yield
        finally:
            cls._active.reset(token)

    @classmethod
    def for_model(cls, model: libsbml.Model) -> _ModelSymbols:
        """Get the lookups for the model, the index if it is being filled.

        Args:
            model: the libsbml.Model the lookups are made in

        Returns:
            the index of `indexed` for the model, else the libsbml lookups
        """
        active = cls._active.get()
        if active is not None and active.model is model:
            return active
        return cls(model, indexed=False)

    def has_symbol(self, sid: str) -> bool:
        """Check whether a rule or an assignment can change the id as it is.

        Args:
            sid: the variable of a rule or the symbol of an assignment

        Returns:
            whether the id is a parameter, species, compartment or the
            species reference of a reactant or product of the model
        """
        if self._is_index:
            return sid in self._parameters or sid in self._symbols
        return bool(
            self.model.getParameter(sid)
            or self.model.getSpecies(sid)
            or self.model.getCompartment(sid)
            or self.model.getSpeciesReference(sid)
        )

    def parameter(self, sid: str) -> libsbml.Parameter | None:
        """Get the parameter of the model with the id.

        Args:
            sid: the id of the parameter

        Returns:
            the parameter, `None` if the model has none with the id
        """
        if self._is_index:
            return self._parameters.get(sid)
        return self.model.getParameter(sid)

    def has_rule(self, variable: str) -> bool:
        """Check whether the model has a rule for the variable.

        Args:
            variable: the variable of the rule

        Returns:
            whether the model has a rule for the variable
        """
        if self._is_index:
            return variable in self._rule_variables
        return bool(self.model.getRuleByVariable(variable))

    def has_initial_assignment(self, symbol: str) -> bool:
        """Check whether the model has an initial assignment for the symbol.

        Args:
            symbol: the symbol of the initial assignment

        Returns:
            whether the model has an initial assignment for the symbol
        """
        if self._is_index:
            return symbol in self._assignment_symbols
        return bool(self.model.getInitialAssignmentBySymbol(symbol))

    def add_parameter(self, parameter: libsbml.Parameter) -> None:
        """Record a parameter which was created in the model.

        Args:
            parameter: the created libsbml.Parameter
        """
        if self._is_index:
            self._parameters.setdefault(parameter.getId(), parameter)

    def add_rule(self, rule: libsbml.Rule) -> None:
        """Record a rule which was created in the model.

        Args:
            rule: the created libsbml rule, its variable set
        """
        if self._is_index:
            self._rule_variables.add(rule.getVariable())

    def add_initial_assignment(self, assignment: libsbml.InitialAssignment) -> None:
        """Record an initial assignment which was created in the model.

        Args:
            assignment: the created libsbml.InitialAssignment, its symbol set
        """
        if self._is_index:
            self._assignment_symbols.add(assignment.getSymbol())


class InitialAssignment(Value):
    """InitialAssignments.

    The unit attribute is only for the case where a parameter must be created
    (which has the unit). In case of an initialAssignment of a value the units
    have to be defined in the math. A value of `None` is an initial assignment
    without math, which SBML allows from L3V2 on.

    A `<comp:port>` names an initial assignment by its metaid, see
    `Sbase._port_reference`.
    """

    #: `libsbml.Model.getElementBySId` does not answer with an initial
    #: assignment, see `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __init__(
        self,
        symbol: str,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
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
        """Construct InitialAssignment."""
        super().__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.symbol = symbol
        self.unit = unit

    def create_sbml(self, model: libsbml.Model) -> libsbml.InitialAssignment:
        """Create InitialAssignment.

        Creates a required parameter if the symbol for the
        initial assignment does not exist in the model.

        Raises:
            ValueError: if the model has an initial assignment for the symbol
                already; a second one makes the model invalid
        """
        symbols = _ModelSymbols.for_model(model)
        if symbols.has_initial_assignment(self.symbol):
            raise ValueError(
                f"An InitialAssignment for symbol '{self.symbol}' exists already, "
                f"a second one with value '{self.value}' makes the model invalid."
            )

        # Create parameter if not existing
        if not symbols.has_symbol(self.symbol):
            symbols.add_parameter(
                Parameter(
                    sid=self.symbol,
                    value=None,
                    unit=self.unit,
                    constant=True,
                    name=self.name,
                ).create_sbml(model)
            )

        obj: libsbml.InitialAssignment = model.createInitialAssignment()
        self._set_fields(obj, model)
        _check_attribute(obj.setSymbol(self.symbol), obj, "symbol", self.symbol, self)
        symbols.add_initial_assignment(obj)
        if self.value is not None:
            _set_math(obj, str(self.value), model)

        self.create_port(model)
        return obj


#: the libsbml rule a `RuleWithVariable` creates; a `TypeVar` of the module rather
#: than a type parameter of the class, because this module postpones its
#: annotations and `typing.get_type_hints` resolves the annotation of a method in
#: the namespace of the module, where a type parameter does not exist
_VariableRuleT = TypeVar("_VariableRuleT", libsbml.AssignmentRule, libsbml.RateRule)


class RuleWithVariable(ValueWithUnit, Generic[_VariableRuleT]):  # noqa: UP046
    """Base of the rules which determine a variable, `AssignmentRule` and `RateRule`.

    The unit attribute is only for the case where a parameter must be created
    for the variable (which has the unit). The units of the value have to be
    defined in the math. A value of `None` is a rule without math, which SBML
    allows from L3V2 on.

    A `<comp:port>` names a rule by its metaid, see `Sbase._port_reference`.
    """

    #: `libsbml.Model.getElementBySId` does not answer with a rule, see
    #: `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __init__(
        self,
        variable: str,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
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
        """Construct the rule for a variable."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable: str = variable

    def _create_rule(self, model: libsbml.Model) -> _VariableRuleT:
        """Create the empty libsbml rule of this class in the model.

        Args:
            model: the libsbml.Model the rule is created in

        Returns:
            the created libsbml rule
        """
        raise NotImplementedError

    def check_model_for_rule(self, model: libsbml.Model) -> None:
        """Check model for rule requirements.

        Creates a required parameter if the variable of the rule does not
        exist in the model, and makes a parameter it changes non-constant.

        Raises:
            ValueError: if the model has a rule for the variable already; a
                second rule makes the model invalid
        """
        rule_type: str = type(self).__name__
        symbols = _ModelSymbols.for_model(model)
        if symbols.has_rule(self.variable):
            raise ValueError(
                f"A rule for variable '{self.variable}' exists already, the "
                f"{rule_type} with value '{self.value}' would be a second one "
                f"and make the model invalid."
            )

        # Create parameter if not existing
        if not symbols.has_symbol(self.variable):
            symbols.add_parameter(
                Parameter(
                    sid=self.variable,
                    value=None,
                    unit=self.unit,
                    constant=False,
                    name=self.name,
                ).create_sbml(model)
            )

        # Make sure the parameter is const=False
        p: libsbml.Parameter | None = symbols.parameter(self.variable)
        if p is not None and p.getConstant() is True:
            logger.warning(
                "Parameter changed by a %s must be 'constant=False', but '%s' "
                "is 'constant=True'; it is set to 'constant=False'.",
                rule_type,
                p.getId(),
            )
            _check_attribute(
                p.setConstant(False), p, "constant", False, f"Parameter({p.getId()})"
            )

    def create_sbml(self, model: libsbml.Model) -> _VariableRuleT:
        """Create the rule in the model.

        Args:
            model: the libsbml.Model the rule is created in

        Returns:
            the created libsbml rule
        """
        self.check_model_for_rule(model)
        obj: _VariableRuleT = self._create_rule(model)
        self._set_fields(obj, model)
        _check_attribute(
            obj.setVariable(self.variable), obj, "variable", self.variable, self
        )
        _ModelSymbols.for_model(model).add_rule(obj)
        if self.value is not None:
            _set_math(obj, str(self.value), model)
        self.create_port(model)
        return obj


class AssignmentRule(RuleWithVariable[libsbml.AssignmentRule]):
    """AssignmentRule, the variable is the value of the math at any time."""

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.variable} = {self.value} [{self.unit}]"

    def _create_rule(self, model: libsbml.Model) -> libsbml.AssignmentRule:
        """Create the empty libsbml.AssignmentRule in the model."""
        return model.createAssignmentRule()


class RateRule(RuleWithVariable[libsbml.RateRule]):
    """RateRule, the math is the rate of change of the variable."""

    _hint_sbo_term: ClassVar[bool] = False

    def __repr__(self) -> str:
        """Get string representation."""
        return f"d{self.variable}/dt = {self.value} [{self.unit}]"

    def _create_rule(self, model: libsbml.Model) -> libsbml.RateRule:
        """Create the empty libsbml.RateRule in the model."""
        return model.createRateRule()


class AlgebraicRule(ValueWithUnit):
    """AlgebraicRule, the math is zero at any time.

    An algebraic rule determines no variable of its own. A value of `None`
    is a rule without math, which SBML allows from L3V2 on.

    A `<comp:port>` names a rule by its metaid, see `Sbase._port_reference`.
    """

    #: `libsbml.Model.getElementBySId` does not answer with a rule, see
    #: `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __repr__(self) -> str:
        """Get string representation."""
        return f"0 = {self.value} [{self.unit}]"

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
        """Construct AlgebraicRule."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

    def create_sbml(self, model: libsbml.Model) -> libsbml.AlgebraicRule:
        """Create AlgebraicRule."""
        rule: libsbml.AlgebraicRule = model.createAlgebraicRule()
        # libsbml finds an algebraic rule by the empty variable
        _ModelSymbols.for_model(model).add_rule(rule)
        self._set_fields(rule, model)
        if self.value is not None:
            _set_math(rule, str(self.value), model)
        self.create_port(model)
        return rule


class Formula(NamedTuple):
    """The math and the unit of a kinetic law, deprecated.

    A kinetic law is a `KineticLaw`; a `Formula` is still accepted by
    `Reaction._process_formula`.
    """

    value: str
    unit: UnitType


class KineticLaw(Sbase):
    """KineticLaw of a Reaction.

    Corresponds to the information in a `libsbml.KineticLaw`: the rate math,
    and the local parameters which are scoped to it.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: a `<kineticLaw>` has no id in an SBML L3V1 document, so a port names it by
    #: its metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

    def __init__(
        self,
        math: str | None,
        unit: UnitType = None,
        local_parameters: list[LocalParameter] | None = None,
        sid: str | None = None,
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
        """Construct a KineticLaw.

        Args:
            math: the rate expression, as an SBML L3 formula string; `None`
                for a kinetic law without math, which SBML allows from L3V2 on
            unit: the unit of the rate; never written to XML in any
                level/version this package currently emits (it existed on
                `libsbml.KineticLaw` only in L1V1, L1V2 and L2V1, and this
                package never wrote it even then). Kept as python state for a
                `KineticLaw` parsed from such an old document, since a future
                write-back needs somewhere to hold it
            local_parameters: the parameters scoped to this kinetic law
            sid: optional SId, kinetic laws only carry one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math
        self.unit = unit
        self.local_parameters = local_parameters if local_parameters else []

    def __repr__(self) -> str:
        """Get string representation."""
        return f"KineticLaw({self.math})"

    def create_sbml(
        self, reaction: libsbml.Reaction, model: libsbml.Model
    ) -> libsbml.KineticLaw:
        """Create the libsbml.KineticLaw on the given reaction.

        Args:
            reaction: the libsbml.Reaction the kinetic law belongs to
            model: the libsbml.Model the reaction is created in, which the
                math is parsed against and which the port, the uncertainties
                and the replacedBy of the kinetic law and of its local
                parameters are created in; handed down, never looked up,
                see `Model._fill_sbml`

        Returns:
            the created libsbml.KineticLaw
        """
        klaw: libsbml.KineticLaw = reaction.createKineticLaw()
        self._set_fields(klaw, model)
        self.create_port(model)

        # local parameters must exist before the math is parsed, so that the
        # formula parser resolves their ids
        for local_parameter in self.local_parameters:
            local_parameter.create_sbml(klaw, model)

        if self.math is None:
            return klaw
        ast_node = libsbml.parseL3FormulaWithModel(self.math, model)
        if ast_node is None:
            logger.error(
                "Kinetic law math could not be parsed: '%s', %s",
                self.math,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(klaw.setMath(ast_node), f"Set math on kinetic law '{self.math}'")
        return klaw


#: a token of an infix gene product association: a run of characters which is
#: neither whitespace nor a parenthesis, so that the string is split on both
_ASSOCIATION_TOKEN: re.Pattern[str] = re.compile(r"[^\s()]+")

#: the operators of an infix gene product association, in the two spellings
#: libsbml's own infix parser accepts for each of them; every other token of an
#: association is a gene product id
_ASSOCIATION_OPERATORS: frozenset[str] = frozenset({"and", "AND", "or", "OR"})


def _gene_product_ids(association: str) -> list[str]:
    """Get the gene products an infix gene product association references.

    The association is split into tokens on whitespace and on parentheses, and
    every token which is not an operator is a gene product id. Only a whole
    token is an operator: an id such as `ORF1`, `brandy` or `sensor` carries
    the letters of one inside it and is a gene product like any other.

    Args:
        association: the association as an infix string of gene product ids,
            e.g. `(ORF1 and b0001) or b0002`

    Returns:
        the id of every gene product the association references, in the order
        of the string and with a repeated id repeated
    """
    return [
        token
        for token in _ASSOCIATION_TOKEN.findall(association)
        if token not in _ASSOCIATION_OPERATORS
    ]


class _SpeciesReference(Sbase):
    """The species reference a `Reaction` writes for one part of its equation.

    A part of a reaction equation is an `EquationPart`, which cannot be an
    `Sbase` because `sbmlutils.reaction_equation` is imported by the factory.
    Its `SBase` fields are written through this class, so that a species
    reference gets them exactly as every other element does, its notes
    normalized by `Sbase._process_notes` included.
    """

    # a species reference is written from an equation string, which has no
    # place for its name or sboTerm
    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    def __init__(self, part: EquationPart):
        """Construct the species reference of a part of an equation.

        Args:
            part: the reactant, product or modifier of the equation
        """
        super().__init__(
            sid=part.sid,
            name=part.name,
            sboTerm=part.sboTerm,
            metaId=part.metaId,
            annotations=part.annotations,
            notes=part.notes,
            keyValuePairs=part.keyValuePairs,
        )
        self.part = part

    def __str__(self) -> str:
        """Get the string of the part, which names it in every report."""
        return str(self.part)

    def _set_fields(
        self,
        sbase: libsbml.SpeciesReference | libsbml.ModifierSpeciesReference,
        model: libsbml.Model,
    ) -> None:
        """Set the fields on the species reference.

        A `libsbml.ModifierSpeciesReference` has no `constant` or
        `stoichiometry` attribute (only its sibling `SpeciesReference`, used
        for reactants and products, does), so those two are only set when
        `sbase` actually is one. Everything else an `SBase` carries, the
        key-value pairs of fbc version 3 included, is written for all three
        roles alike.

        Args:
            sbase: the libsbml species reference created for the part
            model: the libsbml.Model the reaction belongs to
        """
        part = self.part
        if part.species is not None:
            _check_attribute(
                sbase.setSpecies(part.species), sbase, "species", part.species, self
            )
        super()._set_fields(sbase, model)
        if isinstance(sbase, libsbml.SpeciesReference):
            if part.constant is not None:
                _check_attribute(
                    sbase.setConstant(part.constant),
                    sbase,
                    "constant",
                    part.constant,
                    self,
                )
            if part.stoichiometry is not None:
                # a stoichiometry is a plain double, which libsbml accepts at
                # every level and version
                sbase.setStoichiometry(part.stoichiometry)

    def _set_name(self, sbase: Any, name: str) -> None:
        """Set the name, which libsbml rejects on a species reference with a space.

        `SimpleSpeciesReference::setName` (libsbml 5.21.1) erroneously
        applies SId syntax validation to `name`, which SBML L3 defines as a
        plain `string`, not an `SId`; `Species.setName`/`Reaction.setName` do
        not do this. Verified live: `SpeciesReference.setName('reactant
        name')` returns rc=-4 (LIBSBML_INVALID_ATTRIBUTE_VALUE) and leaves
        `getName()` empty, while `SpeciesReference.setName('reactantname')`
        (no space) returns rc=0 and is set. This is a libsbml defect specific
        to `SimpleSpeciesReference` (the base of both `SpeciesReference` and
        `ModifierSpeciesReference`), and there is nothing correct to do about
        it here short of mangling the name, which this deliberately does not
        do. Logged as a warning rather than routed through `check()` (which
        always logs at error level): the name is unfixable from the caller's
        side, and any name containing a space, one of the most common cases,
        would otherwise log as an error on every single reaction.

        Args:
            sbase: the libsbml species reference created for the part
            name: the name to set
        """
        rc = sbase.setName(name)
        if rc != libsbml.LIBSBML_OPERATION_SUCCESS:
            logger.warning(
                "Name '%s' could not be set on species reference for species "
                "'%s': rejected by libsbml with code %s (a known "
                "SimpleSpeciesReference.setName defect which applies SId "
                "syntax validation to the string-typed 'name' attribute).",
                name,
                self.part.species,
                rc,
            )


class Reaction(Sbase):
    """Reaction.

    Class for creating libsbml.Reaction.

    Equations are of the form
    '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]'

    The equation consists of
    - substrates concatenated via '+' on the left side
      (with optional stoichiometric coefficients)
    - separation characters separating the left and right equation sides:
      '<=>' or '<->' for reversible reactions,
      '=>' or '->' for irreversible reactions (irreversible reactions
      are written from left to right)
    - products concatenated via '+' on the right side
      (with optional stoichiometric coefficients)
    - optional list of modifiers within brackets [] separated by ','

    Examples of valid equations are:
        '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]',
        'c__gal1p => c__gal + c__phos',
        'e__h2oM <-> c__h2oM',
        '3 atp + 2.0 phos + ki <-> 16.98 tet',
        'c__gal1p => c__gal + c__phos [c__udp, c__utp]',
        'A_ext => A []',
        '=> cit',
        'acoa =>',
    """

    def __init__(
        self,
        sid: str,
        equation: ReactionEquation | str,
        formula: KineticLaw | Formula | tuple[str, UnitType] | str | None = None,
        pars: list[Parameter] | None = None,
        rules: list[AssignmentRule] | None = None,
        compartment: str | None = None,
        fast: bool = False,
        reversible: bool | None = None,
        lowerFluxBound: str | None = None,
        upperFluxBound: str | None = None,
        geneProductAssociation: str | None = None,
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
        """Construct Reaction."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        self.equation = Reaction._process_equation(equation=equation)
        self.compartment = compartment
        self.reversible = reversible
        self.pars = pars if pars else []
        self.rules = rules if rules else []
        self.formula = Reaction._process_formula(formula=formula)
        self.fast = fast
        self.lowerFluxBound = lowerFluxBound
        self.upperFluxBound = upperFluxBound
        self.geneProductAssociation = geneProductAssociation

    @staticmethod
    def _process_equation(equation: ReactionEquation | str) -> ReactionEquation:
        """Process reaction equation."""
        if isinstance(equation, ReactionEquation):
            return equation
        return ReactionEquation.from_str(str(equation))

    @staticmethod
    def _process_formula(
        formula: KineticLaw | Formula | tuple[str, UnitType] | str | None,
    ) -> KineticLaw | None:
        """Process the reaction formula into a KineticLaw.

        Args:
            formula: a KineticLaw, a `(math, unit)` tuple, a math string, or
                None

        Returns:
            the kinetic law of the reaction, None if no formula was given

        Raises:
            ValueError: if the formula is of an unsupported type
        """
        if formula is None:
            return None
        if isinstance(formula, KineticLaw):
            return formula
        if isinstance(formula, str):
            return KineticLaw(math=formula)
        if isinstance(formula, (tuple, list)):
            math, unit = formula
            return KineticLaw(math=math, unit=unit)
        raise ValueError(f"Unsupported formula: '{formula}'")

    def create_sbml(self, model: libsbml.Model) -> libsbml.Reaction:
        """Create Reaction SBML in model."""
        # parameters and rules
        create_objects(model, self.pars, key="parameters")
        create_objects(model, self.rules, key="rules")

        # reaction
        r: libsbml.Reaction = model.createReaction()
        self._set_fields(r, model)
        # the fbc plugin of the reaction is only dereferenced for a reaction
        # which has fbc content, so a reaction without one is written into a
        # document which declares no fbc, as it has to be
        r_fbc: libsbml.FbcReactionPlugin | None = r.getPlugin("fbc")

        # equation
        for reactant in self.equation.reactants:
            _SpeciesReference(reactant)._set_fields(r.createReactant(), model)

        for product in self.equation.products:
            _SpeciesReference(product)._set_fields(r.createProduct(), model)

        for modifier in self.equation.modifiers:
            _SpeciesReference(modifier)._set_fields(r.createModifier(), model)

        # kinetics
        if self.formula is not None:
            self.formula.create_sbml(r, model)

        # add fbc bounds
        if self.upperFluxBound or self.lowerFluxBound:
            bounds_fbc: libsbml.FbcReactionPlugin = (
                r_fbc
                if r_fbc is not None
                else _fbc_plugin(r, f"The flux bounds of '{self}'")
            )
            if self.upperFluxBound:
                _check_attribute(
                    bounds_fbc.setUpperFluxBound(self.upperFluxBound),
                    bounds_fbc,
                    "upperFluxBound",
                    self.upperFluxBound,
                    self,
                )
            if self.lowerFluxBound:
                _check_attribute(
                    bounds_fbc.setLowerFluxBound(self.lowerFluxBound),
                    bounds_fbc,
                    "lowerFluxBound",
                    self.lowerFluxBound,
                    self,
                )

        # add gpa
        if self.geneProductAssociation:
            association_fbc: libsbml.FbcReactionPlugin = (
                r_fbc
                if r_fbc is not None
                else _fbc_plugin(r, f"The gene product association of '{self}'")
            )
            # parse the string and create the respective GPA
            gpa: libsbml.GeneProductAssociation = (
                association_fbc.createGeneProductAssociation()
            )

            # check all genes are in model; the association names them by id,
            # which is what `setAssociation(usingId=True)` below writes, so the
            # lookup is `getGeneProduct` and not `getGeneProductByLabel`. The
            # model is the one the reaction is created in, which is passed in:
            # `r.getModel()` returns the model of the document even for a
            # reaction inside a `<comp:modelDefinition>` (measured with
            # libsbml 5.21.2), whose gene products are its own.
            model_fbc: libsbml.FbcModelPlugin = _fbc_plugin(
                model, f"The gene product association of '{self}'"
            )
            for gp in _gene_product_ids(self.geneProductAssociation):
                if not model_fbc.getGeneProduct(gp):
                    logger.error("GeneProduct missing in model: `%s`", gp)

            check(
                gpa.setAssociation(
                    self.geneProductAssociation,
                    True,  # bool usingId=False,
                    False,  # bool addMissingGP=True
                ),
                f"set gpa: `{self.geneProductAssociation}`",
            )

        self.create_port(model)
        return r

    def _set_fields(self, sbase: libsbml.Reaction, model: libsbml.Model) -> None:
        """Set fields in libsbml.Reaction."""
        super()._set_fields(sbase, model)

        if self.compartment:
            # the compartment of a reaction is SBML L3 only
            _check_attribute(
                sbase.setCompartment(self.compartment),
                sbase,
                "compartment",
                self.compartment,
                self,
            )
        reversible = (
            self.reversible if self.reversible is not None else self.equation.reversible
        )
        check(sbase.setReversible(reversible), f"Set reversible on '{self.sid}'")

        # `fast` was removed from SBML in L3V2; `setFast` errors on such a
        # document, so it is only called when the level/version being
        # written still supports the attribute.
        supports_fast = sbase.getLevel() < 3 or (
            sbase.getLevel() == 3 and sbase.getVersion() < 2
        )
        if supports_fast:
            check(sbase.setFast(self.fast), f"Set fast on '{self.sid}'")


class EventAssignment(Value):
    """EventAssignment of an Event.

    Assigns the value of the expression to the variable when the event fires.

    The id is set by `Sbase._set_fields` through `setIdAttribute`, see
    `_ID_ATTRIBUTE_TYPECODES`, which never touches `variable`: an L3V1
    document has no place for the id of an event assignment, an L3V2 one
    writes it next to `variable`.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: `libsbml.Model.getElementBySId`, which comp resolves a `comp:idRef`
    #: with, does not answer with an event assignment, so a port names one by
    #: its metaid, see `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __init__(
        self,
        variable: str,
        value: str | float | None,
        sid: str | None = None,
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
        """Construct an EventAssignment.

        Args:
            variable: the id of the element the assignment applies to
            value: the assigned expression, as an SBML L3 formula string;
                `None` for an event assignment without math, which SBML allows
                from L3V2 on
            sid: optional SId; `libsbml.EventAssignment` only gained a real,
                separate `id` attribute in SBML L3V2, and only from L3V2
                onward is it distinct from `variable` (see `_set_fields`
                docstring for the L3V1 behaviour)
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
        """
        super().__init__(
            sid=sid,
            value=value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable = variable

    def __repr__(self) -> str:
        """Get string representation."""
        return f"EventAssignment({self.variable} = {self.value})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.EventAssignment:
        """Create the libsbml.EventAssignment on the given event.

        Args:
            event: the libsbml.Event the assignment belongs to
            model: the libsbml.Model, used to resolve ids in the expression

        Returns:
            the created libsbml.EventAssignment
        """
        ea: libsbml.EventAssignment = event.createEventAssignment()
        self._set_fields(ea, model)
        self.create_port(model)
        check(ea.setVariable(self.variable), f"Set variable '{self.variable}'")
        if self.value is None:
            return ea
        ast_node = libsbml.parseL3FormulaWithModel(str(self.value), model)
        if ast_node is None:
            logger.error(
                "Event assignment math could not be parsed: '%s', %s",
                self.value,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(ea.setMath(ast_node), f"Set math on '{self.variable}'")
        return ea


class Trigger(Sbase):
    """Trigger of an Event.

    Corresponds to a `libsbml.Trigger`: the condition whose change from false
    to true fires the event, and the two flags which qualify it.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: a `<trigger>` has no id in an SBML L3V1 document, so a port names it by
    #: its metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

    def __init__(
        self,
        math: str | None,
        initialValue: bool = False,
        persistent: bool = True,
        sid: str | None = None,
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
        """Construct a Trigger.

        Args:
            math: the condition, as an SBML L3 formula string, e.g.
                `"time >= 10"`; `None` for a trigger without math, which SBML
                allows from L3V2 on
            initialValue: the value of the trigger before the simulation
                starts; with `False` a condition which is true at the start
                fires the event at the start
            persistent: whether a fired event is executed even if the
                condition turns false again before its delay has passed
            sid: optional SId, a trigger only carries one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a trigger only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math
        self.initialValue = initialValue
        self.persistent = persistent

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Trigger({self.math})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.Trigger:
        """Create the libsbml.Trigger on the given event.

        Args:
            event: the libsbml.Event the trigger belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Trigger
        """
        trigger: libsbml.Trigger = event.createTrigger()
        self._set_fields(trigger, model)
        self.create_port(model)
        return trigger

    def _set_fields(self, sbase: libsbml.Trigger, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Trigger.

        Args:
            sbase: the libsbml.Trigger created by `create_sbml`
            model: the libsbml.Model the trigger belongs to
        """
        super()._set_fields(sbase, model)
        if sbase.getLevel() < 3:
            # a trigger has these flags from SBML L3 on, below libsbml rejects
            # them as unexpected attributes, which the caller cannot change
            logger.debug(
                "'trigger' has no initialValue and persistent in SBML L%sV%s, "
                "they are not written.",
                sbase.getLevel(),
                sbase.getVersion(),
            )
        else:
            # initialValue False is not supported by Copasi, a condition on
            # time is the workaround
            check(
                sbase.setInitialValue(self.initialValue),
                f"Set initialValue on trigger '{self.math}'",
            )
            # persistent True is not supported by Copasi, careful with its usage
            check(
                sbase.setPersistent(self.persistent),
                f"Set persistent on trigger '{self.math}'",
            )
        _set_math(sbase, self.math, model)


class Priority(Sbase):
    """Priority of an Event.

    Corresponds to a `libsbml.Priority`: the math which orders the events
    that are executed at the same time, the event with the higher priority
    first.

    libsbml attaches no `CompSBasePlugin` to a `<priority>`, alone among the
    four children of an event, so a `replacedBy` is not offered, see
    `Sbase.create_replaced_by`.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: a `<priority>` has no id in an SBML L3V1 document, so a port names it by
    #: its metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

    def __init__(
        self,
        math: str | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Construct a Priority.

        Args:
            math: the priority, as an SBML L3 formula string; `None` for a
                priority without math, which SBML allows from L3V2 on
            sid: optional SId, a priority only carries one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a priority only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
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
            uncertainties=uncertainties,
        )
        self.math = math

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Priority({self.math})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.Priority | None:
        """Create the libsbml.Priority on the given event.

        Args:
            event: the libsbml.Event the priority belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Priority, `None` below SBML L3, which has no
            priority; that is logged as an error
        """
        priority: libsbml.Priority | None = event.createPriority()
        if priority is None:
            logger.error(
                "An event priority needs SBML L3, the priority '%s' of event "
                "'%s' is not written in SBML L%sV%s.",
                self.math,
                event.getId(),
                event.getLevel(),
                event.getVersion(),
            )
            return None
        self._set_fields(priority, model)
        self.create_port(model)
        return priority

    def _set_fields(self, sbase: libsbml.Priority, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Priority.

        Args:
            sbase: the libsbml.Priority created by `create_sbml`
            model: the libsbml.Model the priority belongs to
        """
        super()._set_fields(sbase, model)
        _set_math(sbase, self.math, model)


class Delay(Sbase):
    """Delay of an Event.

    Corresponds to a `libsbml.Delay`: the math of the time between the firing
    of the event and the execution of its assignments.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: a `<delay>` has no id in an SBML L3V1 document, so a port names it by
    #: its metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

    def __init__(
        self,
        math: str | None,
        sid: str | None = None,
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
        """Construct a Delay.

        Args:
            math: the delay, as an SBML L3 formula string; `None` for a delay
                without math, which SBML allows from L3V2 on
            sid: optional SId, a delay only carries one since SBML L3V2; not
                written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a delay only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Delay({self.math})"

    def create_sbml(self, event: libsbml.Event, model: libsbml.Model) -> libsbml.Delay:
        """Create the libsbml.Delay on the given event.

        Args:
            event: the libsbml.Event the delay belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Delay
        """
        delay: libsbml.Delay = event.createDelay()
        self._set_fields(delay, model)
        self.create_port(model)
        return delay

    def _set_fields(self, sbase: libsbml.Delay, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Delay.

        Args:
            sbase: the libsbml.Delay created by `create_sbml`
            model: the libsbml.Model the delay belongs to
        """
        super()._set_fields(sbase, model)
        _set_math(sbase, self.math, model)


class Event(Sbase):
    """Event.

    An event fires when its trigger, e.g. `time >= 10`, changes from false to
    true, and then executes its assignments, e.g. `{"S1": 5.0}`, after its
    optional delay. The priority orders events which are executed at the same
    time.

    The trigger, the priority and the delay are a `Trigger`, a `Priority` and
    a `Delay`, which carry their own metadata. Each of them is also accepted
    as a formula string or a number, which is normalized into the object;
    this is the documented authoring style, e.g.
    `Event("e1", trigger="time >= 10", priority="1", delay="2")`. `None`
    writes no element at all: an event without a priority or a delay, or,
    from SBML L3V2 on, without a trigger. An element without math, which SBML
    allows from L3V2 on, is an object whose `math` is `None`, e.g.
    `Trigger(None)`.

    `trigger`, `priority` and `delay` normalize what is assigned to them
    after construction in the same way. `trigger_persistent` and
    `trigger_initialValue` read and set the flags of the trigger.
    """

    def __init__(
        self,
        sid: str | None,
        trigger: Trigger | str | float | None,
        assignments: dict[str, str | float] | list[EventAssignment] | None = None,
        trigger_persistent: bool | None = None,
        trigger_initialValue: bool | None = None,
        useValuesFromTriggerTime: bool = True,
        priority: Priority | str | float | None = None,
        delay: Delay | str | float | None = None,
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
        """Construct an Event.

        Args:
            sid: optional SId
            trigger: the trigger, a `Trigger`, or its math as a formula string
                or a number; `None` for an event without a trigger, which SBML
                allows from L3V2 on
            assignments: the event assignments, a list of `EventAssignment`
                or a `{variable: expression}` dict
            trigger_persistent: the `persistent` of the `Trigger` created from
                math, `True` if not given. A `Trigger` keeps its own
                `persistent`, a different value given here is logged as a
                warning and not applied, as is one given without a trigger
            trigger_initialValue: the `initialValue` of the `Trigger` created
                from math, `False` if not given. A `Trigger` keeps its own
                `initialValue`, a different value given here is logged as a
                warning and not applied, as is one given without a trigger
            useValuesFromTriggerTime: whether the assignments are evaluated
                when the event fires rather than when it is executed
            priority: the priority, a `Priority`, or its math as a formula
                string or a number; `None` for an event without a priority
            delay: the delay, a `Delay`, or its math as a formula string or a
                number; `None` for an event without a delay
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement

        Raises:
            TypeError: if the trigger, the priority or the delay is neither
                the object, nor a formula string, nor a number
        """
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        self._trigger: Trigger | None = None
        self._init_trigger(trigger, trigger_persistent, trigger_initialValue)
        self.assignments = Event._process_assignments(assignments)
        self.useValuesFromTriggerTime = useValuesFromTriggerTime

        self._priority: Priority | None = None
        self.priority = priority
        self._delay: Delay | None = None
        self.delay = delay

    @staticmethod
    def _math(value: object, element: str) -> str:
        """Convert the math of a trigger, a priority or a delay to a formula.

        Args:
            value: the math, a formula string, or a number, which is
                converted with `str()`
            element: `"trigger"`, `"priority"` or `"delay"`, for the error

        Returns:
            the math as a formula string

        Raises:
            TypeError: if the value is neither a formula string nor a number;
                a bool is rejected too, `str(True)` is the id `True` rather
                than the constant `true`
        """
        if isinstance(value, str):
            return value
        if isinstance(value, numbers.Real) and not isinstance(value, bool):
            return str(value)
        raise TypeError(
            f"The {element} of an event is a {element.title()}, a formula "
            f"string or a number, not '{value!r}'."
        )

    def _init_trigger(
        self,
        trigger: Trigger | str | float | None,
        persistent: bool | None,
        initialValue: bool | None,
    ) -> None:
        """Set the trigger and the trigger flags given to the constructor.

        The `trigger_persistent` and `trigger_initialValue` arguments
        configure the `Trigger` created from math, which is the documented
        authoring style. A `Trigger` carries its own flags, which win over
        these arguments, so an argument which differs from them is logged as
        a warning, as is one given for an event without a trigger.

        Args:
            trigger: the trigger, a `Trigger`, its math, or `None` for an
                event without a trigger
            persistent: the `trigger_persistent` argument, `None` if it was
                not given
            initialValue: the `trigger_initialValue` argument, `None` if it was
                not given
        """
        self.trigger = trigger
        if not isinstance(trigger, Trigger):
            # created from math with the default flags, or no trigger, for
            # which the setters log that a flag is not applied
            if persistent is not None:
                self.trigger_persistent = persistent
            if initialValue is not None:
                self.trigger_initialValue = initialValue
            return

        for flag, value, attribute in (
            ("trigger_persistent", persistent, "persistent"),
            ("trigger_initialValue", initialValue, "initialValue"),
        ):
            if value is not None and value != getattr(trigger, attribute):
                logger.warning(
                    "Event '%s': '%s=%s' is not applied, its Trigger has '%s=%s'.",
                    self.sid,
                    flag,
                    value,
                    attribute,
                    getattr(trigger, attribute),
                )

    @property
    def trigger(self) -> Trigger | None:
        """Get the trigger, `None` for an event without a trigger."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: Trigger | str | float | None) -> None:
        """Set the trigger.

        Math is normalized into a `Trigger`, which keeps the `persistent` and
        `initialValue` of the trigger it replaces, or takes their defaults,
        `True` and `False`, if the event had no trigger. In 0.10 the flags
        were attributes of the event, which a new trigger string did not
        change.

        Args:
            trigger: the trigger, a `Trigger`, or its math as a formula string
                or a number; `None` for an event without a trigger

        Raises:
            TypeError: if the trigger is neither a `Trigger` nor math
        """
        if trigger is None or isinstance(trigger, Trigger):
            self._trigger = trigger
            return
        replaced = self._trigger
        self._trigger = Trigger(
            math=Event._math(trigger, "trigger"),
            persistent=True if replaced is None else replaced.persistent,
            initialValue=False if replaced is None else replaced.initialValue,
        )

    @property
    def trigger_persistent(self) -> bool | None:
        """Get the `persistent` of the trigger, `None` without a trigger."""
        return None if self._trigger is None else self._trigger.persistent

    @trigger_persistent.setter
    def trigger_persistent(self, persistent: bool) -> None:
        """Set the `persistent` of the trigger.

        Args:
            persistent: the flag; an event without a trigger has nothing to
                set it on, which is logged as a warning
        """
        self._set_trigger_flag("trigger_persistent", "persistent", persistent)

    @property
    def trigger_initialValue(self) -> bool | None:
        """Get the `initialValue` of the trigger, `None` without a trigger."""
        return None if self._trigger is None else self._trigger.initialValue

    @trigger_initialValue.setter
    def trigger_initialValue(self, initialValue: bool) -> None:
        """Set the `initialValue` of the trigger.

        Args:
            initialValue: the flag; an event without a trigger has nothing to
                set it on, which is logged as a warning
        """
        self._set_trigger_flag("trigger_initialValue", "initialValue", initialValue)

    def _set_trigger_flag(self, flag: str, attribute: str, value: bool) -> None:
        """Set a flag of the trigger, or log that the event has no trigger.

        Args:
            flag: the name of the flag on the event, for the warning
            attribute: the name of the flag on the `Trigger`
            value: the value of the flag
        """
        if self._trigger is None:
            logger.warning(
                "Event '%s' has no trigger, '%s=%s' is not applied.",
                self.sid,
                flag,
                value,
            )
            return
        setattr(self._trigger, attribute, value)

    @property
    def priority(self) -> Priority | None:
        """Get the priority, `None` for an event without a priority."""
        return self._priority

    @priority.setter
    def priority(self, priority: Priority | str | float | None) -> None:
        """Set the priority, math is normalized into a `Priority`.

        Args:
            priority: the priority, a `Priority`, or its math as a formula
                string or a number; `None` for an event without a priority

        Raises:
            TypeError: if the priority is neither a `Priority` nor math
        """
        if priority is None or isinstance(priority, Priority):
            self._priority = priority
        else:
            self._priority = Priority(math=Event._math(priority, "priority"))

    @property
    def delay(self) -> Delay | None:
        """Get the delay, `None` for an event without a delay."""
        return self._delay

    @delay.setter
    def delay(self, delay: Delay | str | float | None) -> None:
        """Set the delay, math is normalized into a `Delay`.

        Args:
            delay: the delay, a `Delay`, or its math as a formula string or a
                number; `None` for an event without a delay

        Raises:
            TypeError: if the delay is neither a `Delay` nor math
        """
        if delay is None or isinstance(delay, Delay):
            self._delay = delay
        else:
            self._delay = Delay(math=Event._math(delay, "delay"))

    @staticmethod
    def _process_assignments(
        assignments: dict[str, str | float] | list[EventAssignment] | None,
    ) -> list[EventAssignment]:
        """Normalize the event assignments to a list.

        A model definition writes the assignments as a `{variable:
        expression}` dict, which is the documented authoring style; the
        parser passes a list of `EventAssignment`, which carry their own
        metaId, sboTerm and annotations.

        Args:
            assignments: the assignments as a dict or a list

        Returns:
            the event assignments as `EventAssignment` objects
        """
        if assignments is None:
            return []
        if isinstance(assignments, dict):
            return [
                EventAssignment(variable=variable, value=value)
                for variable, value in assignments.items()
            ]
        return list(assignments)

    def create_sbml(self, model: libsbml.Model) -> libsbml.Event:
        """Create Event SBML in model."""
        event: libsbml.Event = model.createEvent()
        self._set_fields(event, model)
        self.create_port(model)

        return event

    def _set_fields(self, sbase: libsbml.Event, model: libsbml.Model) -> None:
        """Set fields in libsbml.Event."""
        super()._set_fields(sbase, model)

        check(
            sbase.setUseValuesFromTriggerTime(self.useValuesFromTriggerTime),
            f"Set useValuesFromTriggerTime on '{self.sid}'",
        )
        if self.trigger is not None:
            self.trigger.create_sbml(sbase, model)
        if self.priority is not None:
            self.priority.create_sbml(sbase, model)
        if self.delay is not None:
            self.delay.create_sbml(sbase, model)

        for assignment in self.assignments:
            assignment.create_sbml(sbase, model)

    @staticmethod
    def _trigger_from_time(t: float) -> str:
        """Create trigger from given time point."""
        return f"(time >= {t})"

    @staticmethod
    def _assignments_dict(species: list[str], values: list[str]) -> dict[str, str]:
        return dict(zip(species, values, strict=False))


class Constraint(Sbase):
    """Constraint.

    The Constraint object is a mechanism for stating the assumptions under which a model is designed to operate.
    The constraints are statements about permissible values of different quantities in a model.

    The message must be well formated XHTML, e.g.,
        message='<body xmlns="http://www.w3.org/1999/xhtml">ATP must be non-negative</body>'
    """

    #: a `<constraint>` has no id in an SBML L3V1 document, so a port names it by
    #: its metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

    def __init__(
        self,
        sid: str,
        math: str | None = None,
        message: str | None = None,
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
        """Constraint constructor."""
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math
        self.message = message

    def create_sbml(self, model: libsbml.Model) -> libsbml.Constraint:
        """Create Constraint SBML in model."""
        constraint: libsbml.Constraint = model.createConstraint()
        self._set_fields(constraint, model)
        self.create_port(model)
        return constraint

    def _set_fields(self, sbase: libsbml.Constraint, model: libsbml.Model) -> None:
        """Set fields on libsbml.Constraint."""
        super()._set_fields(sbase, model)

        _set_math(sbase, self.math, model)
        if self.message is not None:
            check(
                sbase.setMessage(self.message),
                message=f"Setting message on constraint: '{self.message}'",
            )
