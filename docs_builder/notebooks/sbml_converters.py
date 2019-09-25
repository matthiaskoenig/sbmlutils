#!/usr/bin/env python
# coding: utf-8

# # SBML converters
# `sbmlutils` provides functionality for converting formats to SBML and SBML to some formats.

# In[1]:


from sbmlutils.report import sbmlreport


# ## XPP to SBML
# In this example a given xpp model is converted to SBML.

# In[2]:


from sbmlutils.converters import xpp
from sbmlutils import validation

# convert to SBML
xpp.xpp2sbml(xpp_file="./xpp/SkM_AP_KCa.ode", sbml_file="./xpp/SkM_AP_KCa.xml")

