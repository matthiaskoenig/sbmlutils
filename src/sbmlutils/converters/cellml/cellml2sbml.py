"""Converter from SBML to CellML.

This uses the libcellml library https://libcellml.org/ which can be installed via
    pip install libcellml

Tutorials and information:
https://github.com/libcellml/tutorials
https://github.com/libcellml/jupyter-tutorials

Online opencor JavaScript simulator: https://opencor.ws/appdev/
The simulator can be installed via:

Opencor: https://github.com/opencor/libopencor
pip install git+https://github.com/opencor/libopencor.git

FIXME: issues in libopencor
- [ ] "The linear solver's setup function failed in an unrecoverable manner." for glimeperide kidney.
- [ ] cannot set start, end, steps on simulation
- [ ] precompiled python packages

TODO:
- [ ] Convert units
- [ ] Calculate initial values based on AssignmentRules & InitialAssignments (using libroadrunner)
- [ ] Package in separate package
- [ ] Add tests for functionality
- [ ] Use SBML test suite models as test cases with simulator
- [ ] CellML -> SBML converter

Features currently not supported in the sbml2cellml conversion:
- [ ] UnitDefinitions
- [ ] InitialAssignments -> would be precalculated, i.e. libroadrunner to calculate initial state.
- [ ] FunctionDefinitions -> can be supported via inlining the function or addition assignments
- [ ] Events -> Converted to resets; only subset of syntax supported, currently on support in simulator
"""
from pathlib import Path
import numpy as np

import libsbml
import libcellml
from sbmlutils.console import console


class SBML2CellMLConversionError(IOError):
    """Definition of parser error."""
    pass


def convert_sbml2cellml(sbml_path: Path, verbose: bool = True) -> libcellml.Model:
    """Converter to convert SBML model into CellML.

    The verbose flag allows to get additional information during the conversion.
    """
    # read SBML model
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    m_sbml: libsbml.Model = doc.getModel()
    if not m_sbml:
        raise SBML2CellMLConversionError("No model in SBMLDocument.")
    mid: str = m_sbml.getId() if m_sbml.isSetId() else Path(sbml_path).stem

    # create empty CellML model
    m_cellml: libcellml.Model = libcellml.Model(mid)

    # create component (everything is put int a single compartment
    component = libcellml.Component("sbml")
    m_cellml.addComponent(component)

    # add units
    # FIXME: support unit definitions
    per_second = libcellml.Units("per_second")
    per_second.addUnit("second", -1)
    m_cellml.addUnits(per_second)

    # add time variable
    time_name = "time"
    variable_time = libcellml.Variable(time_name)
    variable_time.setUnits("dimensionless")  # FIXME: correct units
    component.addVariable(variable_time)


    def process_init_value(sid: str, value: float) -> float:
        """Handling processing of NaN values.

        These could be precalculated based on the rules."""
        if np.isnan(value):
            console.print(f"Initial value is nan: {sid}, setting to 1.0", style="warning")
            value = 1.0
        return value

    # add compartments
    c: libsbml.Compartment
    cdict: dict[str, float] = {}
    for c in m_sbml.getListOfCompartments():
        cid: str = c.getId()
        cvalue: float = process_init_value(cid, c.getSize())
        cdict[cid] = cvalue
        v = libcellml.Variable(cid)
        v.setUnits("dimensionless")  # FIXME
        v.setInitialValue(cvalue)
        component.addVariable(v)
        if verbose:
            console.print(f"'{cid}' variable for 'compartment'")

    # add parameters
    p: libsbml.Parameter
    for p in m_sbml.getListOfParameters():
        pid: str = p.getId()
        pvalue: float = process_init_value(pid, p.getValue())
        v = libcellml.Variable(pid)
        v.setUnits("dimensionless")  # FIXME
        v.setInitialValue(pvalue)
        component.addVariable(v)
        if verbose:
            console.print(f"'{pid}' variable for 'parameter'")

    # add species
    s: libsbml.Species
    species_types: dict[str, str] = {}
    for s in m_sbml.getListOfSpecies():
        sid: str = s.getId()
        cid = s.getCompartment()
        v = libcellml.Variable(sid)
        v.setUnits("dimensionless")  # FIXME

        # process initial value
        species_types[sid] = "amount" if s.getHasOnlySubstanceUnits() else "concentration"
        if s.isSetInitialAmount():
            amount = process_init_value(sid, s.getInitialAmount())
            vinit = amount if s.getHasOnlySubstanceUnits() else amount * cdict[cid]
        elif s.isSetInitialConcentration():
            concentration = process_init_value(sid, s.getInitialConcentration())
            vinit = concentration * cdict[cid] if s.getHasOnlySubstanceUnits() else concentration
        v.setInitialValue(vinit)

        component.addVariable(v)
        if verbose:
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
            reaction_terms_all[sid] = f"1.0 dimensionless/{cid} * ({formula_str})"
    reaction_terms = reaction_terms_all
    del reaction_terms_all

    # convert rules and reactions to mathml
    mathml_parts: list[str] = []

    if arules:
        console.rule(f"assignment rules", style="white")
        for vid, formula in arules.items():
            mathml_str = mathml_for_assignment(vid=vid, formula=formula)
            mathml_parts.append(mathml_str)
            if verbose:
                console.print(f"{vid} = {formula}", style="info")
                # console.print(mathml_str)

    if rrules:
        console.rule(f"rate rules", style="white")
        for vid, formula in rrules.items():
            mathml_str = mathml_for_diff(vid=vid, formula=formula, ivid=time_name)
            mathml_parts.append(mathml_str)
            if verbose:
                console.print(f"{vid} = {formula}", style="info")
                # console.print(mathml_str)

    if reaction_terms:
        console.rule(f"reactions", style="white")
        for vid, formula in reaction_terms.items():
            mathml_str = mathml_for_diff(vid=vid, formula=formula, ivid=time_name)
            mathml_parts.append(mathml_str)
            if verbose:
                console.print(f"d{vid}/dt = {formula}", style="info")
                # console.print(mathml_str)

    console.rule(style="white")

    # combine mathml
    cellml_mathml = '<math xmlns="http://www.w3.org/1998/Math/MathML" xmlns:cellml="http://www.cellml.org/cellml/2.0#">\n'
    cellml_mathml += "\n".join(mathml_parts)
    cellml_mathml += "</math>"
    component.setMath(cellml_mathml)
    # console.print(cellml_mathml, style="white")

    event: libsbml.Event
    for event in m_sbml.getListOfEvents():
        console.print(f"Event NOT converted: {event}!", style="error")

    assignment: libsbml.InitialAssignment
    for assignment in m_sbml.getListOfInitialAssignments():
        console.print(f"InitialAssignment NOT converted: {assignment}!", style="error")

    return m_cellml


