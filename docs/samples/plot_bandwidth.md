# scienceplots — bandwidth vs batch size

`sphinx-gallery` scans the repo-root `plots/` directory for any `plot_*.py`
script and generates a standalone page per script, using whatever
matplotlib style the script opts into. The pccx convention is IEEE via
[`scienceplots`](https://github.com/garrettj403/SciencePlots).

The generated gallery card for the demo script is listed in the
[auto-generated plot gallery](../../auto_plots/index.rst) and picked up by
the {doc}`samples index <index>` toctree.

## Authoring pattern

A plot source file is the single source of truth for both the PNG preview
(for social sharing) and the SVG embed (for the docs). The canonical
header is:

```python
"""
Title of the plot
=================

One-liner that becomes the gallery card subtitle.
"""
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

plt.style.use(["science", "ieee", "no-latex"])

# ... data preparation ...
fig, ax = plt.subplots(figsize=(3.4, 2.1))
# ... plotting ...
fig.tight_layout()
plt.show()
```

See `plots/plot_bandwidth.py` for a working example and `CLAUDE.md` §6 for
the full set of plotting conventions (including the determinism rule —
seed every RNG you touch).
