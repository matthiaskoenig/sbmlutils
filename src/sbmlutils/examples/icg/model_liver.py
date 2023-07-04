"""ICG liver model."""
from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.icg import MODEL_BASE_PATH, annotations, templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")
    mmole_per_min_l = UnitDefinition("mmole_per_min_l", "mmole/min/l")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    per_min = UnitDefinition("per_min", "1/min")


_m = Model(
    "icg_liver",
    name="model for icg elimination by the liver",
    notes="""
    # Model for icg elimination by the liver

    ## Description
    Model for hepatic elimination of indocyanine green
    encoded in <a href="http://sbml.org">SBML</a> format.

    **Assumptions:**

    - icg is only metabolized in the liver

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
        "Vext",
        4,
        name="plasma",
        unit=U.liter,
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["plasma"],
        port=True,
    ),
    Compartment(
        "Vli",
        1.5,
        name="liver",
        unit=U.liter,
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["li"],
        port=True,
    ),
    Compartment(
        "Vbi",
        1.0,
        name="bile",
        unit=U.liter,
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["bi"],
        port=True,
    ),
    Compartment(
        "Vfeces",
        1.0,
        name="feces",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        unit=U.liter,
        annotations=annotations.compartments["feces"],
        port=True,
    ),
]

_m.species = [
    Species(
        "icg_ext",
        initialConcentration=0.0,
        name="icg (plasma)",
        compartment="Vext",
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        annotations=annotations.species["icg"],
        port=True,
    ),
    Species(
        sid="bil_ext",
        initialConcentration=0.01,
        name="bilirubin (extern)",
        compartment="Vext",
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        constant=True,
        annotations=annotations.species["bil"],
        notes="""
        Reference range: 0.01 [mmole/l] (~ 1 mg/dl)
        """,
    ),
    Species(
        "icg",
        initialConcentration=0.0,
        name="icg (liver)",
        compartment="Vli",
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        annotations=annotations.species["icg"],
    ),
    Species(
        "icg_bi",
        initialConcentration=0.0,
        name="icg (bile)",
        compartment="Vbi",
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=False,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        annotations=annotations.species["icg"],
    ),
    Species(
        "icg_feces",
        initialConcentration=0.0,
        name="icg (feces)",
        compartment="Vfeces",
        substanceUnit=U.mmole,
        hasOnlySubstanceUnits=True,
        sboTerm=SBO.SIMPLE_CHEMICAL,
        annotations=annotations.species["icg"],
        port=True,
    ),
]

_m.reactions = [
    Reaction(
        "ICGIM",
        name="ICG import",
        equation="icg_ext -> icg [bil_ext]",
        sboTerm=SBO.TRANSPORT_REACTION,
        compartment="Vli",
        pars=[
            Parameter(
                "ICGIM_Vmax",
                value=0.03695988403275034,
                unit=U.mmole_per_min_l,
                name="Vmax for icg import",
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
            Parameter(
                "ICGIM_Km",
                0.021659178617926003,
                unit=U.mM,
                name="Km icg of icg import",
                sboTerm=SBO.MICHAELIS_CONSTANT_FOR_SUBSTRATE,
            ),
            Parameter(
                "ICGIM_ki_bil",
                0.02,
                unit=U.mM,
                name="Ki bilirubin of icg import",
                sboTerm=SBO.INHIBITORY_CONSTANT,
                notes="""
                bilirubin reference range:
                ```
                ~ 0.1 - 5 [g/dl]
                (10 [mg/l] /584.6623 [g/mole]) ~ 0.0171 mmole/l`
                ```

                setting Ki in reference range
                """,
            ),
            Parameter(
                "f_oatp1b3",
                1,
                unit=U.dimensionless,
                name="scaling factor protein amount",
                sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                notes="""
             Parameter for scaling transport protein amount.
             """,
            ),
        ],
        formula=(
            "f_oatp1b3 * ICGIM_Vmax * Vli * icg_ext/"
            "(ICGIM_Km * (1 dimensionless + bil_ext/ICGIM_ki_bil) + icg_ext)",
            U.mmole_per_min,
        ),
        annotations=[
            (BQB.IS, "uniprot/Q9NPD5"),
            (BQB.IS, "omit/0040643"),
            (BQB.IS_ENCODED_BY, "ncit/C106617"),
        ],
        notes="""
        Solute carrier organic anion transporter family member 1B3 (SLCO1B3).
        Often referred to as OATP1B3.
        Bilirubin effect was modeled as competitive inhibition.
        """,
    ),
    # Transport from liver into bile
    Reaction(
        "ICGLI2CA",
        name="ICG export (bile)",
        equation="icg -> icg_bi",
        sboTerm=SBO.TRANSPORT_REACTION,
        compartment="Vli",
        pars=[
            Parameter(
                "ICGLI2CA_Vmax",
                0.0009436727699758908,
                name="Vmax bile export icg",
                unit=U.mmole_per_min_l,
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
            Parameter(
                "ICGLI2CA_Km",
                0.01238865924362501,
                unit=U.mM,
                name="Km bile export icg",
                sboTerm=SBO.MICHAELIS_CONSTANT_FOR_SUBSTRATE,
            ),
        ],
        formula=("ICGLI2CA_Vmax * Vli * icg/(ICGLI2CA_Km + icg)", U.mmole_per_min),
        annotations=[(BQB.IS_VERSION_OF, "uniprot/P21439")],
        notes="""
        Phosphatidylcholine translocator ABCB4
        """,
    ),
    Reaction(
        "ICGLI2BI",
        name="ICG bile transport",
        equation="icg_bi -> icg_feces",
        sboTerm=SBO.TRANSPORT_REACTION,
        compartment="Vli",
        pars=[
            Parameter(
                "ICGLI2BI_Vmax",
                0.00011459660450792535,
                unit=U.per_min,
                sboTerm=SBO.MAXIMAL_VELOCITY,
                name="Vmax bile transport icg",
            ),
        ],
        formula=("ICGLI2BI_Vmax * Vli * icg_bi", U.mmole_per_min),
        notes="""
        As simplification transport directly into feces (no information on
        time course available). No transport proteins involved in the biliary
        secretion into the duodenum.
        """,
    ),
]

model = _m


if __name__ == "__main__":
    results = create_model(model=model, filepath=MODEL_BASE_PATH / f"{model.sid}.xml")
    visualize_sbml(results.sbml_path)
