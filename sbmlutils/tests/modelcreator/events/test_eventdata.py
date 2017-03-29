"""
Test eventdata.
"""
from __future__ import print_function

import unittest

from sbmlutils.modelcreator.events.eventdata import EventData


class TestEventData(unittest.TestCase):

    def test_eventdata(self):
        eid = 'test'
        name = 'E01'
        trigger = 'time == 0'
        assignments = []
        e = EventData(eid, name, trigger, assignments)

        self.assertEqual(e.eid, eid)
        self.assertEqual(e.key, name)
        self.assertEqual(e.trigger, trigger)
        self.assertEqual(e.assignments, assignments)

    def test_rect_dilution_peak(self):
        ed_list = EventData.rect_dilution_peak()
        print('\n* Rectangular peak *')
        for edata in ed_list:
            edata.info()

    def test_gauss_dilution_peak(self):
        ed_list = EventData.gauss_dilution_peak()
        print('\n* Gauss peak *')
        for edata in ed_list:
            edata.info()

    def test_galactose_challenge(self):
        ed_list = EventData.galactose_challenge(tc_start=10, base_value=0.0)
        print('\n* Galactose Challenge *')
        for edata in ed_list:
            edata.info()

    def test_galactose_step_increase(self):
        ed_list = EventData.galactose_step_increase()
        print('\n* Galactose Step *')
        for edata in ed_list:
            edata.info()


if __name__ == "__main__":
    unittest.main()
