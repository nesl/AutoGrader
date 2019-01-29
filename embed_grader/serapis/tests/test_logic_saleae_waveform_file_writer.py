from django.test import TestCase

from serapis.utils.visualizers.fileio.logic_saleae_waveform_file_writer import LogicSaleaeWaveformFileWriter

class LogicSaleaeWaveformFileWriterTestCase(TestCase):
 
    def test_case(self):
        # Simulate a user tries to marshal the output whenever one thing is configured. Expect
        # exceptions except the last step.

        # Assume that Logic Saleae creates the following output file
        raw_data_path = '/tmp/LogicSaleaeWaveformFileWriterTestCase_raw_data_vmwjioplkhwbbcj2j38jm'
        with open(raw_data_path, 'w') as fo:
            fo.write("\n".join([
                'Time[s], Data[Hex]',
                '0.000000000000000, 0',
                '0.633994500000000, 1',
                '0.673993125000000, 0',
                '0.736037562500000, 8',
            ]))

        output_path = '/tmp/LogicSaleaeWaveformFileWriterTestCase_output_0vjn2hj1n2hdunxmm385ufn'

        writer = LogicSaleaeWaveformFileWriter(output_path)

        # add period
        writer.set_period_sec(1)
        with self.assertRaises(Exception):
            writer.marshal()
        
        # add display params
        writer.add_display_param('CTL', 0)
        writer.add_display_param('VAL', [2, 1])
        writer.add_display_param('RST', [3])
        with self.assertRaises(Exception):
            writer.marshal()

        # add raw data path
        writer.set_raw_data_path(raw_data_path)

        writer.marshal()

        with open(output_path, 'rb') as f:
            self.assertEqual(
                    f.read(),
                    b'Period: 1.000000\n' +
                    b'Display start\n' +
                    b'CTL,0\n' +
                    b'VAL,2,1\n' +
                    b'RST,3\n' +
                    b'Display end\n' +
                    b'==\n' +
                    b'Time[s], Data[Hex]\n' +
                    b'0.000000000000000, 0\n' +
                    b'0.633994500000000, 1\n' +
                    b'0.673993125000000, 0\n' +
                    b'0.736037562500000, 8',
            )
