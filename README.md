# md2pdf-converter

[![CI](https://github.com/woowoo29/md2pdf-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/woowoo29/md2pdf-converter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Markdown files to polished PDF documents through a small FastAPI web app and a macOS desktop wrapper.

This project started as a personal utility and a small end-to-end build exercise: upload a `.md` file, choose a print theme, and download a styled PDF. It now serves as a compact portfolio project that shows backend routing, template rendering, async integration with a synchronous library, and a lightweight frontend UX.

## Features

- Drag-and-drop Markdown upload
- Native macOS open/save dialogs in desktop mode
- Four PDF themes: `default`, `github`, `academic`, `dark_print`
- UTF-8 validation for uploaded files
- Styled code blocks, tables, footnotes, task lists, and fenced code support
- Supports `.md` and `.markdown` files
- Reusable service split: Markdown rendering and PDF generation are separated
- Repeat-conversion flow with a "next file" reset action after download

## Portfolio Highlights

- Built a complete user flow instead of a code sample in isolation
- Separated router, service, theme, template, and static asset concerns
- Kept the FastAPI route non-blocking by offloading PDF generation to a thread executor
- Wrapped the same local FastAPI app inside a macOS desktop shell instead of rewriting the UI
- Added tests for core request flows and Markdown rendering behavior
- Documented setup, structure, and technical tradeoffs for easier review

## Tech Stack

- Python
- FastAPI
- Jinja2
- WeasyPrint
- Python-Markdown
- pywebview
- py2app
- Vanilla JavaScript
- CSS

## Project Structure

```text
md2pdf-converter/
├── app/
│   ├── main.py
│   ├── runtime_paths.py
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
├── scripts/
│   └── build_macos_app.sh
├── tests/
├── desktop/
│   ├── __main__.py
│   ├── app.py
│   ├── bridge.py
│   ├── server.py
│   └── single_instance.py
├── install_md2pdf.command
├── LICENSE
├── README.md
├── launch_md2pdf.command
├── requirements-desktop.txt
├── requirements.txt
├── setup.py
└── run.sh
```

## Local Setup

### Fastest macOS option

If you are on macOS and want the app from a repo checkout with one click:

- Double-click `install_md2pdf.command`
- It installs the required Homebrew dependency if needed, builds the desktop app, and opens `md2pdf-converter.app`
- The first run can take a few minutes because it may create a local build environment

If you do not want to build locally, use the prebuilt `.dmg` from GitHub Releases instead.

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

## Desktop Mode

### Run as a local macOS app shell

Install desktop-only dependencies:

```bash
pip install -r requirements-desktop.txt
```

Start the app window directly:

```bash
python -m desktop
```

Desktop mode keeps the same UI and conversion backend, but swaps browser downloads for native macOS open/save dialogs.

### Build an unsigned `.app` and `.dmg`

```bash
bash scripts/build_macos_app.sh
```

Artifacts are created at:

```text
md2pdf-converter.app
dist/md2pdf-converter-unsigned.dmg
```

The build script prefers the active virtualenv's `python`, and otherwise creates an isolated `.venv-desktop-build` environment with macOS `python3`. After building, it copies the finished `.app` bundle to the project root so you can launch it directly from Finder without depending on `dist/`.

For repo users who prefer a single click, `install_md2pdf.command` wraps the dependency check, build step, and app launch.

Because the build is unsigned, macOS may block the first launch. Open it with `Control` + click -> `Open`, or remove the quarantine flag manually after download/copy.

### Sign and notarize for smooth macOS launches

To reduce Gatekeeper warnings for other users, sign the root app bundle with your Developer ID certificate:

```bash
APPLE_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
bash scripts/sign_macos_app.sh
```

Then notarize the DMG with a `notarytool` keychain profile you already stored on this Mac:

```bash
APPLE_NOTARY_PROFILE="NotaryToolProfile" \
bash scripts/notarize_macos_app.sh
```

If you do not have a notary profile yet, create one once with Apple's `xcrun notarytool store-credentials` flow and reuse that profile in future runs.

The desktop app now prefers a single running instance. Launching it again reuses the existing window and forwards newly opened Markdown files into that same session.

## Web Mode

### Optional browser fallback for development

Option A: start from Terminal

```bash
./run.sh
```

Option B: start from Finder on macOS

- Double-click `launch_md2pdf.command`
- The launcher opens `http://127.0.0.1:8000` automatically
- If an old local server is still attached to port `8000`, the launcher restarts it with the current project path

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
- `launch_md2pdf.command` is kept as a browser-mode fallback and development launcher.
- `python -m desktop` opens the same converter inside a native macOS window via `pywebview`.
- The packaged desktop app is currently targeted at Apple Silicon Macs and unsigned local sharing.
- For a public deployment, file-size limits, sanitization rules, and more defensive error handling would be the next steps.

## License

MIT. See [LICENSE](./LICENSE).
