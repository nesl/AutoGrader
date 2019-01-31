from django.test import TestCase

from serapis.utils.visualizers.fileio.logic_saleae_waveform_file_reader import LogicSaleaeWaveformFileReader


class LogicSaleaeWaveformFileReaderTestCase(TestCase):
    
    def test_empty_content_should_fail(self):
        reader = LogicSaleaeWaveformFileReader(b'')
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(
                reader.get_error_code(),
                LogicSaleaeWaveformFileReader.ERROR_CODE_EMPTY_FILE,
        )
        with self.assertRaises(Exception):
            reader.get_period_sec()
        with self.assertRaises(Exception):
            reader.get_num_display_plots()
        with self.assertRaises(Exception):
            reader.get_event_series(series_idx=0)

    def test_non_ascii_content_should_fail(self):
        reader = LogicSaleaeWaveformFileReader(b'\xffbinary\xee')
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(
                reader.get_error_code(), LogicSaleaeWaveformFileReader.ERROR_CODE_NON_ASCII)

    def test_no_metadata_should_fail(self):
        content = "\n".join([
            '0.000000000000000, 0',
            '0.633994500000000, 1',
        ])
        reader = LogicSaleaeWaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), LogicSaleaeWaveformFileReader.ERROR_CODE_FORMAT)

    def test_no_period_should_fail(self):
        content = "\n".join([
            '==',
            '0.000000000000000, 0',
            '0.633994500000000, 1',
        ])
        reader = LogicSaleaeWaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), LogicSaleaeWaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_incomplete_display_block_should_fail(self):
        content = "\n".join([
            'Period: 1',
            'Display start',
            'CTL,0',
            'VAL,3,1',
            '==',
            '0.000000000000000, 0',
            '0.633994500000000, 1',
        ])
        reader = LogicSaleaeWaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), LogicSaleaeWaveformFileReader.ERROR_CODE_FORMAT)
    
    def test_good_example(self):
        content = "\n".join([
            'Period: 1',
            'Display start',
            'CTL,0',
            'VAL,3,1',
            'MID,2',
            'Display end',
            '==',
            '0.000000000000000, 0',
            '0.633994500000000, 1',
            '0.673993125000000, 0',
            '0.736037562500000, 8',
            '0.882473110200000, C',
        ])
        reader = LogicSaleaeWaveformFileReader(content.encode())
        self.assertEqual(reader.is_successfully_parsed(), True)
        self.assertEqual(reader.get_error_code(), None)
        self.assertEqual(reader.get_period_sec(), 1.0)
        self.assertEqual(reader.get_num_display_plots(), 3)
        self.assertEqual(reader.get_event_series(0), (
            'CTL',
            [
                (0.0, 0),
                (0.6339945, 1),
                (0.673993125, 0),
                (1.0, 0),
            ],
        ))
        self.assertEqual(reader.get_event_series(1), (
            'VAL',
            [
                (0.0, 0),
                (0.7360375625, 2),
                (1.0, 2),
            ],
        ))
        self.assertEqual(reader.get_event_series(2), (
            'MID',
            [
                (0.0, 0),
                (0.8824731102, 1),
                (1.0, 1),
            ],
        ))
