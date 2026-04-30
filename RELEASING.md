# Releasing pccx

`pccx` is the canonical architecture and documentation repository for
the FPGA-oriented LLM inference accelerator stack.  Releases are
**specification snapshots**, not compiled artefacts.

## Versioning

- Pre-1.0 (`0.x.y`): minor bumps may carry breaking spec changes.
- Tag format: `vX.Y.Z[-alpha|-beta|-rc]`.
- The documentation site (`hkimw.github.io/pccx`) tracks `main`;
  tagged releases are also published as immutable snapshots through
  `sphinx-multiversion` (see `conf_common.py` `smv_*` allowlists).
- The first tag is planned as `v0.1.0-alpha` — see `CHANGELOG.md`.

## What is in a release

- `docs/` and `ko/docs/` content frozen at the tagged commit.
- `main.tex` → `_static/downloads/pccx-isa-vNNN.pdf` ISA reference.
- `refs.bib` and citation metadata (`CITATION.cff`).
- A short release note summarising the architectural surface that the
  tag covers (e.g. v002 vs v003) and any breaking spec changes.

A release does **not** include built HTML output, RTL source, or
bitstreams.  Implementation artefacts live in
[`pccx-FPGA-NPU-LLM-kv260`](https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260)
and follow that repository's own cadence.

## Pre-flight checks

Before tagging:

1. `make strict` passes (`-W` treats Sphinx warnings as errors) for
   both EN and KO trees.
2. `make lint` is clean (sphinx-lint + codespell).
3. `make linkcheck` is clean — fix or document any external 4xx/5xx.
4. EN and KO trees are in parity (same section count, same `:name:`
   labels, same equation / figure numbering where applicable).
5. `CHANGELOG.md` `[Unreleased]` block is cut to `## [X.Y.Z] - YYYY-MM-DD`.
6. `CITATION.cff` is consistent with the tag's authors and metadata.
7. RTL cross-reference pages have a fresh `Last verified against:
   <SHA>` admonition where the cited RTL changed since the previous
   tag.

## Tagging

```bash
git tag -a vX.Y.Z -m "pccx vX.Y.Z — <one-line summary>"
git push origin vX.Y.Z
```

The deploy workflow rebuilds the docs site; `sphinx-multiversion`
adds the new tag to the version dropdown.

## Drafting on GitHub

```bash
gh release create vX.Y.Z --draft \
   --title "pccx vX.Y.Z — <one-line summary>" \
   --notes-file release_notes/vX.Y.Z.md
```

Use `--prerelease` for `-alpha` / `-beta` / `-rc` tags.  Open the
draft on GitHub, attach the ISA PDF and any errata, then publish.

## After-release

- Open a fresh `## [Unreleased]` block in `CHANGELOG.md`.
- Bump `CITATION.cff` if a `version:` field is being tracked.
- Mirror any docs changes that affect implementation contracts in the
  matching `pccx-FPGA-NPU-LLM-kv260` PR / "Last verified against"
  admonition update.
