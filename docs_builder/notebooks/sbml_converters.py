#!/usr/bin/env python
# coding: utf-8

# # SBML converters
# `sbmlutils` provides functionality for converting formats to SBML and SBML to some formats.

# ## XPP to SBML
# In this example a given xpp model is converted to SBML.

# In[1]:


from sbmlutils.converters import xpp

# convert to SBML
xpp.xpp2sbml(xpp_file="./xpp/SkM_AP_KCa.ode", sbml_file="./xpp/SkM_AP_KCa.xml")


# In[ ]:




