import roadrunner
import pandas as pd

# Loading model and simulating
model = roadrunner.RoadRunner("boundary_condition.xml")  # type: roadrunner.ExecutableModel
model.selections = ["time", "A1", "A2", "[A1]", "[A2]"]

# default simulation
s = model.simulate()
s = pd.DataFrame(s, columns=s.colnames)
print(s.head(5))

print("-" * 80)
# setting initial value on species with "boundaryCondition=False"
model["init(A1)"] = 1000.0
# setting value on species with "boundaryCondition=True"
model["A2"] = 1000.0
s = model.simulate()
s = pd.DataFrame(s, columns=s.colnames)
print(s.head(5))

print("-" * 80)
model.resetAll()
s = model.simulate()
s = pd.DataFrame(s, columns=s.colnames)
print(s.head(5))









# setting initial value on species with "boundaryCondition=False"
model["init(A1)"] = 10.0
# setting initial value on species with "boundaryCondition=True" (results in error)
model["init(A2)"] = 10.0
