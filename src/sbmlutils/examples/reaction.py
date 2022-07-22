"""Create reaction example."""
import numpy as np

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.reaction_equation import EquationPart


model = Model(
    "reaction",
    name="model with reaction",
    notes="""
    # Reaction definition

    This example demonstrates the creation of reactions with constant or
    variable stoichiometry.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    compartments=[
        Compartment(sid="c", name="cytosol", value=np.NaN),
    ],
    species=[
        Species(
            sid="x",
            compartment="c",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            initialConcentration=10.0,
            boundaryCondition=True,
        ),
        Species(
            sid="y",
            compartment="c",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            initialConcentration=0.0,
        ),
    ],
    rules=[
        AssignmentRule(
            "f1",
            "1.0 * time",
            notes="""
            Time dependent variable stoichiometry.
            """,
        ),
        AssignmentRule(
            "f2",
            "2.0 * time",
            notes="""
            Time dependent variable stoichiometry.
            """,
        ),
    ],
    assignments=[
        InitialAssignment(
            "v4_x",
            2.5,
            notes="""
            InitialAssignment for reactant stoichiometry in v4.
            """,
        ),
        InitialAssignment(
            "v4_y",
            5.0,
            notes="""
            InitialAssignment for product stoichiometry in v4.
            """,
        ),
    ],
    reactions=[
        Reaction(
            sid="v1",
            equation="x -> y",
            compartment="c",
            formula="k1 * x",
            pars=[Parameter("k1", 1.0)],
            notes="""
            Reaction with constant stoichiometry 1.0.
            """,
        ),
        Reaction(
            sid="v2",
            equation="1.0 x -> 2.0 y",
            compartment="c",
            formula="k1 * x",
            notes="""
            Reaction with constant stoichiometry.
            """,
        ),
        Reaction(
            sid="v3",
            equation="f1 * x -> f2 * y",
            compartment="c",
            formula="k1 * x",
            notes="""
            Reaction with variable stoichiometry set via AssignmentRules.
            """,
        ),
        Reaction(
            sid="v4",
            equation=ReactionEquation(
                reactants=[
                    EquationPart(species="x", stoichiometry=np.NaN, sid="v4_x"),
                ],
                products=[
                    EquationPart(species="y", stoichiometry=np.NaN, sid="v4_y"),
                ],
                reversible=False,
            ),
            compartment="c",
            formula="k1 * x",
            notes="""
            Reaction with initial assignment of stoichiometry.
            """,
        ),
    ],
)


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(model=model, filepath=EXAMPLES_DIR / f"{model.sid}.xml")
