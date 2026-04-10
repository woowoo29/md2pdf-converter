import markdown


EXTENSIONS = [
    "tables",
    "fenced_code",
    "codehilite",
    "toc",
    "footnotes",
    "attr_list",
    "def_list",
    "pymdownx.tasklist",
    "pymdownx.superfences",
    "pymdownx.highlight",
]

EXTENSION_CONFIGS = {
    "codehilite": {"guess_lang": False},
    "pymdownx.highlight": {"use_pygments": True},
    "pymdownx.tasklist": {"custom_checkbox": True},
}


def render(md_content: str) -> str:
    md = markdown.Markdown(
        extensions=EXTENSIONS,
        extension_configs=EXTENSION_CONFIGS,
    )
    return md.convert(md_content)
