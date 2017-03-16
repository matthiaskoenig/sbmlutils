"""
Handling the creation of on comp model from
multiple model files.
"""
from __future__ import print_function


class CompModel(object):
    def __init__(self, models):
        pass

        def __init__(self, sid, value, compartment, unit=None, constant=False, boundaryCondition=False,
                     hasOnlySubstanceUnits=False, name=None, sboTerm=None, metaId=None):
            super(Species, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
            self.compartment = compartment
            self.constant = constant
            self.boundaryCondition = boundaryCondition
            self.hasOnlySubstanceUnits = hasOnlySubstanceUnits


def create_sbml(self, model):
    obj = _create_specie(model,
                         sid=self.sid,
                         name=self.name,
                         value=self.value,
                         unit=self.unit,
                         compartment=self.compartment,
                         boundaryCondition=self.boundaryCondition,
                         constant=self.constant,
                         hasOnlySubstanceUnits=self.hasOnlySubstanceUnits)
    return obj
