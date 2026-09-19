"""Parse SBML and antimony into the `Model` of `sbmlutils.factory`.

`sbml_to_model` is the inverse of `create_model`. A round trip
`SBML -> sbml_to_model -> create_model -> SBML` preserves SBML core, see
https://github.com/matthiaskoenig/sbmlutils/issues/469. It reads the unit
definitions, the model units and conversionFactor, the function definitions,
compartments, species and parameters, the reactions with their species
references, modifiers and kinetic laws with local parameters, the initial
assignments, rules, events with their trigger, priority, delay and event
assignments, and constraints, and on each of these its id, name, metaid,
sboTerm, notes, annotations and fbc key-value pairs. An element without math,
which SBML allows from L3V2 on, is read without math. It also reads
`fbc:strict` of the model, its gene products and objectives with their flux
objectives, the gene product association of a reaction, as an infix string of
gene product ids, its flux bounds, the charge and chemical formula of a
species, and the user-defined constraints of the model with their components.
A document which declares fbc version 1 is converted to fbc version 2 before
it is read, see `_convert_fbc_v1`.

Not read are the model history, the content of the `distrib`, `comp`, `groups`
and `layout` packages, i.e. uncertainties, submodels, ports and replacements,
and of `fbc` the metadata of a gene product association and of the `and`, `or`
and `geneProductRef` nodes of its association, which the infix string has no
place for, and the fbc version 3 `reaction2` of a flux objective and
`variable2` of a user-defined constraint component, which the factory has no
field for. The `fbc`, `distrib` and `comp` packages a document declares are
declared on the model.
Math is read as an L3 infix string, in which an id named like a MathML
constant or csymbol (`pi`, `INF`, `NaN`, `time`, `avogadro`) cannot be told
apart from the constant, so such an id does not round trip.
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
    Delay,
    Event,
    EventAssignment,
    FluxObjective,
    Function,
    GeneProduct,
    InitialAssignment,
    KeyValuePair,
    KineticLaw,
    LocalParameter,
    Model,
    ModelUnits,
    Objective,
    Package,
    Parameter,
    Priority,
    RateRule,
    Reaction,
    ReactionEquation,
    Species,
    Trigger,
    Unit,
    UnitDefinition,
    UserDefinedConstraint,
    UserDefinedConstraintComponent,
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


def _math(sbase: Any) -> str | None:
    """Get the math of an element as an SBML L3 formula string.

    Args:
        sbase: a libsbml object which has math, e.g. a rule

    Returns:
        the math as an L3 formula string, `None` if the element has no math,
        which SBML allows from L3V2 on
    """
    return libsbml.formulaToL3String(sbase.getMath()) if sbase.isSetMath() else None


def _parse_sbase_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
    """Parse SBase information in dictionary.

    Args:
        sbase: the libsbml.SBase to parse

    Returns:
        the kwargs accepted by `Sbase.__init__`
    """
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
    # https://github.com/matthiaskoenig/sbmlutils/issues/416

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
                    **_parse_sbase_kwargs(kvp),
                )
            )

    kwargs["keyValuePairs"] = kvps
    # notes are the xhtml of the source document; `Sbase._process_notes`
    # detects that and stores them verbatim instead of rendering them
    if d["notes"]:
        kwargs["notes"] = d["notes"]

    return kwargs


def _parse_udef_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
    """Parse SBase information of a UnitDefinition.

    A UnitDefinition has no uncertainties, so that key is removed.

    Args:
        sbase: the libsbml.UnitDefinition to parse

    Returns:
        the kwargs accepted by `UnitDefinition.__init__`
    """
    kwargs = _parse_sbase_kwargs(sbase)
    kwargs.pop("uncertainties", None)
    return kwargs


def _parse_variable_kwargs(sbase: libsbml.SBase) -> dict[str, Any]:
    """Parse SBase information of a Rule, InitialAssignment or similar.

    libsbml aliases `getId`/`isSetId` to the `variable`/`symbol` attribute
    on rules and initial assignments, and to the `variable` attribute on
    an event assignment, so `_parse_sbase_kwargs`'s `sid` is not the real
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
    kwargs = _parse_sbase_kwargs(sbase)
    kwargs["sid"] = sbase.getIdAttribute() if sbase.isSetIdAttribute() else None
    return kwargs


