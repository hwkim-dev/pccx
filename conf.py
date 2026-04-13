# Configuration file for the Sphinx documentation builder.
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

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'node_modules']

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo' # Excellent dark/light mode theme
html_title = 'uCA Documentation'

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}
