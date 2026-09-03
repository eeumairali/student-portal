from django.test import SimpleTestCase

from .models import render_markdown


class ArticleRenderingTests(SimpleTestCase):
	def test_markdown_table_renders_for_public_articles(self):
		rendered = render_markdown(
			"| Topic | Notes |\n| --- | --- |\n| Tables | Work |"
		)

		self.assertIn("<table>", rendered)
		self.assertIn("<th>Topic</th>", rendered)
		self.assertIn("<td>Work</td>", rendered)
