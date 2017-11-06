from django.test import TestCase

from serapis.utils.visualizers.fileio.stm32_waveform_file_reader import STM32WaveformFileReader

class STM32WaveformFileReaderTestCase(TestCase):
    
    def test_empty_content_should_fail(self):
        reader = STM32WaveformFileReader(b'')
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_EMPTY_FILE)
        with self.assertRaises(Exception):
            reader.get_period_sec()
        with self.assertRaises(Exception):
            reader.get_period_ms()
        with self.assertRaises(Exception):
            reader.get_num_display_plots()
        with self.assertRaises(Exception):
            reader.get_event_series()

    def test_non_ascii_content_should_fail(self):
        reader = STM32WaveformFileReader(b'\xffbinary\xee')
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_NON_ASCII)

    def test_no_metadata_should_fail(self):
        content = "\n".join([
            '68, 0, 3',
            '68, 2000, 1',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_FORMAT)

    def test_no_period_should_fail(self):
        content = "\n".join([
            '==',
            '68, 0, 3',
            '68, 2000, 1',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_no_tick_frequency_should_fail(self):
        content = "\n".join([
            'Period: 20',
            '==',
            '68, 0, 3',
            '68, 2000, 1',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_incomplete_display_block_should_fail(self):
        content = "\n".join([
            'Period: 20',
            'Tick frequency: 5000',
            'Display start',
            'CTL,0',
            'VAL,2,1',
            '==',
            '68, 0, 3',
            '68, 2000, 1',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_no_pin_indexes_in_display_block_should_fail(self):
        content = "\n".join([
            'Period: 20',
            'Tick frequency: 5000',
            'Display start',
            'CTL',
            'Display end',
            '==',
            '68, 0, 3',
            '68, 2000, 1',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_good_example_1(self):
        content = "\n".join([
            'Period: 20',
            'Tick frequency: 5000',
            'Display start',
            'CTL,0',
            'VAL,2,1',
            'Display end',
            '==',
            '68, 0, 0',
            '68, 30000, 3',
            '68, 70000, 4',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), True)
        self.assertEqual(reader.get_error_code(), None)
        self.assertEqual(reader.get_period_sec(), 20.)
        self.assertEqual(reader.get_period_ms(), 20000.)
        self.assertEqual(reader.get_num_display_plots(), 2)
        self.assertEqual(reader.get_event_series(0), (
            'CTL',
            [(0., 0), (6000., 1), (14000., 0), (20000., 0)],
        ))
        self.assertEqual(reader.get_event_series(1), (
            'VAL',
            [(0., 0), (6000., 1), (14000., 2), (20000., 2)],
        ))
    
    def test_good_example_2(self):
        # 1. Though not encouraged, the parser should tolerate trailing spaces
        # 2. Test a segment of series in the middle
        content = "\n".join([
            'Period: 0.1 ',
            'Tick frequency: 100 ',
            'Display start  ',
            'CTL,0 ',
            'VAL,2,1  ',
            'RST,3',
            'Display end ',
            '==  ',
            '68, 0, 0',
            '68, 1, 3',
            '68, 2, 15 ',
            '68, 3, 14',
            '68, 4, 4',
            '68, 5, 5  ',
            '68, 6, 6',
            '68, 7, 7',
            '68, 8, 11',
            '68, 9, 13',
            '68, 10, 10',
        ])
        reader = STM32WaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), True)
        self.assertEqual(reader.get_error_code(), None)
        self.assertEqual(reader.get_period_sec(), 0.1)
        self.assertEqual(reader.get_period_ms(), 100.)
        self.assertEqual(reader.get_num_display_plots(), 3)
        
        self.assertEqual(reader.get_event_series(series_idx=0), (
            'CTL',
            [(0., 0), (10., 1), (30., 0), (50., 1), (60., 0), (70., 1), (100., 0)],
        ))
        self.assertEqual(reader.get_event_series(series_idx=1), (
            'VAL',
            [(0., 0), (10., 1), (20, 3), (40., 2), (60., 3), (80., 1), (90., 2), (100., 1)],
        ))
        self.assertEqual(reader.get_event_series(series_idx=2), (
            'RST',
            [(0., 0), (20., 1), (40., 0), (80., 1), (100., 1)],
        ))
        
        self.assertEqual(
                reader.get_event_series(series_idx=0, start_time_ms=15.0, end_time_ms=85.0),
                (
                    'CTL',
                    [(15., 1), (30., 0), (50., 1), (60., 0), (70., 1), (85., 1)],
                ),
        )
        self.assertEqual(
                reader.get_event_series(series_idx=1, start_time_ms=62.0, end_time_ms=77.0),
                (
                    'VAL',
                    [(62., 3), (77., 3)],
                ),
        )
        self.assertEqual(
                reader.get_event_series(series_idx=2, start_time_ms=-100.0, end_time_ms=99999.9),
                (
                    'RST',
                    [(0., 0), (20., 1), (40., 0), (80., 1), (100., 1)],
                ),
        )
