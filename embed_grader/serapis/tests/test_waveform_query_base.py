from django.test import TestCase

from serapis.utils.visualizers.fileio.waveform_query_base import WaveformQueryBase


class MinimumWaveformQueryHelper(WaveformQueryBase):
    def __init__(self):
        pass


class WaveformFileWriterTestCase(TestCase):
 
    def test_clean_waveform_method_perfect_waveform(self):
        # expect to return an unchanged waveform

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(0., 0), (1., 10), (2., 20), (3., 30)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(output_data, data)

    def test_clean_waveform_method_unordered_events(self):
        # expect to sort the events

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(1., 10), (0., 0), (3., 30), (2., 20)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0., 0), (1., 10), (2., 20), (3., 30)],
        )

    def test_clean_waveform_method_start_too_early(self):
        # expect to crop early events

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(-1.5, 85), (-0.5, 95), (0.5, 5), (1.5, 15), (3.0, 30)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0.0, 95), (0.5, 5), (1.5, 15), (3.0, 30)],
        )
    
    def test_clean_waveform_method_start_too_late(self):
        # expect to fill in 0 before the first event

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(0.5, 5), (1.5, 15), (3.0, 30)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0.0, 0), (0.5, 5), (1.5, 15), (3.0, 30)],
        )
    
    def test_clean_waveform_method_stop_too_early(self):
        # expect to extend the last waveform till the end

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(0.0, 0), (2.0, 20)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0.0, 0), (2.0, 20), (3.0, 20)],
        )

    def test_clean_waveform_method_stop_too_late(self):
        # expect to crop events appearing after the end time

        helper = MinimumWaveformQueryHelper()
        
        period_sec = 3.0
        data = [(0.0, 0), (2.0, 20), (4.0, 40), (6.0, 60)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0.0, 0), (2.0, 20), (3.0, 20)],
        )

    def test_clean_waveform_method_messy_waveform(self):
        helper = MinimumWaveformQueryHelper()
        
        period_sec = 5
        data = [(-2, 7), (0.3, 4), (3, 4), (2.2, 16), (4.5, 45)]

        output_data = helper._clean_waveform(data, period_sec)

        self.assertEqual(
                output_data,
                [(0.0, 7), (0.3, 4), (2.2, 16), (3.0, 4), (4.5, 45), (5.0, 45)],
        )

    def test_get_event_series(self):
        helper = MinimumWaveformQueryHelper()

        data = [(float(i), i) for i in range(16)]

        # test single pin, default time range
        output_series = helper._get_event_series(data, pin_indexes=3)
        self.assertEqual(
                output_series,
                [(0.0, 0), (8.0, 1), (15.0, 1)],
        )

        output_series = helper._get_event_series(data, pin_indexes=[2])
        self.assertEqual(
                output_series,
                [(0.0, 0), (4.0, 1), (8.0, 0), (12.0, 1), (15.0, 1)],
        )
        
        # test multiple pins, default time range
        output_series = helper._get_event_series(data, pin_indexes=[3, 2])
        self.assertEqual(
                output_series,
                [(0.0, 0), (4.0, 1), (8.0, 2), (12.0, 3), (15.0, 3)],
        )
        
        # test customized time range
        output_series = helper._get_event_series(data, pin_indexes=1,
                start_time_sec=1.0, end_time_sec=7.0)
        self.assertEqual(
                output_series,
                [(1.0, 0), (2.0, 1), (4.0, 0), (6.0, 1), (7.0, 1)],
        )
        
        output_series = helper._get_event_series(data, pin_indexes=[2, 0],
                start_time_sec=11.5, end_time_sec=14.5)
        self.assertEqual(
                output_series,
                [(11.5, 1), (12.0, 2), (13.0, 3), (14.0, 2), (14.5, 2)],
        )
        
        # test exeeding time bounds
        output_series = helper._get_event_series(data, pin_indexes=3,
                start_time_sec=-100, end_time_sec=100)
        self.assertEqual(
                output_series,
                [(0.0, 0), (8.0, 1), (15.0, 1)],
        )

    def test_get_rising_and_falling_edge_events(self):
        helper = MinimumWaveformQueryHelper()

        data = [(float(i), i) for i in range(16)]

        self.assertEqual(
                helper._get_rising_edge_events(data, pin_index=0),
                [1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0],
        )
        
        self.assertEqual(
                helper._get_falling_edge_events(data, pin_index=1),
                [4.0, 8.0, 12.0],
        )
        
        output = helper._get_rising_edge_events(
                data, pin_index=2, start_time_sec=2, end_time_sec=12)
        self.assertEqual(
                output,
                [4.0, 12.0],
        )
        
        output = helper._get_falling_edge_events(
                data, pin_index=3, start_time_sec=10, end_time_sec=15)
        self.assertEqual(
                output,
                [],
        )
    
    def test_get_rising_and_falling_edge_events(self):
        helper = MinimumWaveformQueryHelper()

        data = [(float(i), 30 - i) for i in range(16)]

        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=-3.2),
                None,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=0.0),
                30,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=0.5),
                30,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=7.7),
                23,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=15.0),
                15,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[4, 3, 2, 1, 0], query_time_sec=15.1),
                None,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=0, query_time_sec=4),
                0,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[1, 4], query_time_sec=10.2),
                1,
        )
        self.assertEqual(
                helper._get_bus_value(data, pin_indexes=[3, 2], query_time_sec=6.1),
                2,
        )
        
