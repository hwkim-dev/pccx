# Architecture Overview

_Last revised: 2026-04-22._

pccx-lab is the **desktop profiler + verification IDE** for the pccx v002
NPU architecture.  It ingests `.pccx` binary traces emitted by xsim
testbenches on the companion `pccx-FPGA-NPU-LLM-kv260` RTL repo and
surfaces everything — timeline, flame graph, roofline, bottleneck
windows, hardware block diagram, Vivado synth utilisation / timing,
waveform, ISA replay — in a single frameless Tauri v2 window.

This document is a flat map of the code base; the "why" of each
subsystem lives in-line in the source.

## Repo layout

```
pccx-lab/
├── src/
│   ├── core/            — pccx-core: headless Rust, no GUI deps
│   │   ├── src/
│   │   │   ├── lib.rs            single public surface
│   │   │   ├── pccx_format.rs    on-disk binary format
│   │   │   ├── trace.rs          NpuTrace + NpuEvent
│   │   │   ├── hw_model.rs       KV260 reference constants
│   │   │   ├── analyzer.rs       TraceAnalyzer trait + 16 builtins ★
│   │   │   ├── research.rs       Citation registry ★
│   │   │   ├── synth_runner.rs   Vivado spawn + log parse
│   │   │   ├── compare.rs        two-trace regression gate
│   │   │   ├── roofline.rs       Williams/Waterman + hierarchical
│   │   │   ├── bottleneck.rs     sliding-window contention detector
│   │   │   ├── report.rs         Markdown renderer
│   │   │   ├── live_window.rs    rolling stats for PerfChart
│   │   │   ├── step_snapshot.rs  deterministic cycle → registers
│   │   │   ├── vivado_timing.rs  report_timing_summary parser
│   │   │   ├── synth_report.rs   utilisation + timing summaries
│   │   │   ├── coverage.rs       UVM coverage JSONL merger
│   │   │   ├── vcd{,_writer}.rs  VCD ingest + emit
│   │   │   ├── chrome_trace.rs   Perfetto JSON writer
│   │   │   ├── isa_replay.rs     Spike-style commit log parser
│   │   │   ├── api_ring.rs       uca_* call ring buffer
│   │   │   └── bin/
│   │   │       ├── pccx_cli.rs       Vivado-shaped TCL runner
│   │   │       ├── pccx_analyze.rs   one-shot analysis CLI ★
│   │   │       ├── from_xsim_log.rs  xsim log → .pccx converter
│   │   │       └── generator.rs      synthetic trace generator
│   │   └── tests/       cross-module integration tests
│   ├── ai_copilot/      — LLM orchestration, depends on core
│   │   └── src/
│   │       ├── lib.rs            catalogue, extensions, uca_sync helper
│   │       ├── copilot.rs        Copilot struct + investigate/explain/rank ★
│   │       └── uvm.rs            UvmStrategy trait + 16 strategies ★
│   ├── uvm_bridge/      — SV / UVM DPI-C adapter, depends on core
│   └── ui/              — Tauri v2 + React 19 desktop shell
│       ├── src/                  TypeScript React components
│       └── src-tauri/            Rust Tauri shell + IPC commands
├── docs/                — Sphinx source + handbook (migrated here)
└── scripts/             — local tooling
```

★ = research-driven additions (2026-Q2 literature sweep).

## Layer contract

```
┌──────────────────────────────────────────────────────────────┐
│  ui/              React 19 + TypeScript + Vite 7             │
│                   Calls into Rust via `invoke("cmd", args)`. │
├──────────────────────────────────────────────────────────────┤
│  src-tauri/       Tauri v2 shell (Rust).  Thin layer — the   │
│                   real business logic lives in core/.        │
├──────────────────────────────────────────────────────────────┤
│  ai_copilot/      Copilot struct; uses core's analyzer       │
│  uvm_bridge/      registry.  No UI deps.                     │
├──────────────────────────────────────────────────────────────┤
│  core/            Pure Rust.  Zero dependency on ui/ or      │
│                   ai_copilot/ — the analyser surface is      │
│                   usable by any host binary.                 │
└──────────────────────────────────────────────────────────────┘
```

