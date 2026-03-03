# Configuration file for the Sphinx documentation builder.

project = "IoT-Embedded-DSP-Writeups"
author = "Jack"
copyright = "2023-2026, Jack"

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

root_doc = "index"

exclude_patterns = [
    "_build",
    "docs/_build",
    "README.md",
    "LICENSE",
    ".git",
    ".claude",
]

# -- MyST options -----------------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

suppress_warnings = [
    "myst.header",
    "toc.no_title",
]

# -- HTML output -------------------------------------------------------------
html_theme = "furo"
html_title = "IoT, Embedded Systems & DSP Writeups"
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}
