#!/usr/bin/env python
# coding: utf-8

# # SBML manipulation
# `sbmlutils` provides functionality for manipulating existing models. Examples are the merging of multiple SBML models in a combined model.
# 
# ## Model merging
# Merge multiple models into a combined model using the `comp` package.

# In[1]:


import os
import libsbml
from pprint import pprint

from sbmlutils import comp
from sbmlutils import validation
from sbmlutils import manipulation
from sbmlutils.tests.data import data_dir

merge_dir = os.path.join(data_dir, 'manipulation', 'merge')

# dictionary of ids & paths of models which should be combined
# here we just bring together the first Biomodels
model_ids = ["BIOMD000000000{}".format(k) for k in range(1, 5)]
model_paths = dict(zip(model_ids,
                       [os.path.join(merge_dir, "{}.xml".format(mid)) for mid in model_ids])
                   )
pprint(model_paths)

# create merged model
output_dir = os.path.join(merge_dir, 'output')
doc = manipulation.merge_models(model_paths, out_dir=output_dir, validate=False)

# validate
Nall, Nerr, Nwarn = validation.check_doc(doc, units_consistency=False)
assert Nerr == 0
assert Nwarn == 0
assert Nall == 0

# write the merged model
print(libsbml.writeSBMLToString(doc))
libsbml.writeSBMLToFile(doc, os.path.join(output_dir, "merged.xml"))

# flatten the merged model
doc_flat = comp.flatten_sbml(doc)
Nall, Nerr, Nwarn = validation.check_doc(doc_flat, units_consistency=False)
libsbml.writeSBMLToFile(doc_flat, os.path.join(output_dir, "merged_flat.xml"));


# In[ ]:




