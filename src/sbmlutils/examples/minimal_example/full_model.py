"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
from pathlib import Path
from typing import List

from sbmlutils.creator import FactoryResult, create_model
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.units import *


# -------------------------------------------------------------------------------------
mid: str = "full_model"
packages: List[str] = ["distrib", "fbc"]
notes = Notes(
    [
        "<h1>full_model</h1>"
        "<h2>Description</h2>"
        "<p>Example demonstrating more complete information in SBML model.</p>",
        templates.terms_of_use,
    ]
)
creators = [
    Creator(
        familyName="Koenig",
        givenName="Matthias",
        email="koenigmx@hu-berlin.de",
        organization="Humboldt-University Berlin, Institute for Theoretical Biology",
        site="https://livermetabolism.com",
    )
]
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_m,
    UNIT_m2,
    UNIT_min,
    UNIT_mmole,
    UNIT_mM,
    UNIT_mmole_per_min,
    UNIT_litre_per_min,
]
compartments: List[Compartment] = [
    Compartment(
        sid="cell",
        metaId="meta_cell",
        value=1.0,
        # unit support
        unit=UNIT_KIND_LITRE,
        spatialDimensions=3,
        constant=True,
        # annotation and sbo support
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=[(BQB.IS, "ncit/C48694")],
        # provenance via notes
        notes="Overall cell compartment with volume set to an arbitrary "
        "value of 1.0.",
        # uncertainties
        uncertainties=[
            Uncertainty(
                formula="normal(1.0, 0.1)",
                uncertParameters=[
                    UncertParameter(type=UNCERTTYPE_MEAN, value=1.0),
                    UncertParameter(type=UNCERTTYPE_STANDARDDEVIATION, value=0.1),
                ],
                uncertSpans=[
                    UncertSpan(
                        type=UNCERTTYPE_RANGE,
                        valueLower=0.2,
                        valueUpper=3.0,
                    ),
                ],
            )
        ],
    ),
]
species: List[Species] = [
    Species(
        sid="S1",
        metaId="meta_S1",
        name="glucose",
        compartment="cell",
        # clean handling of amounts vs. concentrations
        initialConcentration=10.0,
        substanceUnit=UNIT_mmole,
        hasOnlySubstanceUnits=False,
        # additional information via FBC
        sboTerm=SBO.SIMPLE_CHEMICAL,
        chemicalFormula="C6H12O6",
        charge=0,
        annotations=[
            (BQB.IS, "chebi/CHEBI:4167"),
            (BQB.IS, "inchikey/WQZGKKKJIJFFOK-GASJEMHNSA-N"),
        ],
        notes="Species represents D-glucopyranose.",
    ),
    Species(
        sid="S2",
        metaId="meta_S2",
        name="glucose 6-phosphate",
        initialConcentration=10.0,
        compartment="cell",
        substanceUnit=UNIT_mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        chemicalFormula="C6H11O9P",
        charge=0,
        annotations=[(BQB.IS, "chebi/CHEBI:58225")],
    ),
]
parameters: List[Parameter] = [
    Parameter(
        sid="k1",
        value=0.1,
        constant=True,
        unit=UNIT_litre_per_min,
    ),
]
reactions: List[Reaction] = [
    Reaction(
        sid="J0",
        name="hexokinase",
        equation="S1 -> S2",
        # reactions should have compartment set for layouts
        compartment="cell",
        formula=("k1 * S1", UNIT_mmole_per_min),  # [liter/min]* [mmole/liter]
        pars=[
            Parameter(
                sid="J0_lb",
                value=0.0,
                constant=True,
                unit=UNIT_mmole_per_min,
                name="lower flux bound J0",
            ),
            Parameter(
                sid="J0_ub",
                value=1000.0,
                constant=True,
                unit=UNIT_mmole_per_min,
                name="upper flux bound J0",
            ),
        ],
        # additional fbc information (here used for constraint testing)
        lowerFluxBound="J0_lb",
        upperFluxBound="J0_ub",
        notes="Simplified hexokinase reaction ignoring ATP, ADP cofactors."
        "Reaction is not mass and charge balanced.",
        annotations=[(BQB.IS, "uniprot/P17710")],
    ),
]
constraints: List[Constraint] = [
    Constraint("J0_lb_constraint", math="J0 >= J0_lb"),
    Constraint("J0_ub_constraint", math="J0 >= J0_ub"),
]
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        modules=["sbmlutils.examples.minimal_example.full_model"],
        output_dir=Path(__file__).parent,
        # now unit valid model
        units_consistency=True,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
