"""Create reaction example."""
import numpy as np

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.reaction_equation import EquationPart
from sbmlutils.resources import EXAMPLES_DIR


_m = Model(
    "reaction",
    name="model with reaction",
    notes="""
    # Reaction definition
    This example demonstrates the creation of a reaction.
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
            initialConcentration=np.NaN,
        ),
        Species(
            sid="y",
            compartment="c",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            initialConcentration=np.NaN,
        ),
    ],
    rules=[
        # FIXME: the automatic parameter creation must check also for SpeciesReferences!
        # AssignmentRule(
        #     "f1", "1.0 * time",
        #     notes="""
        #     Time dependent variable stoichiometry.
        #     """
        # ),
        # AssignmentRule(
        #     "f2", "2.0 * time",
        #     notes="""
        #     Time dependent variable stoichiometry.
        #     """
        # ),
    ],
    assignments=[
        # FIXME: the automatic parameter creation must check also for SpeciesReferences!
        # InitialAssignment(
        #     "v4_x", 2.5,
        #     notes="""
        #     InitialAssignment for reactant stoichiometry in v4.
        #     """
        # ),
        # InitialAssignment(
        #     "v4_y", 5.0,
        #     notes="""
        #     InitialAssignment for product stoichiometry in v4.
        #     """
        # ),
    ],
    reactions=[
        Reaction(
            sid="v1",
            equation="x -> y",
            compartment="c",
            notes="""
            Reaction with constant stoichiometry 1.0.
            """
        ),
        Reaction(
            sid="v2",
            equation="1.0 x -> 2.0 y",
            compartment="c",
            notes="""
            Reaction with constant stoichiometry.
            """
        ),
        Reaction(
            sid="v3",
            equation="f1 * x -> f2 * y",
            compartment="c",
            notes="""
            Reaction with variable stoichiometry.
            """
        ),
        Reaction(
            sid="v4",
            equation=ReactionEquation(
                reactants=[
                    EquationPart(species="x", stoichiometry=1.0, sid="v4_x"),
                ],
                products=[
                    EquationPart(species="y", stoichiometry=2.0, sid="v4_y"),
                ],
                reversible=False
            ),
            compartment="c",
            notes="""
            Reaction with initial assignment of stoichiometry.
            """
        )
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
