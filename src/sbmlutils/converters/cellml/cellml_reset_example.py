import sys
import libcellml


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
            <ci>alpha</ci>
            <ci>m</ci>
        </apply>
    </apply>
</math>
"""
RESET_TEST = """
<math xmlns="http://www.w3.org/1998/Math/MathML">
    <apply>
        <eq/>
        <ci>m</ci>
        <ci>m_div</ci>
    </apply>
</math>
"""
RESET_VALUE = """
<math xmlns="http://www.w3.org/1998/Math/MathML" xmlns:cellml="http://www.cellml.org/cellml/2.0#">
    <apply>
        <eq/>
        <ci>m</ci>
        <apply>
            <divide/>
            <ci>m</ci>
            <cn cellml:units="dimensionless">2</cn>
        </apply>
    </apply>
</math>
"""

def print_issues(title, logger):
    if logger.issueCount():
        print(title, logger.issueCount())
        for index in range(logger.issueCount()):
            count = index + 1
            print(f'[{count:3}] - ({logger.issue(index).level()}) {logger.issue(index).description()}')

def create_reset_model():
    model = libcellml.Model("cell_growth")
    per_second = libcellml.Units("per_second")
    per_second.addUnit("second", -1)
    model.addUnits(per_second)

    component = libcellml.Component("environment")
    component.setMath(MATH_ODE)
    model.addComponent(component)

    variable_time = libcellml.Variable("t")
    variable_time.setUnits("second")
    variable_1 = libcellml.Variable("m")
    variable_1.setUnits("kilogram")
    variable_1.setInitialValue(0)
    variable_2 = libcellml.Variable("alpha")
    variable_2.setUnits(per_second)
    variable_2.setInitialValue(1.2)
    variable_3 = libcellml.Variable("m_div")
    variable_3.setUnits("kilogram")
    variable_3.setInitialValue(7)
    for variable in [variable_time, variable_1, variable_2, variable_3]:
        component.addVariable(variable)

    reset = libcellml.Reset()
    reset.setOrder(0)
    reset.setTestVariable(variable_1)
    reset.setTestValue(RESET_TEST)
    reset.setVariable(variable_1)
    reset.setResetValue(RESET_VALUE)
    component.addReset(reset)

    return model


def main():
    printer = libcellml.Printer()

    model = create_reset_model()
    print(printer.printModel(model))
    print_issues("Printer: ", printer)

    validator = libcellml.Validator()
    validator.validateModel(model)
    print_issues("Validator: ", validator)

    analyser = libcellml.Analyser()

    analyser.analyseModel(model)

    print_issues("Analyser: ", analyser)

    g = libcellml.Generator()
    gp = libcellml.GeneratorProfile(libcellml.GeneratorProfile.Profile.C)
    g.setModel(analyser.model())
    g.setProfile(gp)

    print(g.interfaceCode())
    print(g.implementationCode())

    return 0


if __name__ == "__main__":
    sys.exit(main())
