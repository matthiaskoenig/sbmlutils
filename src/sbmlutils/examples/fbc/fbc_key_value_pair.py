"""FBC example for KeyValuePairs."""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.validation import ValidationOptions


model = Model(
    "fbc_key_value_pair",
    packages=[Package.FBC_V3],
    creators=templates.creators,
    notes="""
    # Example model with KeyValuePair.

    The `ListOfKeyValuePairs`, forms the basis of a controlled annotation defined by
    the Flux Balance Constraints package. This element defines a structured note or
    descriptive list of keys and associated values.

    """
    + templates.terms_of_use,
    parameters=[
        Parameter(
            sid="p1",
            name="example parameter",
            value=1.0,
            notes="""
            The `ListOfKeyValuePairs` are used to store information in a dictionary
            with additional options for describing the keys via an `uri`.
            """,
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

    sbml_path = EXAMPLES_DIR / "fbc" / f"{model.sid}.xml"

    fac_results = create_model(
        model=model,
        filepath=sbml_path,
        show_sbml=True,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=2,
    )

    from sbmlutils.console import console
    from sbmlutils.parser import sbml_to_model

    model2: Model = sbml_to_model(source=sbml_path)
    console.print(model2.__repr__())
    console.rule()
    console.print(str(model2))

    # console.log(model.parameters[0])
    print(model.parameters[0].keyValuePairs)
    print(model2.parameters[0].keyValuePairs)

    fac_results = create_model(
        model=model2,
        filepath=sbml_path,
        show_sbml=True,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=2,
    )
