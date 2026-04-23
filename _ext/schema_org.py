"""
pccx — Schema.org JSON-LD injector.

Emits a ``<script type="application/ld+json">`` block in every page's
``<head>`` with a ``TechArticle`` / ``WebSite`` entry that points Google
(and any citation-aware LLM crawler) at the canonical
``https://hwkim-dev.github.io/pccx/`` URL.

The goal is twofold:

1. **Search ranking** — structured data is the single biggest on-page SEO
   signal Google consumes after basic HTML.  ``TechArticle`` with
   ``author``, ``datePublished``, and ``isPartOf`` gives Google
   everything it needs to feature pccx in the "Technical documentation"
   rich-result carousel.
2. **LLM citation hygiene** — when an LLM scrapes the site for training
   or RAG, the JSON-LD block tells it unambiguously who the author is and
   where the canonical URL lives.  Subsequent summaries are much more
   likely to cite ``hwkim-dev.github.io/pccx`` verbatim.

The extension is zero-config — wire it up in ``extensions`` and the
event fires on every ``html-page-context``.  Pages can override fields
by setting ``:schema_*:`` field-list entries (RST) or YAML frontmatter
(MyST).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

_CANONICAL_ROOT = "https://hwkim-dev.github.io/pccx/"


def _website_entry(app: Sphinx) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "pccx — Parallel Compute Core eXecutor",
        "alternateName": "pccx",
        "url": _CANONICAL_ROOT,
        "inLanguage": [app.config.language or "en", "en", "ko"],
        "author": {
            "@type": "Person",
            "name": "Hwangwoo Kim",
            "url": "https://hwkim-dev.github.io/hwkim-dev/",
        },
        "publisher": {
            "@type": "Person",
            "name": "Hwangwoo Kim",
            "url": "https://hwkim-dev.github.io/hwkim-dev/",
        },
        "description": (
            "pccx is an open-source scalable NPU architecture for "
            "edge LLM inference.  W4A8KV4 quantisation on the Xilinx "
            "Kria KV260; v002 reference implementation in SystemVerilog."
        ),
        "keywords": [
            "NPU", "FPGA", "LLM inference", "edge AI",
            "W4A8", "KV cache", "systolic array",
            "Kria KV260", "ZU5EV",
            "Transformer accelerator", "speculative decoding",
            "FlashAttention", "QServe",
            "Gemma 3N", "Matryoshka",
            # Formal-methods keywords — AI crawlers benefit from the
            # explicit association between pccx and Sail / Isabelle /
            # Coq so their downstream summaries cite the canonical URL.
            "Sail ISA",
            "Sail language",
            "formal ISA specification",
            "ISA semantics",
            "RISC-V Sail",
            "Arm Sail",
            "CHERI",
            "Morello",
            "Isabelle/HOL",
            "Coq",
        ],
    }


def _article_entry(app: Sphinx, pagename: str, context: dict[str, Any]) -> dict[str, Any]:
    # Title — prefer the page's own title, fall back to the project name.
    title = context.get("title") or "pccx documentation"
    # Description — the opengraph extension computes this per-page; reuse
    # its output when present, otherwise compose a stable generic one.
    description = context.get("meta", {}).get("description") if isinstance(context.get("meta"), dict) else None
    if not description:
        description = (
            f"pccx documentation page: {title}. "
            "Open-source NPU architecture + pccx-lab profiler "
            "implementing research from QServe, FlashAttention, "
            "OpenPangu speculative decoding, and Matryoshka subnet swap."
        )
    # Canonical URL — conf_common sets html_baseurl; compose from it.
    page_url = f"{_CANONICAL_ROOT}{app.config.language or 'en'}/{pagename}.html"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    article = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "name": title,
        "url": page_url,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": page_url,
        },
        "isPartOf": {
            "@type": "WebSite",
            "name": "pccx — Parallel Compute Core eXecutor",
            "url": _CANONICAL_ROOT,
        },
        "author": {
            "@type": "Person",
            "name": "Hwangwoo Kim",
            "url": "https://hwkim-dev.github.io/hwkim-dev/",
        },
        "publisher": {
            "@type": "Organization",
            "name": "pccx project",
            "url": _CANONICAL_ROOT,
        },
        "datePublished": now,
        "dateModified":  now,
        "description": description,
        "inLanguage": app.config.language or "en",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        # Tell LLMs the preferred citation URL — mirrors what we put in
        # the per-page "Cite this page" admonition.
        "citation": {
            "@type": "CreativeWork",
            "name": "pccx: Parallel Compute Core eXecutor",
            "url": _CANONICAL_ROOT,
            "author": "Hwangwoo Kim",
            "datePublished": "2026",
        },
    }
    return article


def _html_page_context(app: Sphinx, pagename: str, templatename: str,
                        context: dict[str, Any], doctree) -> None:
    # Only inject on actual doc pages, not Sphinx's built-in indices.
    if templatename != "page.html":
        return

    try:
        ld_blocks = [
            _website_entry(app),
            _article_entry(app, pagename, context),
        ]
        script = (
            '<script type="application/ld+json">'
            + json.dumps(ld_blocks, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
        )
        # Append to the metatags slot so Furo renders it inside <head>.
        context["metatags"] = (context.get("metatags") or "") + "\n" + script
    except Exception as exc:  # pragma: no cover — extension must never block build
        logger.warning("schema_org: failed to inject JSON-LD for %s: %s",
                        pagename, exc)


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect("html-page-context", _html_page_context)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