**Cardinal rule**: `core/` never depends on anything upstream.  New
analyses live in `core/src/analyzer.rs` and are exposed through
the `TraceAnalyzer` trait — the UI / Copilot / CLI all pick them up
automatically.

## Data flow (single trace)

```
 ┌────────────────────┐                ┌──────────────────────┐
 │ xsim testbench     │ .pccx bytes    │ pccx-core::pccx_format│
 │ (RTL repo)         ├───────────────►│ ::PccxFile::read     │
 └────────────────────┘                └──────────┬───────────┘
                                                  │ NpuTrace
                      ┌───────────────────────────┼───────────────────────────┐
                      ▼                           ▼                           ▼
           ┌───────────────────┐     ┌───────────────────────┐    ┌────────────────────┐
           │  analyze_all()    │     │  step_to_cycle()      │    │  write_vcd()       │
           │  → Vec<Report>    │     │  → RegisterSnapshot   │    │  write_chrome_trace│
           └─────────┬─────────┘     └──────────┬────────────┘    └────────────────────┘
                     │                           │
                     ▼                           ▼
           ┌───────────────────┐     ┌───────────────────────┐
           │ Copilot::         │     │  useRegisterSnapshot   │
           │ investigate_      │     │  (React hook, rAF      │
           │ summary() → str   │     │  debounced + LRU)      │
           └─────────┬─────────┘     └───────────────────────┘
                     │
                     ▼
           LLM system prompt (≤ 2 kB)
```

## Extension hooks

**Add a new analyzer** (`core/`):

```rust
pub struct MyAnalyzer;
impl TraceAnalyzer for MyAnalyzer {
    fn id(&self) -> &'static str            { "my_analyzer" }
    fn display_name(&self) -> &'static str  { "My Analysis" }
    fn description(&self) -> &'static str   { "..." }
    fn analyze(&self, trace: &NpuTrace, hw: &HardwareModel) -> AnalysisReport {
        // ...
    }
}
```

Register it in `analyzer::builtin_analyzers()` — the CLI and UI pick
it up instantly.  See the [Analyzer API page](analyzer_api.md) for the
full recipe plus a reference `DmaLatencyAnalyzer` implementation.

**Add a new UVM strategy** (`ai_copilot/`):

```rust
pub struct MyFix;
impl UvmStrategy for MyFix {
    fn id(&self) -> &'static str   { "my_fix" }
    fn category(&self) -> UvmCategory { UvmCategory::Memory }
    fn applies_to_analyzers(&self) -> &'static [&'static str] {
        &["my_analyzer"]
    }
    fn generate(&self) -> GeneratedStub { /* ... */ }
}
```

Append to `uvm::builtin_strategies()`.  The Copilot will now map
"my_analyzer" findings → "my_fix" automatically.

**Add a new Tauri command**: edit `src-tauri/src/lib.rs`, add the
`#[tauri::command]`-annotated fn, register in `invoke_handler!`.
`Copilot` already exposes the analyzer surface, so wiring is usually
just a one-line bridge.

## Cross-repo boundaries

- **pccx**: canonical v002 spec (you are reading it now).  Numbers,
  bit widths, opcode tables — always match this source.
- **pccx-FPGA-NPU-LLM-kv260**: the RTL repo pccx-lab profiles.  We
  never modify it from pccx-lab's CI; instead `synth_runner` and the
  board bringup scripts drive it read-only.
- **llm-lite**: CPU reference for golden comparisons.  Used by TB
  generators + the `reg_golden` UVM strategy.

## Build state (today)

```text
cargo test --workspace                → 131 passed (90 core lib + 25 core bin + 10 uvm + 6 copilot)
cargo check (src-tauri)               → 0 error
npx tsc --noEmit -p src/ui            → 0 error
npm run build (vite)                  → 3.6 MB main chunk + 14 split, 38 s
```

See [CLI reference](cli.md) for command reference and
[Copilot API](copilot.md) for the AI automation surface.
