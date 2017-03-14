
Interpolation
=============

``sbmlutils`` provides functionality for creating interpolated functions
in SBML models. This allows to drive the model with experimental data
sets.

Dataset
-------

In a first step an experimental data set is loaded as a ``pandas``
DataFrame.

.. code:: python

    import sbmlutils
    # load the data
    import pandas as pd
    data = pd.read_csv('../../interpolation/data1.tsv', '\t')
    print(data)
    
    from matplotlib import pyplot as plt
    plt.plot(data['x'], data['y'], '-o', label="y", color="blue")
    plt.plot(data['x'], data['z'], '-o', label="z", color="red")
    plt.xlabel('x')
    plt.legend();


.. parsed-literal::

         x    y      z
    0  0.0  0.0  10.00
    1  1.0  2.0   5.00
    2  2.0  1.0   2.50
    3  3.0  1.5   1.25
    4  4.0  2.5   0.60
    5  5.0  3.5   0.30



.. image:: _notebooks/docs/Interpolation_files/Interpolation_1_1.png


Interpolate data
----------------

Now we interpolate the experimental data with different methods.

.. code:: python

    # import the interpolation functionality
    from sbmlutils.interpolation import *
    
    # constant interpolation
    ip_constant = Interpolation(data=data, method=INTERPOLATION_CONSTANT)
    ip_constant.write_sbml_to_file("data1_constant.xml")
    
    # linear interpolation
    ip_linear = Interpolation(data=data, method=INTERPOLATION_LINEAR)
    ip_linear.write_sbml_to_file("data1_linear.xml")
    
    # natural cubic spline
    ip_cubic = Interpolation(data=data, method=INTERPOLATION_CUBIC_SPLINE)
    ip_cubic.write_sbml_to_file("data1_cubic.xml")


.. parsed-literal::

     filename : /tmp/tmpYWAHSA/validated.xml
     file size (byte) : 8341
     read time (ms) : 4.124880
     c-check time (ms) : 4.273176
     validation error(s) : 0
     consistency error(s): 0
     validation warning(s) : 0
     consistency warning(s): 0 
    
     filename : /tmp/tmpjegjVu/validated.xml
     file size (byte) : 11902
     read time (ms) : 6.021023
     c-check time (ms) : 5.322933
     validation error(s) : 0
     consistency error(s): 0
     validation warning(s) : 0
     consistency warning(s): 0 
    
     filename : /tmp/tmp1aLtPK/validated.xml
     file size (byte) : 20914
     read time (ms) : 10.004044
     c-check time (ms) : 6.201982
     validation error(s) : 0
     consistency error(s): 0
     validation warning(s) : 0
     consistency warning(s): 0 
    


Simulate
--------

In the next step we can use the interpolation SBML models for
simulation.

.. code:: python

    # simulate
    def plot_data(s, name):
        """ Helper function for plotting interpolation with data. """
        from matplotlib import pyplot as plt
        plt.plot(data['x'], data['y'], 'o', label="y data", color="blue")
        plt.plot(data['x'], data['z'], 'o', label="z data", color="red")
        plt.plot(s['time'], s['y'], '-', label="y", color="blue")
        plt.plot(s['time'], s['z'], '-', label="z", color="red")
        plt.xlabel('time')
        plt.title('{} interpolation'.format(name))
        plt.legend()
    
    import tellurium as te
    for name in ['constant', 'linear', 'cubic']:
        sbml_file = 'data1_{}.xml'.format(name)
        r = te.loads(sbml_file)
    
        # Simulate the interpolation
        r.timeCourseSelections = ['time', 'y', 'z']
        s = r.simulate(0,10,steps=100)
    
        plot_data(s, name=name)
        plt.show()



.. image:: _notebooks/docs/Interpolation_files/Interpolation_5_0.png



.. image:: _notebooks/docs/Interpolation_files/Interpolation_5_1.png



.. image:: _notebooks/docs/Interpolation_files/Interpolation_5_2.png


Combine models
--------------

Combination of a fitted data model with a regular model via comp.

.. code:: python

    from sbmlutils.interpolation import Interpolation, INTERPOLATION_CUBIC_SPLINE
    ip = Interpolation(data=data, method=INTERPOLATION_CUBIC_SPLINE)
    sbml_str = ip.write_sbml_to_string()
    r = te.loads(sbml_str)
    a_spline = r.getAntimony()
    print(a_spline)


