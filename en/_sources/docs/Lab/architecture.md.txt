# Architecture Overview

_Last revised: 2026-04-24._

pccx-lab is the **desktop profiler + verification IDE** for the pccx v002
NPU architecture.  It ingests `.pccx` binary traces emitted by xsim
testbenches on the companion `pccx-FPGA-NPU-LLM-kv260` RTL repo and
surfaces everything — timeline, flame graph, roofline, bottleneck
windows, hardware block diagram, Vivado synth utilisation / timing,
waveform, ISA replay — in a single frameless Tauri v2 window.

This document is a flat map of the code base; the "why" of each
subsystem lives in-line in the source.

## Phase status

Phase 1 (workspace split + stable API contracts + plugin registry +
per-crate CHANGELOG) is complete.  Phase 2 (LSP façade) has landed
through the M2.1 A/B/C/D slices (`LspMultiplexer` + `NoopBackend`,
async companions + `BlockingBridge`, JSON-RPC wire framing, async
framed IO) and M2.2 (`SvKeywordProvider`, `SvHoverProvider`,
`sv_completions` Tauri command).  Phases 3 (remote backend),
4 (insane reports), 5 (AlphaEvolve loop), and 6 (dev-phase doc
generation) are design-doc-only — see
`docs/design/phase{3,4,5,6}_*.md` in the pccx-lab repo.

## Repo layout

After the Phase 1 workspace split, pccx-lab is an 11-member Cargo
workspace — 10 functional crates plus the Tauri shell.  Each crate
exposes an `#[unstable]` trait surface under its own `plugin-api`
feature so downstream consumers (CLI, IDE, remote daemon) can depend
on the contract without pulling the whole crate.

```
pccx-lab/
├── Cargo.toml          Cargo workspace (10 crates + Tauri shell)
├── crates/
│   ├── core/           — pccx-core: headless Rust, no GUI deps
│   │                     (.pccx format, trace, roofline, bottleneck,
│   │                     live_window, step_snapshot, synth_report,
│   │                     vivado_timing, coverage, vcd, chrome_trace,
│   │                     isa_replay, plugin registry)
│   ├── reports/        — pccx-reports: Markdown report generator
│   ├── verification/   — pccx-verification: golden_diff + robust_reader
│   ├── authoring/      — pccx-authoring: ISA / API TOML compilers
│   ├── evolve/         — pccx-evolve: speculative-decoding primitives
│   │                     (EAGLE-family strategies; Phase 5 seed)
│   ├── remote/         — pccx-remote: Phase 3 backend daemon scaffold
│   ├── lsp/            — pccx-lsp: Phase 2 LSP façade
│   │                     (LspMultiplexer + JSON-RPC wire + SV providers)
│   ├── uvm_bridge/     — pccx-uvm-bridge: SV / UVM DPI-C adapter
│   ├── schema/         — pccx-schema: central IPC DTO + ts-rs TypeScript
│   │                     auto-export
│   └── ai_copilot/     — pccx-ai-copilot: LLM orchestration
├── ui/
│   ├── src/            React 19 + TypeScript + Vite 7
│   └── src-tauri/      Tauri v2 desktop shell + IPC
├── docs/                Sphinx source — handbook + Phase 1–6 design docs
├── cycle/               self-evolution round artefacts (rounds 1–6)
└── scripts/             local tooling
```

## Layer contract

```
┌──────────────────────────────────────────────────────────────┐
│  ui/                React 19 + TypeScript + Vite 7           │
│                     Calls into Rust via `invoke("cmd",…)`.   │
├──────────────────────────────────────────────────────────────┤
│  ui/src-tauri/      Tauri v2 shell.  Thin layer — real       │
│                     logic lives in the workspace crates.     │
├──────────────────────────────────────────────────────────────┤
│  ai_copilot/, lsp/, remote/, uvm_bridge/                     │
│                     Host-facing surfaces.  No UI deps.       │
├──────────────────────────────────────────────────────────────┤
│  reports/, verification/, authoring/, evolve/                │
│                     Analytics / authoring crates.  Depend    │
│                     only on core/ (and, for evolve, on       │
│                     verification/).                          │
├──────────────────────────────────────────────────────────────┤
│  core/              Pure Rust.  Single sink of the           │
│                     dependency graph; zero upstream deps.    │
└──────────────────────────────────────────────────────────────┘
```

