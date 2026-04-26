"""
pccx — shared Sphinx configuration.

This module holds every Sphinx knob that must stay identical between the
English (root ``conf.py``) and Korean (``ko/conf.py``) builds. Each concrete
``conf.py`` imports from here and overrides only the language-specific values
(``language``, ``html_theme_options.source_directory``, sphinx-gallery paths,
bibtex path, sitemap filename).

See ``CLAUDE.md`` §2 (Repository Layout) and §3 (Toolchain) for the
rationale behind the extension set.
"""

from __future__ import annotations

import os
import sys
from datetime import date

# Make local extensions under ``_ext/`` importable regardless of which conf.py
# (EN root or KO) triggered the build.
_CONF_COMMON_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CONF_COMMON_DIR)


# =============================================================================
# Project information
# =============================================================================

project = "pccx"
author = "hwkim"
copyright = f"{date.today().year}, {author}"
release = "v002"
version = "v002"


# =============================================================================
# General
# =============================================================================

extensions = [
    # -- Built-in
    "sphinx.ext.mathjax",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.todo",
    # -- MyST
    # NOTE: myst_nb transitively sets up myst_parser. Listing `myst_parser`
    #       separately triggers `setup_sphinx` twice and the second call
    #       blows up with `ValueError: list.remove(x): x not in list` because
    #       it unconditionally removes a core Sphinx transform.
    "myst_nb",
    # -- UI / UX
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_togglebutton",
    "notfound.extension",
    "sphinxext.opengraph",
    "sphinx_sitemap",
    "sphinx_reredirects",
    # -- Diagrams
    "sphinxcontrib.mermaid",
    "sphinxcontrib.wavedrom",
    # -- Plotting
    "matplotlib.sphinxext.plot_directive",
    "sphinx_gallery.gen_gallery",
    # -- Referencing
    "sphinxcontrib.bibtex",
    # NOTE: sphinx_external_toc is intentionally NOT activated here.
    #       See CLAUDE.md §3.5 and §12 (Roadmap).
    # -- Local
    "_ext.rtl_source",
    "_ext.pccx_diagrams",
    "_ext.schema_org",
    "_ext.archive_banner",
]

# Source suffixes are registered by extensions:
#   - ``.rst`` — Sphinx built-in
#   - ``.md``  — registered by myst-nb (which overrides the bare name
#                "markdown" that myst-parser would otherwise claim)
#   - ``.ipynb`` — registered by myst-nb
# We deliberately do NOT set ``source_suffix`` here because the conf.py
# mapping is applied after extension setup and would re-point ``.md`` at
# a parser name ("markdown") that myst-nb does not register.

# Exclusions apply to both builds. Language-specific roots (``ko`` from the
# English build) are excluded in the concrete conf.py.
exclude_patterns = [
    "_build",
    ".venv",
    ".git",
    "Thumbs.db",
    ".DS_Store",
    "node_modules",
    "CLAUDE.md",
    "AGENTS.md",           # per-clone agent pointer (gitignored)
    "GEMINI.md",           # per-clone agent pointer (gitignored)
    "README.md",
    "pccx-*-task.md",      # agent hand-off notes, not user-facing docs
    "requirements*.txt",
    "Makefile",
    # planning / audit markdown at the repo root — not part of the docs site
    "USER_ACTIONS.md",
    "pccx_master_roadmap_final.md",
    "pccx_v002_extended_20toks_plan.md",
    "tinynpu_v003_gemma4_e4b_plan*.md",  # the (1) variant uses a paren
    "tools/**/*.md",       # phase0 audit / vivado plan etc.
    # external RTL repo artifacts — pccx-FPGA cloned at build time
    "codes/v002/README.md",
    "codes/v002/docs/**",
    "codes/v002/**/README.md",   # e.g. codes/v002/hw/vivado/README.md
    "codes/v002/**/*.md",        # any other markdown shipped by the RTL repo
    # sphinx-gallery writes ``sg_execution_times.rst`` at the srcdir root AND
    # inside each gallery_dirs. Neither is ever put in a toctree, so Sphinx
    # emits "undefined label" / "document isn't included in any toctree"
    # warnings. Exclude both; the per-plot gallery pages are still built via
    # ``auto_plots/index``.
    "sg_execution_times.rst",
    "**/sg_execution_times.rst",
    # sphinx-gallery also drops per-plot aux files next to each generated
    # .rst (.py source, .ipynb, .py.md5, .codeobj.json, .zip). Sphinx sees
    # them as candidate documents and emits "multiple files found" warnings
    # because they share a docname with the .rst. Exclude the aux formats
    # at both the top level and nested under subsection directories.
    "auto_plots/*.py",
    "auto_plots/*.ipynb",
    "auto_plots/*.md5",
    "auto_plots/*.codeobj.json",
    "auto_plots/*.zip",
    "auto_plots/**/*.py",
    "auto_plots/**/*.ipynb",
    "auto_plots/**/*.md5",
    "auto_plots/**/*.codeobj.json",
    "auto_plots/**/*.zip",
]


