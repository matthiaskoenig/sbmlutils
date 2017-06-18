from __future__ import print_function, absolute_import
import pytest
import libsbml
from sbmlutils import factory as fac


# EVENTS #
def test_event():
    objects = [
        fac.Parameter(sid="p1", value=0.0, constant=False),
        fac.Event(sid="e1", trigger='time >= 10', assignments={'p1': 10.0})
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    fac.create_objects(model, objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 1


def test_event2():
    objects = [
        fac.Compartment('c', value=1.0),
        fac.Species('S1', value=1.0, compartment='c'),
        fac.Parameter(sid="p1", value=0.0, constant=False),

        fac.Event(sid="e1", trigger='time >= 100', assignments={'p1': 10.0, 'S1': "p1 + 10"})
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    fac.create_objects(model, objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 2






