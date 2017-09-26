from django.template.loader import get_template
from django.template import Context


class VisualizerBase(object):
    
    def __init__(self, raw_content, visualizer_id):
        """
        Process raw_content which is the content of a file to be visualized. visualizer_id is
        guaranteed to be unique across different visualizers.
        """
        pass

    def get_js_files(self):
        """
        Return a list of strings, indicating the required javascript files. Note the order matters
        because one javascript file may depend on another one.
        """
        pass
    
    def get_css_files(self):
        """
        Return a list of strings, indicating the required css files. Note the order matters because
        one css file may depend on another one
        """
        pass

    def get_template_path(self):
        """
        Return a string indicating the template to render the content
        """
        pass

    def get_template_context(self):
        """
        Return a dictionary which includes all the information for the template to render content
        """
        pass

    def get_html(self):
        """
        Return a string which is in html format and is ready to display on web
        """
        template = get_template(self.get_template_path())
        context = Context(self.get_template_context())
        return template.render(context)
