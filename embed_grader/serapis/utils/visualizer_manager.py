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

    def get_js_files(self):
        """
        Return a list indicating all the javascript files that the visualizers request. Note
        the list preserves the order that each visualizer requests
        """
        return self.js_files

    def get_css_files(self):
        """
        Return a list indicating all the css files that the visualizers request. Note the list
        preserves the order that each visualizer requests
        """
        return self.css_files

    def get_visualizations_for_template(self):
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
            from serapis.utils.visualizer.stm32_waveform_visualizer import STM32WaveformVisualizer
            return STM32WaveformVisualizer(*params)
        else:
            from serapis.utils.visualizer.plain_text_visualizer import PlainTextVisualizer
            return PlainTextVisualizer(*params)
