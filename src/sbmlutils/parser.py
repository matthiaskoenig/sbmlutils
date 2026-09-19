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
`fbc:strict` of the model.

Not read are the model history, and the rest of the content of the `fbc`,
`distrib`, `comp`, `groups` and `layout` packages: flux bounds, objectives and
gene products, uncertainties, submodels, ports and replacements. The `fbc`,
`distrib` and `comp` packages a document declares are declared on the model.
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
    Function,
    InitialAssignment,
    KeyValuePair,
    KineticLaw,
    LocalParameter,
    Model,
    ModelUnits,
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


def _parse_model_body(model: libsbml.Model, m: Model) -> None:
    """Parse the body of a model into an already constructed `Model`.

    Populates `m` with everything `sbml_to_model` parses from `model`: unit
    definitions, model units, function definitions, compartments, species,
    parameters, reactions with kinetic laws, initial assignments, rules,
    events, constraints and `fbc:strict`. `model` can be any `libsbml.Model`,
    including a `libsbml.ModelDefinition`, which subclasses it, so the comp
    package can recurse into a model definition with the same parser.

    Args:
        model: the libsbml.Model, or libsbml.ModelDefinition, to parse
        m: the `Model` to populate; already constructed, with its own
            `Sbase` fields, `parsed`, `packages` and `conversionFactor` set
    """
    # fbc:strict, read from the fbc plugin of this `model` rather than
    # passed in by `sbml_to_model`: the fbc model plugin attaches to a comp
    # `ModelDefinition` as well, which a later task parses by recursing into
    # this function, so `m.strict` has to be set from whichever plugin this
    # call was given. fbc version 1 has no `strict` attribute at all
    # (`isSetStrict()` is always `False`), and `_packages_of_document`
    # already upgrades it to `Package.FBC_V2` on the round trip, so it is
    # read here as `True`: fbc version 1 has no notion of a non-strict
    # model, and libsbml's own "convert fbc v1 to fbc v2" converter sets
    # `fbc:strict="true"` unconditionally on every v1 document, flux bounds
    # or not (measured on an otherwise empty model), which is the version
    # `tests/structural.py` compares a v1 document as, see its module
    # docstring.
    model_fbc: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
    if model_fbc is not None:
        if model_fbc.isSetStrict():
            m.strict = model_fbc.getStrict()
        elif model_fbc.getPackageVersion() == 1:
            m.strict = True

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
                **_parse_sbase_kwargs(s),
            )
        )

    # reactions
    r: libsbml.Reaction
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

    # the content of the fbc, distrib, comp, groups and layout packages is not
    # parsed yet, see the module docstring


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
    """
    doc: libsbml.SBMLDocument = read_sbml(
        source=source,
        promote=promote,
        validate=validate,
        validation_options=validation_options,
    )
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
