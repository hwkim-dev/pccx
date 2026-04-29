# Phase 4 — Insane-Level Reports & Concept-to-RTL

**Status:** scaffold landed (`pccx-reports` trait + `MarkdownFormat`); implementation kicks off in Phase 4 proper.
**Scope:** roadmap Weeks 14-18; milestones M4.1 - M4.7 (+ M4.8-4.10 Sail finale).
**Target experience:** reports that **no other tool can approach** — single source of truth for the whole hardware-design lifecycle.

## 1. What "insane-level" means

Not "prettier markdown".  Every report section is:

1. **Generative** — built from a live data model (pccx-core trace +
   synth + verification result), NOT copy-pasted.
2. **Interactive** — waveforms, heatmaps, proof trees respond to user
   input (zoom, filter, replay counter-example).
3. **AI-annotated** — the LLM narrates glitches, hotspots, what-ifs
   at *just* enough length to matter.
4. **Comparable** — every report links its numbers to the benchmark
   database so a reviewer sees "17% faster than Llama-2 at same area"
   at a glance.
5. **Reproducible** — PDF / HTML / Jupyter bundle includes the input
   trace hash + pccx-lab commit SHA so anyone can regenerate.

## 2. Architecture

```
pccx-core (trace / synth / roofline / bottleneck)
    │
    ├──▶ pccx-verification (golden-diff / sail-refine / formal)
    │          │
    │          ▼
    └──▶ pccx-reports  [engine]
              │
              ├── MarkdownFormat  (ships in M1.2)
              ├── HtmlFormat      (M4.1)
              ├── PdfFormat       (M4.1)
              ├── JupyterFormat   (M4.1)
              └── WavedromFormat  (M4.2 — interactive waveforms)
```

All formats implement the same `ReportFormat` trait.  The engine
composes a `Report` document tree; each format walks the tree and
emits its target bytes.

### 2.1 Document tree

```rust
struct Report {
    sections: Vec<Section>,
    metadata: ReportMeta,   // trace hash, pccx-lab SHA, benchmarks seen
}

enum Section {
    Summary(AiNarration),                    // LLM-written exec summary
    Waveform(WaveformRef),                    // M4.2
    Heatmap { kind: HeatmapKind, data: … },   // M4.3
    FormalProof(ProofTreeRef),                // M4.4
    WhatIf(ScenarioRef),                      // M4.5
    ConceptToRtl(DesignSpecRef),              // M4.6
    BenchmarkCompare(BenchmarkRef),           // M4.7
    Raw(String),                              // escape hatch
}
```

## 3. Milestones

### M4.1 — Template engine (Week 14)

- Data-driven rendering: the `Report` tree is the only source of
  truth; formats are pure functions of it.
- HtmlFormat uses Askama (compile-time templates, no runtime
  interpreter).
- PdfFormat uses WeasyPrint (CSS -> PDF, Python dep) OR
  `pdf-writer` (Rust-native).  Pick after benchmarking.
- JupyterFormat emits a notebook whose cells embed the live trace
  fetcher so readers can re-run the analysis interactively.

### M4.2 — Interactive waveform viewer (Week 15)

- WaveDrom extended with AI annotations: hover a glitch, see Sonnet's
  one-sentence explanation ("likely caused by clock-crossing on
  CDC_A").
- Annotations stored in the trace itself (new `.pccx` payload field)
  so they're first-class, not ephemeral.

### M4.3 — Power / area / timing heatmaps (Week 15)

- Vivado / OpenROAD report ingestion via pccx-core::synth_report.
- D3.js heatmap in pccx-ide; hover a tile for LLM hotspot narration
  ("DSP48E2 cluster 3,7 is 92% utilised — consider dual-pumping").
- Export: SVG (static) + JSON (interactive source).

### M4.4 — Formal proof visualiser (Week 16)

- Coq / Lean 4 proof trees (from pccx-verification sail-refine gate)
  rendered as expandable trees.
- Counter-example replay: if a proof fails, the visualiser animates
  the failing input through the Sail model so the user sees *exactly*
  where the RTL and spec diverge.

### M4.5 — "What if?" scenario engine (Week 17)

- Take the current trace + synth report, ask "what if we raised fmax
  to 450 MHz?" or "what if we halved URAM?".
- pccx-evolve surrogate model predicts new area/power/delay in < 10 ms.
- Side-by-side diff report against the baseline.

### M4.6 — Concept-to-RTL flow (Week 17-18, flagship demo)

- User types natural-language spec ("I want a 16-lane INT8 GEMV that
  fits in a KV260").
- Agent team (research + doc drafting subagents) proposes an
  architecture.
- pccx-authoring emits a first-pass ISA + RTL skeleton.
- User reviews, tweaks, rebuilds.
- Total latency goal: spec in, buildable RTL out, < 30 minutes.

### M4.7 — Benchmark database (Week 18)

- Track Gemma-3N E4B, Llama-2 7B, BERT-base as comparison baselines.
- Nightly CI re-runs them on the current commit so the database stays
  honest.
- Report's "vs peers" section auto-pulls from this database.

### M4.8 - M4.10 — Sail finale (Week 18, bonus)

- M4.8: Sail execute semantics 2nd increment — concrete MAC / DMA /
  SFU effects.
- M4.9: Sail → `.pccx` trace emitter (replace `record_event` stub).
- M4.10: Sail ↔ RTL refinement diff plugged into pccx-verification
  as a first-class `VerificationGate`.

## 4. Quality bar

Reports must hold up next to:

- Synopsys DSO.ai's design insight dashboard
- Vivado Design Hub's post-implementation report
- NVIDIA Nsight Compute's kernel profile

Specifically: every number has a source link; every claim has an
explanation; every "insane" AI narration is < 80 words and anchored
to a concrete data point.

## 5. Token budget

- Summary narrations (Haiku): 500 tokens/report.
- What-if scenarios (Sonnet, batched): 1.5 K tokens per 10 scenarios.
- Concept-to-RTL (Opus): 4-8 K tokens per session; amortised across
  the generated artefact.
- Report re-renders are 0-token (format is pure function of tree).
- Cache AI narrations by `(pccx-lab SHA, trace hash, section kind)`.

## 6. Non-goals

- Live collaborative editing of the report (Google-Docs-style).
  Reports are snapshots, not documents.
- 3D chip floor-plan visualisation.  2D heatmaps are sufficient for
  the Phase 4 audience.
- Marketing-grade PDF typography.  IEEE-paper tone (see
  pccx-plotting-rules skill for chart style).

## 7. Open questions

- PdfFormat backend: WeasyPrint (Python dep) vs pdf-writer (pure
  Rust, fewer features).  Decide at M4.1 based on HTML → PDF fidelity.
- Benchmark database storage: in-tree (growing JSON) vs separate
  pccx-bench repo.  Recommend separate repo to avoid pccx-lab bloat.
- Concept-to-RTL UX: chat interface vs forms + preview.  Prototype
  both during Week 17, user test before Week 18 lock-in.
