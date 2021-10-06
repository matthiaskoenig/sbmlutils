"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
from pathlib import Path

import libsbml

from sbmlutils import EXAMPLES_DIR
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    l_per_min = UnitDefinition("l_per_min", "l/min")


_m = Model(
    sid="complete_model",
    packages=["distrib", "fbc"],
    notes="""
    # Complete model
    Example demonstrating more complete information in SBML model.
    Showcasing combination of multiple features.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
)
_m.compartments = [
    Compartment(
        sid="cell",
        metaId="meta_cell",
        value=1.0,
        # unit support
        unit=U.liter,
        spatialDimensions=3,
        constant=True,
        # annotation and sbo support
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=[(BQB.IS, "ncit/C48694")],
        # provenance via notes
        notes="""
        Overall cell compartment with volume set to an arbitrary value of 1.0.
        """,
        # uncertainties
        uncertainties=[
            Uncertainty(
                formula="normal(1.0, 0.1)",
                uncertParameters=[
                    UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=1.0),
                    UncertParameter(
                        type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.1
                    ),
                ],
                uncertSpans=[
                    UncertSpan(
                        type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                        valueLower=0.2,
                        valueUpper=3.0,
                    ),
                ],
            )
        ],
    ),
]
_m.species = [
    Species(
        sid="S1",
        metaId="meta_S1",
        name="glucose",
        compartment="cell",
        # clean handling of amounts vs. concentrations
        initialConcentration=10.0,
        substanceUnit=U.mmole,
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
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        chemicalFormula="C6H11O9P",
        charge=0,
        annotations=[(BQB.IS, "chebi/CHEBI:58225")],
    ),
]
_m.parameters = [
    Parameter(
        sid="k1",
        value=0.1,
        constant=True,
        unit=U.l_per_min,
        sboTerm=SBO.KINETIC_CONSTANT,
    ),
]
_m.reactions = [
    Reaction(
        sid="J0",
        name="hexokinase",
        equation="S1 -> S2",
        # reactions should have compartment set for layouts
        compartment="cell",
        formula=("k1 * S1", U.mmole_per_min),  # [liter/min]* [mmole/liter]
        pars=[
            Parameter(
                sid="J0_lb",
                value=0.0,
                constant=True,
                unit=U.mmole_per_min,
                name="lower flux bound J0",
            ),
            Parameter(
                sid="J0_ub",
                value=1000.0,
                constant=True,
                unit=U.mmole_per_min,
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
_m.constraints = [
    Constraint("J0_lb_constraint", math="J0 >= J0_lb"),
    Constraint("J0_ub_constraint", math="J0 >= J0_ub"),
]


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        # now unit valid model
        units_consistency=True,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
