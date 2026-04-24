# Copilot API

_Page in flux.  Refreshed 2026-04-24 to match pccx-lab HEAD._

The pre-Phase-1 `Copilot` struct (with `investigate()`,
`investigate_summary()`, `explain()`, `rank_by_severity()`,
`suggest_fix()`, `generate_report()`) has been retired.  Today
`pccx-ai-copilot` ships a thin set of static helpers for the Tauri UI
plus two unstable trait scaffolds on which Phase 2 / Phase 5 orchestration
will land.  The AI-driven natural-language-to-UVM workflow is being
rebuilt on top of the Phase 2 **pccx-lsp façade** — which landed its
A-slice (`LspMultiplexer` + `NoopBackend`) and B-slice (async companions,
`BlockingBridge`, `SpawnConfig` / `LspSubprocess`) in Phase 2 M2.1.

This page documents what is shippable today.  The richer façade will
be refreshed as the concrete verible / rust-analyzer / Claude backends
land against the lsp provider traits.

## Static helpers (`pccx-ai-copilot`)

Four functions + one registry constant, all callable without any struct
construction.  Covers the subset of the old Copilot surface that the
Tauri UI still needs today.

### `compress_context(cycles: u64, bottlenecks: usize) -> String`

Compresses trace statistics into a concise LLM prompt prefix.  Output
is ~300 characters — safe to prepend to any user query.

```rust
use pccx_ai_copilot::compress_context;

let ctx = compress_context(5_423_940, 19_179);
// "NPU trace: 5423940 total simulation cycles across a 32×32 systolic
//  MAC array with 32 cores at 1 GHz (est. 5423.9 µs wall-time). 19179
//  high-occupancy DMA bottleneck intervals detected. AXI bus contention
//  visible during simultaneous multi-core DMA. Peak theoretical: 2.05
//  TOPS."
```

### `generate_uvm_sequence(strategy: &str) -> String`

Returns a SystemVerilog UVM sequence stub for a named mitigation
strategy.  Unknown slugs fall back to a `generic_opt_seq` TODO stub.

```rust
use pccx_ai_copilot::generate_uvm_sequence;

let sv = generate_uvm_sequence("l2_prefetch");
// class l2_prefetch_seq extends uvm_sequence;
//   `uvm_object_utils(l2_prefetch_seq)
//
//   task body();
//     // Stagger DMA requests by AXI transaction overhead (15 cycles)
//     foreach (cores[i]) begin ...
//   endtask
// endclass : l2_prefetch_seq
```

### `list_uvm_strategies() -> Vec<&'static str>`

Enumerates every strategy slug `generate_uvm_sequence` recognises.  Used
by UI pickers and by the forthcoming LSP / agent orchestrator to avoid
hard-coding the match arms.

Current list (Phase 1 HEAD):

| slug                         | what the body does                                  |
|------------------------------|-----------------------------------------------------|
| `l2_prefetch`                | Stagger DMA reads by AXI transaction overhead.      |
| `barrier_reduction`          | Wavefront barrier in place of global sync.          |
| `dma_double_buffer`          | Ping-pong compute / DMA across adjacent tiles.      |
| `systolic_pipeline_warmup`   | Pre-roll the MAC array before the first real tile.  |
| `weight_fifo_preload`        | Front-load HP weight FIFOs during setup window.     |

Five entries, down from the thirteen-row intent-routing table in the
pre-Phase-1 doc.  The richer strategy set (`back_pressure_gate`,
`kv_cache_thrash_probe`, `speculative_draft_probe`, …) has not been
re-landed; track progress in pccx-lab
`docs/design/phase5_alphaevolve.md`.

### `get_available_extensions() -> Vec<Extension>`

Returns the extension catalogue the Tauri UI's Extensions tab renders.
Covers local LLMs, hardware-acceleration plugins, cloud bridges,
analysis plugins, and export plugins.  See `ExtensionCategory` in the
crate source for the enum surface.

## Unstable traits (Phase 1 M1.2)

Two scaffolds that Phase 2 IntelliSense and Phase 5 agent orchestration
will implement.  Both are public but carry the crate's "unstable until
v0.3" marker and are gated behind the `plugin-api` feature.

