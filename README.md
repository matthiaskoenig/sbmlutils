
<h1><img alt="sbmlutils logo" src="./docs_builder/images/sbmlutils-logo-small.png" height="60" /> sbmlutils: python utilities for SBML</h1>

[![PyPI version](https://badge.fury.io/py/sbmlutils.svg)](https://badge.fury.io/py/sbmlutils)
[![GitHub version](https://badge.fury.io/gh/matthiaskoenig%2Fsbmlutils.svg)](https://badge.fury.io/gh/matthiaskoenig%2Fsbmlutils)
[![Build Status](https://travis-ci.org/matthiaskoenig/sbmlutils.svg?branch=develop)](https://travis-ci.org/matthiaskoenig/sbmlutils)
[![Documentation Status](https://readthedocs.org/projects/sbmlutils/badge/?version=latest)](http://sbmlutils.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/matthiaskoenig/sbmlutils/branch/develop/graph/badge.svg)](https://codecov.io/gh/matthiaskoenig/sbmlutils)
[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=flat-square)](http://opensource.org/licenses/LGPL-3.0)
[![DOI](https://zenodo.org/badge/55952847.svg)](https://zenodo.org/badge/latestdoi/55952847)


<b><a href="https://orcid.org/0000-0003-1725-179X" title="orcid id"><img src="./docs_builder/images/orcid.png" height="15"/></a> Matthias König</b>

`sbmlutils` is a collection of python utilities for working with [SBML](http://www.sbml.org) models implemented on top of [libSBML](http://sbml.org/Software/libSBML)
and other libraries available from [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils)

Features include among others

* HTML reports of SBML models
* helper functions for model creation, manipulation, and annotation
* interpolation functions to add experimental data to models
* implementation of dynamic flux balance analysis (DFBA)
* file converters (XPP)

For a more detailed description and examples see the documentation at   
<a href="https://sbmlutils.readthedocs.io/en/latest/" alt="sbmlutils logo"><img alt="sbmlutils logo" src="./docs_builder/images/readthedocs-logo.png" height="20" /></a>
  
### How to cite
[![DOI](https://zenodo.org/badge/55952847.svg)](https://zenodo.org/badge/latestdoi/55952847)  

### License
* Source Code: [LGPLv3](http://opensource.org/licenses/LGPL-3.0)
* Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)


## Installation
`sbmlutils` is available from [pypi](https://pypi.python.org/pypi/sbmlutils) and 
can be installed via 
```
pip install sbmlutils
```

### Requirements
`tkinter` is required which can be installed via
```
apt-get install python-tk
apt-get install python3-tk
```

### Develop version
The latest develop version can be installed via
```
pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop
```
Or via cloning the repository and installing via
```
pip install -e .
```

## Release notes
### 0.1.8
* DFBA release

### 0.1.7a0
* xpp converter
* updated SBML reports


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


&copy; 2017 Matthias König
