from sbmlutils.factory import *
from sbmlutils.io import validate_sbml, write_sbml
from sbmlutils.metadata import *
from sbmlutils.metadata.sbo import *
from sbmlutils.modelcreator.creator import CoreModel
from sbmlutils.units import *


def test_modelcreator_1(tmpdir):
    """Test complex model creation.
    If this test fails the respective notebook must be updated:
    :return:
    """
    UNIT_TIME = "s"
    UNIT_VOLUME = "m3"
    UNIT_LENGTH = "m"
    UNIT_AREA = "m2"
    UNIT_AMOUNT = "itm"
    UNIT_FLUX = "itm_per_s"

    model_dict = {
        "packages": ["fbc"],
        "mid": "example_model",
        "model_units": ModelUnits(
            time=UNIT_TIME,
            extent=UNIT_AMOUNT,
            substance=UNIT_AMOUNT,
            length=UNIT_LENGTH,
            area=UNIT_VOLUME,
            volume=UNIT_AREA,
        ),
        "units": {
            # using predefined units
            UNIT_s,
            UNIT_kg,
            UNIT_m,
            UNIT_m2,
            UNIT_m3,
            UNIT_mM,
            UNIT_per_s,
            # defining some additional units
            Unit("itm", [(UNIT_KIND_ITEM, 1.0)]),
            Unit("itm_per_s", [(UNIT_KIND_ITEM, 1.0), (UNIT_KIND_SECOND, -1.0)]),
            Unit("itm_per_m3", [(UNIT_KIND_ITEM, 1.0), (UNIT_KIND_METRE, -3.0)]),
        },
        "compartments": [
            Compartment(
                sid="extern",
                name="external compartment",
                value=1.0,
                unit=UNIT_VOLUME,
                constant=True,
                spatialDimensions=3,
            ),
            Compartment(
                sid="cell",
                name="cell",
                value=1.0,
                unit=UNIT_VOLUME,
                constant=True,
                spatialDimensions=3,
            ),
            Compartment(
                sid="membrane",
                name="membrane",
                value=1.0,
                unit=UNIT_AREA,
                constant=True,
                spatialDimensions=2,
            ),
        ],
        "species": [
            # exchange species
            Species(
                sid="A",
                name="A",
                initialAmount=0,
                substanceUnit=UNIT_AMOUNT,
                hasOnlySubstanceUnits=True,
                compartment="extern",
                sboTerm=SBO_SIMPLE_CHEMICAL,
            ),
            Species(
                sid="C",
                name="C",
                initialAmount=0,
                substanceUnit=UNIT_AMOUNT,
                hasOnlySubstanceUnits=True,
                compartment="extern",
                sboTerm=SBO_SIMPLE_CHEMICAL,
            ),
            # internal species
            Species(
                sid="B1",
                name="B1",
                initialAmount=0,
                substanceUnit=UNIT_AMOUNT,
                hasOnlySubstanceUnits=True,
                compartment="cell",
                sboTerm=SBO_SIMPLE_CHEMICAL,
            ),
            Species(
                sid="B2",
                name="B2",
                initialAmount=0,
                substanceUnit=UNIT_AMOUNT,
                hasOnlySubstanceUnits=True,
                compartment="cell",
                sboTerm=SBO_SIMPLE_CHEMICAL,
            ),
        ],
        "parameters": [
            Parameter(
                sid="ub_R1",
                value=1.0,
                unit=UNIT_FLUX,
                constant=True,
                sboTerm=SBO_FLUX_BOUND,
            ),
            Parameter(
                sid="zero",
                value=0.0,
                unit=UNIT_FLUX,
                constant=True,
                sboTerm=SBO_FLUX_BOUND,
            ),
            Parameter(
                sid="ub_default",
                value=1000,
                unit=UNIT_FLUX,
                constant=True,
                sboTerm=SBO_FLUX_BOUND,
            ),
        ],
        "reactions": [
            # metabolic reactions
            Reaction(
                sid="R1",
                name="A import (R1)",
                equation="A <-> B1",
                fast=False,
                reversible=True,
                compartment="membrane",
                lowerFluxBound="zero",
                upperFluxBound="ub_R1",
            ),
            Reaction(
                sid="R2",
                name="B1 <-> B2 (R2)",
                equation="B1 <-> B2",
                fast=False,
                reversible=True,
                compartment="cell",
                lowerFluxBound="zero",
                upperFluxBound="ub_default",
            ),
            Reaction(
                sid="R3",
                name="B2 export (R3)",
                equation="B1 <-> C",
                fast=False,
                reversible=True,
                compartment="membrane",
                lowerFluxBound="zero",
                upperFluxBound="ub_default",
            ),
            # exchange reactions
            ExchangeReaction(species_id="A"),
            ExchangeReaction(species_id="B1"),
        ],
        "objectives": [
            Objective(
                sid="R3_maximize",
                objectiveType="maximize",
                fluxObjectives={"R3": 1.0},
                active=True,
            )
        ],
    }

    # create SBMLDocument
    core_model = CoreModel.from_dict(model_dict)
    doc = core_model.create_sbml()

    # write SBML file
    sbml_str = write_sbml(doc=doc, validate=True)
