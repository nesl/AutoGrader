class VisualizerManager(Object):

	def __init__(self):
		self.js_files = set()
		self.css_files = set()
		self.visualizations = []

	def add_file(field_name, raw_content, url):
		from serapis.utils.visualizer.plain_text_visualizer import PlainTextVisualizer
		visualizer = PlainTextVisualizer(raw_content)

		visualizer.js_files.update(VisualizerClass.get_js_files())
		visualizer.css_files.update(VisualizerClass.get_css_files())
		self.visualizations.append({
			'field_name': field_name,
			'html': visualizer.get_html(),
			'url': url,
		})

	def get_js_files(self):
		"""
		Return a set object indicating all the javascript files that the visualizers requests
		"""
		return self.js_files

	def get_css_files(self):
		"""
		Return a set object indicating all the css files that the visualizers requests
		"""
		return self.css_files

	def get_visualizations_for_template(self):
		return self.visualizations
