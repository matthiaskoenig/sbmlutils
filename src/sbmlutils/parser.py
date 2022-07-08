"""Parse Models in internal model format."""
from pathlib import Path
from typing import Any, Dict, Optional, Union

import libsbml

from sbmlutils.factory import *
from sbmlutils.io.sbml import read_sbml
from sbmlutils.log import get_logger
from sbmlutils.reaction_equation import EquationPart


logger = get_logger(__name__)


def sbml_to_model(
    source: Union[Path, str],
    validate: bool = False,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
) -> Model:
    """Parse SBML model.

    LocalParameters are promoted.
    """
    doc: libsbml.SBMLDocument = read_sbml(
        source=source,
        promote=True,
        validate=validate,
        log_errors=log_errors,
        units_consistency=units_consistency,
        modeling_practice=modeling_practice,
        internal_consistency=internal_consistency,
    )
    model: libsbml.Model = doc.getModel()

    def parse_sbase_kwargs(sbase: libsbml.SBase) -> Dict[str, Any]:
        """Parse SBase information in dictionary."""
        kwargs: Dict[str, Any] = {}
        kwargs["sid"] = sbase.getId() if sbase.isSetId() else None
        kwargs["metaId"] = sbase.getMetaId() if sbase.isSetMetaId() else None
        kwargs["name"] = sbase.getName() if sbase.isSetName() else None
        kwargs["sboTerm"] = sbase.getSBOTermID() if sbase.isSetSBOTerm() else None

        # FIXME:
        # annotations
        # notes
        # port
        # uncertainties
        # replacedBy

        return kwargs

    if not model:
        logger.error("No model in SBMLDocument.")

    m = Model(**parse_sbase_kwargs(model))

    p: libsbml.Parameter
    for p in model.getListOfParameters():
        m.parameters.append(
            Parameter(
                value=p.getValue() if p.isSetValue else None,
                # unit=p.getUnits(),
                constant=p.getConstant() if p.isSetConstant() else None,
                **parse_sbase_kwargs(p)
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
                **parse_sbase_kwargs(c)
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
                **parse_sbase_kwargs(s)
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
                    **parse_sbase_kwargs(reactant)
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
                    **parse_sbase_kwargs(product)
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
        m.assignments.append(InitialAssignment(value=formula, **parse_sbase_kwargs(ia)))

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
                    **parse_sbase_kwargs(rule)
                )
            )
        elif typecode == libsbml.SBML_RATE_RULE:
            m.rate_rules.append(
                RateRule(
                    variable=rule.getVariable() if rule.isSetVariable() else None,
                    value=formula,
                    **parse_sbase_kwargs(rule)
                )
            )
        elif typecode == libsbml.SBML_ALGEBRAIC_RULE:
            m.algebraic_rules.append(
                AlgebraicRule(value=formula, **parse_sbase_kwargs(rule))
            )

    # events

    # constraints

    # fbc

    # groups

    # distrib

    return m


if __name__ == "__main__":
    from sbmlutils.console import console
    from sbmlutils.resources import REPRESSILATOR_SBML

    m = sbml_to_model(REPRESSILATOR_SBML)
    console.print(m)
    create_model(
        models=m,
        output_dir=Path(__file__).parent,
        filename="repressilator.xml",
        units_consistency=False,
        sbml_level=3,
        sbml_version=2,
    )
