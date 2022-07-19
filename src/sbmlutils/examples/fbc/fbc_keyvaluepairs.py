"""FBA example with ListOfKeyValuePairs."""
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
    "fbc_keyvaluepairs",
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
    parameters=[
        Parameter(
            sid="ub",
            name="default upper bound",
            value=float("Inf"),
            # unit=U.mmole_per_hr,
            constant=True,
            keyValuePairs=[
                KeyValuePair(
                    key="keyX", value="47", uri="https://tinyurl.com/ybyr7b62"
                ),
                KeyValuePair(
                    key="ZZkey", value="level 5", uri="urn:tinyurl.com:example:kvp"
                ),
                KeyValuePair(
                    key="x-factor",
                    value="intangible metaphysical property",
                    uri="https://tinyurl.com/ybyr7b62",
                ),
            ],
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
    )
