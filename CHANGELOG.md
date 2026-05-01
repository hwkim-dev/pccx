# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## v0.1.0-alpha

First public alpha snapshot of the canonical pccx architecture, ISA,
and documentation site under the `pccxai` organization. Mirrors the
release draft at
[`docs/releases/v0.1.0-alpha.md`](docs/releases/v0.1.0-alpha.md).

### Highlights

- First snapshot of the canonical pccx architecture, ISA, and
  documentation site under the `pccxai` organization.
- Bilingual (EN + KO) Sphinx site with `numfig`, MyST and MyST-NB,
  multiversion publishing, and Furo dark/light theme; live at
  `https://pccxai.github.io/pccx/`.
- ISA package (`isa_pkg.sv`) cross-referenced from the docs through
  `literalinclude` against the `codes/v002/` clone produced at build
  time from the sibling RTL repository.
- ISA preprint PDF build (`isa-pdf.yml`, `xelatex`) producing the
  tracked `_static/downloads/pccx-isa-v002.pdf`.
- Repo-validation CI (`repo-validate`) covering URL hygiene,
  brand-name guard, Pages build sanity, and required-checks
  enforcement on `main`.
- Three-stage GitHub ruleset on `main` (force-push and branch-deletion
  block, PR-required, required status checks). Direct push to `main`
  is blocked.
- Citation metadata in tree: `CITATION.cff`, `CHANGELOG.md`,
  `RELEASING.md`.

### Known limitations

- W4A8 throughput numbers in the docs are framed as planning targets,
  not measured silicon results.
- v002 RTL is referenced from the `pccxai/pccx-FPGA-NPU-LLM-kv260`
  sibling repo at build time; this repo does not contain a bitstream
  or place-and-route closure.
- The KV cache memory model section is documentation-level; the
  on-chip layout is described, not benchmarked.
- v003 architecture is roadmap only; no scaffolding has landed.
- Localization beyond EN and KO is tracked under
  `M2 — v0.3 Community Localization` and is not part of this snapshot.

### Validation

- `make strict` builds clean (zero warnings) on EN and KO sources.
- `make linkcheck` clean on the weekly cron.
- `repo-validate` required check green on `main`.
- ISA PDF build green on `main`.
- Sphinx Pages deploy green; `https://pccxai.github.io/pccx/` returns
  HTTP 200.
- No standalone-vendor brand-token leaks in tracked sources
  (word-boundary scan).

[Unreleased]: https://github.com/pccxai/pccx/compare/HEAD...HEAD
