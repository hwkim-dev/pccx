# Analyzer API

The `TraceAnalyzer` trait is the single abstraction every analysis
in pccx-lab implements.  Consumers (UI / CLI / Copilot / extensions)
never call individual `roofline::analyze()` / `bottleneck::detect()`
free functions anymore — they iterate the registry and pattern-match
on `AnalysisPayload` variants.

## Trait

```rust
pub trait TraceAnalyzer: Send + Sync {
    fn id(&self)           -> &'static str;        // stable id
    fn display_name(&self) -> &'static str;        // menu label
    fn description(&self)  -> &'static str;        // one-sentence blurb
    fn analyze(&self, trace: &NpuTrace, hw: &HardwareModel) -> AnalysisReport;
}
```

**Purity requirement**: `analyze()` must not mutate external state or
issue IPC.  The registry reserves the right to parallelise calls.

## Return shape

```rust
pub struct AnalysisReport {
    pub analyzer_id: String,       // == analyzer's id()
    pub summary:     String,       // ≤ 500 chars — LLM-ready
    pub payload:     AnalysisPayload,
}

pub enum AnalysisPayload {
    Roofline(RooflinePointPayload),
    RooflineHierarchical(Vec<RooflineBand>),
    Bottleneck(Vec<BottleneckInterval>),
    Custom(serde_json::Value),   // for new analyzers without a typed variant
    Text,                        // summary is the whole result
}
```

`Custom` is the escape hatch — experimental analyzers can carry any
JSON-serialisable payload without modifying the core enum.

## Built-in registry

| id | display | payload | what it reports |
|---|---|---|---|
| `roofline` | Roofline | `Roofline` | Williams/Waterman AI vs. achieved GOPS |
| `roofline_hier` | Hierarchical Roofline | `RooflineHierarchical` | Per-memory-tier dwell (Ilic 2014, Yang 2020) |
| `bottleneck` | Bottleneck Windows | `Bottleneck` | Sliding-window contention detector |
| `dma_util` | DMA Utilisation | `Custom` (`DmaUtilisationPayload`) | Read/write/MAC cycle share, starved vs. saturated flags |
| `stall_histogram` | Stall Histogram | `Custom` (`StallHistogramPayload`) | Log-bucket distribution of `SYSTOLIC_STALL` durations |
| `per_core_throughput` | Per-Core Throughput | `Custom` (`PerCoreThroughputPayload`) | MAC share per `core_id` + balance σ |
| `latency_distribution` | Latency Distribution | `Custom` (`LatencyDistributionPayload`) | P50/P95/P99 of `API_CALL` durations + worst callers |
| `power_estimate` | Power Estimate | `Custom` (`PowerEstimatePayload`) | Dynamic W + % of KV260 7 W TDP; thermal-bound flag |
| `kv_cache_pressure` | KV-Cache Pressure | `Custom` (`KvCachePressurePayload`) | Per-decode KV footprint vs L2 URAM; flags HBM spill |
| `phase_classifier` | Prefill/Decode Phase | `Custom` (`PhaseClassifierPayload`) | Tags spans as prefill/decode/idle; wall-clock split |
| `ai_trend` | Arithmetic Intensity Trend | `Custom` (`AiTrendPayload`) | Rolling-window AI (ops/byte); flags prefill→decode collapse |
| `dma_burst_efficiency` | DMA Burst Efficiency | `Custom` (`DmaBurstEfficiencyPayload`) | AXI effective BW after overhead amortisation |
| `matryoshka_footprint` | Matryoshka Subnet | `Custom` (`MatryoshkaFootprintPayload`) | Gemma-3N E2B/E4B swap savings projection |
| `moe_sparsity` | MoE Expert Sparsity | `Custom` (`MoESparsityPayload`) | Per-expert activation rate; flags over-sparse routing |
| `flash_attention_tile` | FlashAttention Tile Efficiency | `Custom` (`FlashAttentionTilePayload`) | Share of MAC bursts meeting tile threshold |
| `dual_hp_port_balance` | Dual-HP-Port Balance | `Custom` (`DualHpPortBalancePayload`) | HP0/1 vs HP2/3 traffic share; one-port starvation |

### Research lineage

The post-2025 analyzers are grounded in recent literature so the
UVM Copilot can cite evidence when narrating findings.  See the
[Research lineage page](research.md) for the complete auto-generated
citation table.

## Running everything

```rust
use pccx_core::{analyze_all, HardwareModel, NpuTrace};

let hw = HardwareModel::pccx_reference();
for report in analyze_all(&trace, &hw) {
    println!("[{}] {}", report.analyzer_id, report.summary);
}
```

## Writing a new analyzer

```rust
use pccx_core::analyzer::{TraceAnalyzer, AnalysisReport, AnalysisPayload};
use pccx_core::{NpuTrace, HardwareModel};

pub struct DmaLatencyAnalyzer;

impl TraceAnalyzer for DmaLatencyAnalyzer {
    fn id(&self) -> &'static str           { "dma_latency" }
    fn display_name(&self) -> &'static str { "DMA Latency Distribution" }
    fn description(&self) -> &'static str  {
        "Distribution of DMA_READ durations; flags long-tail outliers."
    }
    fn analyze(&self, trace: &NpuTrace, _hw: &HardwareModel) -> AnalysisReport {
        let durs: Vec<u64> = trace.events.iter()
            .filter(|e| e.event_type == "DMA_READ")
            .map(|e| e.duration)
            .collect();
        let max  = durs.iter().copied().max().unwrap_or(0);
        let mean = if durs.is_empty() { 0.0 }
                   else { durs.iter().sum::<u64>() as f64 / durs.len() as f64 };
        AnalysisReport {
            analyzer_id: self.id().to_string(),
            summary: format!("{} DMA reads · mean {:.0} cy · max {} cy",
                             durs.len(), mean, max),
            payload: AnalysisPayload::Text,
        }
    }
}
```

**To ship it**:

1. Append `Box::new(DmaLatencyAnalyzer)` to `builtin_analyzers()`.
2. Re-export from `lib.rs` if consumers will construct the type directly.
3. Add a unit test in `analyzer::tests`.
4. (Optional) Add a `Citation` entry in `core/src/research.rs`.
5. `cargo test -p pccx-core` should pass.

The Copilot picks up the new analyzer through the registry; the UI
sees it via the same `invoke("run_all_analyzers", ...)` Tauri command.

## Summary formatting convention

- Keep `summary` ≤ 500 chars.
- Start with the metric: `"AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound"`.
- Reserved uppercase prefixes drive the UI severity colour:
  - `error:` / `HBM-SPILL` / `OVER-SPARSE` / `PORT-STARVED` / `TILE-BOUND` / `AI-COLLAPSE` / `OVERHEAD-BOUND` → red
  - `THERMAL-BOUND` / `PREFILL-BOUND` / `DECODE-BOUND` / `SWAP-E2B` → amber
- The Copilot joins all summaries into one LLM system prompt; this
  is why each one must stand on its own without reader context.
