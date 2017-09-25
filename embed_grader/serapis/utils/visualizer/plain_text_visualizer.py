from serapis.utils.visualizer.visualizer_base import VisualizerBase


class PlainTextVisualizer(VisualizerBase):
    
    def __init__(self, raw_content):
        if len(raw_content) == 0:
            content = '(Empty file)'
        else:
            try:
                content = raw_content.decode('ascii')
            except:
                content = '(The file includes non-ascii characters)'
        self.template_context = {'content': content}

    def get_js_files(self):
        return set()
    
    def get_css_files(self):
        return set()

    def get_template_path(self):
        return 'serapis/visualizers/plain_text_visualizer.html'

    def get_template_context(self):
        return self.template_context
