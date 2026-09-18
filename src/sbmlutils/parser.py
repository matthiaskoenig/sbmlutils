"""Parse Models in internal model format.

FIXME: no support for modelHistory

"""

import logging
from pathlib import Path
from typing import Any

import antimony
import libsbml
from pymetadata.omex import ManifestEntry, Omex

from sbmlutils.console import console
from sbmlutils.factory import (
    AlgebraicRule,
    AssignmentRule,
    Compartment,
    Constraint,
    Event,
    EventAssignment,
    Function,
    InitialAssignment,
    KeyValuePair,
    KineticLaw,
    LocalParameter,
    Model,
    ModelUnits,
    Package,
    Parameter,
    RateRule,
    Reaction,
    ReactionEquation,
    Species,
    Unit,
    UnitDefinition,
    create_model,
)
from sbmlutils.io.sbml import read_sbml
from sbmlutils.metadata import BQB, BQM
from sbmlutils.reaction_equation import EquationPart
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo
from sbmlutils.validation import ValidationOptions

logger = logging.getLogger(__name__)


def antimony_to_sbml(
    source: Path | str,
) -> str:
    """Parse antimony model to SBML string."""
    status: int
    if isinstance(source, str) and "model" in source:
        status = antimony.loadAntimonyString(source)
    else:
        if not isinstance(source, Path):
            logger.error(
                "All antimony paths should be of type 'Path', but '%s' found for: %s",
                type(source),
                source,
            )
            source = Path(source)

        status = antimony.loadAntimonyFile(str(source))

    # log errors
    if status != -1:
        logger.error("Antimony status: %s", status)
        logger.error(antimony.getLastError())
        # antimony.getSBMLWarnings()

    sbml_str: str = antimony.getSBMLString()

    return sbml_str


def antimony_to_model(
    source: Path | str,
    validate: bool = False,
    promote: bool = False,
    validation_options: ValidationOptions | None = None,
) -> Model:
    """Parse antimony model."""
    sbml_str = antimony_to_sbml(
        source=source,
    )

    return sbml_to_model(
        source=sbml_str,
        validate=validate,
        promote=promote,
        validation_options=validation_options,
    )


# TODO: validation & validation options

#: the package prefix of a document mapped to the `Package` of sbmlutils
_PACKAGE_FOR_PREFIX: dict[str, Package] = {
    "comp": Package.COMP_V1,
    "distrib": Package.DISTRIB_V1,
}


def _packages_of_document(doc: libsbml.SBMLDocument) -> list[Package]:
    """Determine the SBML packages a document declares.

    Args:
        doc: the SBMLDocument to inspect

    Returns:
        the packages of the document which sbmlutils supports
    """
    packages: list[Package] = []
    for k in range(doc.getNumPlugins()):
        plugin: libsbml.SBasePlugin = doc.getPlugin(k)
        prefix: str = plugin.getPrefix()
        if prefix == "fbc":
            version: int = plugin.getPackageVersion()
            packages.append(Package.FBC_V3 if version >= 3 else Package.FBC_V2)
        elif prefix in _PACKAGE_FOR_PREFIX:
            packages.append(_PACKAGE_FOR_PREFIX[prefix])
    return packages