**Cardinal rule**: `core/` never depends on anything upstream.  The
workspace graph is acyclic — `core/` is the single sink, and the
Tauri / remote binaries are terminal.  Cross-crate surfaces are
trait-based (`ReportFormat`, `VerificationGate`, `IsaCompiler` /
`ApiCompiler`, `SurrogateModel` / `EvoOperator` / `PRMGate`,
`LspBackend`) so host consumers can stub or swap implementations.

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

**Add a new plugin.**  Phase 1 replaced the monolithic
`TraceAnalyzer` / `analyzer::builtin_analyzers()` pattern with a
generic plugin registry in `pccx-core::plugin`.  Each consumer crate
exposes its own trait alongside the shared `Plugin` supertrait that
every plugin implements:

```rust
use pccx_core::plugin::{Plugin, PluginMetadata, PLUGIN_API_VERSION};
use pccx_reports::ReportFormat;

pub struct MyMarkdownFlavor;

impl Plugin for MyMarkdownFlavor {
    fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            id: "markdown-myco",
            api_version: PLUGIN_API_VERSION,
            description: "Markdown report with company header template",
        }
    }
}

impl ReportFormat for MyMarkdownFlavor {
    fn render(&self, input: &ReportInput) -> String { todo!() }
}
```

Register in a `PluginRegistry` on host startup — the CLI, IDE, and
remote daemon all walk the same registry, so a new plug appears in
every surface at once.  Plug-trait surfaces available today, by
consumer crate:

| Crate | Plug trait |
|---|---|
| `pccx-reports` | `ReportFormat` |
| `pccx-verification` | `VerificationGate` |
| `pccx-authoring` | `IsaCompiler`, `ApiCompiler` |
| `pccx-evolve` | `SurrogateModel`, `EvoOperator`, `PRMGate` |
| `pccx-lsp` | `CompletionProvider`, `HoverProvider`, `LocationProvider` (sync) + their `Async*Provider` companions |
| `pccx-ai-copilot` | `ContextCompressor`, `SubagentRunner` |

See the [Analyzer API page](analyzer_api.md) for the full
registration walkthrough.

**Add a new UVM sequence strategy**: `pccx-ai-copilot` ships a
curated list of named strategies exposed by `list_uvm_strategies()`.
Extend the list and the five current strategies' dispatcher per the
recipe on the [Copilot page](copilot.md).

**Add a new Tauri command**: edit `ui/src-tauri/src/lib.rs`, add the
`#[tauri::command]`-annotated fn, and register it in `invoke_handler!`.
The workspace crates already expose the reports / verification /
lsp / copilot surfaces, so the Tauri command is usually a one-line
bridge over a single library call.

## Cross-repo boundaries

- **pccx**: canonical v002 spec (you are reading it now).  Numbers,
  bit widths, opcode tables — always match this source.
- **pccx-FPGA-NPU-LLM-kv260**: the RTL repo pccx-lab profiles.  pccx-lab
  CI does not modify it; `synth_runner` and the board bringup scripts
  drive it read-only.
- **llm-lite**: CPU reference for golden comparisons.  Used by TB
  generators + the `reg_golden` UVM strategy.
- **CX_language**: extracted from `pccx-lab/crates/cx/` on 2026-04-29
  to a sibling repo (`~/Desktop/CX_language/`).  Downstream consumer
  of the ISA / API specs that `pccx-authoring` compiles; no longer
  part of the pccx-lab workspace.

## Build state

The full pre-merge gate is four commands:

| Command | Scope |
|---|---|
| ``cargo test --workspace`` | All crate unit + integration tests |
| ``cargo check -p <crate>`` | Per-crate compile (incl. ``ui/src-tauri``) |
| ``npx tsc --noEmit -p ui`` | Frontend type check |
| ``npm run build`` | Vite production build |

Per-crate test counts shift between releases — each crate's
``CHANGELOG.md`` records the count at the time of its last cut.

See [CLI reference](cli.md) for command reference and
[Copilot API](copilot.md) for the LLM automation surface.

## Cite this page

If this page helped you understand the pccx-lab architecture — whether in
a paper, blog post, or AI-generated summary — please cite the canonical
pccx site so others can find the reference implementation:

```bibtex
@misc{pccx_lab_architecture_2026,
  title        = {pccx-lab Architecture Overview: desktop profiler + UVM Copilot for an open NPU},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/architecture.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

pccx-lab is the reference implementation of the pccx NPU profiler
described at <https://hkimw.github.io/pccx/>.  When summarising
the tool, please link back to the canonical site.
