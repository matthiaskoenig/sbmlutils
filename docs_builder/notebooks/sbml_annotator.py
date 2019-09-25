#!/usr/bin/env python
# coding: utf-8

# # SBML annotator
# `sbmlutils` provides functionality for annotating SBML models.
# Annotation is the process of adding metadata to the model and model components. These metadata are mostly from biological ontologies or biological databases.

# In[1]:


from sbmlutils.report import sbmlreport


# ### Annotate existing model
# In the first example annotations from an excel file are added to an existing model.
# The following annotations are written to the [./annotations/demo.xml](./annotations/demo.xml) based on pattern matching.
# 
# Annotations are written for the given `sbml_type` for all SBML identifiers which match the given pattern.

# In[2]:


from sbmlutils.annotation.annotator import ModelAnnotator
df = ModelAnnotator.read_annotations_df("./annotations/demo_annotations.xlsx", format="xlsx")
df


# In[3]:


from sbmlutils.annotation.annotator import annotate_sbml_file

# create SBML report without performing units checks
annotate_sbml_file(f_sbml="./annotations/demo.xml", 
                   f_annotations="./annotations/demo_annotations.xlsx", 
                   f_sbml_annotated="./annotations/demo_annotated.xml")


# ### Annotate during model creation
# In the second example the model is annotated during the model creation process. Annotations are encoded as simple tuples consisting of MIRIAM identifiers terms and identifiers.org parts.
# 
# The list of tuples can be provided on object generation
# 
# ```
#     Species(sid='e__gal', compartment='ext', initialConcentration=3.0,
#                 substanceUnit=UNIT_KIND_MOLE, boundaryCondition=True,
#                 name='D-galactose', sboTerm=SBO_SIMPLE_CHEMICAL,
#                 annotations=[
#                     (BQB.IS, "bigg.metabolite/gal"),  # galactose
#                     (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
#                     (BQB.IS, "vmhmetabolite/gal"),
#                 ]
#             ),
# ```
# 
# For the full example see [model_with_annotations.py](./model_with_annotations.py)

# In[4]:


import os
from sbmlutils.modelcreator.creator import Factory
factory = Factory(modules=['model_with_annotations'],
                  target_dir='./models')
[_, _, sbml_path] = factory.create()

# check the annotations on the species
import libsbml
doc = libsbml.readSBMLFromFile(sbml_path)  # type: libsbml.SBMLDocument
model = doc.getModel()  # type: libsbml.Model
s1 = model.getSpecies('e__gal')  # type: libsbml.Species
print(s1.toSBML())

