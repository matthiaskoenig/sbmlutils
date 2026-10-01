"""The elements of the fbc package.

Exchange reactions, gene products, objectives with their flux
objectives and user defined constraints with their components.
"""

from __future__ import annotations

from typing import Any, ClassVar

import libsbml

from sbmlutils.factory._core import (
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    _check_attribute,
    _fbc_plugin,
    _fbc_version_allows,
    _set_variable_type,
)
from sbmlutils.factory.core_elements import Reaction
from sbmlutils.factory.distrib import Uncertainty
from sbmlutils.metadata import SBO
from sbmlutils.notes import Notes
from sbmlutils.validation import check

PREFIX_EXCHANGE_REACTION = "EX_"


class ExchangeReaction(Reaction):
    """Exchange reactions define substances which can be exchanged.

     This is important for FBC models.

     EXCHANGE_IMPORT (-INF, 0): is defined as negative flux through the exchange
     reaction, i.e. the upper bound must be 0, the lower bound some negative value,
        e.g. -INF

    EXCHANGE_EXPORT (0, INF): is defined as positive flux through the exchange reaction,
        i.e. the lower bound must be 0, the upper bound some positive value,
        e.g. INF
    """

    PREFIX = "EX_"

    def __init__(
        self,
        species_id: str,
        compartment: str | None = None,
        fast: bool = False,
        reversible: bool = True,
        lowerFluxBound: str | None = None,
        upperFluxBound: str | None = None,
        geneProductAssociation: str | None = None,
        name: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct ExchangeReaction."""
        super().__init__(
            sid=ExchangeReaction.PREFIX + species_id,
            equation=f"{species_id} ->",
            sboTerm=SBO.EXCHANGE_REACTION,
            name=name,
            compartment=compartment,
            fast=fast,
            reversible=reversible,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            lowerFluxBound=lowerFluxBound,
            upperFluxBound=upperFluxBound,
            geneProductAssociation=geneProductAssociation,
            uncertainties=uncertainties,
            port=port,
            replacedBy=replacedBy,
        )


class GeneProduct(Sbase):
    """GeneProduct.

    GeneProduct is a new FBC class derived from SBML SBase that inherits metaid
    and sboTerm, as well as the subcomponents for Annotation and Notes.
    The purpose of this class is to define a single gene product. It implements
    two required attributes id and label as well as two optional attributes
    name and associatedSpecies.

    libsbml attaches no `CompSBasePlugin` to an `<fbc:geneProduct>`, so a
    `replacedBy` is not offered, see `Sbase.create_replaced_by`.
    """

    def __init__(
        self,
        sid: str,
        label: str,
        associatedSpecies: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Create a GeneProduct."""
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
        self.associatedSpecies = associatedSpecies
        self.label = label

    def create_sbml(self, model: libsbml.Model) -> libsbml.GeneProduct:
        """Create the libsbml.GeneProduct in the model.

        Args:
            model: the libsbml.Model the gene product is created in

        Returns:
            the created libsbml.GeneProduct

        Raises:
            ValueError: if the model has no fbc plugin, see `_fbc_plugin`
        """
        model_fbc: libsbml.FbcModelPlugin = _fbc_plugin(
            model, f"The gene product '{self}'"
        )
        gene_product: libsbml.GeneProduct = model_fbc.createGeneProduct()
        self._set_fields(gene_product, model=model)

        self.create_port(model)

        # the label is a plain string which libsbml accepts in every form
        gene_product.setLabel(self.label)
        if self.associatedSpecies:
            _check_attribute(
                gene_product.setAssociatedSpecies(self.associatedSpecies),
                gene_product,
                "associatedSpecies",
                self.associatedSpecies,
                self,
            )

        return gene_product


class UserDefinedConstraintComponent(Sbase):
    """UserDefinedConstraintComponent.

    libsbml attaches no `CompSBasePlugin` to an
    `<fbc:userDefinedConstraintComponent>`, so a `replacedBy` is not offered,
    see `Sbase.create_replaced_by`.
    """

    def __init__(
        self,
        coefficient: str,
        variable: str,
        variableType: str | None = None,
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
        """Create a UserDefinedConstraintComponent."""
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
        self.variable = variable
        self.coefficient = coefficient
        # `None` is "the component has no variableType", which fbc writes as
        # an absent attribute; the tested value is `is not None`, since
        # `libsbml.FBC_VARIABLE_TYPE_LINEAR` is `0` and falsy
        self.variableType = (
            FluxObjective.normalize_variable_type(variableType)
            if variableType is not None
            else None
        )

    def create_sbml(
        self,
        constraint: libsbml.UserDefinedConstraint,
        model: libsbml.Model,
    ) -> libsbml.UserDefinedConstraintComponent:
        """Create the libsbml.UserDefinedConstraintComponent in the constraint.

        Args:
            constraint: the libsbml.UserDefinedConstraint the component
                belongs to
            model: the libsbml.Model the constraint is created in, which the
                fields of the component are written with; handed down, never
                looked up, see `Model._fill_sbml`

        Returns:
            the created libsbml.UserDefinedConstraintComponent
        """
        component: libsbml.UserDefinedConstraintComponent = (
            constraint.createUserDefinedConstraintComponent()
        )
        self._set_fields(component, model)
        self.create_port(model)

        check(component.setVariable(self.variable), f"set variable `{self.variable}`")
        check(
            component.setCoefficient(self.coefficient),
            f"set coefficient `{self.coefficient}`",
        )
        if self.variableType is not None:
            _set_variable_type(component, self.variableType, self)

        return component


class UserDefinedConstraint(Sbase):
    """UserDefinedConstraint.

    The FBC UserDefinedConstraint class is derived from SBML SBase and inherits
    metaid and sboTerm, as well as the subcomponents for Annotation and Notes.
    It’s purpose is to define non-stoichiometric constraints, that is
    constraints that are not necessarily defined by the stoichiometrically coupled
    reaction network. In order to achieve, we defined a new type of linear
    constraint, the UserDefinedConstraint

    libsbml attaches no `CompSBasePlugin` to an
    `<fbc:userDefinedConstraint>`, so a `replacedBy` is not offered, see
    `Sbase.create_replaced_by`.
    """

    def __init__(
        self,
        lowerBound: str,
        upperBound: str,
        components: list[UserDefinedConstraintComponent] | dict[str, str] | None = None,
        variableType: str | None = libsbml.FBC_VARIABLE_TYPE_LINEAR,
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
        """Create an UserDefinedConstraint."""
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
        self.lowerBound = lowerBound
        self.upperBound = upperBound

        # normalize components
        self.components: list[UserDefinedConstraintComponent] = []
        if components:
            if isinstance(components, dict):
                # create FluxObjectives from dict
                for variable, coefficient in components.items():
                    self.components.append(
                        UserDefinedConstraintComponent(
                            variable=variable,
                            coefficient=coefficient,
                            variableType=variableType,
                        )
                    )
            else:
                for component in components:
                    # infer variableType from the constraint; a component
                    # which states one keeps it, `libsbml.
                    # FBC_VARIABLE_TYPE_LINEAR` included, which is `0`
                    if component.variableType is None:
                        component.variableType = variableType
                    self.components.append(component)

    def create_sbml(self, model: libsbml.Model) -> libsbml.UserDefinedConstraint | None:
        """Create the libsbml.UserDefinedConstraint in the model.

        An `<fbc:userDefinedConstraint>` is fbc **version 3**. In an fbc
        version 2 document libsbml creates the element and answers every one
        of `setUpperBound`, `setLowerBound`, `setVariable`, `setCoefficient`
        and `setVariableType` with `LIBSBML_UNEXPECTED_ATTRIBUTE`, so all
        that would be written is an empty `<fbc:userDefinedConstraint/>`,
        which is invalid. Such a document is reported once for the constraint
        and gets no element, the way a key-value pair is refused, see
        `_fbc_version_allows`.

        Args:
            model: the libsbml.Model the constraint is created in

        Returns:
            the created constraint, `None` if the fbc version of the document
            cannot carry one
        """
        model_fbc: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
        if not _fbc_version_allows(model_fbc, 3, "user defined constraint(s)", 1, self):
            return None
        if model_fbc is None:
            # not reachable: a document without an fbc plugin is one of the
            # cases `_fbc_version_allows` refuses. Spelled out rather than
            # asserted, which `python -O` removes, so that the plugin is
            # known not to be `None` below
            return None

        udc: libsbml.UserDefinedConstraint = model_fbc.createUserDefinedConstraint()
        self._set_fields(udc, model)
        self.create_port(model)
        _check_attribute(
            udc.setUpperBound(self.upperBound),
            udc,
            "upperBound",
            self.upperBound,
            self,
        )
        _check_attribute(
            udc.setLowerBound(self.lowerBound),
            udc,
            "lowerBound",
            self.lowerBound,
            self,
        )
        for component in self.components:
            component.create_sbml(constraint=udc, model=model)

        return udc


class FluxObjective(Sbase):
    """FluxObjective.

    libsbml attaches no `CompSBasePlugin` to an `<fbc:fluxObjective>`, so a
    `replacedBy` is not offered, see `Sbase.create_replaced_by`.
    """

    fbc_variable_types: ClassVar[set[str]] = {
        libsbml.FBC_VARIABLE_TYPE_LINEAR,
        libsbml.FBC_VARIABLE_TYPE_QUADRATIC,
        libsbml.FBC_VARIABLE_TYPE_INVALID,
        "linear",
        "quadratic",
        "invalid",
    }

    def __init__(
        self,
        reaction: str,
        coefficient: float,
        variableType: str | None = None,
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
        """Create a FluxObjective."""
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
        self.reaction = reaction
        self.coefficient = coefficient
        # `None` is "the flux objective has no variableType", which fbc writes
        # as an absent attribute; the tested value is `is not None`, since
        # `libsbml.FBC_VARIABLE_TYPE_LINEAR` is `0` and falsy
        self.variableType = (
            FluxObjective.normalize_variable_type(variableType)
            if variableType is not None
            else None
        )

    @classmethod
    def normalize_variable_type(cls, variable_type: str) -> str:
        """Normalize variable type."""
        if variable_type not in cls.fbc_variable_types:
            raise ValueError(
                f"Unsupported objective type `{variable_type}`. Supported are "
                f"`{FluxObjective.fbc_variable_types}`."
            )

        if variable_type == "linear":
            variable_type = libsbml.FBC_VARIABLE_TYPE_LINEAR
        elif variable_type == "quadratic":
            variable_type = libsbml.FBC_VARIABLE_TYPE_QUADRATIC
        elif variable_type == "invalid":
            variable_type = libsbml.FBC_VARIABLE_TYPE_INVALID
        return variable_type

    def create_sbml(
        self, objective: libsbml.Objective, model: libsbml.Model
    ) -> libsbml.FluxObjective:
        """Create the libsbml.FluxObjective in the objective.

        Args:
            objective: the libsbml.Objective the flux objective belongs to
            model: the libsbml.Model the objective is created in, which the
                fields of the flux objective are written with; handed down,
                never looked up, see `Model._fill_sbml`

        Returns:
            the created libsbml.FluxObjective
        """
        flux_objective: libsbml.FluxObjective = objective.createFluxObjective()
        self._set_fields(flux_objective, model)
        self.create_port(model)

        _check_attribute(
            flux_objective.setReaction(self.reaction),
            flux_objective,
            "reaction",
            self.reaction,
            self,
        )
        # a coefficient is a plain double, which libsbml accepts in every form
        flux_objective.setCoefficient(self.coefficient)
        if self.variableType is not None:
            _set_variable_type(flux_objective, self.variableType, self)

        return flux_objective


class Objective(Sbase):
    """Objective.

    libsbml attaches no `CompSBasePlugin` to an `<fbc:objective>`, so a
    `replacedBy` is not offered, see `Sbase.create_replaced_by`.
    """

    objective_types: ClassVar[set[str]] = {
        libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        libsbml.OBJECTIVE_TYPE_MINIMIZE,
        "maximize",
        "minimize",
        "max",
        "min",
    }

    def __init__(
        self,
        sid: str,
        objectiveType: str = libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        active: bool = True,
        fluxObjectives: list[FluxObjective] | dict[str, float] | None = None,
        variableType: str | None = libsbml.FBC_VARIABLE_TYPE_LINEAR,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Create an Objective.

        FluxObjectives can either be provided as a list of FluxObjectives or as a
        dictionary with the reaction ids as keys and the coefficients as values.
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
        self.objectiveType = self.normalize_objective_type(objectiveType)
        self.active = active

        # normalize fluxObjectives
        self.fluxObjectives: list[FluxObjective] = []
        if fluxObjectives:
            if isinstance(fluxObjectives, dict):
                # create FluxObjectives from dict
                for rid, coefficient in fluxObjectives.items():
                    self.fluxObjectives.append(
                        FluxObjective(
                            reaction=rid,
                            coefficient=coefficient,
                            variableType=variableType,
                        )
                    )
            else:
                for flux_objective in fluxObjectives:
                    # infer variableType from objective; a flux objective
                    # which states one keeps it, `libsbml.
                    # FBC_VARIABLE_TYPE_LINEAR` included, which is `0`
                    if flux_objective.variableType is None:
                        flux_objective.variableType = variableType
                    self.fluxObjectives.append(flux_objective)

    @classmethod
    def normalize_objective_type(cls, objective_type: str) -> str:
        """Normalize objective type."""
        if objective_type not in Objective.objective_types:
            raise ValueError(
                f"Unsupported objective type `{objective_type}`. Supported are "
                f"`{Objective.objective_types}`."
            )
        if objective_type in {"min", "minimize"}:
            objective_type = libsbml.OBJECTIVE_TYPE_MINIMIZE
        elif objective_type in {"max", "maximize"}:
            objective_type = libsbml.OBJECTIVE_TYPE_MAXIMIZE

        return objective_type

    def create_sbml(self, model: libsbml.Model) -> libsbml.Objective:
        """Create Objective.

        An objective whose `active` is set becomes the `activeObjective` of
        the model. The objectives of a model are written in the order they
        are defined in, so of several active ones the last one written wins,
        and a model whose objectives are all inactive gets no active
        objective at all.

        Args:
            model: the libsbml.Model the objective is created in

        Returns:
            the created libsbml.Objective

        Raises:
            ValueError: if the model has no fbc plugin, see `_fbc_plugin`
        """
        model_fbc: libsbml.FbcModelPlugin = _fbc_plugin(
            model, f"The objective '{self}'"
        )
        objective: libsbml.Objective = model_fbc.createObjective()
        self._set_fields(objective, model)
        self.create_port(model)
        # `Objective.normalize_objective_type` refuses every type which is
        # not one libsbml knows, so this cannot fail
        objective.setType(self.objectiveType)
        if self.active:
            _check_attribute(
                model_fbc.setActiveObjectiveId(self.sid),
                model_fbc,
                "activeObjective",
                self.sid,
                self,
            )
        for flux_objective in self.fluxObjectives:
            flux_objective.create_sbml(objective=objective, model=model)

        return objective
