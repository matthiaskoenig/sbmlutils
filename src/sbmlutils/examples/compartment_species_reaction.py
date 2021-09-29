"""Example model for creating an SBML ODE model."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min", "min")
    liter = UnitDefinition("liter", "liter")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    mmole = UnitDefinition("mmole", "mmole")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")


model = Model(
    "compartment_species_reaction",
    name="model with compartments, species, reactions",
    notes="""
    # Model with compartment, species, reaction
    This example demonstrates how to create compartments, species and reactions.
    The `Model.objects` are used to store the different objects.
    """
    + templates.terms_of_use,
    creators=[
        Creator(
            familyName="König",
            givenName="Matthias",
            email="koenigmx@hu-berlin.de",
            organization="Humboldt-University Berlin, Institute for Theoretical Biology",
            site="https://livermetabolism.com",
            orcid="0000-0003-1725-179X",
        )
    ],
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.liter,
    ),
    objects=[
        Compartment(
            "c",
            1.0,
            unit=U.liter,
            name="cytosol",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            notes="""
            **Compartment**

            Compartments can be generated via the `Compartment` object. It is best
            practise to set a `name`, `unit` and `sboTerm`. Use the `notes` field
            to describe the model component.
            """,
        ),
        Species(
            "S1",
            initialConcentration=5.0,
            compartment="c",
            substanceUnit=U.mmole,
            name="S1",
            hasOnlySubstanceUnits=False,
            sboTerm=SBO.SIMPLE_CHEMICAL,
            notes="""
            **Species**

            Species can be generated via the `Species` object. It is best
            practise to set a `name` and `sboTerm`. The `hasOnlySubstanceUnits`
            determine if the species is in amount [`substanceUnit`]
            (`hasOnlySubstanceUnits=True`) or concentration
            [`substanceUnit/compartmentUnit`] (`hasOnlySubstanceUnits=True`).
            Use the `notes` field to describe the model component.
            """,
        ),
        Parameter(
            "R1_Km",
            name="Km R1",
            value=0.1,
            unit=U.mmole,
            sboTerm=SBO.MICHAELIS_CONSTANT,
            notes="""
            **Parameter**

            Parameters can be generated via the `Parameter` object. It is best
            practise to set a `name`, `unit` and `sboTerm`.
            Use the `notes` field to describe the model component.
            """,
        ),
        Parameter(
            "R1_Vmax",
            name="Vmax R1",
            value=10.0,
            unit=U.mmole_per_min,
            sboTerm=SBO.MAXIMAL_VELOCITY,
        ),
        InitialAssignment(
            "S1",
            "10.0 mM",
            unit=U.mM,
            notes="""
            **InitialAssignment**

            InitialAssignments are generated via the `InitialAssignment` object.
            These allow to calculate the values of parameters, species or compartments
            at the begin of the simulation. Here we set the initial concentration of
            `S1` to `10 mM`.
            """,
        ),
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=model,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
