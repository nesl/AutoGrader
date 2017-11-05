from django.test import TestCase

from serapis.utils.visualizers.fileio.stm32_waveform_file_reader import STM32WaveformFileReader

class STM32WaveformFileReaderTestCase(TestCase):
    def test_empty_content_should_fail(self):
        reader = STM32WaveformFileReader('')
        self.assertEqual(reader.is_successfully_parsed(), False)
        self.assertEqual(reader.get_error_code(), STM32WaveformFileReader.ERROR_CODE_EMPTY_FILE)
        self.assertRaises(Exception, reader.get_period_sec())
