from django.template.loader import get_template
from django.template import Context


class VisualizerManager(object):

    def __init__(self):
        self.js_files = []
        self.css_files = []
        self.visualizations = []

    def add_file(self, field_name, raw_content, url):
        visualizer = self._get_visualizer(field_name, raw_content,
                visualizer_id=len(self.visualizations))
        self._update_list(self.js_files, visualizer.get_js_files() or [])
        self._update_list(self.css_files, visualizer.get_css_files() or [])
        self.visualizations.append({
            'field_name': field_name,
            'html': visualizer.get_html(),
            'url': url,
        })

    def render_js(self):
        """
        Return a list of <script> tags in html format. These tags are for importing the javascript
        files that the visualizers request. Note the list preserves the order that each visualizer
        requests.
        """
        template = get_template('serapis/visualizers/visualizer_manager/render_js.html')
        return template.render(Context({'js_files': self.js_files}))

    def render_css(self):
        """
        Return a list of <link> tags in html format. These tags are for importing the css files
        that the visualizers request. Note the list preserves the order that each visualizer
        requests.
        """
        template = get_template('serapis/visualizers/visualizer_manager/render_css.html')
        return template.render(Context({'css_files': self.css_files}))

    def get_visualizations(self):
        """
        Return a list of dictionaries, which always include 'field_name', 'html', and 'url'
        """
        return self.visualizations

    def _update_list(self, target_list, supplement_list):
        for o in supplement_list:
            if o not in target_list:
                target_list.append(o)

    def _get_visualizer(self, field_name, raw_content, visualizer_id):
        params = (raw_content, visualizer_id)
        if field_name.endswith('.stm32.waveform'):
            from serapis.utils.visualizers.stm32_waveform_visualizer import STM32WaveformVisualizer
            return STM32WaveformVisualizer(*params)
        elif field_name.endswith('.logicsaleae.waveform'):
            from serapis.utils.visualizers.logic_saleae_waveform_visualizer import LogicSaleaeWaveformVisualizer
            return LogicSaleaeWaveformVisualizer(*params)
        else:
            from serapis.utils.visualizers.plain_text_visualizer import PlainTextVisualizer
            return PlainTextVisualizer(*params)
