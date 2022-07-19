"""Example creating linear chain.

This demonstrates core SBML functionality in combination with using patterns.
`sbmlutils` allows to generate patterns of objects by combining loops in combination
with string patterns. In this example we create a kinetic model of a linear chain.
"""
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.validation import ValidationOptions


n_chain = 20
model = Model(
    sid="linear_chain",
    notes="""
    # Linear chain

    Example model for the programatic creation of a linear chain.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    compartments=[
        Compartment(sid="cell", value=1.0),
    ],
    species=[
        Species(sid="S1", initialConcentration=10.0, compartment="cell"),
    ],
)
for k in range(n_chain):
    model.species.append(
        Species(
            sid=f"S{k + 2}",
            initialConcentration=0.0,
            compartment="cell",
            name=f"Species {k +2}",
        ),
    )
    model.parameters.append(
        Parameter(sid=f"k{k+1}", value=0.1, name=f"rate constant {k+1}"),
    )
    model.reactions.append(
        Reaction(
            sid=f"J{k+1}", equation=f"S{k+1} -> S{k+2}", formula=f"k{k+1} * S{k+1}"
        ),
    )

if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    factory_results = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
    visualize_sbml(sbml_path=factory_results.sbml_path)
