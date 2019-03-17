# -*- coding=utf-8 -*-
"""
Example model for creating an SBML ODE model.
"""
from sbmlutils.units import *
from sbmlutils.sbo import *
from sbmlutils.factory import *
from sbmlutils.modelcreator import templates

# ---------------------------------------------------------------------------------------------------------------------
mid = 'example1'
version = 1
notes = Notes([
    """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example model showing how to create compartments, species and reactions.
    </p>
    """,
    templates.terms_of_use
])
creators = [
    Creator(familyName='Koenig',
            givenName='Matthias',
            email='koenigmx@hu-berlin.de',
            organization='Humboldt-University Berlin, Institute for Theoretical Biology',
            site="https://livermetabolism.com")
]

# ---------------------------------------------------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------------------------------------------------
UNIT_VOLUME = UNIT_KIND_LITRE
UNIT_SUBSTANCE = UNIT_mmole
UNIT_TIME = UNIT_min
UNIT_FLUX = UNIT_mmole_per_min

model_units = ModelUnits(time=UNIT_TIME, extent=UNIT_SUBSTANCE, substance=UNIT_SUBSTANCE,
                         length=UNIT_KIND_METER, area=UNIT_m2, volume=UNIT_VOLUME)
units = [
    UNIT_min,
    UNIT_mmole,
    UNIT_mM,
    UNIT_mmole_per_min,
]

# ---------------------------------------------------------------------------------------------------------------------
# --- Functions ---
# ---------------------------------------------------------------------------------------------------------------------
functions = []

# ---------------------------------------------------------------------------------------------------------------------
# Compartments
# ---------------------------------------------------------------------------------------------------------------------
compartments = [
    Compartment("c", 1.0, unit=UNIT_VOLUME)
]

# ---------------------------------------------------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------------------------------------------------
species = [
    Species("S1", initialConcentration=5.0,  compartment="c", substanceUnit=UNIT_SUBSTANCE, name="S1", hasOnlySubstanceUnits=False,
            sboTerm=SBO_SIMPLE_CHEMICAL)
]

# ---------------------------------------------------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------------------------------------------------
parameters = ([
    Parameter('R1_Km', name="Km R1", value=0.1, units=UNIT_mM, sboTerm=SBO_MICHAELIS_CONSTANT),
    Parameter('R1_Vmax', name="Vmax R1", value=10.0, units=UNIT_FLUX, sboTerm=SBO_MAXIMAL_VELOCITY),
])

# ---------------------------------------------------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------------------------------------------------
assignments = [
    InitialAssignment('S1', '10.0', UNIT_mM),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------------------------------------------------
rules = []

# ---------------------------------------------------------------------------------------------------------------------
# Reactions
# ---------------------------------------------------------------------------------------------------------------------
reactions = [

]


if __name__ == "__main__":

    import os
    from sbmlutils.modelcreator.creator import Factory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    factory = Factory(modules=['sbmlutils.examples.models.example1.model'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create()

