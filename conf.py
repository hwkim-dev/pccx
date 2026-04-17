# Configuration file for the Sphinx documentation builder.
import os
import sys

# -- Project information -----------------------------------------------------

project = 'pccx'
copyright = '2026, hwkim'
author = 'hwkim'
release = 'v001'
language = 'en'

# -- General configuration ---------------------------------------------------

extensions = [
    'myst_parser',
    'sphinx.ext.graphviz',
    'sphinxcontrib.mermaid',
]

myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence"]

graphviz_output_format = 'svg'
mermaid_output_format = 'raw'
mermaid_version = '10.9.0'
mermaid_init_config = {
    "startOnLoad": False,
    "securityLevel": "loose",
    "flowchart": {
        "htmlLabels": True,
        "curve": "basis",
        "useMaxWidth": False,
        "padding": 12,
    },
    "sequence": {
        "useMaxWidth": False,
        "mirrorActors": False,
    },
}

templates_path = ['_templates']
exclude_patterns = [
    '_build', 'Thumbs.db', '.DS_Store', 'node_modules', 'ko',
    '.venv', '.git', 'CLAUDE.md', 'README.md',
]

# -- Options for HTML output -------------------------------------------------

html_theme = 'pydata_sphinx_theme'
html_title = 'pccx Documentation'

html_theme_options = {
    "logo": {
        "text": "pccx",
        "alt_text": "pccx - Parallel Compute Core eXecutor",
    },
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "secondary_sidebar_items": ["page-toc"],
    "show_prev_next": True,
    "navigation_depth": 4,
    "show_toc_level": 2,
    "search_bar_text": "Search pccx docs...",
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/hwkim-dev/pccx",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
        {
            "name": "Personal Site",
            "url": "https://hwkim-dev.github.io/hwkim-dev/",
            "icon": "fa-solid fa-user",
            "type": "fontawesome",
        },
    ],
    "pygments_light_style": "friendly",
    "pygments_dark_style": "monokai",
    "footer_start": ["copyright", "personal-link"],
    "footer_end": ["sphinx-version"],
}

html_static_path = ['_static']
html_js_files = [
    'language-switcher.js',
    'image-lightbox.js',
]
html_css_files = [
    'language-switcher.css',
    'mermaid-theme.css',
    'image-lightbox.css',
]
