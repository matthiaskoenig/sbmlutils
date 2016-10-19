"""
Try to run a single step simulation.
@author: Matthias Koenig
"""

from __future__ import print_function, division
import roadrunner
print(roadrunner.__version__)


# Load model results in warnings about fbc v2
from toymodel.settings import comp_ode_file, top_level_file
# rr = roadrunner.RoadRunner(comp_ode_file)
rr = roadrunner.RoadRunner(top_level_file)

# boundary and floating species in selection

sel = ['time'] \
        + ["".join(["[", item, "]"]) for item in rr.model.getBoundarySpeciesIds()] \
        + ["".join(["[", item, "]"]) for item in rr.model.getFloatingSpeciesIds()]
rr.timeCourseSelections = sel

# simulate multiple steps
result = rr.simulate(start=0, end=10, steps=100)
print(result)
