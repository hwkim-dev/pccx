# SVG — themed 4×4 PE array

The figure below is hand-authored SVG that expresses colors via
`currentColor` and Furo CSS custom properties, so it inverts correctly when
the reader toggles dark mode. No raster fallback is shipped.

```{figure} /_static/diagrams/sample_pe_array.svg
:name: fig-sample-pe-array
:alt: A 4 by 4 grid of PEs with activation flowing left-to-right and partial sums flowing top-to-bottom.
:width: 80%

{numref}`fig-sample-pe-array`: weight-stationary dataflow in a toy 4×4 PE
array. Activations stream along rows (brand-primary arrows), weights stay
resident inside each PE (dashed accent arrows in the legend), and partial
sums accumulate down each column.
```

## Why currentColor + CSS variables

- **One asset, both themes.** The stroke/fill tokens resolve against
  `--color-foreground-primary`, `--color-brand-primary`, and the custom
  `--pccx-accent` declared in `conf_common.py`.
- **Diff-friendly.** The file is text, so every Pull Request that changes
  it reviews as a real diff — not a binary delta.
- **Zero network dependency.** The SVG is served with the site and parses
  locally; there is no client-side rendering library to ship or version.

See `CLAUDE.md` §5.2 for the absolute rules new SVG assets must follow
(no hardcoded colors, `viewBox` only, `<title>` + `<desc>` for a11y).
