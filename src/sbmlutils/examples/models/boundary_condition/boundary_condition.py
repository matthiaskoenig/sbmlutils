from typing import Dict

from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.modelcreator.creator import CoreModel
from sbmlutils.units import *
from sbmlutils.validation import validate_doc


m1_dict = {
    "mid": "m1_boundary_condition",
    "compartments": [Compartment(sid="C", value=1.0)],
    "species": [
        Species(
            sid="S1",
            initialConcentration=10.0,
            compartment="C",
            hasOnlySubstanceUnits=False,
            boundaryCondition=True,
        )
    ],
    "parameters": [Parameter(sid="k1", value=1.0)],
    "reactions": [
        Reaction(sid="R1", equation="S1 ->", formula=("k1 * S1 * sin(time)", None))
    ],
    "assignments": [],
}

m2_dict = m1_dict.copy()
m2_dict["mid"] = "m2_boundary_condition"
m2_dict["assignments"] = [AssignmentRule("S1", 20.0)]


core_model = CoreModel.from_dict(model_dict=m1_dict)
core_model.create_sbml()
core_model.write_sbml("m1_boundary_condition.xml")
[Nall, Nerr, Nwar] = validate_doc(core_model.doc, units_consistency=False)

core_model = CoreModel.from_dict(model_dict=m2_dict)
core_model.create_sbml()
core_model.write_sbml("m2_boundary_condition.xml")
[Nall, Nerr, Nwar] = validate_doc(core_model.doc, units_consistency=False)
