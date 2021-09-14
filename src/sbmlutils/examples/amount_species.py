"""Model with amount and concentration species."""

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.report.sbmlreport import create_online_report

from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    s = UnitDefinition("s", "s")
    mmole = UnitDefinition("mmole", "mmole")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
    kg = UnitDefinition("kg", "kg")
    per_s = UnitDefinition("per_s", "1/s")
    mmole_per_s = UnitDefinition("mmole_per_s", "mmole/s")


model = Model(
    sid="amount_species_example",
    notes="""
    # Example model with species in amounts and concentrations
    ## Description
    This example model demonstrates how to define species in amounts and concentrations.
    The key is to set the `hasOnlySubstanceUnits` on the species.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    model_units=ModelUnits(
        time=U.s,
        substance=U.mmole,
        extent=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.m3,
    ),
    units=U,
    objects=[
        Compartment(
            sid="Vc", value=1e-06, unit=U.m3, constant=False, name="cell compartment",
            sboTerm=SBO.PHYSICAL_COMPARTMENT
        ),
        Species(
            sid="Aglc",
            notes="""
            Species in amounts. The unit of the species is the `substanceUnit`,
            i.e. [mmole].
            """,
            name="glucose",
            compartment="Vc",
            initialAmount=5.0,
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=True,
            boundaryCondition=False,
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Species(
            sid="Cglc6p",
            notes="""
            Species in concentration via the `hasOnlySubstanceUnit=False`.
            The unit of the species is the
            `substanceUnit/compartmentUnit`, i.e. [mmole/litre].
            """,
            name="glucose 6-phosphate",
            compartment="Vc",
            initialAmount=0.0,
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=False,
            boundaryCondition=False,
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Reaction(
            sid="R1",
            equation="Aglc => Cglc6p",
            compartment="Vc",
            pars=[Parameter("k1", 1.0, U.per_s)],
            rules=[],
            formula=("k1 * Aglc", U.mmole_per_s),
            sboTerm=SBO.BIOCHEMICAL_REACTION,
        ),
        AssignmentRule("Vc", "2.0 m3 * exp(time/1 s)"),
    ],
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=model,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    results = create()
