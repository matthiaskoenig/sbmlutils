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
    from notebook import BASE_DIR
    
    sbmlreport.create_report(
        sbml_path=BASE_DIR / "models" / "BIOMD0000000012.xml", 
        output_dir=BASE_DIR / "reports", 
        units_consistency=False
    )


.. parsed-literal::

    [1m[92m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/BIOMD0000000012.xml
    valid                    : TRUE
    check time (s)           : 0.009
    --------------------------------------------------------------------------------
    [0m[0m


Platelet metabolism
~~~~~~~~~~~~~~~~~~~

In the second example we create a report for a model for Human platelet
metabolism from the BiGG model database:
http://bigg.ucsd.edu/models/iAT_PLT_636 The example contains an SBML
error because the ``listOfFluxObjectives`` cannot be empty.

The created SBML report can be accessed from
`./reports/iAT_PLT_636.xml.html <./reports/iAT_PLT_636.xml.html>`__.

.. code:: ipython3

    # create SBML report without performing units checks
    sbmlreport.create_report(
        BASE_DIR / "models" / "iAT_PLT_636.xml.gz", 
        output_dir= BASE_DIR / "reports", 
        units_consistency=False, 
        modeling_practice=False
    )


.. parsed-literal::

    [47m[30mENone: General SBML conformance (core, L14, code)[0m[0m
    [91m[Error] Document does not conform to the SBML XML schema[0m
    [94mAn SBML XML document must conform to the XML Schema for the corresponding SBML Level, Version and Release. The XML Schema for SBML defines the basic SBML object structure, the data types used by those objects, and the order in which the objects may appear in an SBML document.
     listOfFluxObjectives cannot be empty.
    [0m
    read_sbml error '/home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/iAT_PLT_636.xml.gz': SBMLDocumentErrors encountered while reading the SBML file.
    ERROR:root:[1m[91m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/iAT_PLT_636.xml.gz
    valid                    : FALSE
    validation error(s)      : 1
    validation warnings(s)   : 0
    check time (s)           : 0.879
    --------------------------------------------------------------------------------
    [0m[0m
    ERROR:sbmlutils.validation:[47m[30mE0: General SBML conformance (core, L14, code)[0m[0m
    [91m[Error] Document does not conform to the SBML XML schema[0m
    [94mAn SBML XML document must conform to the XML Schema for the corresponding SBML Level, Version and Release. The XML Schema for SBML defines the basic SBML object structure, the data types used by those objects, and the order in which the objects may appear in an SBML document.
     listOfFluxObjectives cannot be empty.
    [0m


