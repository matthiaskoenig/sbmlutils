"""Parse Models in internal model format.

FIXME: no support for notes
FIXME: no support for modelHistory

"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import libsbml

from sbmlutils import RESOURCES_DIR
from sbmlutils.factory import *
from sbmlutils.io.sbml import read_sbml, validate_sbml
from sbmlutils.log import get_logger
from sbmlutils.metadata import BQB, BQM
from sbmlutils.reaction_equation import EquationPart
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo
from sbmlutils.validation import ValidationOptions


logger = get_logger(__name__)


def sbml_to_model(
    source: Union[Path, str],
    validate: bool = False,
    promote: bool = False,
    validation_options: ValidationOptions = ValidationOptions(),
) -> Model:
    """Parse SBML model."""
    doc: libsbml.SBMLDocument = read_sbml(
        source=source,
        promote=promote,
        validate=validate,
        validation_options=validation_options,
    )
    model: libsbml.Model = doc.getModel()

    def parse_sbase_kwargs(sbase: libsbml.SBase) -> Dict[str, Any]:
        """Parse SBase information in dictionary."""
        d = SBMLDocumentInfo.sbase_dict(sbase)
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
                qualifier: Union[BQB, BQM]
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
        kvps: List[KeyValuePair] = []
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
        # if d["notes"]:
        #     kwargs["notes"] = d["notes"]  # This is an XML string.

        return kwargs

    if not model:
        logger.error("No model in SBMLDocument.")

    m = Model(**parse_sbase_kwargs(model))
    # FIXME: parse packages
    m.packages = [Package.FBC_V3]

    p: libsbml.Parameter
    for p in model.getListOfParameters():
        d = parse_sbase_kwargs(p)
        print(d)
        m.parameters.append(
            Parameter(
                value=p.getValue() if p.isSetValue else None,
                # unit=p.getUnits(),
                constant=p.getConstant() if p.isSetConstant() else None,
                **d,
            )
        )

    c: libsbml.Compartment
    for c in model.getListOfCompartments():
        m.compartments.append(
            Compartment(
                value=c.getSize() if c.isSetSize() else None,
                constant=c.getConstant() if c.isSetConstant() else None,
                spatialDimensions=c.getSpatialDimensions()
                if c.isSetSpatialDimensions()
                else None,
                # unit=p.getUnits(),
                **parse_sbase_kwargs(c),
            )
        )

    s: libsbml.Species
    for s in model.getListOfSpecies():
        m.species.append(
            Species(
                compartment=s.getCompartment() if s.isSetCompartment() else None,
                initialAmount=s.getInitialAmount() if s.isSetInitialAmount() else None,
                initialConcentration=s.getInitialConcentration()
                if s.isSetInitialConcentration()
                else None,
                constant=s.getConstant() if s.isSetConstant() else None,
                hasOnlySubstanceUnits=s.getHasOnlySubstanceUnits()
                if s.isSetHasOnlySubstanceUnits()
                else None,
                boundaryCondition=s.getBoundaryCondition()
                if s.isSetBoundaryCondition()
                else None,
                # unit=p.getUnits(),
                **parse_sbase_kwargs(s),
            )
        )

    # reactions
    r: libsbml.Reaction
    for r in model.getListOfReactions():

        # FIXME: better equation support.
        equation = ReactionEquation(
            reversible=r.getReversible() if r.isSetReversible() else None
        )
        reactant: libsbml.SpeciesReference
        for reactant in r.getListOfReactants():
            equation.reactants.append(
                EquationPart(
                    species=reactant.getSpecies() if reactant.isSetSpecies() else None,
                    stoichiometry=reactant.getStoichiometry()
                    if reactant.isSetStoichiometry()
                    else None,
                    constant=reactant.getConstant()
                    if reactant.isSetConstant()
                    else True,
                    **parse_sbase_kwargs(reactant),
                )
            )
            product: libsbml.SpeciesReference
        for product in r.getListOfProducts():
            equation.products.append(
                EquationPart(
                    species=product.getSpecies() if product.isSetSpecies() else None,
                    stoichiometry=product.getStoichiometry()
                    if product.isSetStoichiometry()
                    else None,
                    constant=product.getConstant() if product.isSetConstant() else True,
                    **parse_sbase_kwargs(product),
                )
            )
        modifier: libsbml.SpeciesReference
        for modifier in r.getListOfModifiers():
            if modifier.isSetSpecies():
                equation.modifiers.append(modifier.getSpecies())

        # formula
        ast = None
        if r.isSetKineticLaw():
            klaw: libsbml.KineticLaw = r.getKineticLaw()
            ast: Optional[libsbml.ASTNode] = (
                klaw.getMath() if klaw.isSetMath() else None
            )
        formula: Optional[str] = libsbml.formulaToL3String(ast) if ast else None

        m.reactions.append(
            Reaction(equation=equation, formula=formula, **parse_sbase_kwargs(r))
        )

    # initial assignment
    ia: libsbml.InitialAssignment
    for ia in model.getListOfInitialAssignments():
        ast: Optional[libsbml.ASTNode] = ia.getMath() if ia.isSetMath() else None
        formula: Optional[str] = libsbml.formulaToL3String(ast) if ast else None
        m.assignments.append(
            InitialAssignment(
                symbol=ia.getSymbol() if ia.isSetSymbol() else None,
                value=formula,
                **parse_sbase_kwargs(ia),
            )
        )

    # rules
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        ast: Optional[libsbml.ASTNode] = rule.getMath() if rule.isSetMath() else None
        formula: Optional[str] = libsbml.formulaToL3String(ast) if ast else None
        typecode: int = rule.getTypeCode()
        if typecode == libsbml.SBML_ASSIGNMENT_RULE:
            m.rules.append(
                AssignmentRule(
                    variable=rule.getVariable() if rule.isSetVariable() else None,
                    value=formula,
                    **parse_sbase_kwargs(rule),
                )
            )
        elif typecode == libsbml.SBML_RATE_RULE:
            m.rate_rules.append(
                RateRule(
                    variable=rule.getVariable() if rule.isSetVariable() else None,
                    value=formula,
                    **parse_sbase_kwargs(rule),
                )
            )
        elif typecode == libsbml.SBML_ALGEBRAIC_RULE:
            m.algebraic_rules.append(
                AlgebraicRule(value=formula, **parse_sbase_kwargs(rule))
            )

    # events
    # constraints

    # FIXME:
    # comp
    # ports
    # fbc
    # groups
    # distrib

    return m


if __name__ == "__main__":
    from sbmlutils.console import console

    # from sbmlutils.resources import REPRESSILATOR_SBML
    #
    # model_path: Path = Path(__file__).parent / "repressilator.xml"
    #
    # m = sbml_to_model(REPRESSILATOR_SBML)
    # console.print(m)
    # create_model(
    #     model=m,
    #     filepath=model_path,
    #     sbml_level=3,
    #     sbml_version=2,
    #     validation_options=ValidationOptions(units_consistency=False),
    # )
    # SBMLDocumentInfo.from_sbml(model_path)
    # model = sbml_to_model(source=sbml_path, validate=True, validation_options=ValidationOptions(
    #     units_consistency=False)
    # )

    sbml_path = Path(RESOURCES_DIR / "models//semantic/00927/00927-sbml-l1v2.xml")
    validate_sbml(
        source=sbml_path, validation_options=ValidationOptions(units_consistency=False)
    )

    doc = libsbml.readSBMLFromFile(str(sbml_path))
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_GENERAL_CONSISTENCY, True)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_IDENTIFIER_CONSISTENCY, True)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MATHML_CONSISTENCY, True)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, True)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_SBO_CONSISTENCY, True),
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_OVERDETERMINED_MODEL, True)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_SBO_CONSISTENCY, True),

    count = doc.checkInternalConsistency()
    # count = doc.checkConsistency()
    if count > 0:
        for i in range(count):
            print(f"*** Error {i}")
            error: libsbml.SBMLError = doc.getError(i)
            print(error.getMessage())
    else:
        print("no errors")
