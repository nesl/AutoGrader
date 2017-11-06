import json
import re

"""
WaveformQueryBase is an abstract class which provides waveform event cleaning methods and handy
query methods, such as retrieving all rising edges.
"""

class WaveformQueryBase(object):

    def __init__(self):
        raise Exception("Does not expect to be directly instantiated ")

    def _clean_waveform(self, data, period_sec):
        """
        This method crops the events that are beyond the specified time range, or if the specified
        waveform is too short, the method will extend the waveform to align with the two ends of
        the time range. That means, the first event of the cleaned waveform will be at time 0, and
        the last one will be at time period_sec.

        Boundary handling:
          - If there is no event in data, it will be filled in a waveform of 0 from begin to the
            end.
          - If the waveform starts earlier than time 0, a new event at time 0 will be created. The
            waveform value of this new event is set to whatever it has to be (the previous event
            value). All the events before time 0 will be truncated.
          - If the waveform starts later then time 0, a value of 0 will be filled in between time 0
            to the original waveform start time
          - If the waveform stops later than period_sec, the method will crop after time period_sec
          - If the waveform stops before than period_sec, it assumes the device keeps output the
          - same value till the end.

        Params:
          data: A list of tuples. Each tuple contains two elements, a real number indicating the
              timestamp in second, and an integer representing bus value.
          period_sec: A real number indicating the length of the time range. The time range always
              starts at 0.

        Return:
          A list of tuples. Same format as data.
        """

        # clone the data passed in
        new_data = list(data)

        # We cannot continue if there is no sample points in data - we assume the device outputs
        # 0 all the time.
        if len(new_data) == 0:
            new_data = [(0.0, 0), (period_sec, 0)]

        # If there is an event right before time 0, then it is the waveform value at time 0.
        early_events = [e for e in new_data if e[0] < 0.]
        if len(early_events) > 0:
            target_event = max(early_events)  # the event right before time 0
            new_data.append((0.0, target_event[1]))

        # make events in an ascending order, and filter out anything not withing the range
        new_data.sort()
        new_data = list(filter(lambda x: 0. <= x[0] and x[0] <= period_sec, new_data))
            
        # If the first event value starts later than time 0, fill in bus value 0 till the first
        # event
        if new_data[0][0] != 0.:
            new_data[0:0] = [(0.0, 0)]

        # Add a dummy end pin value event (with the event value of the last event)
        if new_data[-1][0] < period_sec:
            new_data.append((period_sec, new_data[-1][1]))

        return new_data

    def _rearrange_bus(self, pin_indexes, original_bus_value):
        """
        A bus value is defined as a binary number when laying down all the pin values in order.
        This function reshuffle the order of pins (may only consider a subset of them.) The first
        index of the pin_indexes will be the most significant value.

        Params:
          pin_indexes: a list presenting pins to be considered
          original_bus_value: an integer
        """
        ret = 0
        for i in pin_indexes:
            ret <<= 1
            ret |= ((original_bus_value & (1 << i)) >> i)
        return ret

    def _get_event_series(self, data, pin_indexes, start_time_sec=None, end_time_sec=None):
        """
        Get the events within the specified time range. The event can be a bus value if pin_indexes
        is specified as a list, including all the pins to be considered. When start_time_sec and/or
        end_time_sec is None, it is configured as the following default values: start_time_sec will
        be the timestamp of the first event (theorically to be 0.0), and end_time_sec will be the
        timestamp of the last event (theorically to be period length.)

        Params:
          data: A list of tuples representing the waveform. This method assumes that data is
              cleaned by _cleaned_waveform().
          pin_indexes: Can be an integer or a list of integers. Representing how a new bus is
              arranged, the first element is the most significant value.
          start_time_sec: A Float number
          end_time_sec: A Float number
        Returns:
          A list of (time, bus_value) representing a time series. Align with both start_time_sec
              and end_time_sec. Will filter out duplicate transitions.
        """

        # convert pin_indexes to a list if it is an integer
        if type(pin_indexes) is int:
            pin_indexes = [pin_indexes]

        # replace the default value
        if start_time_sec is None:
            start_time_sec = data[0][0]
        if end_time_sec is None:
            end_time_sec = data[-1][0]

        # correct the time bounds if they are not correctly set
        start_time_sec = max(data[0][0], start_time_sec)
        end_time_sec = min(data[-1][0], end_time_sec)

        # get bus value based on pin configurations
        series_data = [(t, self._rearrange_bus(pin_indexes, bus_value)) for t, bus_value in data]

        # get transitions within the range
        middle_idx_events = list(filter(
            lambda x: start_time_sec <= x[1][0] and x[1][0] <= end_time_sec,
            enumerate(series_data),
        ))
        candidate_events = [e for _, e in middle_idx_events]

        # handle start boundary
        sidx = middle_idx_events[0][0]
        if sidx > 0 and candidate_events[0][0] > start_time_sec:
            candidate_events[0:0] = [(start_time_sec, series_data[sidx - 1][1])]

        # filter out repeating transitions
        ret_events = []
        ret_events.append(candidate_events[0])
        for cur_event in candidate_events[1:]:
            t, bus_value = cur_event
            if bus_value != ret_events[-1][1]:
                ret_events.append(cur_event)

        # handle end boundary
        if ret_events[-1][0] < end_time_sec:
            ret_events.append((end_time_sec, ret_events[-1][1]))
        
        return ret_events
