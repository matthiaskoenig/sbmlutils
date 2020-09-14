#!/usr/bin/env python
# coding: utf-8

# # SBML annotation
# Annotation of model components with meta-information is an important step during model building. Annotation is the process of adding metadata to the model and model components. These metadata are mostly from biological ontologies or biological databases.
# 
# `sbmlutils` provides functionality for annotating SBML models which can be used during model creation or later on to add annotations to SBML models. Annotations have the form of RDF triples consisting of the model component to annotate (subject), the relationship between model component and annotation term (predicate), and a term which describes the meaning of the component (object), which often comes from an ontology of defined terms.
# 
# The predicates come from a clearly defined set of predicates, the MIRIAM qualifiers (https://co.mbine.org/standards/qualifiers).
# Ideally the objects, i.e. annotations, are defined in an ontology which is registered at https://identifiers.org (see https://registry.identifiers.org/registry for available resources).
# 
# For more information of the importance of model annotations and best practises we refer to
# 
# > Neal, M.L., König, M., Nickerson, D., Mısırlı, G., Kalbasi, R., Dräger, A., Atalag, K., Chelliah, V., Cooling, M.T., Cook, D.L. and Crook, S., 2019. Harmonizing semantic annotations for computational models in biology. Briefings in bioinformatics, 20(2), pp.540-550. [10.1093/bib/bby087](https://doi.org/10.1093/bib/bby087)
# 
# > Le Novère, N., Finney, A., Hucka, M., Bhalla, U.S., Campagne, F., Collado-Vides, J., Crampin, E.J., Halstead, M., Klipp, E., Mendes, P. and Nielsen, P., 2005. Minimum information requested in the annotation of biochemical models (MIRIAM). Nature biotechnology, 23(12), pp.1509-1515. https://www.nature.com/articles/nbt1156
# 
# Annotations in `sbmlutils` consist of associating `(predictate, object)` tuples to model components. For instance to describe that a `species` in the model is a certain entry from CHEBI, we associate `(BQB.IS, "chebi/CHEBI:28061")` with the species. In addition the special subset of annotations to the Systems Biology Ontology (SBO) can be directly set on all model components via the `sboTerm` attribute.

# In[1]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# ### Annotate during model creation
# In the example the model is annotated during the model creation process. Annotations are encoded as simple tuples consisting of MIRIAM identifiers terms and identifiers.org parts. The list of tuples is provided on object creation. In the example we annotate a `species`

# In[2]:


from sbmlutils.units import *
from sbmlutils.factory import *
from sbmlutils.annotation import *
from sbmlutils.modelcreator.creator import CoreModel
from sbmlutils.validation import validate_doc

model_dict = {
    'mid': 'example_annotation',
    'compartments': [
        Compartment(sid="C", value=1.0, sboTerm=SBO_PHYSICAL_COMPARTMENT)
    ],
    'species': [
        Species(sid='gal', compartment='C', initialConcentration=3.0,
                name='D-galactose', sboTerm=SBO_SIMPLE_CHEMICAL,
                annotations=[
                    (BQB.IS, "bigg.metabolite/gal"),  # galactose
                    (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
                    (BQB.IS, "vmhmetabolite/gal"),
                ]
        )
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# For a more complete example see [model_with_annotations.py](./model_with_annotations.py) which creates annotations of the form
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

# In[3]:


import os
from sbmlutils.modelcreator.creator import Factory
factory = Factory(modules=['model_with_annotations'],
                  output_dir='./models')
[_, _, sbml_path] = factory.create()

# check the annotations on the species
import libsbml
doc = libsbml.readSBMLFromFile(sbml_path)  # type: libsbml.SBMLDocument
model = doc.getModel()  # type: libsbml.Model
s1 = model.getSpecies('e__gal')  # type: libsbml.Species
print(s1.toSBML())


# ### Annotate existing model
# An alternative approach is to annotate existing models from external annotation files.
# For instance we can define the annotations in an external file which we then add to the model based on identifier matching.
# The following annotations are written to the [./annotations/demo.xml](./annotations/demo.xml) based on pattern matching.
# 
# Annotations are written for the given `sbml_type` for all SBML identifiers which match the given pattern.

# In[4]:


from sbmlutils.annotation.annotator import ModelAnnotator
df = ModelAnnotator.read_annotations_df("./annotations/demo_annotations.xlsx", file_format="xlsx")
df


# In[5]:


from sbmlutils.annotation.annotator import annotate_sbml

# create SBML report without performing units checks
annotate_sbml(f_sbml="./annotations/demo.xml",
              annotations_path="./annotations/demo_annotations.xlsx",
              filepath="./annotations/demo_annotated.xml")


# In[ ]:




