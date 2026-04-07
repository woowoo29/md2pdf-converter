import unittest

from app.services import markdown_service


class MarkdownServiceTests(unittest.TestCase):
    def test_render_supports_tables_and_task_lists(self):
        markdown_text = """
# Sample

- [x] shipped

| Name | Value |
| --- | --- |
| A | B |
"""

        html = markdown_service.render(markdown_text)

        self.assertIn("<h1", html)
        self.assertIn("<table>", html)
        self.assertIn('type="checkbox"', html)
        self.assertIn("checked", html)

    def test_render_supports_fenced_code_blocks(self):
        markdown_text = """
```python
print("hello")
```
"""

        html = markdown_service.render(markdown_text)

        self.assertIn("<pre>", html)
        self.assertTrue("highlight" in html or "codehilite" in html)
        self.assertIn("print", html)
