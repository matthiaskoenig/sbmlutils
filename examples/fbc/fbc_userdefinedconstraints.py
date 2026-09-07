"""FBA example with UserDefinedConstraints."""

from pathlib import Path

import numpy as np

from sbmlutils.factory import *
from sbmlutils.validation import ValidationOptions


class U(Units):
    """UnitsDefinition."""

    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")
    hr = UnitDefinition("hr")
    mmole_per_l = UnitDefinition("mmole_per_l", "mmole/liter")
    mmole_per_hr = UnitDefinition("mmole_per_hr", "mmole/hr")


model = Model(
    "fbc_user_defined_constraints",
    packages=[Package.FBC_V3],
    notes="""
    # Model with the user defined constraints of fbc version 3

    A user defined constraint bounds a linear combination of fluxes and
    variables, i.e., `uc1 <= 1.0 * RGLX - 1.0 * RXLG <= uc1`. The bounds and the
    coefficients of the combination are parameters of the model.
    """,
    compartments=[
        Compartment("cell", value=1.0),
    ],
    species=[
        Species("S1", initialAmount=NaN, compartment="cell"),
    ],
    parameters=[
        # bounds of the constraints
        Parameter(sid="uc1", value=5),
        Parameter(sid="uc2lb", value=2),
        Parameter(sid="uc2ub", value=np.inf),
        # the variable of the second constraint
        Parameter(sid="Avar", value=NaN, constant=False),
        # coefficients of the components, referenced by the components
        Parameter(sid="coef_plus_one", value=1.0),
        Parameter(sid="coef_minus_one", value=-1.0),
        Parameter(sid="coef_two", value=2.0),
    ],
    reactions=[
        Reaction("RGLX", equation="S1 -> "),
        Reaction("RXLG", equation="-> S1"),
        Reaction("RGDP", equation="S1 -> "),
    ],
    user_defined_constraints=[
        UserDefinedConstraint(
            lowerBound="uc1",
            upperBound="uc1",
            components={
                "RGLX": "coef_plus_one",
                "RXLG": "coef_minus_one",
            },
            variableType="linear",
        ),
        UserDefinedConstraint(
            lowerBound="uc2lb",
            upperBound="uc2ub",
            components={
                "Avar": "coef_two",
                "RGDP": "coef_minus_one",
            },
            variableType="linear",
        ),
    ],
)

if __name__ == "__main__":
    fac_results = create_model(
        model=model,
        filepath=Path.cwd() / f"{model.sid}.xml",
        show_sbml=True,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=1,
    )
