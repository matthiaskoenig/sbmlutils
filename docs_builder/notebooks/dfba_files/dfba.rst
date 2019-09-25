DFBA
====

This section describes how to run dynamic FBA (DFBA) with ``sbmlutils``.

.. code:: ipython3

    %matplotlib inline

.. code:: ipython3

    import os
    import sbmlutils
    from sbmlutils import dfba
    from sbmlutils.dfba import utils

Simulate DFBA model
-------------------

To run an existing DFBA model call use ``simulate_dfba``.

.. code:: ipython3

    # get the absolute path to the top model
    from sbmlutils.dfba.toy_wholecell import settings as toysettings
    from sbmlutils.dfba.toy_wholecell import model_factory as toyfactory
    from sbmlutils.dfba.toy_wholecell import simulate as toysimulate
    
    sbml_path = os.path.join(utils.versioned_directory(toysettings.OUT_DIR, toysettings.VERSION), 
                             toysettings.TOP_LOCATION)
    print(sbml_path)
    
    # run simulation with the top model
    from sbmlutils.dfba.simulator import simulate_dfba
    df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=50, dt=5.0)
    df


.. parsed-literal::

    /home/mkoenig/git/sbmlutils/sbmlutils/dfba/toy_wholecell/results/v15/toy_wholecell_top.xml


.. parsed-literal::

    /home/mkoenig/git/sbmlutils/sbmlutils/dfba/model.py:125 [1;31mUserWarning[0m: No top level model found.


::


    ---------------------------------------------------------------------------

    ValueError                                Traceback (most recent call last)

    <ipython-input-3-54c1d0606a90> in <module>
         10 # run simulation with the top model
         11 from sbmlutils.dfba.simulator import simulate_dfba
    ---> 12 df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=50, dt=5.0)
         13 df


    ~/git/sbmlutils/sbmlutils/dfba/simulator.py in simulate_dfba(sbml_path, tstart, tend, dt, pfba, abs_tol, rel_tol, lp_solver, ode_integrator, **kwargs)
         40     start_time = timeit.default_timer()
         41     # Load model
    ---> 42     dfba_model = DFBAModel(sbml_path=sbml_path)
         43 
         44     # simulation


    ~/git/sbmlutils/sbmlutils/dfba/model.py in __init__(self, sbml_path)
         53             self.dt = None
         54 
    ---> 55             self._process_top()
         56             self._process_models()
         57             self._process_dt()


    ~/git/sbmlutils/sbmlutils/dfba/model.py in _process_top(self)
        125             warnings.warn("No top level model found.")
        126 
    --> 127         self.framework_top = builder.get_framework(self.model_top)
        128         if self.framework_top is not builder.MODEL_FRAMEWORK_ODE:
        129             warnings.warn("The top level model framework is not ode: {}".format(self.framework_top))


    ~/git/sbmlutils/sbmlutils/dfba/builder.py in get_framework(model)
         88     if type(model) not in [libsbml.Model, libsbml.ModelDefinition]:
         89         raise ValueError("Framework must be defined on either Model/ModelDefinition, "
    ---> 90                          "but given: {}".format(model))
         91 
         92     framework = None


    ValueError: Framework must be defined on either Model/ModelDefinition, but given: None


Toy example
-----------

.. code:: ipython3

    from sbmlutils.dfba.toy_wholecell import settings as toysettings
    from sbmlutils.dfba.toy_wholecell import model_factory as toyfactory
    from sbmlutils.dfba.toy_wholecell import simulate as toysimulate
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # create the toy model
    toyfactory.create_model(test_dir)
    # here the files are generated
    sbml_path = os.path.join(utils.versioned_directory(test_dir, toysettings.VERSION),
                             toysettings.TOP_LOCATION)
    print(sbml_path)
    # simulate
    dfs = toysimulate.simulate_toy(sbml_path, test_dir, dts=[1.0], figures=False)
    
    toysimulate.print_species(dfs=dfs)
    toysimulate.print_fluxes(dfs=dfs)
    print(dfs[0].head())


.. parsed-literal::

    Create directory: /tmp/tmphq_jsv_y/v15


.. parsed-literal::

    ERROR:root:Providing model units as dict is deprecated, use 'ModelUnits' instead.
    ERROR:root:Using notes strings is deprecated, use 'Notes' instead.


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-4-a5f5520095be> in <module>
          7 
          8 # create the toy model
    ----> 9 toyfactory.create_model(test_dir)
         10 # here the files are generated
         11 sbml_path = os.path.join(utils.versioned_directory(test_dir, toysettings.VERSION),


    ~/git/sbmlutils/sbmlutils/dfba/toy_wholecell/model_factory.py in create_model(output_dir)
        387 
        388     # create sbml
    --> 389     doc_fba = fba_model(settings.FBA_LOCATION, directory, annotations=annotations)
        390     bounds_model(settings.BOUNDS_LOCATION, directory, doc_fba=doc_fba, annotations=annotations)
        391     update_model(settings.UPDATE_LOCATION, directory, doc_fba=doc_fba, annotations=annotations)


    ~/git/sbmlutils/sbmlutils/dfba/toy_wholecell/model_factory.py in fba_model(sbml_file, directory, annotations)
        153 
        154     # reactions
    --> 155     r1 = mc.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
        156                             reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
        157     r2 = mc.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,


    AttributeError: module 'sbmlutils.factory' has no attribute 'create_reaction'


Diauxic growth
--------------

.. code:: ipython3

    '''
    from sbmlutils.dfba.diauxic_growth import settings as dgsettings
    from sbmlutils.dfba.diauxic_growth import model_factory as dgfactory
    from sbmlutils.dfba.diauxic_growth import simulate as dgsimulate
    from sbmlutils.dfba.diauxic_growth import analyse as dganalyse
    
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    # create the model
    dgfactory.create_model(test_dir)
    
    # top model file
    sbml_path = os.path.join(utils.versioned_directory(test_dir, dgsettings.VERSION),
                             dgsettings.TOP_LOCATION)
    print(sbml_path)
    
    # run DFBA
    dfs = dgsimulate.simulate_diauxic_growth(sbml_path, test_dir, dts=[0.01], figures=False)
    
    # plot results
    dganalyse.print_species(dfs=dfs)
    dganalyse.print_fluxes(dfs=dfs)
    print(dfs[0].head())
    '''




.. parsed-literal::

    '\nfrom sbmlutils.dfba.diauxic_growth import settings as dgsettings\nfrom sbmlutils.dfba.diauxic_growth import model_factory as dgfactory\nfrom sbmlutils.dfba.diauxic_growth import simulate as dgsimulate\nfrom sbmlutils.dfba.diauxic_growth import analyse as dganalyse\n\nimport tempfile\ntest_dir = tempfile.mkdtemp()\n\n# create the model\ndgfactory.create_model(test_dir)\n\n# top model file\nsbml_path = os.path.join(utils.versioned_directory(test_dir, dgsettings.VERSION),\n                         dgsettings.TOP_LOCATION)\nprint(sbml_path)\n\n# run DFBA\ndfs = dgsimulate.simulate_diauxic_growth(sbml_path, test_dir, dts=[0.01], figures=False)\n\n# plot results\ndganalyse.print_species(dfs=dfs)\ndganalyse.print_fluxes(dfs=dfs)\nprint(dfs[0].head())\n'



