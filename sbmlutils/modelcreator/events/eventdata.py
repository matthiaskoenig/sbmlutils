"""
Functions for creating SBML model events.
The information for the creation of events is handled via EventData objects.
The EventData is used to generate the SBML events for the model.

Necessary to create trigger events to guarantee proper integration
even when using variable step sizes.

Here only the triggers are defined. Part of the events are encoded directly in the model.

"""
from __future__ import print_function


class EventData(object):
    def __init__(self, eid, name, trigger, assignments):
        self.eid = eid
        self.key = name
        self.trigger = trigger
        self.assignments = assignments

    def info(self):
        info_str = "'-' * 20\n" \
                   "{}\n" \
                   "{}\n" \
                   "{}\n" \
                   "{}\n".format(self.eid, self.key, self.trigger, self.assignments)
        print(info_str)

    @staticmethod
    def _trigger_from_time(t):
        return '(time >= {})'.format(t)

    @staticmethod
    def _assignments_dict(species, values):
        return dict(zip(species, values))

    @classmethod
    def rect_dilution_peak(cls):
        """ Creates rectangular dilution peak.
        Creates a dilution peak in the given species beginning at the
        start time and with the provided duration.
        """
        ed1 = EventData("EDIL_0", "pre peak [PP]",
                        cls._trigger_from_time(0.0),
                        {'peak_status': '0 dimensionless',
                         'peak_type': '0 dimensionless'})
        ed2 = EventData("EDIL_1", "peak [PP]",
                        cls._trigger_from_time("t_peak"),
                        {'peak_status': '1 dimensionless',
                         'peak_type': '0 dimensionless'})
        ed3 = EventData("EDIL_2", "post peak [PP]",
                        cls._trigger_from_time("t_peak_end"),
                        {'peak_status': '0 dimensionless',
                         'peak_type': '0 dimensionless'})
        return ed1, ed2, ed3

    @classmethod
    def gauss_dilution_peak(cls):
        """ Creates gauss dilution peak. """
        ed1 = EventData("EDIL_0", "pre peak [PP]",
                        cls._trigger_from_time(0.0),
                        {'peak_status': '0 dimensionless',
                         'peak_type': '1 dimensionless'})
        ed2 = EventData("EDIL_1", "peak [PP]",
                        cls._trigger_from_time("mu_peak-4 dimensionless*sigma_peak"),
                        {'peak_status': '1 dimensionless',
                         'peak_type': '1 dimensionless'})
        ed3 = EventData("EDIL_2", "post peak [PP]",
                        cls._trigger_from_time("mu_peak+4 dimensionless*sigma_peak"),
                        {'peak_status': '0 dimensionless',
                         'peak_type': '1 dimensionless'})
        return ed1, ed2, ed3

    @classmethod
    def galactose_challenge(cls, tc_start, base_value=0.0, peak_variable='gal_challenge'):
        """ Creates event data for galactose challenge. """
        ed1 = EventData("ECHA_0", "pre challenge [PP]",
                        cls._trigger_from_time(0.0),
                        {'PP__gal': '{} mM'.format(base_value)})

        ed2 = EventData("ECHA_1", "galactose challenge",
                        cls._trigger_from_time(tc_start),
                        {'PP__gal': peak_variable})
        return ed1, ed2

    @classmethod
    def galactose_step_increase(cls):
        """ Stepwise increase in PP__gal over time. """
        event_data = []
        duration = 1000.0
        for k in range(0, 21):
            time = 0.0 + k * duration
            gal = 0.0 + k * 0.5
            ed = EventData('ESTEP_{}'.format(k), "galactose step",
                           cls._trigger_from_time(time),
                           {'PP__gal': '{} mM'.format(gal)})
            event_data.append(ed)
        return event_data
