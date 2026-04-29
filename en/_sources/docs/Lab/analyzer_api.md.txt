# Analyzer API

_Page in flux.  Refreshed 2026-04-24 to match pccx-lab HEAD._

Phase 1 retired the pre-split `TraceAnalyzer` trait and the monolithic
`analyzer::builtin_analyzers()` list.  In its place pccx-core ships a
small generic **plugin-registry primitive** that every workspace crate
(reports, verification, authoring, evolve, lsp, ai_copilot, …) reuses
for its own trait-object plugins.  Callers now register plugins against
a per-crate `PluginRegistry<P>` instead of calling a fixed builtin list.

This page documents the primitive and how a consuming crate hangs its
plugin trait off it.  The 16-entry curated analyzer catalogue from
pre-Phase-1 has not been re-landed yet — when it returns it will live
inside one of the analytics crates (reports or a new `pccx-analytics`)
and be registered via this primitive.  Until then pccx-core exposes the
raw free functions (`roofline::analyze`, `bottleneck::detect`, …) and a
thin `pccx-reports::render_markdown` wrapper.

## Primitive

```rust
// pccx_core::plugin
pub const PLUGIN_API_VERSION: u32 = 1;

#[derive(Debug, Clone, Copy)]
pub struct PluginMetadata {
    pub id:           &'static str,  // stable identifier
    pub api_version:  u32,           // must equal PLUGIN_API_VERSION
    pub description:  &'static str,  // one-line blurb
}

pub trait Plugin {
    fn metadata(&self) -> PluginMetadata;
}

pub struct PluginRegistry<P: Plugin> {
    /* private Vec<P> */
}

impl<P: Plugin> PluginRegistry<P> {
    pub fn new() -> Self;
    pub fn register(&mut self, plugin: P) -> Result<(), PluginError>;
    pub fn all(&self)  -> &[P];
    pub fn find(&self, id: &str) -> Option<&P>;
    pub fn len(&self)  -> usize;
    pub fn is_empty(&self) -> bool;
}
```

`register` is the only fallible entry point; it rejects any plugin
whose `api_version` differs from `PLUGIN_API_VERSION` so out-of-tree
dylibs built against a stale header are refused up front.  Duplicate
ids are permitted — first registration wins on `find`.  Thread-safety
is the caller's responsibility; wrap in a `Mutex` / `RwLock` when
sharing across threads.

## Why generic over `P`?

A single registry type accommodates every plugin kind each crate
defines — `ReportFormat` (reports), `VerificationGate` (verification),
`IsaCompiler` / `ApiCompiler` (authoring), `SurrogateModel` /
`EvoOperator` / `PRMGate` (evolve), `CompletionProvider` /
`HoverProvider` / `LocationProvider` (lsp), `ContextCompressor` /
`SubagentRunner` (ai_copilot).  Each crate's unstable trait is a
supertrait of `Plugin`, gets its own `PluginRegistry<CrateTrait>`
instance, and is iterated independently at the call site.

## Registering a plugin

A consumer crate defines its own trait, makes it a supertrait of
`Plugin`, and offers a registry instance to its host:

```rust
use pccx_core::plugin::{Plugin, PluginMetadata, PluginRegistry,
                        PLUGIN_API_VERSION};

// 1.  Crate trait — extend `Plugin`.
pub trait ReportFormat: Plugin {
    fn render(&self, trace: &NpuTrace) -> String;
}

// 2.  Concrete implementation.
pub struct MarkdownReport;

impl Plugin for MarkdownReport {
    fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            id:          "markdown",
            api_version: PLUGIN_API_VERSION,
            description: "GitHub-flavoured Markdown report renderer",
        }
    }
}

impl ReportFormat for MarkdownReport {
    fn render(&self, trace: &NpuTrace) -> String { /* … */ }
}

// 3.  Host constructs a registry keyed on the concrete plugin type
//     and registers instances.
let mut reports: PluginRegistry<MarkdownReport> = PluginRegistry::new();
reports.register(MarkdownReport)?;
```

Crates that want heterogeneous plugins behind one trait object can
either (a) wrap each concrete type and implement `Plugin` for a thin
enum, or (b) wait for Phase 2/4 — the upcoming dylib loader lands
`Box<dyn CrateTrait>`-shaped registration when the C-ABI contract
stabilises.

Callers iterate with `registry.all()` or look up by id with
`registry.find("markdown")`.

## Error surface

```rust
#[derive(Debug, Clone, thiserror::Error)]
pub enum PluginError {
    #[error("plugin '{id}' declares API version {got}; \
             host expects {expected}")]
    ApiMismatch { expected: u32, got: u32, id: &'static str },
}
```

`ApiMismatch` is the only runtime error today.  Dylib load failures
(symbol missing, C-ABI mismatch, unload panic) will reuse this enum
when the Phase 2/4 dynamic loader arrives — the registry will then
gain `load_dylib(path)` on top of the in-process `register`.

## Stability

Everything in `pccx_core::plugin` is **unstable until pccx-lab v0.3**.
The enum is `#[non_exhaustive]` in spirit — new variants land without a
SemVer major bump during the Phase 1/2 window.

Dylib-loading machinery (libloading + C-ABI `register()` symbol + safe
drop on unload) is **not yet implemented**; it lands during Phase 2/4
once an out-of-tree plugin actually ships.  Until then every registry
is an in-process `Vec<Box<dyn T>>`.

## Cross-crate plugin traits as of Phase 1

| Crate             | Trait(s) gated behind `Plugin`                               |
|-------------------|--------------------------------------------------------------|
| `pccx-reports`    | `ReportFormat`                                               |
| `pccx-verification`| `VerificationGate`                                          |
| `pccx-authoring`  | `IsaCompiler`, `ApiCompiler`                                 |
| `pccx-evolve`     | `SurrogateModel`, `EvoOperator`, `PRMGate`                   |
| `pccx-lsp`        | `CompletionProvider`, `HoverProvider`, `LocationProvider`    |
| `pccx-ai-copilot` | `ContextCompressor`, `SubagentRunner`                        |

Every trait in this table is scaffolded behind the crate's
`plugin-api` feature flag; concrete implementations land incrementally
as the Phase 2–5 workstreams complete.  See each crate's
`CHANGELOG.md` for the per-trait landing timeline.

## Related

- [CLI reference](cli.md) — which binaries exist today after the
  workspace split, and what surface each one actually covers.
- [Copilot API](copilot.md) — the current `pccx-ai-copilot` static
  helpers plus the Phase 2 pccx-lsp provider traits.
- [Research lineage](research.md) — currently a placeholder; the
  citation registry was in `core/src/research.rs`, which was removed
  in Phase 1.

## Cite this page

When referring to the pccx-core plugin-registry primitive in papers,
blog posts, or AI summaries, please cite:

```bibtex
@misc{pccx_lab_analyzer_api_2026,
  title        = {pccx-core plugin registry: the generic primitive every pccx-lab crate hangs its trait-object plugins off},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/analyzer_api.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

The primitive lives at
<https://github.com/hkimw/pccx-lab/blob/main/crates/core/src/plugin.rs>.