```rust
/// Token-budgeted compressor for chat history, trace summary, or doc
/// excerpts.  Deterministic head/tail trimmers and learned
/// LLMLingua-style compressors both implement this.
pub trait ContextCompressor {
    fn compress(&self, input: &str, target_tokens: usize) -> String;
    fn name(&self) -> &'static str;
}

/// Runs a single subagent task (log-grinder, research-scout,
/// doc-drafter) and returns its reply.  Drives the parallel-subagent
/// pattern pccx-ide and pccx-remote share.
pub trait SubagentRunner {
    fn run(&self, task: &str, context: &str) -> anyhow::Result<String>;
    fn name(&self) -> &'static str;
}
```

No concrete implementations ship with pccx-lab v0.2.x — they land as
Phase 2 / Phase 5 progress.  Every downstream consumer should treat
these signatures as subject to change until pccx-lab v0.3.

## pccx-lsp (Phase 2 M2.1)

The IntelliSense façade is where the AI / LSP / cache fan-out lives
going forward.  Three sync provider traits plus their async companions:

```rust
pub trait CompletionProvider {
    fn complete(&self, language: Language, file: &str,
                pos: SourcePos, source: &str)
        -> Result<Vec<Completion>, LspError>;
    fn name(&self) -> &'static str;
}

pub trait HoverProvider {
    fn hover(&self, language: Language, file: &str,
             pos: SourcePos, source: &str)
        -> Result<Option<Hover>, LspError>;
    fn name(&self) -> &'static str;
}

pub trait LocationProvider {
    fn definitions(&self, language: Language, file: &str,
                   pos: SourcePos, source: &str)
        -> Result<Vec<SourceRange>, LspError>;
    fn references(&self, language: Language, file: &str,
                  pos: SourcePos, source: &str)
        -> Result<Vec<SourceRange>, LspError>;
    fn name(&self) -> &'static str;
}
```

Routing happens through `LspMultiplexer`:

```rust
use pccx_lsp::{Language, LspMultiplexer, NoopBackend};

let mut m = LspMultiplexer::new();
m.register(
    Language::SystemVerilog,
    Box::new(NoopBackend),   // later: verible wrapper
    Box::new(NoopBackend),
    Box::new(NoopBackend),
);
let completions = m.complete(
    Language::SystemVerilog, "foo.sv",
    SourcePos { line: 0, character: 0 },
    "module foo;",
)?;
```

`NoopBackend` returns empty results — the deliberate "I have nothing
here" answer used while a real backend is being wired up.  For async
workflows, `BlockingBridge<P>` lifts any sync provider into the
`AsyncCompletionProvider` / `AsyncHoverProvider` / `AsyncLocationProvider`
trait via `tokio::task::spawn_blocking`.  External LSP servers
(verible, rust-analyzer, clangd) spawn through `SpawnConfig` +
`LspSubprocess`; the JSON-RPC codec on top of those pipes lands in a
follow-on slice.

The `CompletionSource` enum distinguishes results from an upstream LSP,
a Claude-Haiku fast predictor, a Claude-Sonnet deep predictor, or an
AST-hash cache — the future AI pipeline feeds back into this enum so
the UI can render provenance badges next to every suggestion.

See pccx-lab's `docs/design/phase2_intellisense.md` for the end-state
design (AI fan-out, tower-lsp adapter, Monaco wiring).

## UI-facing static commands

Between now and the full façade, the Tauri UI calls directly into the
static helpers via `invoke("compress_context", …)`,
`invoke("generate_uvm_sequence", …)`, and
`invoke("list_uvm_strategies")`.  The bridge is a one-liner per
function in `ui/src-tauri/src/lib.rs`.  There is no longer a
single `invoke("copilot_investigate", …)` umbrella call.

## Related

- [Analyzer API](analyzer_api.md) — the plugin-registry primitive all
  per-crate plugin traits (including `ContextCompressor` /
  `SubagentRunner`) hang off.
- [CLI reference](cli.md) — the binaries currently shipping; the old
  `pccx_analyze` umbrella does not exist today.

## Cite this page

```bibtex
@misc{pccx_lab_copilot_2026,
  title        = {pccx-ai-copilot and pccx-lsp: current AI / IntelliSense surface of pccx-lab after Phase 1},
  author       = {Kim, Hwangwoo},
  year         = {2026},
  howpublished = {\url{https://hwkim-dev.github.io/pccx/en/docs/Lab/copilot.html}},
  note         = {Part of pccx: \url{https://hwkim-dev.github.io/pccx/}}
}
```

The helpers documented here live at
<https://github.com/hwkim-dev/pccx-lab/blob/main/crates/ai_copilot/src/lib.rs>;
the LSP façade at
<https://github.com/hwkim-dev/pccx-lab/blob/main/crates/lsp/src/lib.rs>.
