
<img alt="sbmlutils logo" src="./docs_builder/images/sbmlutils-logo-small.png" height="60" />
 
[![Build Status](https://travis-ci.org/matthiaskoenig/sbmlutils.svg?branch=develop)](https://travis-ci.org/matthiaskoenig/sbmlutils)
[![Documentation Status](https://readthedocs.org/projects/sbmlutils/badge/?version=latest)](http://sbmlutils.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/matthiaskoenig/sbmlutils/branch/develop/graph/badge.svg)](https://codecov.io/gh/matthiaskoenig/sbmlutils)
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)
[![DOI](https://zenodo.org/badge/55952847.svg)](https://zenodo.org/badge/latestdoi/55952847)

# sbmlutils: Python utilities for SBML
`sbmlutils` is a collection of python utilities for working with [SBML](http://www.sbml.org) models implemented on top of the [libSBML](http://sbml.org/Software/libSBML) python bindings.

Features are among others

* HTML reports of SBML models
* helper functions for model creation and manipulation
* interpolation functions to add experimental data to models
* implementation of dynamic flux balance analysis (DFBA).

For a more detailed description and examples see the documentation.

    @MISC{sbmlutils,
      author        = {Matthias König},
      title         = {sbmlutils: python utilities for SBML},
      month         = {Mar.},
      year          = {2017},
      doi           = "{10.5281/zenodo.439006}",
      url           = "{http://dx.doi.org/10.5281/zenodo.439006}"
    }

The project code is available from [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils).

## License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Documentation
[![Documentation Status](https://readthedocs.org/projects/sbmlutils/badge/?version=latest)](http://sbmlutils.readthedocs.io/en/latest/)  
Documentation with examples is available at 
<a href="https://sbmlutils.readthedocs.io/en/latest/" alt="sbmlutils logo"><img alt="sbmlutils logo" src="./docs_builder/images/readthedocs-logo.png" height="20" /></a>

## Installation
`sbmlutils` can be installed either via `pip` or directly from the source code.

### Stable version
`sbmlutils` can be installed from [https://pypi.python.org/pypi/sbmlutils](https://pypi.python.org/pypi/sbmlutils) via 
```
pip install sbmlutils
```

### Develop version
The latest develop version is available via
```
pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop
```
Or via cloning the repository and installing via
```
pip install -e .
```

### Requirements
`tkinter` is required which can be installed for python 2 via
```
apt-get install python-tk
```
or for python 3 via
```
apt-get install python3-tk
```

## Release notes

### 0.1.6
* update SBML reports (fbc & comp support)
* modelcreator fixes
* DFBA examples updated & annotated
* annotation fixes

### 0.1.4
* documentation update
* DFBA update & bug fixes
* DFBA examples (toy and diauxic growth)
* bug fixes

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


&copy; 2017 Matthias König.
