from io import BytesIO
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

BASE_DIR = Path(__file__).resolve().parent.parent.parent
THEMES_DIR = BASE_DIR / "app" / "themes"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

VALID_THEMES = {"default", "github", "academic", "dark_print"}


def generate(html_body: str, theme: str = "default") -> bytes:
    if theme not in VALID_THEMES:
        theme = "default"

    template = _jinja_env.get_template("pdf_wrapper.html")
    full_html = template.render(
        body_html=html_body,
        theme=theme,
        themes_dir=str(THEMES_DIR),
    )

    font_config = FontConfiguration()
    stylesheets = [
        CSS(filename=str(THEMES_DIR / "base.css"), font_config=font_config),
        CSS(filename=str(THEMES_DIR / f"{theme}.css"), font_config=font_config),
    ]

    buf = BytesIO()
    HTML(string=full_html, base_url=str(BASE_DIR)).write_pdf(
        buf,
        stylesheets=stylesheets,
        font_config=font_config,
    )
    buf.seek(0)
    return buf.read()
