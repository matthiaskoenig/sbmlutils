"""Example model for creating an SBML ODE model."""

from sbmlutils.examples import templates, EXAMPLE_RESULTS_DIR
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


_m = Model(
    "core_example2",
    notes="""
    # Example `core_example2`
    ## Description
    This example demonstrates how to create compartments, species and reactions.
    The `Model.objects` are used to store the different objects.
    """ + templates.terms_of_use,
    creators=[
        Creator(
            familyName="König",
            givenName="Matthias",
            email="koenigmx@hu-berlin.de",
            organization="Humboldt-University Berlin, Institute for Theoretical Biology",
            site="https://livermetabolism.com",
            orcid="0000-0003-1725-179X"
        )
    ],
    model_units=ModelUnits(
        time=UNIT_min,
        extent=UNIT_mmole,
        substance=UNIT_mmole,
        length=UNIT_m,
        area=UNIT_m2,
        volume=UNIT_KIND_LITRE,
    ),
    units=[
        UNIT_m,
        UNIT_m2,
        UNIT_min,
        UNIT_mmole,
        UNIT_mM,
        UNIT_mmole_per_min,
    ],
    objects=[
        Compartment(
            "c", 1.0, unit=UNIT_KIND_LITRE,
            name="cytosol",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            notes="""
            **Compartment**

            Compartments can be generated via the `Compartment` object. It is best
            practise to set a `name`, `unit` and `sboTerm`. Use the `notes` field
            to describe the model component.
            """
        ),
        Species(
            "S1",
            initialConcentration=5.0,
            compartment="c",
            substanceUnit=UNIT_mmole,
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
            """
        ),
        Parameter(
            "R1_Km", name="Km R1", value=0.1, unit=UNIT_mM,
            sboTerm=SBO.MICHAELIS_CONSTANT,
            notes="""
            **Parameter**

            Parameters can be generated via the `Parameter` object. It is best
            practise to set a `name`, `unit` and `sboTerm`.
            Use the `notes` field to describe the model component.
            """
        ),
        Parameter(
            "R1_Vmax",
            name="Vmax R1",
            value=10.0,
            unit=UNIT_mmole_per_min,
            sboTerm=SBO.MAXIMAL_VELOCITY,
        ),
        InitialAssignment(
            "S1", "10.0 mM", unit=UNIT_mM,
            notes="""
            **InitialAssignment**

            InitialAssignments are generated via the `InitialAssignment` object.
            These allow to calculate the values of parameters, species or compartments
            at the begin of the simulation. Here we set the initial concentration of
            `S1` to `10 mM`.
            """
        )
    ]
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
