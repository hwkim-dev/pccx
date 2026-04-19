"""
pccx — RTL source link injector.

Reads a per-document ``rtl_source`` value (RST top-of-document field list or
MyST YAML frontmatter) and inserts an admonition immediately under the page
title containing a "View on GitHub" link (single source) or a bullet list
of links (multiple sources).

Usage
=====

RST::

    :rtl_source: hw/rtl/NPU_top.sv

    NPU Top-Level
    =============

Multi-file (comma- or newline-separated)::

    :rtl_source: hw/rtl/MAT_CORE/GEMM_systolic_top.sv,
                 hw/rtl/VEC_CORE/GEMV_top.sv

MyST::

    ---
    rtl_source:
      - hw/rtl/NPU_top.sv
    ---

Configuration (``conf_common.py``):

``rtl_source_repo_url``
    Base GitHub repository URL. Default:
    ``https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260``.

``rtl_source_ref``
    Branch / tag / SHA used for ``/blob/<ref>/`` permalinks. Default: ``main``.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def _find_top_field_container(doctree: nodes.document) -> Optional[nodes.Element]:
    """First docinfo / field_list node appearing before any section."""
    for child in doctree.children:
        if isinstance(child, nodes.section):
            return None
        if isinstance(child, (nodes.docinfo, nodes.field_list)):
            return child
    return None


def _extract_rst_rtl_source(doctree: nodes.document) -> Optional[str]:
    container = _find_top_field_container(doctree)
    if container is None:
        return None
    for field in container.traverse(nodes.field):
        name_node = field.children[0]
        body_node = field.children[1]
        if name_node.astext().strip() == "rtl_source":
            return body_node.astext().strip()
    return None


def _normalize(raw) -> List[str]:
    """Normalize a raw rtl_source value into a clean list of repo-relative paths."""
    if raw is None:
        return []
    if isinstance(raw, list):
        items: Iterable = (str(x) for x in raw)
    else:
        items = str(raw).replace("\n", ",").split(",")
    cleaned: List[str] = []
    for item in items:
        path = item.strip().lstrip("/")
        if path:
            cleaned.append(path)
    return cleaned


def _resolve_rtl_source(app: Sphinx, doctree: nodes.document,
                        docname: str) -> List[str]:
    # MyST YAML frontmatter lands in env.metadata during parse.
    meta = app.env.metadata.get(docname, {})
    if meta.get("rtl_source"):
        return _normalize(meta.get("rtl_source"))
    # RST field list: read directly from the doctree (collectors have not run yet).
    return _normalize(_extract_rst_rtl_source(doctree))


# ---------------------------------------------------------------------------
# Admonition construction
# ---------------------------------------------------------------------------

_STRINGS = {
    "en": {
        "title":    "RTL source on GitHub",
        "single":   "SystemVerilog source documented on this page:",
        "multiple": "SystemVerilog sources documented on this page:",
        "view":     "View on GitHub",
    },
    "ko": {
        "title":    "GitHub RTL 원본",
        "single":   "이 페이지가 참조하는 SystemVerilog 원본:",
        "multiple": "이 페이지가 참조하는 SystemVerilog 원본 파일:",
        "view":     "GitHub에서 보기",
    },
}


def _lang(app: Sphinx) -> str:
    return "ko" if (app.config.language or "en").startswith("ko") else "en"


def _build_url(base: str, ref: str, path: str) -> str:
    return f"{base.rstrip('/')}/blob/{ref}/{path}"


def _link_node(url: str, text: str) -> nodes.reference:
    link = nodes.reference(
        "", "",
        refuri=url,
        classes=["pccx-rtl-source__link"],
    )
    link["target"] = "_blank"
    link += nodes.Text(text)
    return link


def _build_admonition(app: Sphinx, sources: List[str]) -> nodes.Element:
    strings = _STRINGS[_lang(app)]
    base = app.config.rtl_source_repo_url
    ref = app.config.rtl_source_ref

    admon = nodes.admonition(classes=["pccx-rtl-source", "note"])
    admon += nodes.title(text=strings["title"])

    if len(sources) == 1:
        path = sources[0]
        url = _build_url(base, ref, path)

        intro = nodes.paragraph()
        intro += nodes.Text(strings["single"] + " ")
        intro += nodes.literal(text=path)
        admon += intro

        cta = nodes.paragraph(classes=["pccx-rtl-source__cta"])
        cta += _link_node(url, f"{strings['view']} \u2192")
        admon += cta
        return admon

    intro = nodes.paragraph()
    intro += nodes.Text(strings["multiple"])
    admon += intro

    bullet = nodes.bullet_list(classes=["pccx-rtl-source__list"])
    for path in sources:
        url = _build_url(base, ref, path)
        item = nodes.list_item()
        para = nodes.paragraph()
        para += nodes.literal(text=path)
        para += nodes.Text(" \u2014 ")
        para += _link_node(url, strings["view"])
        item += para
        bullet += item
    admon += bullet
    return admon


# ---------------------------------------------------------------------------
# Event hook
# ---------------------------------------------------------------------------

def _insert_admonition(doctree: nodes.document, admon: nodes.Element) -> None:
    """Insert admonition immediately after the first section's title."""
    for section in doctree.traverse(nodes.section):
        section.insert(1, admon)
        return
    doctree.insert(0, admon)


def on_doctree_read(app: Sphinx, doctree: nodes.document) -> None:
    docname = app.env.docname
    sources = _resolve_rtl_source(app, doctree, docname)
    if not sources:
        return
    if not app.config.rtl_source_repo_url:
        logger.warning(
            "[rtl_source] %r declares rtl_source but rtl_source_repo_url is "
            "unset; skipping.",
            docname,
        )
        return
    _insert_admonition(doctree, _build_admonition(app, sources))


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup(app: Sphinx) -> dict:
    app.add_config_value(
        "rtl_source_repo_url",
        "https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260",
        "env",
    )
    app.add_config_value("rtl_source_ref", "main", "env")
    app.connect("doctree-read", on_doctree_read)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
