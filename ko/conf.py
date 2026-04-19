"""
pccx — Korean Sphinx configuration.

Thin wrapper: pulls every shared knob from the repo-root :mod:`conf_common`
and only overrides language-specific values. See ``CLAUDE.md`` §2.
"""

from __future__ import annotations

import sys
from pathlib import Path

# conf_common.py lives at the repo root; ``ko/conf.py`` is one level down.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT))

from conf_common import *                          # noqa: F401,F403
from conf_common import (                          # noqa: F401
    exclude_patterns,
    html_theme_options,
    sphinx_gallery_conf,
    build_footer_icons,
)


# -- Language ----------------------------------------------------------------

language = "ko"


# -- Static & templates ------------------------------------------------------

# ``_static`` and ``_templates`` live at the repo root so both languages share
# them (single source of truth for CSS/JS/slot overrides).
html_static_path = ["../_static"]
templates_path = ["../_templates"]


# -- Exclusions --------------------------------------------------------------

# The Korean build's srcdir is ``ko/``. Exclude the English-specific roots that
# the shared ``exclude_patterns`` references (they'd resolve under ``ko/``
# otherwise and Sphinx would warn).
exclude_patterns = [
    *exclude_patterns,
    # The English tree sits outside srcdir; no exclusion needed for `docs/`.
    # But the codes/ exclusions from conf_common are relative to *this* srcdir,
    # so rewrite them with the correct depth.
    "../codes/v002/README.md",
    "../codes/v002/docs/**",
]


# -- Theme options -----------------------------------------------------------

html_theme_options = {
    **html_theme_options,
    "source_directory": "ko/docs/",
    "announcement": (
        '한국어 버전 · '
        '<a href="/pccx/en/">View in English →</a>'
    ),
    "footer_icons": build_footer_icons("ko"),
}


# -- sphinx-gallery ---------------------------------------------------------

# Share the single plots/ directory at the repo root so plot scripts don't
# need to be duplicated per language. Outputs land under ko/auto_plots/.
sphinx_gallery_conf = {
    **sphinx_gallery_conf,
    "examples_dirs": "../plots",       # <repo>/plots
    "gallery_dirs":  "auto_plots",     # <repo>/ko/auto_plots
}


# -- Referencing & SEO ------------------------------------------------------

bibtex_bibfiles = ["../refs.bib"]
sitemap_filename = "sitemap-ko.xml"


# -- Localized strings ------------------------------------------------------

html_title = "pccx 문서"
html_short_title = "pccx 문서"

numfig_format = {
    "figure":     "그림 %s",
    "table":      "표 %s",
    "code-block": "리스팅 %s",
    "section":    "섹션 %s",
}

notfound_context = {
    "title": "페이지를 찾을 수 없습니다",
    "body": (
        "<h1>404 — 페이지 없음</h1>"
        "<p>요청하신 페이지는 이 버전의 pccx 에 존재하지 않습니다.</p>"
        '<p><a href="/pccx/ko/">문서 루트로 돌아가기</a></p>'
    ),
}
