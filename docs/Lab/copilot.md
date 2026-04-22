# Copilot API

The `Copilot` struct is the canonical entry point for every
AI-driven workflow in pccx-lab.  It wraps:

- an optional reference to the currently-loaded `NpuTrace`
- the pccx KV260 reference `HardwareModel`
- the full `TraceAnalyzer` registry from `pccx-core`
- the `UvmStrategy` registry from `pccx-ai-copilot::uvm`

Consumers construct one instance per trace load and then drive it
through the methods below.

## Construction

```rust
use pccx_ai_copilot::Copilot;

let c = Copilot::new(Some(&trace));
// or
let c = Copilot::new(None);   // no trace yet; investigate() returns []
```

Callers that want to extend the analyzer registry mutate
`c.analyzers.push(...)` before the first `investigate()` call.

## Methods

### `investigate() -> Vec<AnalysisReport>`

Runs every registered analyzer against the trace.  Returns reports
in registry order.  Empty when no trace is loaded.

### `investigate_summary() -> String`

Collapses all reports into a single LLM-ready system prompt.  Each
line is `"- [<analyzer_id>] <summary>"`; total length is bounded by
the number of analyzers × 500 chars per summary.

```rust
let prompt = c.investigate_summary();
// Trace analysis summary (automated):
// - [roofline] AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound
// - [dma_util] DMA SATURATED: read 46% + write 46% pinned — compute only 4%
// - [bottleneck] 19179 windows · DmaRead×12787, DmaWrite×6392
// ...
```

Feed this straight into an LLM's `system` channel.

### `rank_by_severity() -> Vec<AnalysisReport>`

Server-side equivalent of the dashboard's severity sort.  Returns the
reports reordered so error-class findings come first, then warnings,
then informational entries.  Ties break on registry declaration order
so the output is stable across repeated calls.

```rust
let top = c.rank_by_severity();
println!("most urgent: {}", top[0].summary);
```

### `explain(analyzer_id: &str) -> Option<String>`

Long-form Markdown explainer for a single analyzer.  Pulls every
matching `research::Citation` and formats them alongside the analyzer's
description and its latest finding.

```rust
let md = c.explain("kv_cache_pressure").unwrap();
// # KV-Cache Pressure (kv_cache_pressure)
// Projects per-decode KV-cache footprint against L2 URAM; cites …
//
// ## Latest finding
// HBM-SPILL: decode 512 tokens → 60000 KB KV …
//
// ## Research lineage
// - **QServe …** (2024) — [2405.04532](…). _Why_: …
```

Returns `None` when the id is not in the registry, so the UI can
distinguish "unknown id" from "no trace loaded".

### `suggest_fix(intent: &str) -> (String, String)`

Natural-language intent → (strategy_slug, SystemVerilog_stub).
Uses keyword rules when the slug isn't in the intent verbatim.

```rust
let (slug, sv) = c.suggest_fix("please reduce DMA barrier contention");
// slug == "barrier_reduction"
// sv   == "class barrier_reduction_seq extends uvm_sequence; …"
```

**Keyword routing** — the Copilot looks for these substrings (in
priority order) and maps them to a canonical strategy:

| Intent keywords | Strategy | Research lineage |
|---|---|---|
| `barrier`, `sync` | `barrier_reduction` | — |
| `prefetch`, `dma` | `l2_prefetch` | Packing-Prefetch (arxiv 2508.08457) |
| `thermal`, `tdp`, `power`, `heat` | `back_pressure_gate` | KV260 7 W PL TDP; Hybrid-Systolic ISLPED 2025 |
| `latency`, `tail`, `p95`, `p99`, `jitter` | `kv_cache_thrash_probe` | HERMES 2025 tail-latency model |
| `early exit`, `edge-cloud` | `early_exit_decoder` | arxiv 2505.21594 |
| `speculative`, `draft`, `spec decode` | `speculative_draft_probe` | OpenPangu NPU (arxiv 2603.03383 — 1.35×) |
| `evict`, `sparsif`, `kv drop` | `sparsified_kv_eviction` | LoopServe + EVICPRESS |
| `w4a8`, `kv4`, `quantize`, `qserve`, `qoq` | `qoq_kv4_quantize` | QServe (arxiv 2405.04532) + QQQ |
| `matryoshka`, `subnet`, `e2b`, `e4b` | `matryoshka_subnet_switch` | arxiv 2205.13147 |
| `wavelet`, `low-rank`, `long context` | `wavelet_attention_probe` | arxiv 2312.07590 |
| `flash`, `tile`, `softmax` | `flash_attention_tile_probe` | FlashAttention-2/3 |
| `moe`, `expert`, `mixture` | `kv_cache_thrash_probe` | Switch Transformer (arxiv 2101.03961) |
| `throughput`, `core` | `back_pressure_gate` | — |

### `generate_report(synth: Option<&SynthReport>) -> String`

Delegates to `pccx-core::report::render_markdown`.  Pass a parsed
`SynthReport` (from `synth_report::load_from_files` or
`synth_runner::run`) to include utilisation + timing tables.

## Registry extension

```rust
// Runtime-register an extra analyzer before investigate().
let mut c = Copilot::new(Some(&trace));
c.analyzers.push(Box::new(MyCustomAnalyzer));
let reports = c.investigate();
```

Strategy registry is queried via `uvm::strategies_for_analyzer(id)` —
the Copilot uses this to map any analyzer's findings to a candidate
mitigation set without hard-coded keyword matching.

## Using it from automation

```rust
use pccx_ai_copilot::Copilot;
use pccx_core::{PccxFile, NpuTrace};
use std::fs::File;

fn summarise(path: &str) -> anyhow::Result<String> {
    let mut f = File::open(path)?;
    let pccx = PccxFile::read(&mut f)?;
    let trace = NpuTrace::from_payload(&pccx.payload)?;
    let c = Copilot::new(Some(&trace));
    Ok(c.investigate_summary())
}
```

Pairs naturally with `pccx_analyze <trace.pccx>` for CI pipelines —
the CLI prints the equivalent of `investigate_summary()` by default.

## Error handling

`Copilot` is infallible by design.  Every method returns a value even
when the trace is missing (empty `Vec` / `"No trace loaded"` string /
empty SV stub / `None` from `explain`).  The caller's empty-state
branch is the correct place to decide whether to render a welcome
screen, toast, or CI skip — never inside the copilot.