def _charge(species_fbc: libsbml.FbcSpeciesPlugin | None) -> float | None:
    """Get the fbc charge of a species.

    libsbml keeps the integer charge of fbc version 2 and the double charge of
    fbc version 3 apart: it reads and writes only the one of the version of
    the document, and the getter of the other one returns 0. The charge is
    therefore read through the accessor of the version of the plugin, and as
    the same python type the writer needs for it, since
    `FbcSpeciesPlugin.setCharge` dispatches on that type: an `int` sets the
    fbc version 2 charge, a `float` the fbc version 3 one.

    Args:
        species_fbc: the fbc plugin of a species, `None` for a document
            without fbc

    Returns:
        the charge, `None` if the species has none
    """
    if species_fbc is None or not species_fbc.isSetCharge():
        return None
    if species_fbc.getPackageVersion() >= 3:
        charge_double: float = species_fbc.getChargeAsDouble()
        return charge_double
    charge: int = species_fbc.getCharge()
    return charge


def _objective_type(objective: libsbml.Objective) -> str:
    """Get the type of an objective, `maximize` for a document which has none.

    `fbc:type` is required on an objective, so a document without it is
    invalid, and `Objective` has no field for a missing one:
    `Objective.normalize_objective_type` refuses `None` as well as the empty
    string `getType()` returns for an unset attribute. Reading what is there
    is what a parser does, so such an objective is read with the `maximize` of
    the `Objective` default and the problem is logged.

    Args:
        objective: the libsbml.Objective to read

    Returns:
        the type of the objective, `"maximize"` if it has none
    """
    if objective.isSetType():
        objective_type: str = objective.getType()
        return objective_type
    logger.error(
        "Objective '%s' has no 'fbc:type', which fbc requires of every "
        "objective; it is read as 'maximize'.",
        objective.getIdAttribute(),
    )
    return "maximize"


def _variable_type(
    sbase: libsbml.FluxObjective | libsbml.UserDefinedConstraintComponent,
) -> str | None:
    """Get the fbc variableType of a flux objective or a constraint component.

    `variableType` was added in fbc version 3, so it is unset on every fbc
    version 2 document, and an fbc version 3 document which omits it is
    invalid. Either way the element states none, which `FluxObjective` and
    `UserDefinedConstraintComponent` hold as `None` and write as an absent
    attribute: an element read without a variable type is written without one
    rather than being given the `"linear"` the fbc version 3 default implies.

    Args:
        sbase: the flux objective or constraint component to read

    Returns:
        the name of the variable type, `None` if the element has none
    """
    if not sbase.isSetVariableType():
        return None
    variable_type: str = sbase.getVariableTypeAsString()
    return variable_type


def _gene_product_association(
    reaction_fbc: libsbml.FbcReactionPlugin | None,
) -> str | None:
    """Get the gene product association of a reaction as an infix string of ids.

    `Reaction.geneProductAssociation` holds the association as an infix string
    which `Reaction.create_sbml` writes with `setAssociation(infix,
    usingId=True, addMissingGP=False)`, so the string has to name the gene
    products by their id. `FbcAssociation.toInfix(usingId=True)` is the
    accessor of that side; `toInfix()` writes the labels, which are the gene
    names and neither unique nor resolvable as an id.

    Args:
        reaction_fbc: the fbc plugin of a reaction, `None` for a document
            without fbc

    Returns:
        the association as an infix string of gene product ids, `None` if the
        reaction has no association, or one without an `and`, `or` or
        `geneProductRef` child
    """
    if reaction_fbc is None or not reaction_fbc.isSetGeneProductAssociation():
        return None
    gpa: libsbml.GeneProductAssociation = reaction_fbc.getGeneProductAssociation()
    if not gpa.isSetAssociation():
        return None
    association: libsbml.FbcAssociation = gpa.getAssociation()
    infix: str = association.toInfix(True)
    return infix


