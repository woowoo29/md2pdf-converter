from io import BytesIO

from jinja2 import Environment, FileSystemLoader

from app import runtime_paths

_jinja_env = Environment(loader=FileSystemLoader(str(runtime_paths.templates_dir())))

VALID_THEMES = {"default", "github", "academic", "dark_print"}


def _load_weasyprint():
    runtime_paths.configure_dynamic_library_paths()

    try:
        from weasyprint import CSS, HTML
        from weasyprint.text.fonts import FontConfiguration
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "WeasyPrint dependencies are not available. "
            "Install the required system libraries and run the app via `run.sh`."
        ) from exc

    return HTML, CSS, FontConfiguration


def generate(html_body: str, theme: str = "default") -> bytes:
    HTML, CSS, FontConfiguration = _load_weasyprint()

    if theme not in VALID_THEMES:
        theme = "default"

    template = _jinja_env.get_template("pdf_wrapper.html")
    full_html = template.render(
        body_html=html_body,
        theme=theme,
        themes_dir=str(runtime_paths.themes_dir()),
    )

    font_config = FontConfiguration()
    stylesheets = [
        CSS(filename=str(runtime_paths.themes_dir() / "base.css"), font_config=font_config),
        CSS(filename=str(runtime_paths.themes_dir() / f"{theme}.css"), font_config=font_config),
    ]

    buf = BytesIO()
    HTML(string=full_html, base_url=str(runtime_paths.resource_root())).write_pdf(
        buf,
        stylesheets=stylesheets,
        font_config=font_config,
    )
    buf.seek(0)
    return buf.read()
