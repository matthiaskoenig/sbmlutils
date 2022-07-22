"""FBA example with UserDefinedConstraints."""
import numpy as np

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
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
    # creators=templates.creators,
    # notes="""
    # # Model with fbc version 3
    # Example creating fbc model with KeyValuePairs.
    #
    # The `ListOfKeyValuePairs`, forms the basis of a controlled annotation defined by
    # the Flux Balance Constraints package. This element defines a structured note or
    # descriptive list of keys and associated values.
    # """
    # + templates.terms_of_use,
    # units=U,
    # model_units=ModelUnits(
    #     time=U.hr,
    #     extent=U.mmole,
    #     substance=U.mmole,
    #     length=U.meter,
    #     area=U.m2,
    #     volume=U.liter,
    # ),
    compartments=[
        Compartment("cell", value=1.0),
    ],
    species=[
        Species("S1", initialAmount=NaN, compartment="cell"),
    ],
    parameters=[
        Parameter(sid="uc1", value=5),
        Parameter(sid="uc2lb", value=2),
        Parameter(sid="uc2ub", value=np.Inf),
        Parameter(sid="Avar", value=NaN, constant=False),
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
                "RGLX": 1.0,
                "RXLG": -1.0,
            },
            variableType="linear",
        ),
        UserDefinedConstraint(
            lowerBound="uc2lb",
            upperBound="uc2ub",
            components={
                "Avar": 2.0,
                "RGDP": -1.0,
            },
            variableType="linear",
        ),
    ],
)

if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    fac_results = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        show_sbml=True,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=1,
    )
