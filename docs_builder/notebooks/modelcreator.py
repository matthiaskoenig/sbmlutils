#!/usr/bin/env python
# coding: utf-8

# # Modelcreator
# `sbmlutils` provides helpers for the creation of SBML models from scratch.
# 
# ## Create FBA Model
# This example demonstrates the creation of an SBML FBA model from scratch.

# In[1]:


from sbmlutils import fbc
from sbmlutils import sbmlio
from sbmlutils import factory
from sbmlutils.dfba import builder

from sbmlutils.units import *
from sbmlutils.factory import *


# ### Unit definitions
# Units for the model are defined in the following manner.

# In[2]:


model_units = ModelUnits(time=UNIT_KIND_SECOND, 
                         extent=UNIT_KIND_ITEM, 
                         substance=UNIT_KIND_ITEM, 
                         length=UNIT_KIND_METRE,
                         area='m2', 
                         volume='m3')

units = [
    Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)]),
    Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
    Unit('item_per_s', [(UNIT_KIND_ITEM, 1.0),
                           (UNIT_KIND_SECOND, -1.0)]),
    Unit('item_per_m3', [(UNIT_KIND_ITEM, 1.0),
                            (UNIT_KIND_METRE, -3.0)]),
]

# constants for reuse
UNIT_TIME = UNIT_KIND_SECOND
UNIT_AMOUNT = UNIT_KIND_ITEM
UNIT_AREA = 'm2'
UNIT_VOLUME = 'm3'
UNIT_CONCENTRATION = 'item_per_m3'
UNIT_FLUX = 'item_per_s'


# ### Model building
# Creation of FBA model using multiple packages (`comp`, `fbc`).

# In[3]:


# Create SBMLDocument with fba
doc = builder.template_doc_fba(model_id="toy")
model = doc.getModel()

factory.create_objects(model, units)
factory.set_model_units(model, model_units)

objects = [
    # compartments
    Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                   spatialDimensions=3),
    Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimensions=3),
    Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimensions=2),

    # exchange species
    Species(sid='A', name="A", initialAmount=0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
               compartment="extern"),
    Species(sid='C', name="C", initialAmount=0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
               compartment="extern"),

    # internal species
    Species(sid='B1', name="B1", initialAmount=0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
               compartment="cell"),
    Species(sid='B2', name="B2", initialAmount=0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
               compartment="cell"),

    # bounds
    Parameter(sid="ub_R1", value=1.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
    Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
    Parameter(sid="ub_default", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True,
                 sboTerm=builder.FLUX_BOUND_SBO),
]
factory.create_objects(model, objects)

# reactions
r1 = factory.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
                        reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
r2 = factory.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,
                        reactants={"B1": 1}, products={"B2": 1}, compartment='cell')
r3 = factory.create_reaction(model, rid="R3", name="B2 export (R3)", fast=False, reversible=True,
                        reactants={"B2": 1}, products={"C": 1}, compartment='membrane')

# flux bounds
fbc.set_flux_bounds(r1, lb="zero", ub="ub_R1")
fbc.set_flux_bounds(r2, lb="zero", ub="ub_default")
fbc.set_flux_bounds(r3, lb="zero", ub="ub_default")

# exchange reactions
builder.create_exchange_reaction(model, species_id="A", flux_unit=UNIT_FLUX)
builder.create_exchange_reaction(model, species_id="C", flux_unit=UNIT_FLUX)

# objective function
model_fbc = model.getPlugin("fbc")
fbc.create_objective(model_fbc, oid="R3_maximize", otype="maximize",
                    fluxObjectives={"R3": 1.0}, active=True)

# write SBML file
import tempfile
sbml_file = tempfile.NamedTemporaryFile(suffix=".xml")
sbmlio.write_sbml(doc=doc, filepath=sbml_file.name)


# In[ ]:




