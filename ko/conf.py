# Configuration file for the Sphinx documentation builder (Korean).
import os
import sys

# -- Project information -----------------------------------------------------

project = 'pccx'
copyright = '2026, hwkim'
author = 'hwkim'
release = 'v001'

# -- General configuration ---------------------------------------------------

extensions = [
    'myst_parser',
]

templates_path = ['../_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'node_modules']

# -- Options for HTML output -------------------------------------------------

html_theme = 'pydata_sphinx_theme'
html_title = 'pccx 문서'
language = 'ko'

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
    "search_bar_text": "pccx 문서 검색...",
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/hwkim-dev/pccx",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
    ],
    "pygments_light_style": "friendly",
    "pygments_dark_style": "monokai",
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version"],
}

html_static_path = ['../_static']
html_js_files = ['language-switcher.js']
html_css_files = ['language-switcher.css']
