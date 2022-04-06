Overview
============
Introduction
------------
**sbmlutils** are python utilities for working with `SBML <http://www.sbml.org>`_.
This python package provides handy features like HTML reports of SBML models, helper functions for model creation and manipulation, interpolation functions to add experimental data to models, or annotation of models.

Main features of **sbmlutils** are

- :ref:`SBML creator` : The modelcreator provides utilities for the creation of SBML models. Supports `comp` and `fbc` models. Model information is managed in python data structures which are used to create the models.
- :ref:`SBML distrib` : Support for encoding distributions and uncertainties in SBML.
- :ref:`SBML report` : HTML report of SBML models `https://sbml4humans.de <https://sbml4humans.de>`__. This provides overview of the model contents.
- :ref:`SBML annotation` : Helper functions for the annotation of SBML models. Annotations are hereby defined in separate annotation files with annotations being matched to ids based on regular expression matching.
- :ref:`SBML converters` : Converters from and to SBML, e.g. xpp.

Source code is available from
`https://github.com/matthiaskoenig/sbmlutils
<https://github.com/matthiaskoenig/sbmlutils>`_.

Interactive report is available from
`https://sbml4humans.de <https://sbml4humans.de>`__.

To report bugs, request features or asking questions please file an
`issue
<https://github.com/matthiaskoenig/sbmlutils/issues>`_.

If you use sbmlutils please cite
`https://doi.org/10.5281/zenodo.597149
<https://doi.org/10.5281/zenodo.597149>`_.

Installation
------------
The sbmlutils package is available from `pypi
<https://pypi.python.org/pypi/sbmlutils>`_ and can be installed via::

    pip install sbmlutils


For detailed installation instructions see
`https://github.com/matthiaskoenig/sbmlutils
<https://github.com/matthiaskoenig/sbmlutils>`_.

Funding
-------
Matthias König is supported by the Federal Ministry of Education and Research (BMBF, Germany)
within the research network Systems Medicine of the Liver (**LiSyM**, grant number 031L0054) 
and by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 
"`QuaLiPerF <https://qualiperf.de>`__ (Quantifying Liver Perfusion-Function Relationship in Complex Resection - 
A Systems Medicine Approach)" by grant number 436883643.
SBML4Humans was funded as part of `Google Summer of Code 2021 <https://summerofcode.withgoogle.com/>`__.
