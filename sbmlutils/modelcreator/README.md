# SBML Model Creator
The model creator creates SBML models from stored information.
The information is handled in python data structures like lists and dictionaries.

## Model structure
Models consist of
* Cell.py: cell model information
* Reactions.py: reaction information
* ?

Models should be able to import information from general models.
This is handled via the combination of the dictionaries/list of the various models.
The combined model is the combination of the information, with later information
overwriting the general information of the model.


Necessary to handle multiple model variants via events.

Within the cellular models it is necessary to define which values are local and which are
global. This is achieved via compartment prefixes
e__
c__
...

names are always defined for the un-prefixed identifiers.


TODO: single cell models
TODO: annotations, description and model history

TODO: galactose tissue models (flow & pressure)


TODO: make the model creation reproducible, i.e. sort by ids

## Annotations
Annotations are defined in separate annotation files. 
For a id regular pattern the annotations are listed.

### SpeciesRole in reactions
Within the reaction equations the role of the species have to be defined, i.e. the
SBO terms for the SpeciesReferences.
In addition the kinetic law has to be annotated.
