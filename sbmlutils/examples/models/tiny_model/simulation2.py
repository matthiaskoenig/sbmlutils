"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""
from __future__ import print_function, division

import os

import model2 as model
import roadrunner
import pandas as pd
from matplotlib import pylab as plt


# SBML file
tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'results',
                         '{}_{}.xml'.format(model.mid, model.version))


r = roadrunner.RoadRunner(tiny_sbml)
r.timeCourseSelections = ["time"] + r.model.getBoundarySpeciesIds() + r.model.getFloatingSpeciesIds() + r.model.getReactionIds() + r.model.getGlobalParameterIds()
r.timeCourseSelections += ["[{}]".format(key) for key in r.model.getFloatingSpeciesIds()]
print(r)
s = r.simulate(0, 400, steps=400)
df = pd.DataFrame(s, columns=s.colnames)
# r.plot()

f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
ax1.set_title("SBML species")
ax1.plot(df.time, df['[atp]'])
ax1.plot(df.time, df['[adp]'])
ax1.plot(df.time, df['a_sum'], color="grey", label="[atp]+[adp]")
ax1.set_ylabel("concentration [mmole/litre]=[mM]")

ax2.set_title("SBML reactions")
ax2.plot(df.time, df.ATPASE)
ax2.set_ylabel("reaction rate [mmole/s]")

for ax in (ax1, ax2):
    ax.legend()
    ax.set_xlabel("time [s]")

plt.show()
f.savefig("tiny_example.png", bbox_inches="tight")


#r = roadrunner.RoadRunner(tiny_sbml)
#r.integrator.setValue("relative_tolerance", 1E-18)
#r.integrator.setValue("absolute_tolerance", 1E-18)
#s = r.simulate(0, 100, steps=100)
#df = pd.DataFrame(s, columns=s.colnames)
#r.plot()




