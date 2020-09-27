"""
Test eventdata.
"""
from sbmlutils.modelcreator.events.eventdata import EventData


def test_eventdata():
    eid = "test"
    name = "E01"
    trigger = "time == 0"
    assignments = []
    e = EventData(eid, name, trigger, assignments)

    assert e.eid == eid
    assert e.key == name
    assert e.trigger == trigger
    assert e.assignments == assignments


def test_rect_dilution_peak():
    ed_list = EventData.rect_dilution_peak()
    for edata in ed_list:
        edata.info()


def test_gauss_dilution_peak():
    ed_list = EventData.gauss_dilution_peak()
    for edata in ed_list:
        edata.info()


def test_galactose_challenge():
    ed_list = EventData.galactose_challenge(tc_start=10, base_value=0.0)
    for edata in ed_list:
        edata.info()


def test_galactose_step_increase():
    ed_list = EventData.galactose_step_increase()
    for edata in ed_list:
        edata.info()