def _parse_fbc_model(model_fbc: libsbml.FbcModelPlugin, m: Model) -> None:
    """Parse the fbc content of a model itself into an already constructed `Model`.

    This is what the fbc plugin of a model carries: `fbc:strict`, the gene
    products, the objectives with their flux objectives and which of them is
    active, and the user-defined constraints of fbc version 3 with their
    components. The fbc content of a species, of a reaction and of any element
    with key-value pairs belongs to those elements and is read where they are.

    Args:
        model_fbc: the fbc plugin of a libsbml.Model or libsbml.ModelDefinition
        m: the `Model` to populate
    """
    # `fbc:strict`. A model which does not state it leaves `m.strict` at
    # `None`, which is written as `fbc:strict="false"`, the weakest claim:
    # that is the case for a document which declared fbc version 1, whose
    # `strict` `_convert_fbc_v1` unsets again, since claiming `true` for a
    # model which never said so makes every `constant="false"` species
    # reference of it an error (libsbml 2020714).
    if model_fbc.isSetStrict():
        m.strict = model_fbc.getStrict()

    # the gene products, which the associations of the reactions reference by
    # id; `Model._create_sbml` creates them before the reactions, so that
    # `Reaction.geneProductAssociation` resolves every id it names
    gene_product: libsbml.GeneProduct
    for gene_product in model_fbc.getListOfGeneProducts():
        m.gene_products.append(
            GeneProduct(
                label=gene_product.getLabel(),
                associatedSpecies=(
                    gene_product.getAssociatedSpecies()
                    if gene_product.isSetAssociatedSpecies()
                    else None
                ),
                **_parse_sbase_kwargs(gene_product),
            )
        )

    # fbc objectives; `active` is not an attribute of an objective, it is
    # the `activeObjective` of the list, which names at most one of them
    objectives: libsbml.ListOfObjectives = model_fbc.getListOfObjectives()
    active: str | None = (
        objectives.getActiveObjective() if objectives.isSetActiveObjective() else None
    )
    objective: libsbml.Objective
    for objective in objectives:
        flux_objectives: list[FluxObjective] = []
        flux_objective: libsbml.FluxObjective
        for flux_objective in objective.getListOfFluxObjectives():
            flux_objectives.append(
                FluxObjective(
                    reaction=flux_objective.getReaction(),
                    coefficient=flux_objective.getCoefficient(),
                    variableType=_variable_type(flux_objective),
                    **_parse_sbase_kwargs(flux_objective),
                )
            )
        m.objectives.append(
            Objective(
                objectiveType=_objective_type(objective),
                active=objective.getIdAttribute() == active,
                fluxObjectives=flux_objectives,
                # every flux objective carries the variableType of the
                # document, so none of them is to be given the authoring
                # default of the objective
                variableType=None,
                **_parse_sbase_kwargs(objective),
            )
        )

    # fbc user-defined constraints, added in fbc version 3
    constraint_fbc: libsbml.UserDefinedConstraint
    for constraint_fbc in model_fbc.getListOfUserDefinedConstraints():
        components: list[UserDefinedConstraintComponent] = []
        component: libsbml.UserDefinedConstraintComponent
        for component in constraint_fbc.getListOfUserDefinedConstraintComponents():
            components.append(
                UserDefinedConstraintComponent(
                    coefficient=component.getCoefficient(),
                    variable=component.getVariable(),
                    variableType=_variable_type(component),
                    **_parse_sbase_kwargs(component),
                )
            )
        m.user_defined_constraints.append(
            UserDefinedConstraint(
                lowerBound=constraint_fbc.getLowerBound(),
                upperBound=constraint_fbc.getUpperBound(),
                components=components,
                # as above, every component carries its own
                variableType=None,
                **_parse_sbase_kwargs(constraint_fbc),
            )
        )


