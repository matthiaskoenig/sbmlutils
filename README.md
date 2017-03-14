# sbmlutils
[![Build Status](https://travis-ci.org/matthiaskoenig/sbmlutils.svg?branch=develop)](https://travis-ci.org/matthiaskoenig/sbmlutils)
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.61737.svg)](http://dx.doi.org/10.5281/zenodo.61737)

**sbmlutils** are a collection of python utilities for working with [SBML](http://www.sbml.org) models.
 This utilities are implemented on top of the libsbml python bindings. This package works with the latest
 develop version of libsbml.

    @MISC{libsbgnpy,
      author        = {Matthias Koenig},
      title         = {sbmlutils: python utilities for SBML},
      month         = {Sep.},
      year          = {2016},
      doi           = "{10.5281/zenodo.61737}",
      url           = "{http://dx.doi.org/10.5281/zenodo.61737}",
      howpublished  = {https://github.com/matthiaskoenig/sbmlutils/blob/master/README.md}
    }

## License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Features
### modelcreator
The modelcreator provides utilities to create SBML models.
Model information is managed in python data structures which are used
to create the models.

The model definition consists of
* `Cell.py`: basic model information
* `Reactions.py`: reaction information

Models can extend other models and reuse information from 
defined models.

### dfba
Simulator for simulation of multi-framework SBML models.
Currently, supports dynamic FBA by coupling ODE and FBA models.

### annotator
The annotator provides simple means for the annotation of models.
Annotations are hereby defined in separate annotation files with 
annotations being matched to ids based on regular expression matching.

### report
HTML report of SBML models. This provides simple overview of the 
information defined in the model

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

## Development


----
&copy; 2017 Matthias König.
