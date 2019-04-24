"""
Runs ODE and FBA simulation with the model.

memote model report can be generated via:
memote report snapshot --filename tiny_example_10_memote.html tiny_example_10.xml

"""
import os

import model
import roadrunner
import pandas as pd
from matplotlib import pylab as plt
from sbmlutils.modelcreator.creator import Factory
import cobra
from cobra.io import read_sbml_model

# -----------------------------------------------------------------------------
# create model
# -----------------------------------------------------------------------------
models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

print('-'*80)
print(models_dir)
print('-' * 80)

factory = Factory(modules=['sbmlutils.examples.models.tiny_model.model'],
                  target_dir=os.path.join(models_dir, 'results'),
                  annotations=os.path.join(models_dir, 'annotations.xlsx'))
_, _, tiny_sbml = factory.create(tmp=False)


# -----------------------------------------------------------------------------
# run ode simulation
# -----------------------------------------------------------------------------
# tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                         'results',
#                         '{}_{}.xml'.format(model.mid, model.version))


r = roadrunner.RoadRunner(tiny_sbml)
r.timeCourseSelections = ["time"] + r.model.getBoundarySpeciesIds() + r.model.getFloatingSpeciesIds() + r.model.getReactionIds() + r.model.getGlobalParameterIds()
r.timeCourseSelections += ["[{}]".format(key) for key in r.model.getFloatingSpeciesIds()]
# print(r)
s = r.simulate(0, 400, steps=400)
df = pd.DataFrame(s, columns=s.colnames)
# r.plot()

f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
ax1.set_title("SBML species")
ax1.plot(df.time, df['[glc]'])
ax1.plot(df.time, df['[g6p]'])
ax1.plot(df.time, df['[atp]'])
ax1.plot(df.time, df['[adp]'])
ax1.plot(df.time, df['a_sum'], color="grey", linestyle="--", label="[atp]+[adp]")
ax1.set_ylabel("concentration [mmole/litre]=[mM]")

ax2.set_title("SBML reactions")
ax2.plot(df.time, 1E6*df.GK)
ax2.plot(df.time, 1E6*df.ATPPROD)
ax2.set_ylabel("reaction rate 1E-6[mmole/s]")

for ax in (ax1, ax2):
    ax.legend()
    ax.set_xlabel("time [s]")

plt.show()
f.savefig("./results/{}_{}_roadrunner.png".format(model.mid, model.version), bbox_inches="tight")


# -----------------------------------------------------------------------------
# fba simulation
# -----------------------------------------------------------------------------

model = read_sbml_model(tiny_sbml)
print(model)


# Iterate through the the objects in the model
print("Reactions")
print("---------")
for x in model.reactions:
    print("%s : %s [%s<->%s]" % (x.id, x.reaction, x.lower_bound, x.upper_bound))

print("")
print("Metabolites")
print("-----------")
for x in model.metabolites:
    print('%9s (%s) : %s, %s, %s' % (x.id, x.compartment, x.formula, x.charge,  x.annotation))

print("")
print("Genes")
print("-----")
for x in model.genes:
    associated_ids = (i.id for i in x.reactions)
    print("%s is associated with reactions: %s" %
          (x.id, "{" + ", ".join(associated_ids) + "}"))


solution = model.optimize()
print(solution)