def _parse_model_body(model: libsbml.Model, m: Model) -> None:
    """Parse the body of a model into an already constructed `Model`.

    Populates `m` with everything `sbml_to_model` parses from `model`: unit
    definitions, model units, function definitions, compartments, species,
    parameters, reactions with kinetic laws, initial assignments, rules,
    events and constraints, with the gene product association and the flux
    bounds of a reaction and the charge and chemical formula of a species, and
    the fbc content of the model itself, see `_parse_fbc_model`. `model` can
    be any `libsbml.Model`, including a `libsbml.ModelDefinition`, which
    subclasses it, so the comp package can recurse into a model definition
    with the same parser.

    Args:
        model: the libsbml.Model, or libsbml.ModelDefinition, to parse
        m: the `Model` to populate; already constructed, with its own
            `Sbase` fields, `parsed`, `packages` and `conversionFactor` set
    """
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
        m.units.append(UnitDefinition(units=units, **_parse_udef_kwargs(udef)))

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
        m.functions.append(Function(value=_math(fd), **_parse_sbase_kwargs(fd)))

    p: libsbml.Parameter
    for p in model.getListOfParameters():
        d = _parse_sbase_kwargs(p)
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
                # SBML declares spatialDimensions a double from L3 on, and
                # `getSpatialDimensions` is the accessor of the unsigned
                # integer attribute of L2, which returns 0 for a value which
                # is not integral, e.g. the 2.7 of test suite case 01310
                spatialDimensions=(
                    c.getSpatialDimensionsAsDouble()
                    if c.isSetSpatialDimensions()
                    else None
                ),
                unit=c.getUnits() if c.isSetUnits() else None,
                **_parse_sbase_kwargs(c),
            )
        )

    s: libsbml.Species
    for s in model.getListOfSpecies():
        species_fbc: libsbml.FbcSpeciesPlugin | None = s.getPlugin("fbc")
        m.species.append(
            Species(
                charge=_charge(species_fbc),
                chemicalFormula=(
                    species_fbc.getChemicalFormula()
                    if species_fbc is not None and species_fbc.isSetChemicalFormula()
                    else None
                ),
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
                **_parse_sbase_kwargs(s),
            )
        )

    # reactions
    r: libsbml.Reaction
    formula: str | None

    for r in model.getListOfReactions():
        reaction_fbc: libsbml.FbcReactionPlugin | None = r.getPlugin("fbc")
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
                    **_parse_sbase_kwargs(reactant),
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
                    **_parse_sbase_kwargs(product),
                )
            )
        modifier: libsbml.ModifierSpeciesReference
        for modifier in r.getListOfModifiers():
            if modifier.isSetSpecies():
                equation.modifiers.append(
                    EquationPart(
                        species=modifier.getSpecies(),
                        **_parse_sbase_kwargs(modifier),
                    )
                )

        # kinetic law
        kinetic_law: KineticLaw | None = None
        if r.isSetKineticLaw():
            klaw: libsbml.KineticLaw = r.getKineticLaw()
            local_parameters: list[LocalParameter] = []
            lp: libsbml.LocalParameter
            for lp in klaw.getListOfLocalParameters():
                local_parameters.append(
                    LocalParameter(
                        value=lp.getValue() if lp.isSetValue() else None,
                        unit=lp.getUnits() if lp.isSetUnits() else None,
                        **_parse_sbase_kwargs(lp),
                    )
                )
            kinetic_law = KineticLaw(
                math=_math(klaw),
                local_parameters=local_parameters,
                **_parse_sbase_kwargs(klaw),
            )

        m.reactions.append(
            Reaction(
                equation=equation,
                formula=kinetic_law,
                reversible=r.getReversible() if r.isSetReversible() else None,
                compartment=r.getCompartment() if r.isSetCompartment() else None,
                fast=r.getFast() if r.isSetFast() else False,
                lowerFluxBound=(
                    reaction_fbc.getLowerFluxBound()
                    if reaction_fbc is not None and reaction_fbc.isSetLowerFluxBound()
                    else None
                ),
                upperFluxBound=(
                    reaction_fbc.getUpperFluxBound()
                    if reaction_fbc is not None and reaction_fbc.isSetUpperFluxBound()
                    else None
                ),
                geneProductAssociation=_gene_product_association(reaction_fbc),
                **_parse_sbase_kwargs(r),
            )
        )

    # initial assignment
    ia: libsbml.InitialAssignment
    for ia in model.getListOfInitialAssignments():
        m.assignments.append(
            InitialAssignment(
                symbol=ia.getSymbol(),
                value=_math(ia),
                **_parse_variable_kwargs(ia),
            )
        )

    # rules
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        formula = _math(rule)
        typecode: int = rule.getTypeCode()
        if typecode == libsbml.SBML_ASSIGNMENT_RULE:
            m.rules.append(
                AssignmentRule(
                    variable=rule.getVariable(),
                    value=formula,
                    **_parse_variable_kwargs(rule),
                )
            )
        elif typecode == libsbml.SBML_RATE_RULE:
            m.rate_rules.append(
                RateRule(
                    variable=rule.getVariable(),
                    value=formula,
                    **_parse_variable_kwargs(rule),
                )
            )
        elif typecode == libsbml.SBML_ALGEBRAIC_RULE:
            m.algebraic_rules.append(
                AlgebraicRule(value=formula, **_parse_variable_kwargs(rule))
            )

    # events
    e: libsbml.Event
    for e in model.getListOfEvents():
        # an absent trigger, priority or delay is `None`, one without math is
        # an object whose math is `None`
        trigger: Trigger | None = None
        if e.isSetTrigger():
            t: libsbml.Trigger = e.getTrigger()
            trigger = Trigger(
                math=_math(t),
                initialValue=t.getInitialValue() if t.isSetInitialValue() else True,
                persistent=t.getPersistent() if t.isSetPersistent() else True,
                **_parse_sbase_kwargs(t),
            )
        priority: Priority | None = None
        if e.isSetPriority():
            pr: libsbml.Priority = e.getPriority()
            priority = Priority(math=_math(pr), **_parse_sbase_kwargs(pr))
        delay: Delay | None = None
        if e.isSetDelay():
            de: libsbml.Delay = e.getDelay()
            delay = Delay(math=_math(de), **_parse_sbase_kwargs(de))

        assignments: list[EventAssignment] = []
        ea: libsbml.EventAssignment
        for ea in e.getListOfEventAssignments():
            assignments.append(
                EventAssignment(
                    variable=ea.getVariable(),
                    value=_math(ea),
                    **_parse_variable_kwargs(ea),
                )
            )

        m.events.append(
            Event(
                trigger=trigger,
                assignments=assignments,
                useValuesFromTriggerTime=(
                    e.getUseValuesFromTriggerTime()
                    if e.isSetUseValuesFromTriggerTime()
                    else True
                ),
                priority=priority,
                delay=delay,
                **_parse_sbase_kwargs(e),
            )
        )

    # constraints
    constraint: libsbml.Constraint
    for constraint in model.getListOfConstraints():
        m.constraints.append(
            Constraint(
                math=_math(constraint),
                message=(
                    constraint.getMessageString() if constraint.isSetMessage() else None
                ),
                **_parse_sbase_kwargs(constraint),
            )
        )

    # fbc, on the plugin of this `model` rather than on one passed in by
    # `sbml_to_model`: the fbc model plugin attaches to a comp
    # `ModelDefinition` as well, which a later task parses by recursing into
    # this function
    model_fbc: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
    if model_fbc is not None:
        _parse_fbc_model(model_fbc, m)

    # the content of the distrib, comp, groups and layout packages is not
    # parsed yet, see the module docstring


