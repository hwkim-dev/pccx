# Mermaid — NPU block diagram

Mermaid renders on the client, so the diagram below picks up Furo's
dark/light theme automatically via the `neutral` Mermaid palette configured
in `conf_common.py`.

```{mermaid}
flowchart LR
    HOST[Host CPU] -- AXI-Lite --> CTRL[NPU Controller]
    CTRL --> GEMM[GEMM Core<br/>32×32 · 2-MAC DSP]
    CTRL --> GEMV[GEMV Core<br/>4 × 32-MAC]
    CTRL --> SFU[SFU / CVO]
    CTRL --> DMA[DMA]
    GEMM <-- HP0/HP1 --> DDR[(DDR4)]
    GEMV <-- HP2/HP3 --> DDR
    DMA  <-- ACP    --> DDR
    GEMV -. direct FIFO .-> SFU
    GEMM --> L2[(Shared L2<br/>URAM 1.75 MB)]
    GEMV --> L2
    SFU  --> L2
```

The flowchart should compose without a round trip to a rendering service —
if the box renders blank, check the browser console for a Mermaid parse
error (most often caused by reserved keywords inside labels).

## When to reach for Mermaid

- High-level flow, state-machine, or sequence diagrams that benefit from
  being diffable text.
- **Quick sketches only**: fidelity is secondary to authoring speed.

**Warning for NPU Architecture:**
For performance-critical datapath diagrams, PE arrays, or memory layouts,
**DO NOT use Mermaid**. Use hand-crafted SVG following the
`CLAUDE.md §5.2` guidelines to ensure exact proportions and technical
accuracy.
