import json
import re
import random

from serapis.utils.visualizer.visualizer_base import VisualizerBase


class STM32WaveformVisualizer(VisualizerBase):
    """
    An example of the file content looks like the following:

      Period: 20
      Tick frequency: 5000
      Display start
      CTL,0
      VAL,2,1
      Display end
      ==
      68, 0, 0
      68, 30000, 3
      68, 70000, 4

    The file content should consist of two sections, separated by "==" line. These two sections
    are metadata section and waveform section.

    The interpretation of the metadata section of the presented example is the following: The total
    period of the waveform is 20 seconds. In each second, there are 5000 ticks. The display block
    (surrounding by "Display start" and "Display end" lines) specifies the configuration of all the
    plots, one per line. The configuration includes the plot label, and which pins are included in
    this plot. In this example, two plots of waveform are going to be displayed. The first waveform
    is labeled as "CTL", which captures the changes of 0th pin. The second waveform is called
    "VAL", which combines the 2nd pin (the most significant) and 1st pin (the least significant).

    The waveform section is composed of several lines, each line contains 3 numbers separated by
    commas. These numbers are: event type, timestamp in tick, and bus value (the value of putting
    all the pins in order.)

    Taking the second waveform as an example, we will display 3 transitions:
      - at 0th tick, the value is 0
      - at 30000th tick, the value is 1
      - at 70000th tick, the value is 2

    """

    def __init__(self, raw_content):
        if len(raw_content) == 0:
            self.template_context = {
                    'con_visualize': False,
                    'plain_text': '(Empty file)',
            }
        else:
            try:
                content = raw_content.decode('ascii')
            except:
                self.template_context = {
                        'con_visualize': False,
                        'plain_text': '(Parsing error: The file includes non-ascii characters)'
                }

            self.template_context = self._parse_content(content)
            if self.template_context is None:
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

    def get_js_files(self):
        return [
                "https://www.amcharts.com/lib/3/amcharts.js",
                "https://www.amcharts.com/lib/3/serial.js",
                "https://www.amcharts.com/lib/3/xy.js",
                "https://www.amcharts.com/lib/3/plugins/export/export.min.js",
                "https://www.amcharts.com/lib/3/themes/light.js",
        ]
    
    def get_css_files(self):
        return [
                "https://www.amcharts.com/lib/3/plugins/export/export.css",
        ]

    def get_template_path(self):
        return 'serapis/visualizers/stm32_waveform_visualizer.html'

    def get_template_context(self):
        return self.template_context

    def _parse_content(self, content):
        try:
            lines = content.strip().split('\n')
            num_total_lines = len(lines)
            line_idx = 0

            # E.g., Period: 20
            matches = re.search(r'^Period: *(\d+(\.\d*)?)', lines[line_idx])
            if not matches:
                return None
            period_ms = float(matches.group(1)) * 1000.
            line_idx += 1

            # E.g., Tick frequency: 5000
            matches = re.search(r'^Tick frequency: *(\d+(\.\d*)?)', lines[line_idx])
            if not matches:
                return None
            tick_ms = 1000. / float(matches.group(1))
            line_idx += 1

            # E.g., Display start
            #       CTL,0
            #       VAL,2,1
            #       Display end
            if not lines[line_idx].startswith('Display start'):
                return None
            line_idx += 1

            plot_configs = []
            while line_idx < num_total_lines and not lines[line_idx].startswith('Display end'):
                terms = lines[line_idx].split(',')
                plot_configs.append({
                    'label': terms[0],
                    'pins': [int(x) for x in terms[1:]],
                    'id': 'waveform%d' % line_idx,
                })
                line_idx += 1

            line_idx += 1

            # E.g., ==
            if not lines[line_idx].startswith('=='):
                return None
            line_idx += 1

            # E.g., 68, 0, 0
            #       68, 30000, 3
            #       68, 70000, 4
            line_terms = [l.strip().split(',') for l in lines[line_idx:]]
            bus_values = [(float(l[1]) * tick_ms, int(l[2]))
                    for l in line_terms if int(l[0]) == 68]
            
            # If there are no pin value events or the first pin value event does not start at
            # time 0, add an event with time 0 in the beginning
            if len(bus_values) == 0:
                bus_values = [(0.0, 0)]
            elif bus_values[0][0] != 0:
                bus_values[0:0] = [(0.0, 0)]

            # Add a dummy end pin value event
            bus_values.append((period_ms, 0))

            plot_series_json = list(map(
                lambda config: self._compute_plot_json(config, bus_values),
                plot_configs,
            ))
            return {
                    'can_visualize': True,
                    'plot_series_json': plot_series_json,
                    'visualizer_id': 'vis%d' % random.randint(0, 1000000)
            }
            
        except:
            return None

    def _compute_plot_json(self, plot_config, bus_values):
        last_val = -1
        pins = plot_config['pins']
        series_timestamps = []
        series_values = []
        for i in range(len(bus_values) - 1):
            val = 0
            for pidx in pins:
                val = (val << 1) | ((bus_values[i][1] >> pidx) & 1)
            if val != last_val:
                series_timestamps.append(bus_values[i][0])
                series_values.append(val)
                series_timestamps.append(bus_values[i + 1][0] - 0.01)
                series_values.append(val)
                last_val = val
        return json.dumps({
            'timestamps': series_timestamps,
            'values': series_values,
            'label': plot_config['label'],
            'id': plot_config['id'],
        })