def _convert_fbc_v1(doc: libsbml.SBMLDocument) -> None:
    """Convert a document which declares fbc version 1 to fbc version 2, in place.

    fbc version 1 states a flux bound as an `fbc:fluxBound` element of the
    model, which names its reaction, its operation and its value; from fbc
    version 2 on a bound is a parameter which the reaction references. There
    is no `Model` field for the version 1 element, and `create_model` writes
    fbc version 2 or 3 in any case, so the document is brought to the version
    which is written before it is read, by libsbml's own converter: every
    bound becomes a parameter of the generated id `fb_<reaction>_<operation>`
    which carries its value. This is the same conversion the structural
    comparison of the round trip applies, see the docstring of
    `tests/structural.py`.

    The converter also sets `fbc:strict="true"`, which is an attribute fbc
    version 1 does not have and a claim the source never made. It is unset
    again on every model of the document, so that the model is read without a
    `strict` and written as `fbc:strict="false"`: a strict model requires the
    `constant` attribute of every species reference to be `true`, which turns
    11 of the 12 fbc version 1 cases of the SBML test suite from valid into
    invalid, 54 errors of libsbml 2020714 each, and a round trip must not
    turn a valid model into an invalid one.

    The whole document is converted, so a `comp:modelDefinition` of it is read
    as fbc version 2 as well, and its invented `strict` is unset as well.

    Args:
        doc: the SBMLDocument to convert, which the caller owns; a document
            which does not declare fbc version 1 is not touched

    Raises:
        ValueError: if libsbml cannot convert the document
    """
    fbc: libsbml.SBMLDocumentPlugin | None = doc.getPlugin("fbc")
    if fbc is None or fbc.getPackageVersion() != 1:
        return

    properties = libsbml.ConversionProperties()
    properties.addOption("convert fbc v1 to fbc v2", True)
    status: int = doc.convert(properties)
    if status != libsbml.LIBSBML_OPERATION_SUCCESS:
        raise ValueError(f"libsbml cannot convert fbc v1 to fbc v2: {status}")

    # every model of the document, which is the model and every comp model
    # definition; `getListOfAllElements` yields both
    element: libsbml.SBase
    for element in doc.getListOfAllElements():
        element_fbc: libsbml.SBasePlugin | None = element.getPlugin("fbc")
        if isinstance(element_fbc, libsbml.FbcModelPlugin):
            element_fbc.unsetStrict()


