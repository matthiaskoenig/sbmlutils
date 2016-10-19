"""
Single integration step with roadrunner.

For the dynamical adaption of the step size a single step must be integrated
with the ODE solver.
"""
from __future__ import print_function, division
import roadrunner
print(roadrunner.__version__)
# 1.4.1; Compiler: gcc 4.8.4, C++ version: 199711; JIT Compiler: LLVM-3.4; Date: Nov 11 2015, 14:36:20

# Load model results in warnings about fbc v2
from toymodel.settings import ode_bounds_file
rr = roadrunner.RoadRunner(ode_bounds_file)

# simulate multiple steps
result = rr.simulate(start=0, end=10, steps=5)
print(result)

# simulate multiple steps with variable steps
rr.integrator.setSetting("variable_step_size", True)
result = rr.simulate(start=0, end=1, points=2)
print(result)

# simulate a single internal step without giving the end time ?
result = rr.simulate(start=0, end=1, steps=1)
print(result)

