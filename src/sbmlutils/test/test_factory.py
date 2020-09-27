"""
Testing the factory methods.
"""
import pytest

import libsbml
from sbmlutils import factory
from sbmlutils.factory import *


def test_reaction_creation():
    """ Test Equation.
        bA: A_ext => A; (scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A);
    """
    rt = Reaction(
        sid='bA',
        name='bA (A import)',
        equation='A_ext => A []',
        compartment='membrane',
        pars=[],
        rules=[],
        formula=('scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A', 'mole_per_s')
    )
    assert rt


def test_event():
    objects = [
        Parameter(sid="p1", value=0.0, constant=False),
        Event(sid="e1", trigger='time >= 10', assignments={'p1': 10.0})
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 1


def test_event2():
    objects = [
        Compartment('c', value=1.0),
        Species('S1', initialAmount=1.0, compartment='c'),
        Parameter(sid="p1", value=0.0, constant=False),
        Event(sid="e1", trigger='time >= 100', assignments={'p1': 10.0, 'S1': "p1 + 10"})
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 2