# --- MathML processing ---
xml_prefix = '<?xml version="1.0" encoding="UTF-8"?>'
# FIXME: handle via regular expression to be more robust
mathml_prefixes = [
    '<math xmlns="http://www.w3.org/1998/Math/MathML">',
    '<math xmlns="http://www.w3.org/1998/Math/MathML" xmlns:sbml="http://www.sbml.org/sbml/level3/version2/core">'
]
mathml_suffix = '</math>'

def process_mathml_for_cellml(formula: str):
    """Process and cleanup Mathml.
    Removes prefix and suffix from the formula

    """
    ast: libsbml.ASTNode = libsbml.parseL3Formula(formula)
    mathml_str = libsbml.writeMathMLToString(ast)
    # cleanup unnecessary mathml parts
    mathml_str = mathml_str.replace(xml_prefix, '')
    for prefix in mathml_prefixes:
        mathml_str = mathml_str.replace(prefix, '')
    mathml_str = mathml_str.replace(mathml_suffix, '')

    # handle inline units
    mathml_str = mathml_str.replace("sbml:units", 'cellml:units')


    # cleanup whitespace
    mathml_str = mathml_str.strip()



    return mathml_str


def mathml_for_diff(vid, formula, ivid:str = "t"):
    """Create mathml for differential.

    d {vid}/d {ivid} = {formula}
    """
    rhs_str = process_mathml_for_cellml(formula)
    mathml_str = f"""<apply>
  <eq/>
  <apply>
    <diff/>
    <bvar>
      <ci>{ivid}</ci>
    </bvar>
    <ci>{vid}</ci>
  </apply>
  {rhs_str}
</apply>
    """
    return mathml_str


def mathml_for_assignment(vid, formula):
    """Create mathml for assignment.

    {vid} = {formula}
    """
    rhs_str = process_mathml_for_cellml(formula)
    mathml_str = f"""<apply>
  <eq/>
  <ci>{vid}</ci>
  {rhs_str}
</apply>
"""
    return mathml_str


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
    # console.print("CellML model is valid.", style="success")
    return 0


if __name__ == "__main__":
    from sbmlutils.converters.cellml.cellml_simulator import run_cellml_timecourse

    # converted models
    model_names = [
        "glimepiride_kidney",
        "glimepiride_liver",
        "glimepiride_intestine",
        "glimepiride_body",
        "glimepiride_body_flat",
    ]
    for name in model_names:
        sbml_path = Path(__file__).parent / "models" / f"{name}.xml"
        cellml_path = sbml_path.parent / f"{sbml_path.stem}.cellml"
        model: libcellml.Model = convert_sbml2cellml(sbml_path=sbml_path)
        write_model_to_file(model=model, cellml_path=cellml_path)
        run_cellml_timecourse(cellml_path)



