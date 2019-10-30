""" FIXME: figure out what is going on with model simulations. """


import roadrunner
import pandas as pd

def simulate(r: roadrunner.RoadRunner):
    r.timeCourseSelections = ["time", "Aglc", "[Aglc]", "R1", "Vc"]
    s = r.simulate(start=0, end=2, steps=100)
    return pd.DataFrame(s, columns=s.colnames)


# instance by model loading
r1 = roadrunner.RoadRunner("Koenig_amount_species_1.xml")  # type: roadrunner.RoadRunner

# new instance from initial state
sbml_str = r1.getCurrentSBML()
r2 = roadrunner.RoadRunner(sbml_str)  # type: roadrunner.RoadRunner

# simulate
s1 = simulate(r1)

# create a new instance from final state
sbml_str = r1.getCurrentSBML()
r3 = roadrunner.RoadRunner(sbml_str)  # type: roadrunner.RoadRunner

# simulate r2 and r3
s2 = simulate(r2)
s3 = simulate(r3)


# --- plotting ---
from matplotlib import pyplot as plt
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

print(s1.columns)
ax1.plot(s1.time, s1.Aglc, '-', label="r1")
ax1.plot(s2.time, s2.Aglc, '-', label="r2")
ax1.plot(s3.time, s3.Aglc, '-', label="r3")
ax1.set_ylabel("amount")

ax2.plot(s1.time, s1.Vc, '-', label="r1")
ax2.plot(s2.time, s2.Vc, '-', label="r2")
ax2.plot(s3.time, s3.Vc, '-', label="r3")

for ax in (ax1, ax2):
    ax.set_xlabel("time")
    ax.legend()
plt.show()

print(s3.head())