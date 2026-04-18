"""
pccx — English Sphinx configuration.

Thin wrapper: pulls every shared knob from :mod:`conf_common` and only
overrides language-specific values. See ``CLAUDE.md`` §2 (Repository
Layout) for the dual-source rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make conf_common importable regardless of where sphinx-build is invoked from.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from conf_common import *                          # noqa: F401,F403
from conf_common import (                          # noqa: F401  (explicit re-mutation)
    exclude_patterns,
    html_theme_options,
    sphinx_gallery_conf,
)


# -- Language ----------------------------------------------------------------

language = "en"


# -- Exclusions -------------------------------------------------------------

# The English build's srcdir is the repo root. Exclude the Korean source tree
# and anything inside it so Sphinx doesn't double-index it.
exclude_patterns = [
    *exclude_patterns,
    "ko",
    "ko/**",
]


# -- Theme options ----------------------------------------------------------

html_theme_options = {
    **html_theme_options,
    "source_directory": "docs/",
    "announcement": (
        'English version · '
        '<a href="/pccx-FPGA-NPU-LLM-kv260/ko/">한국어로 보기 →</a>'
    ),
}


# -- sphinx-gallery (paths relative to this conf) ---------------------------

sphinx_gallery_conf = {
    **sphinx_gallery_conf,
    "examples_dirs": "plots",          # <repo>/plots
    "gallery_dirs":  "auto_plots",     # <repo>/auto_plots
}


# -- Referencing & SEO ------------------------------------------------------

bibtex_bibfiles = ["refs.bib"]
sitemap_filename = "sitemap-en.xml"
