Introduction
============
**sbmlutils** are python utilities for working with `SBML <http://www.sbml.org>`_.
This provides handy features like HTML reports of SBML models, helper functions for model creation and manipulation,
interpolation functions to add experimental data to models, or implementation of dynamic flux balance analysis (DFBA).

To cite libsbgnpy use the following BibTex or equivalent::

    @MISC{sbmlutils,
      author        = {Matthias König},
      title         = {sbmlutils: python utilities for SBML},
      month         = {Feb.},
      year          = {2017},
      doi           = "{10.5281/zenodo.399008}",
      url           = "{http://dx.doi.org/10.5281/zenodo.399008}"
    }

Source code is available from
`https://github.com/matthiaskoenig/sbmlutils
<https://github.com/matthiaskoenig/sbmlutils>`_.

To report bugs, request features or asking questions please file an
`issue
<https://github.com/matthiaskoenig/sbmlutils/issues>`_.

Installation
------------
The libsbgn-python package is available from `pypi
<https://github.com/matthiaskoenig/sbmlutils>`_ and can be installed via::

    pip install sbmlutils


Features
--------
The following lists the main features. For examples see the examples section.

DFBA
~~~~
Simulator for dynamic flux balance analysis (DFBA) of SBML model.
For more information see also `<http://github.com/matthiaskoenig/dfba>`_.

SBML report
~~~~~~~~~~~
HTML report of SBML models. This provides overview of the model contents.

SBML modelcreator
~~~~~~~~~~~~~~~~~
The modelcreator provides utilities for the creation of SBML models.
Supports `comp` and `fbc` models. Model information is managed in python data
structures which are used to create the models.

* `Cell.py`: basic model information
* `Reactions.py`: reaction information

Models can extend other models and reuse information from
defined models.

SBML annotator
~~~~~~~~~~~~~~
Helper functions for the annotation of SBML models.
Annotations are hereby defined in separate annotation files with
annotations being matched to ids based on regular expression matching.

SBML interpolation
~~~~~~~~~~~~~~~~~~
Helper functions for working with data interpolation in SBML models.


Examples
--------
In the following sections examples are provided. All examples are available as
interactive `jupyter notebooks <http://jupyter.readthedocs.org/en/latest/install.html>`_.

To run the examples clone the git repository
::

    git clone https://github.com/matthiaskoenig/sbmlutils.git

and start jupyter in the notebooks folder
::

    cd sbmlutils/docs_builder/notebooks
    jupyter notebook index.ipynb

We are working on updating the examples. A more complete documentation will be available with the next release.

