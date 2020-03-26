SBML converters
===============

``sbmlutils`` provides functionality for converting formats to SBML and
SBML to some formats.

.. code:: ipython3

    from sbmlutils.report import sbmlreport

XPP to SBML
-----------

In this example a given xpp model is converted to SBML.

.. code:: ipython3

    from sbmlutils.converters import xpp
    from sbmlutils import validation
    
    # convert to SBML
    xpp.xpp2sbml(xpp_file="./xpp/SkM_AP_KCa.ode", sbml_file="./xpp/SkM_AP_KCa.xml")


.. parsed-literal::

    ERROR:root:Using notes strings is deprecated, use 'Notes' instead.


.. parsed-literal::

    --------------------------------------------------------------------------------
    xpp2sbml:  ./xpp/SkM_AP_KCa.ode -> ./xpp/SkM_AP_KCa.xml
    --------------------------------------------------------------------------------
    [1m[92m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/xpp/SkM_AP_KCa.xml
    valid                    : TRUE
    check time (s)           : 0.011
    --------------------------------------------------------------------------------
    [0m[0m