def sbml_to_model(
    source: Path | str,
    validate: bool = False,
    promote: bool = False,
    validation_options: ValidationOptions | None = None,
) -> Model:
    """Parse an SBML document into the `Model` of `sbmlutils.factory`, see the module docstring.

    Args:
        source: an SBML file path, an SBML string, or a URL, passed through
            to `sbmlutils.io.sbml.read_sbml`
        validate: whether to validate the document while reading it
        promote: whether to promote local parameters to global parameters
        validation_options: which validation checks to run, only used when
            `validate` is `True`

    Returns:
        the parsed `Model`, with `parsed` set to `True` so that it is
        written back out without the authoring hints of a model definition

    Raises:
        AttributeError: if `source` has no model; `read_sbml` only logs that
            case, it does not raise
        ValueError: if the document declares fbc version 1 and libsbml cannot
            convert it to fbc version 2
    """
    doc: libsbml.SBMLDocument = read_sbml(
        source=source,
        promote=promote,
        validate=validate,
        validation_options=validation_options,
    )
    # validation above reports on the document as it was given; the conversion
    # of fbc version 1 changes the document, so it comes after it
    _convert_fbc_v1(doc)
    model: libsbml.Model = doc.getModel()

    if not model:
        logger.error("No model in SBMLDocument.")

    m = Model(**_parse_sbase_kwargs(model))
    # a parsed model carries whatever the source file had, so the authoring
    # hints of `Sbase._set_fields` are noise when it is written back out
    m.parsed = True
    m.packages = _packages_of_document(doc)
    m.conversionFactor = (
        model.getConversionFactor() if model.isSetConversionFactor() else None
    )

    _parse_model_body(model, m)

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
