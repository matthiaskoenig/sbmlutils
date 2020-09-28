#!/usr/bin/env python
# coding: utf-8

# # SBML report
# `sbmlutils` can create HTML reports from given SBML files. Such an HTML report provides a 
# simple entry point to get an overview over an existing SBML model or browse content of a model in a more human-readable format.
# 
# ## Create report
# The following example demonstrates how an SBML report can be created from given models.

# In[1]:


from sbmlutils.report import sbmlreport


# ### Repressilator
# The first report is for the repressilator downloaded from biomodels (https://www.ebi.ac.uk/biomodels/BIOMD0000000012).
# To create a report on provides the path to the SBML file and the directory where the report should be written. As part of the model report creation the model is validated by default. In this example we deactivate the `units_consistency` checks.
# 
# The created SBML report can be accessed from [./reports/BIOMD0000000012.html](./reports/BIOMD0000000012.html).

# In[2]:


# create SBML report without performing units checks
from notebook import BASE_DIR

sbmlreport.create_report(
    sbml_path=BASE_DIR / "models" / "BIOMD0000000012.xml", 
    output_dir=BASE_DIR / "reports", 
    units_consistency=False
)


# ### Platelet metabolism
# In the second example we create a report for a model for Human platelet metabolism from the BiGG model database:
# http://bigg.ucsd.edu/models/iAT_PLT_636
# The example contains an SBML error because the `listOfFluxObjectives` cannot be empty.
#     
# The created SBML report can be accessed from [./reports/iAT_PLT_636.xml.html](./reports/iAT_PLT_636.xml.html).

# In[3]:


# create SBML report without performing units checks
sbmlreport.create_report(
    BASE_DIR / "models" / "iAT_PLT_636.xml.gz", 
    output_dir= BASE_DIR / "reports", 
    units_consistency=False, 
    modeling_practice=False
)


# In[ ]:




