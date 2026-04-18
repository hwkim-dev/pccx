# Toolchain Demos

Reference pages exercising every diagram / plot pipeline wired into the
pccx Sphinx build. They exist so any regression in the toolchain surfaces
as a visible break on a dedicated page rather than inside a real
architecture chapter.

```{toctree}
:maxdepth: 1

mermaid_blockdiagram
wavedrom_axi_read
svg_themed_demo
plot_bandwidth
../../auto_plots/index
```

**Coverage matrix.**

| Demo                                | Pipeline under test           | Theme-aware? |
| ----------------------------------- | ----------------------------- | :---:       |
| [](mermaid_blockdiagram)            | `sphinxcontrib-mermaid`       | ✓ (neutral) |
| [](wavedrom_axi_read)               | `sphinxcontrib-wavedrom`      | — (raster)  |
| [](svg_themed_demo)                 | Inline SVG + Furo CSS vars    | ✓           |
| [](plot_bandwidth)                  | `scienceplots` + `sphinx-gallery` | ✓ (palette) |

See `CLAUDE.md` §5 (Diagram Authoring Rules) and §6 (Plotting Conventions)
for the authoring conventions these pages are meant to demonstrate.
