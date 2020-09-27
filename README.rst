sbmlutils: python utilities for SBML
====================================

``sbmlutils`` is a collection of python utilities for working with
`SBML <http://www.sbml.org>`__ models implemented on top of
`libsbml <http://sbml.org/Software/libSBML>`__ and other libraries
available from https://github.com/matthiaskoenig/sbmlutils

Features include among others

-  HTML reports of SBML models
-  helper functions for model creation, manipulation, and annotation
-  interpolation functions to add experimental data to models
-  file converters (XPP)

Documentation is available at https://sbmlutils.readthedocs.io

How to cite
^^^^^^^^^^^
.. image:: https://zenodo.org/badge/55952847.svg
   :target: https://zenodo.org/badge/latestdoi/55952847
   :alt: Zenodo DOI

License
^^^^^^^
* Source Code: `LGPLv3 <http://opensource.org/licenses/LGPL-3.0>`__
* Documentation: `CC BY-SA 4.0 <http://creativecommons.org/licenses/by-sa/4.0/>`__

## Funding
Matthias König is supported by the Federal Ministry of Education and Research (BMBF, Germany)
within the research network Systems Medicine of the Liver (**LiSyM**, grant number 031L0054).


Installation
------------
`sbmlutils` is available from [pypi](https://pypi.python.org/pypi/sbmlutils) and 
can be installed via:: 

    pip install sbmlutils

Requirements
^^^^^^^^^^^^^
`tkinter` is required which can be installed on linux via::

    apt-get install python-tk
    apt-get install python3-tk

Please see the respective installation instructions for your operating system.

Develop version
^^^^^^^^^^^^^^^
The latest develop version can be installed via::

    pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop

Or via cloning the repository and installing via::

    git clone https://github.com/matthiaskoenig/sbmlutils.git
    cd sbmlutils
    pip install -e .

Release notes
-------------
0.3.11
^^^^^^
* support and CI-CD for Mac-OS and Windows
* switch from travis to github actions
* python 3.8 support
* fixed pep8 issues
* type annotations and documentations
* removed __future__ imports
* refactored unittest to pytest
* refactored DFBA to https://github.com/matthiaskoenig/dfba
* cobra and optlang now optional
* cleanup of function signatures
* more coprehensive type annotations

0.3.9
^^^^^
* full support for distrib (distributions and uncertainty)

0.3.8
^^^^^
* python 3.7 support (dropping py3.5)
* model manipulation (merging of models)

0.3.7
^^^^^
* documentation updated
* additional annotation formats supported
* support of formula and charge on species
* fixed tests
* bug fixes

0.3.6
^^^^^
* support for mass and charge
* refactored and simplified Reactions
* better port support
* Exchange reaction template

0.3.4 - 0.3.5
^^^^^^^^^^^^^
* improved annotation support (inline annotations, annotation by url)
* checking against MIRIAM collections and patterns

0.3.1 - 0.3.3
^^^^^^^^^^^^^
* libSBML 5.18.0
* initial distrib support

0.3.0a1
^^^^^^^^^^^
* better comp support
* layout support
* improved fbc report
* bug fixes
* dropping support for python2

0.2.0
^^^^^
* better comp support
* hasOnlySubstanceUnits in sbmlreport added
* initialAmounts and initialConcentrations supported in sbmlcreator
* bug fixes

0.1.9
^^^^^
* update dependencies
* pip 10 fixes installer
* fixed unit tests
* bug fixes

0.1.8
^^^^^
* DFBA release

0.1.7a0
^^^^^^^
* xpp converter
* updated SBML reports

0.1.6
^^^^^
* update SBML reports (fbc & comp support)
* modelcreator fixes
* DFBA examples updated & annotated
* annotation fixes

0.1.4
^^^^^
* documentation update
* DFBA update & bug fixes
* DFBA examples (toy and diauxic growth)
* bug fixes

0.1.3
^^^^^
* python 3 support
* clean travis build with pip
* DFBA implementation
* bugfixes & improvements

0.1.2
^^^^^
* fixed unittests and bug fixes

0.1.1
^^^^^
* bug fixes, refactoring, unit tests
* model creator examples

0.1.0
^^^^^
* initial release


© 2017-2020 Matthias König
