import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_index_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("markdown to pdf", response.text.lower())
        self.assertIn("nextConvertBtn", response.text)

    def test_healthz_returns_ok(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("app.routers.convert.pdf_service.generate", return_value=b"%PDF-1.4 test")
    def test_convert_returns_pdf_download(self, mock_generate):
        response = self.client.post(
            "/convert",
            files={"file": ("notes.md", b"# Hello\n\n- [x] done", "text/markdown")},
            data={"theme": "github"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("filename*=UTF-8''notes.pdf", response.headers["content-disposition"])

        mock_generate.assert_called_once()
        html_body, theme = mock_generate.call_args.args
        self.assertIn("<h1", html_body)
        self.assertEqual(theme, "github")

    def test_convert_rejects_non_markdown_extension(self):
        response = self.client.post(
            "/convert",
            files={"file": ("notes.txt", b"plain text", "text/plain")},
            data={"theme": "default"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Only .md files are supported.")

    def test_convert_rejects_non_utf8_content(self):
        response = self.client.post(
            "/convert",
            files={"file": ("korean.md", "한글".encode("cp949"), "text/markdown")},
            data={"theme": "default"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "File must be UTF-8 encoded.")

    @patch(
        "app.routers.convert.pdf_service.generate",
        side_effect=RuntimeError("WeasyPrint dependencies are not available."),
    )
    def test_convert_surfaces_pdf_generation_error(self, mock_generate):
        response = self.client.post(
            "/convert",
            files={"file": ("notes.md", b"# Hello", "text/markdown")},
            data={"theme": "default"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "WeasyPrint dependencies are not available.",
        )
        mock_generate.assert_called_once()