.. parsed-literal::

     filename : /tmp/tmppPHrUr/validated.xml
     file size (byte) : 20914
     read time (ms) : 7.255793
     c-check time (ms) : 6.713867
     validation error(s) : 0
     consistency error(s): 0
     validation warning(s) : 0
     consistency warning(s): 0 
    
    // Created by libAntimony v2.9.0
    model *Interpolation_cubic_spline()
    
      // Assignment Rules:
      y := piecewise(-0.901913875598*(time - 0)^3 + 0*(time - 0)^2 + 2.9019138756*(time - 0) + 0, (time >= 0) && (time <= 1), 1.50956937799*(time - 1)^3 + -2.70574162679*(time - 1)^2 + 0.196172248804*(time - 1) + 2, (time >= 1) && (time <= 2), -0.636363636364*(time - 2)^3 + 1.82296650718*(time - 2)^2 + -0.686602870813*(time - 2) + 1, (time >= 2) && (time <= 3), 0.0358851674641*(time - 3)^3 + -0.0861244019139*(time - 3)^2 + 1.05023923445*(time - 3) + 1.5, (time >= 3) && (time <= 4), -0.00717703349282*(time - 4)^3 + 0.0215311004785*(time - 4)^2 + 0.985645933014*(time - 4) + 2.5, (time >= 4) && (time <= 5), 0);
      z := piecewise(0.58995215311*(time - 0)^3 + 0*(time - 0)^2 + -5.58995215311*(time - 0) + 10, (time >= 0) && (time <= 1), -0.44976076555*(time - 1)^3 + 1.76985645933*(time - 1)^2 + -3.82009569378*(time - 1) + 5, (time >= 1) && (time <= 2), -0.0409090909091*(time - 2)^3 + 0.420574162679*(time - 2)^2 + -1.62966507177*(time - 2) + 2.5, (time >= 2) && (time <= 3), -0.0366028708134*(time - 3)^3 + 0.297846889952*(time - 3)^2 + -0.911244019139*(time - 3) + 1.25, (time >= 3) && (time <= 4), -0.0626794258373*(time - 4)^3 + 0.188038277512*(time - 4)^2 + -0.425358851675*(time - 4) + 0.6, (time >= 4) && (time <= 5), 0);
    
      // Other declarations:
      var y, z;
    end
    


.. code:: python

    # combine the models with antimony
    a_test = a_spline + """
    model *test()
        // add spline submodel to the model
        A: Interpolation_cubic_spline();
        
        J0: S1 -> S2; k1*S1;
        J1: $S3 -> S2; k1*S3;
        J2: $S4 -> S2; k1*S4;
        S1 = 10.0; S2=0.0; S3=0.0; S4=0.0
        k1 = 0.3;
        
        // use the submodel info in model not working
        A.y is y;
        A.z is z;
        
        S3 := y
        S4 := z
    end
    """
    
    r2 = te.loada(a_test)
    print(r2.getAntimony())
    r2.timeCourseSelections = ['time'] + r2.getBoundarySpeciesIds() + r2.getFloatingSpeciesIds()
    print(r2.timeCourseSelections)
    
    s = r2.simulate(0, 10, 101)
    r2.plot(s)


.. parsed-literal::

    // Created by libAntimony v2.9.0
    model *test()
    
      // Compartments and Species:
      species S1, S2, $S3, $S4;
    
      // Assignment Rules:
      S3 := y;
      y := piecewise(-0.901913875598*(time - 0)^3 + 0*(time - 0)^2 + 2.9019138756*(time - 0) + 0, (time >= 0) && (time <= 1), 1.50956937799*(time - 1)^3 + -2.70574162679*(time - 1)^2 + 0.196172248804*(time - 1) + 2, (time >= 1) && (time <= 2), -0.636363636364*(time - 2)^3 + 1.82296650718*(time - 2)^2 + -0.686602870813*(time - 2) + 1, (time >= 2) && (time <= 3), 0.0358851674641*(time - 3)^3 + -0.0861244019139*(time - 3)^2 + 1.05023923445*(time - 3) + 1.5, (time >= 3) && (time <= 4), -0.00717703349282*(time - 4)^3 + 0.0215311004785*(time - 4)^2 + 0.985645933014*(time - 4) + 2.5, (time >= 4) && (time <= 5), 0);
      S4 := z;
      z := piecewise(0.58995215311*(time - 0)^3 + 0*(time - 0)^2 + -5.58995215311*(time - 0) + 10, (time >= 0) && (time <= 1), -0.44976076555*(time - 1)^3 + 1.76985645933*(time - 1)^2 + -3.82009569378*(time - 1) + 5, (time >= 1) && (time <= 2), -0.0409090909091*(time - 2)^3 + 0.420574162679*(time - 2)^2 + -1.62966507177*(time - 2) + 2.5, (time >= 2) && (time <= 3), -0.0366028708134*(time - 3)^3 + 0.297846889952*(time - 3)^2 + -0.911244019139*(time - 3) + 1.25, (time >= 3) && (time <= 4), -0.0626794258373*(time - 4)^3 + 0.188038277512*(time - 4)^2 + -0.425358851675*(time - 4) + 0.6, (time >= 4) && (time <= 5), 0);
    
      // Reactions:
      J0: S1 -> S2; k1*S1;
      J1: $S3 -> S2; k1*S3;
      J2: $S4 -> S2; k1*S4;
    
      // Species initializations:
      S1 = 10;
      S2 = 0;
    
      // Variable initializations:
      k1 = 0.3;
    
      // Other declarations:
      var y, z;
      const k1;
    end
    
    ['time', 'S3', 'S4', 'S1', 'S2']



.. image:: _notebooks/docs/Interpolation_files/Interpolation_8_1.png




.. parsed-literal::

    <module 'matplotlib.pyplot' from '/usr/local/lib/python2.7/dist-packages/matplotlib/pyplot.pyc'>



