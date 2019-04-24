#!/usr/bin/env python
# coding: utf-8

# # DFBA
# This section describes how to run dynamic FBA (DFBA) with `sbmlutils`.

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


import os
import sbmlutils
from sbmlutils import dfba
from sbmlutils.dfba import utils


# ## Simulate DFBA model
# To run an existing DFBA model call use `simulate_dfba`.

# In[3]:


# get the absolute path to the top model
from sbmlutils.dfba.toy_wholecell import settings as toysettings
from sbmlutils.dfba.toy_wholecell import model_factory as toyfactory
from sbmlutils.dfba.toy_wholecell import simulate as toysimulate

sbml_path = os.path.join(utils.versioned_directory(toysettings.OUT_DIR, toysettings.VERSION), 
                         toysettings.TOP_LOCATION)
print(sbml_path)

# run simulation with the top model
from sbmlutils.dfba.simulator import simulate_dfba
df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=50, dt=5.0)
df


# ## Toy example

# In[4]:


from sbmlutils.dfba.toy_wholecell import settings as toysettings
from sbmlutils.dfba.toy_wholecell import model_factory as toyfactory
from sbmlutils.dfba.toy_wholecell import simulate as toysimulate

import tempfile
test_dir = tempfile.mkdtemp()

# create the toy model
toyfactory.create_model(test_dir)
# here the files are generated
sbml_path = os.path.join(utils.versioned_directory(test_dir, toysettings.VERSION),
                         toysettings.TOP_LOCATION)
print(sbml_path)
# simulate
dfs = toysimulate.simulate_toy(sbml_path, test_dir, dts=[1.0], figures=False)

toysimulate.print_species(dfs=dfs)
toysimulate.print_fluxes(dfs=dfs)
print(dfs[0].head())


# ## Diauxic growth

# In[5]:


'''
from sbmlutils.dfba.diauxic_growth import settings as dgsettings
from sbmlutils.dfba.diauxic_growth import model_factory as dgfactory
from sbmlutils.dfba.diauxic_growth import simulate as dgsimulate
from sbmlutils.dfba.diauxic_growth import analyse as dganalyse

import tempfile
test_dir = tempfile.mkdtemp()

# create the model
dgfactory.create_model(test_dir)

# top model file
sbml_path = os.path.join(utils.versioned_directory(test_dir, dgsettings.VERSION),
                         dgsettings.TOP_LOCATION)
print(sbml_path)

# run DFBA
dfs = dgsimulate.simulate_diauxic_growth(sbml_path, test_dir, dts=[0.01], figures=False)

# plot results
dganalyse.print_species(dfs=dfs)
dganalyse.print_fluxes(dfs=dfs)
print(dfs[0].head())
'''


# In[ ]:




