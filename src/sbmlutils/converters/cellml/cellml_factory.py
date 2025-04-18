"""Converter to cellml.
https://libcellml.org/
 pip install libcellml
Tutorials: https://github.com/libcellml/tutorials
https://github.com/libcellml/jupyter-tutorials

Online simulator: https://opencor.ws/appdev/

Opencor: https://github.com/opencor/libopencor
pip install git+https://github.com/opencor/libopencor.git

"""
from pathlib import Path
from typing import Optional

import numpy as np

from sbmlutils.console import console

import libsbml
import libcellml
from sbmlutils.converters.cellml.cellml_simulator import run_cellml_timecourse




def example_cellml() -> libcellml.Model:
    """Simple example CellML model.

    # example math
    # m: mass, [m] = kg
    # alpha: rate constant, [alpha] = 1/s
    # dm/dt = alpha * m

    """
    MATH_ODE = """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
        <apply>
            <eq/>
            <apply>
                <diff/>
                <bvar>
                    <ci>t</ci>
                </bvar>
                <ci>m</ci>
            </apply>
            <apply>
                <times/>
                <apply>
                  <minus/>
                  <ci>alpha</ci>
                </apply>
                <ci>m</ci>
            </apply>
        </apply>
    </math>
    """
    # create model
    model_id: str = "test_model"
    model = libcellml.Model(model_id)

    # add units
    per_second = libcellml.Units("per_second")
    per_second.addUnit("second", -1)
    model.addUnits(per_second)

    # create component (everything is put int a single compartment
    component = libcellml.Component("component")

    # add equations to component
    component.setMath(MATH_ODE)
    model.addComponent(component)

    variable_time = libcellml.Variable("t")
    variable_time.setUnits("second")

    # parameters and states are variables
    variable_m = libcellml.Variable("m")
    variable_m.setUnits("kilogram")
    variable_m.setInitialValue(10)

    variable_alpha = libcellml.Variable("alpha")
    variable_alpha.setUnits(per_second)
    variable_alpha.setInitialValue(0.05)

    for variable in [variable_time, variable_m, variable_alpha, ]:
        component.addVariable(variable)

    return model

def convert_sbml2cellml(sbml_path: Path) -> libcellml.Model:
    """Converter to convert SBML model into CellML."""
    from sbmlutils.io.sbml import read_sbml
    doc: libsbml.SBMLDocument = read_sbml(sbml_path)
    m_sbml: libsbml.Model = doc.getModel()
    mid: str = m_sbml.getId()
    m_cellml: libcellml.Model = libcellml.Model(mid)

    # dictionary for collecting the math

    # add units
    # FIXME: support unit definitions
    per_second = libcellml.Units("per_second")
    per_second.addUnit("second", -1)
    m_cellml.addUnits(per_second)

    # create component (everything is put int a single compartment
    component = libcellml.Component("component")
    m_cellml.addComponent(component)

    # add compartments
    c: libsbml.Compartment
    cdict: dict[str, float] = {}
    for c in m_sbml.getListOfCompartments():
        cid: str = c.getId()
        cvalue: float = c.getSize()
        cdict[cid] = cvalue
        v = libcellml.Variable(cid)
        v.setUnits("dimensionless")  # FIXME
        v.setInitialValue(cvalue)
        component.addVariable(v)
        console.print(f"'{cid}' variable for 'compartment'")

    # add parameters
    p: libsbml.Parameter
    for p in m_sbml.getListOfParameters():
        pid: str = p.getId()
        pvalue: float = p.getValue()
        if np.isnan(pvalue):
            console.print(f"Initial value is nan: {pid}, setting to 1.0", style="warning")
            pvalue = 1.0
        v = libcellml.Variable(pid)
        v.setUnits("dimensionless")  # FIXME
        v.setInitialValue(pvalue)
        component.addVariable(v)
        console.print(f"'{pid}' variable for 'parameter'")

    # add species
    s: libsbml.Species
    species_types: dict[str, str] = {}
    for s in m_sbml.getListOfSpecies():
        sid: str = s.getId()
        cid = s.getCompartment()
        v = libcellml.Variable(sid)
        v.setUnits("dimensionless")  # FIXME

        if s.getHasOnlySubstanceUnits():
            # amount
            species_types[sid] = "amount"
            if s.isSetInitialAmount():
                v.setInitialValue(s.getInitialAmount())
            elif s.isSetInitialConcentration():
                v.setInitialValue(s.getInitialConcentration() * cdict[cid])
        else:
            # concentration
            species_types[sid] = "concentration"
            if s.isSetInitialAmount():
                v.setInitialValue(s.getInitialAmount()/cdict[cid])
            elif s.isSetInitialConcentration():
                v.setInitialValue(s.getInitialConcentration())

        component.addVariable(v)
        console.print(f"'{sid}' variable for 'species'")

    # collect rules
    arules: dict[str, str] = {}
    rrules: dict[str, str] = {}
    rule: libsbml.AssignmentRule
    for rule in m_sbml.getListOfRules():
        vid: str = rule.getVariable()
        vmath: libsbml.ASTNode = rule.getMath()
        rule_type = rule.getTypeCode()
        if rule_type == libsbml.SBML_ASSIGNMENT_RULE:
            arules[vid] = libsbml.formulaToL3String(vmath)
        elif rule_type == libsbml.SBML_RATE_RULE:
            rrules[vid] = libsbml.formulaToL3String(vmath)

    # collect math for reactions
    reaction_terms: dict[str, str] = {}
    r: libsbml.Reaction
    for r in m_sbml.getListOfReactions():
        klaw: libsbml.KineticLaw = r.getKineticLaw()
        math = klaw.getMath()
        formula = libsbml.formulaToL3String(math)
        reactant: libsbml.SpeciesReference

        # the updates have to be either in amount/time or concentration/time depending
        # on the variable

        for reactant in r.getListOfReactants():
            reactant_id: str = reactant.getSpecies()
            formula_str = f"- ({formula})"
            if reactant_id in reaction_terms:
                reaction_terms[reactant_id] = f"{reaction_terms[reactant_id]} {formula_str}"
            else:
                reaction_terms[reactant_id] = formula_str

        product: libsbml.SpeciesReference
        for product in r.getListOfProducts():
            product_id: str = product.getSpecies()
            formula_str = f"+ ({formula})"
            if product_id in reaction_terms:
                reaction_terms[product_id] = f"{reaction_terms[product_id]} {formula_str}"
            else:
                reaction_terms[product_id] = formula_str

    # amount/concentration
    reaction_terms_all = {}
    for sid, formula_str in reaction_terms.items():
        if species_types[sid] == "amount":
            reaction_terms_all[sid] = formula_str
        elif species_types[sid] == "concentration":
            cid = m_sbml.getSpecies(sid).getCompartment()
            reaction_terms_all[sid] = f"1/{cid} * ({formula_str})"
    reaction_terms = reaction_terms_all
    del reaction_terms_all

    # convert rules and reactions to mathml
    if arules:
        console.rule(f"assignment rules", style="white")
        for key, formula in arules.items():
            console.print(f"{key} = {formula}", style="info")

    if rrules:
        console.rule(f"rate rules", style="white")
        for key, formula in rrules.items():
            console.print(f"{key} = {formula}", style="info")

    if reaction_terms:
        console.rule(f"reactions", style="white")
        for key, formula in reaction_terms.items():
            console.print(f"d{ key}/dt = {formula}", style="info")

    console.rule(style="white")

    return m_cellml


def write_model_to_string(model: libcellml.Model) -> str:
    """Write CellML model to string."""
    printer = libcellml.Printer()
    model_xml_str: str = printer.printModel(model)
    return model_xml_str


def write_model_to_file(model: libcellml.Model, cellml_path: Path) -> None:
    """Write CellML model to file."""
    model_xml_str: str = write_model_to_string(model)
    with open(cellml_path, "w", encoding="utf-8") as f_cellml:
        f_cellml.write(model_xml_str)


def print_issues(title, logger):
    if logger.issueCount():
        console.print(title, logger.issueCount())
        for index in range(logger.issueCount()):
            count = index + 1
            console.print(
                f'[{count:3}] - ({logger.issue(index).level()}) {logger.issue(index).description()}')


def validate_cellml(model: libcellml.Model) -> str:
    """Validation of cellml."""
    printer = libcellml.Printer()
    print_issues("Printer: ", printer)

    validator = libcellml.Validator()
    validator.validateModel(model)
    print_issues("Validator: ", validator)

    analyser = libcellml.Analyser()
    analyser.analyseModel(model)
    print_issues("Analyser: ", analyser)

    # g = libcellml.Generator()
    # gp = libcellml.GeneratorProfile(libcellml.GeneratorProfile.Profile.C)
    # g.setModel(analyser.model())
    # g.setProfile(gp)

    # print(g.interfaceCode())
    # print(g.implementationCode())

    return 0


if __name__ == "__main__":

    # example model
    # cellml_model_path = "test_model.cellml"
    # model = example_cellml()
    # validate_cellml(model)
    # write_model_to_file(model=model, cellml_path=cellml_model_path)
    # run_cellml_timecourse(cellml_model_path)

    # converted model
    sbml_model_path = "glimepiride_kidney.xml"
    cellml_model_path = "glimepiride_kidney.cellml"
    model: libcellml.Model = convert_sbml2cellml(sbml_path=sbml_model_path)
    validate_cellml(model)
    write_model_to_file(model=model, cellml_path=cellml_model_path)
    run_cellml_timecourse(cellml_model_path)



