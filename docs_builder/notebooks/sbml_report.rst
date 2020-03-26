SBML report
===========

``sbmlutils`` can create HTML reports from given SBML files. Such an
HTML report provides a simple entry point to get an overview over an
existing SBML model or browse content of a model in a more
human-readable format.

Create report
-------------

The following example demonstrates how an SBML report can be created
from given models.

.. code:: ipython3

    from sbmlutils.report import sbmlreport

Repressilator
~~~~~~~~~~~~~

The first report is for the repressilator downloaded from biomodels
(https://www.ebi.ac.uk/biomodels/BIOMD0000000012). To create a report on
provides the path to the SBML file and the directory where the report
should be written. As part of the model report creation the model is
validated by default. In this example we deactivate the
``units_consistency`` checks.

The created SBML report can be accessed from
`./reports/BIOMD0000000012.html <./reports/BIOMD0000000012.html>`__.

.. code:: ipython3

    # create SBML report without performing units checks
    sbmlreport.create_report("./models/BIOMD0000000012.xml", report_dir="./reports", 
                                  units_consistency=False)


.. parsed-literal::

    [1m[92m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/BIOMD0000000012.xml
    valid                    : TRUE
    check time (s)           : 0.008
    --------------------------------------------------------------------------------
    [0m[0m
    SBML report created: ./reports/BIOMD0000000012.html


Platelet metabolism
~~~~~~~~~~~~~~~~~~~

In the second example we create a report for a model for Human platelet
metabolism from the BiGG model database:
http://bigg.ucsd.edu/models/iAT\_PLT\_636

The created SBML report can be accessed from
`./reports/iAT\_PLT\_636.xml.html <./reports/iAT_PLT_636.xml.html>`__.

.. code:: ipython3

    # create SBML report without performing units checks
    sbmlreport.create_report("./models/iAT_PLT_636.xml.gz", report_dir="./reports", 
                                  units_consistency=False, modeling_practice=False)


.. parsed-literal::

    ERROR:root:[1m[91m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/iAT_PLT_636.xml.gz
    valid                    : FALSE
    validation error(s)      : 1
    validation warnings(s)   : 0
    check time (s)           : 1.265
    --------------------------------------------------------------------------------
    [0m[0m
    ERROR:root:[47m[30mE0: SBML component consistency (fbc, L76, code)[0m[0m
    [91m[Error] An <objective> must have one <listOfFluxObjectives>.[0m
    [94mAn <objective> object must have one and only one instance of the <listOfFluxObjectives> object. 
    Reference: L3V1 Fbc V2, Section 3.6
     <objective> 'obj' has no listOfFluxObjectives.
    [0m


.. parsed-literal::

    SBML report created: ./reports/iAT_PLT_636.xml.html

