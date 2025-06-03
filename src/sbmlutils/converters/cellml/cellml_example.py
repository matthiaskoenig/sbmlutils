from pathlib import Path

import libcellml

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

if __name__ == "__main__":
    from sbmlutils.converters.cellml.cellml2sbml import validate_cellml, write_model_to_file
    from sbmlutils.converters.cellml.cellml_simulator import (
        run_cellml_timecourse,
        plot_cellml_timecourse,
    )

    # create example model
    model = example_cellml()
    validate_cellml(model)
    cellml_path = Path("./models/test_model.cellml")
    write_model_to_file(model=model, cellml_path=cellml_path)

    # simulate example model
    df, units = run_cellml_timecourse(cellml_path)
    plot_cellml_timecourse(df=df, units=units)
