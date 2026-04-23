# pccx preprint

LaTeX source for an arXiv / Zenodo-submittable preprint describing the
pccx v002 architecture, the Sail formal spec, and the pccx-lab
profiler.  One file (`main.tex`), one bib (`refs.bib`), stock TeX Live.

## Build

```bash
latexmk -pdf main.tex
# → main.pdf
```

Requires TeX Live 2023+ with `lmodern`, `hyperref`, `natbib`,
`listings`, `booktabs`, `microtype`, `geometry`.

## Status

- ✅ Title page, abstract, section skeleton with content for
  §Architecture + §Sail Formal Specification.
- ⏳ §Introduction, §Lab, §Evidence, §Conclusion flagged **TODO** —
  filled as measurements land (see the
  [Evidence page](https://hwkim-dev.github.io/pccx/en/docs/Evidence/index.html)).

## Publishing

1. Fill the TODO sections once KV260 tok/s numbers are in hand.
2. Build `main.pdf`.
3. Zenodo release (pinned DOI); update `_ext/schema_org.py` citation
   block to point at the DOI.
4. arXiv submission — category `cs.AR` (Hardware Architecture),
   cross-list to `cs.LG`.

## Canonical URL

Preprint stays at
<https://hwkim-dev.github.io/pccx/en/> via a `:download:` link
on the landing page once published.  The bibtex key in
`_ext/schema_org.py` JSON-LD will resolve to the Zenodo DOI — AI
crawlers that ingest the site will attribute any summary of pccx
content back to the canonical paper and repo.
