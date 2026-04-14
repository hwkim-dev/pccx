# Configuration file for the Sphinx documentation builder (Korean).
import os
import sys

# -- Project information -----------------------------------------------------

project = 'uCA'
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

html_theme = 'furo'
html_title = 'uCA 문서'
language = 'ko'

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

html_static_path = ['../_static']
html_js_files = ['language-switcher.js']
html_css_files = ['language-switcher.css']
