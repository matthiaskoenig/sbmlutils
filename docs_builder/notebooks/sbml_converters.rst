SBML converters
===============

``sbmlutils`` provides functionality for converting formats to SBML and
SBML to some formats.

XPP to SBML
-----------

In this example a given xpp model is converted to SBML.

.. code:: ipython3

    from sbmlutils.converters import xpp
    
    # convert to SBML
    xpp.xpp2sbml(xpp_file="./xpp/SkM_AP_KCa.ode", sbml_file="./xpp/SkM_AP_KCa.xml")


.. parsed-literal::

    Using notes strings is deprecated, use 'Notes' instead.
    All SBML paths should be of type 'Path', but '<class 'str'>' found for: ./xpp/SkM_AP_KCa.xml


.. parsed-literal::

    --------------------------------------------------------------------------------
    xpp2sbml:  ./xpp/SkM_AP_KCa.ode -> ./xpp/SkM_AP_KCa.xml
    --------------------------------------------------------------------------------
    [1m[92m
    --------------------------------------------------------------------------------
    ./xpp/SkM_AP_KCa.xml
    valid                    : TRUE
    check time (s)           : 0.009
    --------------------------------------------------------------------------------
    [0m[0m


