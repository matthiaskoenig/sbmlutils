"""Model with amount and concentration species."""

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.report.sbmlreport import create_report, create_online_report
from sbmlutils.units import *


model = Model(
    sid="amount_species_example",
    notes="""
    # Example model with species in amounts and concentrations
    ## Description
    This example model demonstrates how to define species in amounts and concentrations.
    The key is to set the `hasOnlySubstanceUnits` on the species.
    """ + templates.terms_of_use,
    creators=templates.creators,
    model_units=ModelUnits(
        time=UNIT_s,
        substance=UNIT_mmole,
        extent=UNIT_mmole,
        length=UNIT_m,
        area=UNIT_m2,
        volume=UNIT_m3,
    ),
    units=[
        UNIT_s,
        UNIT_kg,
        UNIT_m,
        UNIT_m2,
        UNIT_m3,
        UNIT_mM,
        UNIT_mmole,
        UNIT_per_s,
        UNIT_mmole_per_s,
    ],
    objects=[
        Compartment(
            sid="Vc", value=1e-06, unit=UNIT_m3, constant=False, name="cell compartment"
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
            substanceUnit=UNIT_mmole,
            hasOnlySubstanceUnits=True,
            boundaryCondition=False,
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
            substanceUnit=UNIT_mmole,
            hasOnlySubstanceUnits=False,
            boundaryCondition=False,
        ),
        Reaction(
            sid="R1",
            equation="Aglc => Cglc6p",
            compartment="Vc",
            pars=[Parameter("k1", 1.0, UNIT_per_s)],
            rules=[],
            formula=("k1 * Aglc", UNIT_mmole_per_s),
        ),
        AssignmentRule("Vc", "2.0 m3 * exp(time/1 s)")
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
    create_online_report(sbml_path=results.sbml_path, server="http://localhost:3456")
