"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *
from sbmlutils.validation import ValidationOptions


model = Model(
    sid="minimal_model",
    packages=[Package.FBC_V2],
    compartments=[
        Compartment(sid="cell", value=1.0, port=True),
    ],
    species=[
        Species(sid="S1", initialConcentration=10.0, compartment="cell", port=True),
        Species(sid="S2", initialConcentration=0.0, compartment="cell"),
    ],
    parameters=[
        Parameter(sid="k1", value=0.1),
    ],
    reactions=[
        Reaction(sid="J0", equation="S1 -> S2", formula="k1 * S2"),
    ],
)

if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    fac_result = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
    visualize_sbml(sbml_path=fac_result.sbml_path, delete_session=True)
