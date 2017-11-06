from django.test import TestCase

from serapis.utils.visualizers.fileio.stm32_waveform_file_writer import STM32WaveformFileWriter

class STM32WaveformFileWriterTestCase(TestCase):
 
    def test_case_1(self):
        # Simulate a user tries to marshal the output whenever one thing is configured. Expect
        # exceptions except the last step.

        output_path = '/tmp/STM32WaveformFileWriterTestCase_case1_uenckqpmvhejivn47vjwnc9'

        writer = STM32WaveformFileWriter(output_path)

        # add period
        writer.set_period_sec(20)
        with self.assertRaises(Exception):
            writer.marshal()
        
        # add tick frequency
        writer.set_tick_frequency(5000)
        with self.assertRaises(Exception):
            writer.marshal()

        # add display params
        writer.add_display_param('CTL', 0)
        writer.add_display_param('VAL', [2, 1])

        # add data
        writer.add_event(68, 0, 0)
        writer.add_event(68, 30000, 3)
        writer.add_event(68, 70000, 4)

        writer.marshal()

        with open(output_path, 'rb') as f:
            self.assertEqual(
                    f.read(),
                    b'Period: 20.000000\n' +
                    b'Tick frequency: 5000.000000\n' +
                    b'Display start\n' +
                    b'CTL,0\n' +
                    b'VAL,2,1\n' +
                    b'Display end\n' +
                    b'==\n' +
                    b'68,0,0\n' +
                    b'68,30000,3\n' +
                    b'68,70000,4',
            )
        
        writer = STM32WaveformFileWriter(output_path)

    def test_case_2(self):
        output_path = '/tmp/STM32WaveformFileWriterTestCase_case2_kvlh3ifj18f9ejzncmdjqyd'

        writer = STM32WaveformFileWriter(output_path)

        writer.set_period_ms(50)
        writer.set_tick_frequency(100)
        writer.add_display_param('CTL', 0)
        writer.add_display_param('RST', [3])
        writer.add_display_param('VAL', [2, 1])
        for i in range(6):
            writer.add_event(68, i, i * 3)

        writer.marshal()

        with open(output_path, 'rb') as f:
            self.assertEqual(
                    f.read(),
                    b'Period: 0.050000\n' +
                    b'Tick frequency: 100.000000\n' +
                    b'Display start\n' +
                    b'CTL,0\n' +
                    b'RST,3\n' +
                    b'VAL,2,1\n' +
                    b'Display end\n' +
                    b'==\n' +
                    b'68,0,0\n' +
                    b'68,1,3\n' +
                    b'68,2,6\n' +
                    b'68,3,9\n' +
                    b'68,4,12\n' +
                    b'68,5,15',
            )
