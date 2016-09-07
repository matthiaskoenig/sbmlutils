# sbmlutils
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&amp;hosted_button_id=RYHNRJFBMWD5N" title="Donate to this project using Paypal"><img src="https://img.shields.io/badge/paypal-donate-yellow.svg" alt="PayPal donate button" /></a>
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)

**sbmlutils** are a collection of python utilities for working with [SBML](http://www.sbml.org) models.
 This utilities are implemented on top of the libsbml python bindings. This package works with the latest
 develop version of libsbml.

Features
* SBML model creator
* SBML annotator
* SBML report

## Installation
Either install directly from the git repository
```
pip install git+https://github.com/matthiaskoenig/sbmlutils.git
```
clone the repository locally
```
git clone https://github.com/matthiaskoenig/sbmlutils.git
cd sbmlutils
python setup.py install
```
To work in develop use
```
python setup.py develop
```
### Requirements
* libsbml python bindings


## License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Features
### SBML Model Creator
The model creator creates SBML models from stored information.
The information is handled in python data structures like lists and dictionaries.

#### Model structure
Models consist of
* Cell.py: cell model information
* Reactions.py: reaction information

Models should be able to import information from general models.
This is handled via the combination of the dictionaries/list of the various models.
The combined model is the combination of the information, with later information
overwriting the general information of the model.

Within the reaction equations the role of the species have to be defined, i.e. the
SBO terms for the SpeciesReferences.
In addition the kinetic law has to be annotated.

### SBML annotator
Annotations are defined in separate annotation files. 
For a id regular pattern the annotations are listed.

### SBML Report
HTML report of SBML models.


## Changelog
**v0.1.2** [2016-09-07]
* fixed unittests and bug fixes

**v0.1.1** [2016-05-12]
* bug fixes, refactoring, unit tests
* model creator examples

**v0.1.0** [2015-05-01]
* first release


----
&copy; 2016 Matthias König.