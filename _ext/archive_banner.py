"""
pccx — archive → latest redirect banner.

Replaces the previous "language-switcher" top announcement (which was
redundant with the sidebar EN · 한국어 switch) with a **context-aware
redirect** that only fires on archived pages.

Concretely: when the current document lives under ``docs/archive/`` we
override Furo's ``announcement`` setting with a banner pointing the
reader at the currently-active version (``docs/v002/``).  On every
other page the banner stays empty, keeping the chrome clean.

The extension is intentionally a thin ``html-page-context`` hook so
Furo's existing announcement slot renders the HTML with no template
override — same mechanism, different content per page.
"""

from __future__ import annotations

from typing import Any

from sphinx.application import Sphinx

# Active version the archive should redirect to.  Update this once per
# major cutover (see the pccx CLAUDE.md §8.4 cutover ceremony).
_ACTIVE_VERSION = "v002"

# Short labels — the KO copy is the Korean translation of the EN copy.
_BANNERS: dict[str, dict[str, str]] = {
    "en": {
        "prefix": "📼 Archived page · ",
        "link":   f"jump to the latest ({_ACTIVE_VERSION}) →",
    },
    "ko": {
        "prefix": "📼 아카이브 페이지 · ",
        "link":   f"최신 ({_ACTIVE_VERSION}) 문서로 이동 →",
    },
}


def _html_page_context(app: Sphinx, pagename: str, templatename: str,
                        context: dict[str, Any], doctree) -> None:
    # Only docs/archive/** qualifies — every other page gets no banner.
    if not pagename.startswith("docs/archive/"):
        return

    lang = (app.config.language or "en").lower()
    copy = _BANNERS.get(lang, _BANNERS["en"])

    # URL of the active-version index page.  Preserve the Sphinx
    # relative-link semantics so sphinx-multiversion / language
    # subdirectories resolve correctly.
    target = f'{context.get("pathto")("docs/" + _ACTIVE_VERSION + "/index")}'
    banner_html = (
        f'{copy["prefix"]}<a class="pccx-archive-redirect" '
        f'href="{target}">{copy["link"]}</a>'
    )

    # Furo reads this from theme_options["announcement"] at build time,
    # but it also honours the context-level override when set.
    context["theme_announcement"] = banner_html


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect("html-page-context", _html_page_context)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