# =============================================================================
# MyST
# =============================================================================

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "amsmath",
    "html_image",
    "attrs_inline",
    "attrs_block",
    "linkify",
    "substitution",
    "tasklist",
    "fieldlist",
    "smartquotes",
    "replacements",
    "strikethrough",
]
myst_heading_anchors = 3
myst_url_schemes = ("http", "https", "mailto", "ftp")
myst_linkify_fuzzy_links = False

# myst-nb: render notebooks but don't execute by default (deterministic CI).
nb_execution_mode = "off"
nb_merge_streams = True


# =============================================================================
# Figures / labels / TODOs
# =============================================================================

numfig = True
numfig_format = {
    "figure":     "Figure %s",
    "table":      "Table %s",
    "code-block": "Listing %s",
    "section":    "Section %s",
}

# Prefix labels with document name so identical section titles across the many
# index.rst files don't collide.
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3

# Leave nitpicky off by default; enable locally via `-n` when tightening refs.
nitpicky = False

# ``autosectionlabel`` auto-generates an anchor for every section heading in
# every document. When two sections in the same file happen to share a title
# (e.g. a "Summary" block repeated per subsystem) it warns and wins on every
# strict build. Silence only the autosectionlabel channel — we still want all
# other ref warnings surfaced.
suppress_warnings = [
    "autosectionlabel.*",
]

# Show TODOs only when explicitly requested (kept out of production output).
todo_include_todos = os.environ.get("PCCX_SHOW_TODOS", "0") == "1"


# =============================================================================
# Theme (Furo)
# =============================================================================

html_theme = "furo"
html_title = "pccx"
html_short_title = "pccx docs"

# Footer icon glyphs — themed via ``currentColor`` so dark/light inherit.
_ICON_GITHUB = (
    '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
    'viewBox="0 0 16 16" width="1em" height="1em" aria-hidden="true">'
    '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 '
    '5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-'
    '2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 '
    '1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-'
    '3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 '
    '2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 '
    '2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
    '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38'
    'A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
)
_ICON_CHIP = (
    '<svg fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true">'
    '<rect x="6" y="6" width="12" height="12" rx="1.2"/>'
    '<rect x="10" y="10" width="4" height="4" fill="currentColor" stroke="none"/>'
    '<path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>'
    '</svg>'
)
_ICON_PERSON = (
    '<svg fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true">'
    '<circle cx="12" cy="8" r="3.5"/>'
    '<path d="M4.5 20.5c1-3.5 4-5.5 7.5-5.5s6.5 2 7.5 5.5"/>'
    '</svg>'
)
_ICON_BEAKER = (
    '<svg fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true">'
    '<path d="M9 3h6"/>'
    '<path d="M10 3v6.2L4.6 19a1 1 0 0 0 .86 1.5h13.08a1 1 0 0 0 .86-1.5L14 9.2V3"/>'
    '<path d="M6.8 14h10.4"/>'
    '</svg>'
)


def build_footer_icons(lang_prefix: str = "en") -> list:
    """Assemble the labeled footer icon row for pccx.

    Order (left → right): RTL → Lab → Docs → Blog.

    ``lang_prefix`` (``'en'`` / ``'ko'``) only alters the pccx-lab link so a
    KO-page click lands on the KO sub-site; the other destinations are
    language-agnostic external repos / pages.
    """
    lab_url = f"https://hwkim-dev.github.io/pccx/{lang_prefix}/lab/"
    return [
        {
            "name":  "RTL implementation — github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260",
            "url":   "https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260",
            "class": "pccx-footer-icon",
            "html": (
                _ICON_CHIP
                + '<span class="pccx-footer-icon__label">RTL</span>'
            ),
        },
        {
            "name":  "pccx-lab — simulator & AI profiler",
            "url":   lab_url,
            "class": "pccx-footer-icon",
            "html": (
                _ICON_BEAKER
                + '<span class="pccx-footer-icon__label">Lab</span>'
            ),
        },
        {
            "name":  "Docs repository — github.com/hwkim-dev/pccx",
            "url":   "https://github.com/hwkim-dev/pccx",
            "class": "pccx-footer-icon",
            "html": (
                _ICON_GITHUB
                + '<span class="pccx-footer-icon__label">Docs</span>'
            ),
        },
        {
            "name":  "Author portfolio — hwkim-dev.github.io/hwkim-dev",
            "url":   "https://hwkim-dev.github.io/hwkim-dev/",
            "class": "pccx-footer-icon",
            "html": (
                _ICON_PERSON
                + '<span class="pccx-footer-icon__label">Blog</span>'
            ),
        },
    ]


html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/hwkim-dev/pccx/",
    "source_branch": "main",
    # source_directory is set per-language in the concrete conf.py.
    "light_css_variables": {
        "color-brand-primary":           "#0b5fff",
        "color-brand-content":           "#0b5fff",
        "color-announcement-background": "#fff5cf",
        "color-announcement-text":       "#6b5900",
        # Custom tokens consumed by custom.css / SVG diagrams.
        "pccx-accent":                   "#ff7a00",
        "pccx-muted-border":             "#dbe1ea",
    },
    "dark_css_variables": {
        "color-brand-primary":           "#7aa8ff",
        "color-brand-content":           "#7aa8ff",
        "color-announcement-background": "#332a00",
        "color-announcement-text":       "#f9e58b",
        "pccx-accent":                   "#ffb470",
        "pccx-muted-border":             "#3a4049",
    },
    "footer_icons": build_footer_icons("en"),
}

