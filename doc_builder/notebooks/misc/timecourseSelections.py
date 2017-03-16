
# coding: utf-8

# # Result selections
# The `timecourseSelections` on the roadrunner object define what is part of the simulation.
# By default only `time` and `concentrations` are part of the timecourseSelections.
# To add additional selections just add the required sbml ids to the selection.
# An example is given below.

# In[1]:

get_ipython().magic(u'matplotlib inline')
from __future__ import print_function
import tellurium as te


# In[2]:

r = te.loada("""
S1 -> S2; k1*S1-k2*S2;
S1 = 10.0; S2 = 0.0;
k1 = 0.2; k2 = 0.1;
""")


# In[3]:

# default selections in results
print(r.timeCourseSelections)
s = r.simulate(start=0, end=10, steps=10)
print(s)


# In[4]:

# add additional ids to the timecourse selections
r.timeCourseSelections += r.getGlobalParameterIds() + r.getCompartmentIds()
print(r.timeCourseSelections)


# In[5]:

# reset to initial concentrations
r.reset()
s2 = r.simulate(start=0, end=10, steps=10)
print(s2)


# In[ ]:
