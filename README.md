# md2pdf-converter

[![CI](https://github.com/woowoo29/md2pdf-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/woowoo29/md2pdf-converter/actions/workflows/ci.yml)

Markdown files to polished PDF documents through a small FastAPI web app.

This project started as a personal utility and a small end-to-end build exercise: upload a `.md` file, choose a print theme, and download a styled PDF. It now serves as a compact portfolio project that shows backend routing, template rendering, async integration with a synchronous library, and a lightweight frontend UX.

## Features

- Drag-and-drop Markdown upload
- Four PDF themes: `default`, `github`, `academic`, `dark_print`
- UTF-8 validation for uploaded files
- Styled code blocks, tables, footnotes, task lists, and fenced code support
- Reusable service split: Markdown rendering and PDF generation are separated
- Repeat-conversion flow with a "next file" reset action after download

## Portfolio Highlights

- Built a complete user flow instead of a code sample in isolation
- Separated router, service, theme, template, and static asset concerns
- Kept the FastAPI route non-blocking by offloading PDF generation to a thread executor
- Added tests for core request flows and Markdown rendering behavior
- Documented setup, structure, and technical tradeoffs for easier review

## Tech Stack

- Python
- FastAPI
- Jinja2
- WeasyPrint
- Python-Markdown
- Vanilla JavaScript
- CSS

## Project Structure

```text
md2pdf-converter/
├── app/
│   ├── main.py
│   ├── routers/
│   │   └── convert.py
│   ├── services/
│   │   ├── markdown_service.py
│   │   └── pdf_service.py
│   ├── templates/
│   │   ├── index.html
│   │   └── pdf_wrapper.html
│   └── themes/
│       ├── base.css
│       ├── default.css
│       ├── github.css
│       ├── academic.css
│       └── dark_print.css
├── static/
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── app.js
├── tests/
├── LICENSE
├── README.md
├── requirements.txt
└── run.sh
```

## Local Setup

### 1. Install system dependency

On macOS:

```bash
brew install pango
```

### 2. Install Python packages

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the app

```bash
./run.sh
```

Then open:

```text
http://127.0.0.1:8000
```

## Running Tests

The test suite is intentionally lightweight and uses Python's built-in `unittest` runner.

```bash
python -m unittest discover -s tests
```

## Notes

- The app is currently optimized for local/personal use.
- WeasyPrint needs system libraries, so `run.sh` sets the required library path for macOS.
- For a public deployment, file-size limits, sanitization rules, and more defensive error handling would be the next steps.

## License

MIT. See [LICENSE](./LICENSE).
