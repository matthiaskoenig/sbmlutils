# sbmlutils
[![Build Status](https://travis-ci.org/matthiaskoenig/sbmlutils.svg?branch=develop)](https://travis-ci.org/matthiaskoenig/sbmlutils)
[![codecov](https://codecov.io/gh/matthiaskoenig/sbmlutils/branch/develop/graph/badge.svg)](https://codecov.io/gh/matthiaskoenig/sbmlutils)
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

## Installation
The latest stable version can be installed via 
```
pip install sbmlutils
```

The latest develop version is available via
```
pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop
```

Or via cloning the repository and installing via
```
pip install -e .
```

## Release notes

### 0.1.3
* python 3 support
* clean travis build with pip
* DFBA implementation
* bugfixes & improvements

### 0.1.2
* fixed unittests and bug fixes

### 0.1.1
* bug fixes, refactoring, unit tests
* model creator examples

### 0.1.0
* initial release

----
&copy; 2017 Matthias König.
