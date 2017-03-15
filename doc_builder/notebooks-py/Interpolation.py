
# coding: utf-8

# # Interpolation
# `sbmlutils` provides functionality for creating interpolated functions in SBML models. This allows to drive the model with experimental data sets. 
# 
# ## Dataset
# In a first step an experimental data set is loaded as a `pandas` DataFrame.

# In[1]:

#!!! DO NOT CHANGE !!! THIS FILE WAS CREATED AUTOMATICALLY FROM NOTEBOOKS !!! CHANGES WILL BE OVERWRITTEN !!! CHANGE CORRESPONDING NOTEBOOK FILE !!!
from __future__ import print_function, division

import pandas as pd

data = pd.read_csv('../../interpolation/data1.tsv', '\t')
print(data)

from matplotlib import pyplot as plt
plt.plot(data['x'], data['y'], '-o', label="y", color="blue")
plt.plot(data['x'], data['z'], '-o', label="z", color="red")
plt.xlabel('x')
plt.legend();


# ## Interpolate data
# Now we interpolate the experimental data with different methods.

# In[2]:

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


# ## Simulate
# In the next step we can use the interpolation SBML models for simulation.

# In[3]:

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


# ## Combine models
# Combination of a fitted data model with a regular model via comp.

# In[4]:

from sbmlutils.interpolation import Interpolation, INTERPOLATION_CUBIC_SPLINE
ip = Interpolation(data=data, method=INTERPOLATION_CUBIC_SPLINE)
sbml_str = ip.write_sbml_to_string()
r = te.loads(sbml_str)
a_spline = r.getAntimony()
print(a_spline)


# In[5]:

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


# In[6]:



