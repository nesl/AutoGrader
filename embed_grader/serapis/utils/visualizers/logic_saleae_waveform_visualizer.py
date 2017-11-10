import json
import re

from embed_grader import settings

from serapis.utils.visualizers.visualizer_base import VisualizerBase
from serapis.utils.visualizers.fileio.logic_saleae_waveform_file_reader import LogicSaleaeWaveformFileReader


class LogicSaleaeWaveformVisualizer(VisualizerBase):

    def __init__(self, raw_content, visualizer_id):
        reader = LogicSaleaeWaveformFileReader(raw_content)
        error_code = reader.get_error_code()

        if error_code == LogicSaleaeWaveformFileReader.ERROR_CODE_EMPTY_FILE:
            self.template_context = {
                    'con_visualize': False,
                    'plain_text': '(Empty file)',
            }
        elif error_code == LogicSaleaeWaveformFileReader.ERROR_CODE_NON_ASCII:
            self.template_context = {
                    'con_visualize': False,
                    'plain_text': '(Parsing error: The file includes non-ascii characters)'
            }
        elif error_code == LogicSaleaeWaveformFileReader.ERROR_CODE_FORMAT:
            plain_text = '\n'.join([
                '(Parsing error: file format is not correct. Show original content below)',
                '',
                '************************************************************************',
                '',
                content,
            ])
            self.template_context = {
                    'con_visualize': False,
                    'plain_text': plain_text,
            }
        else:
            num_plots = reader.get_num_display_plots()
            plot_series_json = [self._compute_plot_json(reader, i, visualizer_id)
                    for i in range(num_plots)]
            self.template_context = {
                    'can_visualize': True,
                    'plot_series_json': plot_series_json,
                    'visualizer_id': 'vis%d' % visualizer_id,
            }

    def get_js_files(self):
        return [
                "https://www.amcharts.com/lib/3/amcharts.js",
                "https://www.amcharts.com/lib/3/serial.js",
                "https://www.amcharts.com/lib/3/xy.js",
                "https://www.amcharts.com/lib/3/plugins/export/export.min.js",
                "https://www.amcharts.com/lib/3/themes/light.js",
                settings.STATIC_URL + "serapis/js/visualizers/logic_saleae_waveform_visualizer_helper.js",
        ]
    
    def get_css_files(self):
        return [
                "https://www.amcharts.com/lib/3/plugins/export/export.css",
        ]

    def get_template_path(self):
        return 'serapis/visualizers/logic_saleae_waveform_visualizer.html'

    def get_template_context(self):
        return self.template_context

    def _compute_plot_json(self, reader, plot_idx, visualizer_id):
        plot_name, plot_events = reader.get_event_series(plot_idx)
        
        # plot_events is a list of (timestamp_sec, bus_value). Here we convert timestamps into
        # microseconds because it's easier to visualize (I hope...)
        plot_events = [(t * 1e6, v) for t, v in plot_events]

        transition_width = 0.001

        series_timestamps = []
        series_values = []

        for i in range(len(plot_events) - 1):
            series_timestamps.append(plot_events[i][0])
            series_values.append(plot_events[i][1])
            series_timestamps.append(plot_events[i+1][0] - transition_width)
            series_values.append(plot_events[i][1])
        
        div_id = 'waveform%d-%d' % (visualizer_id, plot_idx)

        return json.dumps({
            'timestamps': series_timestamps,
            'values': series_values,
            'label': plot_name,
            'id': div_id,
        })