def sbml_to_model(
    source: Path | str,
    validate: bool = False,
    promote: bool = False,
    validation_options: ValidationOptions | None = None,
) -> Model:
    """Parse SBML model."""
    doc: libsbml.SBMLDocument = read_sbml(
        source=source,
        promote=promote,
        validate=validate,
        validation_options=validation_options,
    )
    model: libsbml.Model = doc.getModel()

    def parse_sbase_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
        """Parse SBase information in dictionary."""
        # the sboTerm is already carried by the `sboTerm` kwarg below; a real
        # CVTerm must not be synthesized for it, or a round trip would turn the
        # sboTerm attribute into a duplicated annotation, see
        # https://github.com/matthiaskoenig/sbmlutils/issues/469
        d = SBMLDocumentInfo.sbase_dict(sbase, include_sbo_cvterm=False)
        kwargs = {
            "sid": d["id"],
            "name": d["name"],
            "metaId": d["metaId"],
            "sboTerm": d["sbo"],
            "annotations": [],
        }

        # annotations
        if d["cvterms"]:
            for cvterm in d["cvterms"]:
                qualifier_str = cvterm["qualifier"]
                qualifier: BQB | BQM
                if qualifier_str.startswith("BQB_"):
                    qualifier = BQB.__getitem__(qualifier_str[4:])
                elif qualifier_str.startswith("BQM_"):
                    qualifier = BQM.__getitem__(qualifier_str[4:])

                for resource in cvterm["resources"]:
                    kwargs["annotations"].append((qualifier, resource))

        # model history
        # FIXME: currently not supported consistently, see
        # https: // github.com / matthiaskoenig / sbmlutils / issues / 416

        # notes
        # FIXME: support merging of notes, see

        # keyValuePairs
        sbase_fbc: libsbml.FbcSBasePlugin = sbase.getPlugin("fbc")
        kvps: list[KeyValuePair] = []
        if sbase_fbc:
            kvp: libsbml.KeyValuePair
            for kvp in sbase_fbc.getListOfKeyValuePairs():
                kvps.append(
                    KeyValuePair(
                        key=kvp.getKey(),
                        value=kvp.getValue(),
                        uri=kvp.getUri() if kvp.isSetUri() else None,
                        **parse_sbase_kwargs(kvp),
                    )
                )

        kwargs["keyValuePairs"] = kvps
        # notes are the xhtml of the source document; `Sbase._process_notes`
        # detects that and stores them verbatim instead of rendering them
        if d["notes"]:
            kwargs["notes"] = d["notes"]

        return kwargs

    def parse_udef_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
        """Parse SBase information of a UnitDefinition.

        A UnitDefinition has no uncertainties, so that key is removed.

        Args:
            sbase: the libsbml.UnitDefinition to parse

        Returns:
            the kwargs accepted by `UnitDefinition.__init__`
        """
        kwargs = parse_sbase_kwargs(sbase)
        kwargs.pop("uncertainties", None)
        return kwargs

    def parse_variable_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
        """Parse SBase information of a Rule, InitialAssignment or similar.

        libsbml aliases `getId`/`isSetId` to the `variable`/`symbol` attribute
        on rules and initial assignments, and to the `variable` attribute on
        an event assignment, so `parse_sbase_kwargs`'s `sid` is not the real
        id: it reports the variable name whether or not the source XML
        actually carried an id attribute. Passing it through would resurrect
        it as a real, separately-declared SId on the round trip, which then
        collides with the variable's own element (a compartment, species or
        parameter of that same id). `isSetIdAttribute` is the accessor which
        reflects the actual L3 core `id` attribute.

        Args:
            sbase: the libsbml Rule, InitialAssignment, AlgebraicRule or
                EventAssignment to parse

        Returns:
            the kwargs accepted by the corresponding `Sbase` subclass, with
            `sid` set from the real id attribute, `None` if the source did
            not set one. `sid` is a required key even when its value is
            `None`: `AlgebraicRule.__init__` takes it as a required
            parameter, so it must not be popped from the kwargs.
        """
        kwargs = parse_sbase_kwargs(sbase)
        kwargs["sid"] = sbase.getIdAttribute() if sbase.isSetIdAttribute() else None
        return kwargs

    if not model:
        logger.error("No model in SBMLDocument.")

    m = Model(**parse_sbase_kwargs(model))
    # a parsed model carries whatever the source file had, so the authoring
    # hints of `Sbase._set_fields` are noise when it is written back out
    m.parsed = True
    m.packages = _packages_of_document(doc)
    m.conversionFactor = (
        model.getConversionFactor() if model.isSetConversionFactor() else None
    )

    # unit definitions
    udef: libsbml.UnitDefinition
    for udef in model.getListOfUnitDefinitions():
        units: list[Unit] = []
        u: libsbml.Unit
        for u in udef.getListOfUnits():
            units.append(
                Unit(
                    kind=libsbml.UnitKind_toString(u.getKind()),
                    exponent=u.getExponent() if u.isSetExponent() else 1.0,
                    scale=u.getScale() if u.isSetScale() else 0,
                    multiplier=u.getMultiplier() if u.isSetMultiplier() else 1.0,
                )
            )
        m.units.append(UnitDefinition(units=units, **parse_udef_kwargs(udef)))

    # model units
    m.model_units = ModelUnits(
        time=model.getTimeUnits() if model.isSetTimeUnits() else None,
        extent=model.getExtentUnits() if model.isSetExtentUnits() else None,
        substance=model.getSubstanceUnits() if model.isSetSubstanceUnits() else None,
        length=model.getLengthUnits() if model.isSetLengthUnits() else None,
        area=model.getAreaUnits() if model.isSetAreaUnits() else None,
        volume=model.getVolumeUnits() if model.isSetVolumeUnits() else None,
    )

    # function definitions
    fd: libsbml.FunctionDefinition
    for fd in model.getListOfFunctionDefinitions():
        ast = fd.getMath() if fd.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        if formula:
            m.functions.append(Function(value=formula, **parse_sbase_kwargs(fd)))

    p: libsbml.Parameter
    for p in model.getListOfParameters():
        d = parse_sbase_kwargs(p)
        # print(d)
        m.parameters.append(
            Parameter(
                value=p.getValue() if p.isSetValue() else None,
                unit=p.getUnits() if p.isSetUnits() else None,
                constant=p.getConstant() if p.isSetConstant() else True,
                **d,
            )
        )

    c: libsbml.Compartment
    for c in model.getListOfCompartments():
        m.compartments.append(
            Compartment(
                value=c.getSize() if c.isSetSize() else None,
                constant=c.getConstant() if c.isSetConstant() else True,
                spatialDimensions=(
                    c.getSpatialDimensions() if c.isSetSpatialDimensions() else None
                ),
                unit=c.getUnits() if c.isSetUnits() else None,
                **parse_sbase_kwargs(c),
            )
        )

    s: libsbml.Species
    for s in model.getListOfSpecies():
        m.species.append(
            Species(
                compartment=s.getCompartment(),
                initialAmount=s.getInitialAmount() if s.isSetInitialAmount() else None,
                initialConcentration=(
                    s.getInitialConcentration()
                    if s.isSetInitialConcentration()
                    else None
                ),
                constant=s.getConstant() if s.isSetConstant() else False,
                hasOnlySubstanceUnits=(
                    s.getHasOnlySubstanceUnits()
                    if s.isSetHasOnlySubstanceUnits()
                    else False
                ),
                boundaryCondition=(
                    s.getBoundaryCondition() if s.isSetBoundaryCondition() else False
                ),
                substanceUnit=(
                    s.getSubstanceUnits() if s.isSetSubstanceUnits() else None
                ),
                conversionFactor=(
                    s.getConversionFactor() if s.isSetConversionFactor() else None
                ),
                **parse_sbase_kwargs(s),
            )
        )

    # reactions
    r: libsbml.Reaction
    ast: libsbml.ASTNode | None
    formula: str | None

    for r in model.getListOfReactions():
        equation = ReactionEquation(
            reversible=r.getReversible() if r.isSetReversible() else True
        )
        reactant: libsbml.SpeciesReference
        for reactant in r.getListOfReactants():
            equation.reactants.append(
                EquationPart(
                    species=reactant.getSpecies(),
                    stoichiometry=(
                        reactant.getStoichiometry()
                        if reactant.isSetStoichiometry()
                        else None
                    ),
                    constant=(
                        reactant.getConstant() if reactant.isSetConstant() else True
                    ),
                    **parse_sbase_kwargs(reactant),
                )
            )
            product: libsbml.SpeciesReference
        for product in r.getListOfProducts():
            equation.products.append(
                EquationPart(
                    species=product.getSpecies(),
                    stoichiometry=(
                        product.getStoichiometry()
                        if product.isSetStoichiometry()
                        else None
                    ),
                    constant=product.getConstant() if product.isSetConstant() else True,
                    **parse_sbase_kwargs(product),
                )
            )
        modifier: libsbml.ModifierSpeciesReference
        for modifier in r.getListOfModifiers():
            if modifier.isSetSpecies():
                equation.modifiers.append(
                    EquationPart(
                        species=modifier.getSpecies(),
                        **parse_sbase_kwargs(modifier),
                    )
                )

        # kinetic law
        kinetic_law: KineticLaw | None = None
        if r.isSetKineticLaw():
            klaw: libsbml.KineticLaw = r.getKineticLaw()
            ast = klaw.getMath() if klaw.isSetMath() else None
            math = libsbml.formulaToL3String(ast) if ast else None
            if math:
                local_parameters: list[LocalParameter] = []
                lp: libsbml.LocalParameter
                for lp in klaw.getListOfLocalParameters():
                    local_parameters.append(
                        LocalParameter(
                            value=lp.getValue() if lp.isSetValue() else None,
                            unit=lp.getUnits() if lp.isSetUnits() else None,
                            **parse_sbase_kwargs(lp),
                        )
                    )
                kinetic_law = KineticLaw(
                    math=math,
                    local_parameters=local_parameters,
                    **parse_sbase_kwargs(klaw),
                )

        m.reactions.append(
            Reaction(
                equation=equation,
                formula=kinetic_law,
                reversible=r.getReversible() if r.isSetReversible() else None,
                compartment=r.getCompartment() if r.isSetCompartment() else None,
                fast=r.getFast() if r.isSetFast() else False,
                **parse_sbase_kwargs(r),
            )
        )

    # initial assignment
    ia: libsbml.InitialAssignment
    for ia in model.getListOfInitialAssignments():
        ast = ia.getMath() if ia.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        if formula:
            m.assignments.append(
                InitialAssignment(
                    symbol=ia.getSymbol(),
                    value=formula,
                    **parse_variable_kwargs(ia),
                )
            )

    # rules
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        ast = rule.getMath() if rule.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        typecode: int = rule.getTypeCode()
        if formula:
            if typecode == libsbml.SBML_ASSIGNMENT_RULE:
                m.rules.append(
                    AssignmentRule(
                        variable=rule.getVariable(),
                        value=formula,
                        **parse_variable_kwargs(rule),
                    )
                )
            elif typecode == libsbml.SBML_RATE_RULE:
                m.rate_rules.append(
                    RateRule(
                        variable=rule.getVariable(),
                        value=formula,
                        **parse_variable_kwargs(rule),
                    )
                )
            elif typecode == libsbml.SBML_ALGEBRAIC_RULE:
                m.algebraic_rules.append(
                    AlgebraicRule(value=formula, **parse_variable_kwargs(rule))
                )

    # events
    k: int
    e: libsbml.Event
    for k, e in enumerate(model.getListOfEvents()):
        trigger: libsbml.Trigger | None = e.getTrigger() if e.isSetTrigger() else None
        if trigger is None or not trigger.isSetMath():
            logger.error("Event '%s' has no trigger, it is skipped.", e.getId())
            continue

        assignments: list[EventAssignment] = []
        ea: libsbml.EventAssignment
        for ea in e.getListOfEventAssignments():
            ast = ea.getMath() if ea.isSetMath() else None
            value = libsbml.formulaToL3String(ast) if ast else None
            if value is not None:
                assignments.append(
                    EventAssignment(
                        variable=ea.getVariable(),
                        value=value,
                        **parse_variable_kwargs(ea),
                    )
                )

        priority_ast = (
            e.getPriority().getMath()
            if e.isSetPriority() and e.getPriority().isSetMath()
            else None
        )
        delay_ast = (
            e.getDelay().getMath()
            if e.isSetDelay() and e.getDelay().isSetMath()
            else None
        )

        event_kwargs = parse_sbase_kwargs(e)
        if event_kwargs["sid"] is None:
            # `Event.__init__` requires `sid` as a `str`; the SBML L2/L3
            # event id is in practice always set, but is formally optional,
            # so a deterministic fallback stands in for a missing one rather
            # than raising.
            event_kwargs["sid"] = f"event{k}"
        m.events.append(
            Event(
                trigger=libsbml.formulaToL3String(trigger.getMath()),
                assignments=assignments,
                trigger_persistent=(
                    trigger.getPersistent() if trigger.isSetPersistent() else True
                ),
                trigger_initialValue=(
                    trigger.getInitialValue() if trigger.isSetInitialValue() else True
                ),
                useValuesFromTriggerTime=(
                    e.getUseValuesFromTriggerTime()
                    if e.isSetUseValuesFromTriggerTime()
                    else True
                ),
                priority=(
                    libsbml.formulaToL3String(priority_ast) if priority_ast else None
                ),
                delay=libsbml.formulaToL3String(delay_ast) if delay_ast else None,
                **event_kwargs,
            )
        )

    # constraints
    constraint: libsbml.Constraint
    for constraint in model.getListOfConstraints():
        ast = constraint.getMath() if constraint.isSetMath() else None
        formula = libsbml.formulaToL3String(ast) if ast else None
        m.constraints.append(
            Constraint(
                formula=formula,
                message=(
                    constraint.getMessageString() if constraint.isSetMessage() else None
                ),
                **parse_sbase_kwargs(constraint),
            )
        )

    # FIXME:
    # comp
    # ports
    # fbc
    # groups
    # distrib

    return m


if __name__ == "__main__":
    from sbmlutils.resources import BIOMODELS_CURATED_PATH, REPRESSILATOR_SBML

    omex_path: Path = BIOMODELS_CURATED_PATH / "BIOMD0000000003.omex"

    omex = Omex().from_omex(omex_path)
    entry: ManifestEntry
    for entry in omex.manifest.entries:
        if entry.is_sbml():
            sbml_path: Path = omex.get_path(entry.location)

            m = sbml_to_model(REPRESSILATOR_SBML)
            console.print(m)
            create_model(
                model=m,
                filepath=sbml_path,
                sbml_level=3,
                sbml_version=2,
                validation_options=ValidationOptions(units_consistency=False),
            )
            SBMLDocumentInfo.from_sbml(sbml_path)
            model = sbml_to_model(
                source=sbml_path,
                validate=True,
                validation_options=ValidationOptions(units_consistency=False),
            )