templates_path = ["_templates"]
html_static_path = ["_static"]     # KO conf overrides to ["../_static"]

# ``_extra`` lives next to _static but is copied to the site root untouched
# so llms.txt / robots.txt are served as /pccx/llms.txt, /pccx/robots.txt.
# (KO conf overrides the path prefix to ``../_extra``.)
html_extra_path = ["_extra"]

html_css_files = [
    "custom.css",
    "image-lightbox.css",
    "language-switcher.css",
]
html_js_files = [
    "image-lightbox.js",
    "language-switcher.js",
]

html_show_sphinx = False
html_show_sourcelink = False
html_permalinks_icon = "¶"
html_last_updated_fmt = "%Y-%m-%d"


# =============================================================================
# Diagrams
# =============================================================================

graphviz_output_format = "svg"

mermaid_version = "10.9.0"
mermaid_output_format = "raw"
mermaid_init_js = (
    "mermaid.initialize({"
    "startOnLoad: true,"
    "theme: 'neutral',"
    "securityLevel: 'loose',"
    "flowchart: {htmlLabels: true, curve: 'basis', useMaxWidth: true, padding: 12},"
    "sequence:  {useMaxWidth: true, mirrorActors: false}"
    "});"
)

# WaveDrom: use the CDN-hosted JS renderer by default (client-side). If SSR
# becomes mandatory, switch to wavedrompy via `render_using_wavedrompy = True`.
offline_skin_js_path = None
offline_wavedrom_js_path = None


# =============================================================================
# Plotting (matplotlib + sphinx-gallery)
# =============================================================================

plot_formats = [("svg", 100), ("png", 200)]
plot_html_show_source_link = True
plot_html_show_formats = False

# Shared defaults; concrete conf.py overrides ``examples_dirs`` / ``gallery_dirs``.
sphinx_gallery_conf = {
    "examples_dirs":            "plots",       # relative to srcdir
    "gallery_dirs":             "auto_plots",
    "filename_pattern":         r"/plot_",
    "plot_gallery":             "True",
    "download_all_examples":    False,
    "remove_config_comments":   True,
    "within_subsection_order":  "FileNameSortKey",
    "thumbnail_size":           (400, 280),
    "matplotlib_animations":    False,
    "default_thumb_file":       None,
}


# =============================================================================
# Referencing
# =============================================================================

bibtex_bibfiles = ["refs.bib"]            # KO conf overrides to ["../refs.bib"]
bibtex_default_style = "unsrt"
bibtex_reference_style = "author_year"

intersphinx_mapping = {
    "python":     ("https://docs.python.org/3/",            None),
    "numpy":      ("https://numpy.org/doc/stable/",         None),
    "matplotlib": ("https://matplotlib.org/stable/",        None),
    "sphinx":     ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_timeout = 10


# =============================================================================
# SEO / social
# =============================================================================

html_baseurl = "https://hwkim-dev.github.io/pccx/"
sitemap_url_scheme = "{link}"
# sitemap_filename is overridden per-language in concrete conf.py.

ogp_site_url = "https://hwkim-dev.github.io/pccx/"
ogp_site_name = "pccx — Parallel Compute Core eXecutor"
ogp_image = None                         # add once a social card exists
ogp_type = "website"
ogp_enable_meta_description = True


# =============================================================================
# 404
# =============================================================================

notfound_context = {
    "title": "Page not found",
    "body": (
        "<h1>404 — Not Found</h1>"
        "<p>The page you were looking for does not exist in this version of pccx.</p>"
        '<p><a href="/pccx/">Back to the project root</a></p>'
    ),
}
notfound_urls_prefix = "/pccx/"


# =============================================================================
# Redirects (populate as URL paths change)
# =============================================================================

redirects: dict[str, str] = {
    # "legacy/path.html": "docs/v002/new_path.html",
}


# =============================================================================
# sphinx-multiversion
# =============================================================================

smv_tag_whitelist = r"^v\d+\.\d+.*$"
smv_branch_whitelist = r"^(main|v\d+-dev)$"
smv_remote_whitelist = None
smv_released_pattern = r"^tags/v\d+\.\d+.*$"
smv_outputdir_format = "{ref.name}"
smv_prefer_remote_refs = False


# =============================================================================
# linkcheck
# =============================================================================

linkcheck_ignore = [
    r"^http://localhost.*",
    r"^https?://.*\.local.*",
    # GitHub anchor links can flap; relax only when truly flaky.
]
linkcheck_timeout = 15
linkcheck_retries = 2
linkcheck_workers = 4
linkcheck_anchors = True
linkcheck_allowed_redirects = {
    r"https://github\.com/.*":  r"https://github\.com/.*",
}
