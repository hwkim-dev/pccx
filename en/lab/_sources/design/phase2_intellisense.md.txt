# Phase 2 — IntelliSense-Level Intelligence

**Status:** scaffold landed (2026-04-24); implementation kicks off in Phase 2 proper.
**Scope:** roadmap Weeks 6-9; milestones M2.1 - M2.6.
**Prior art:** Visual Studio IntelliSense, VSCode's LSP stack, Codeium, GitHub Copilot.

## 1. Goal

Make pccx-ide feel like a professional IDE for hardware + system design.
The experience target: completion within 100 ms (p95) including AI
augmentation; hover cards within 150 ms; cross-artifact go-to-def that
walks from an RTL identifier to the Sail spec row that defines its
opcode to the docs page that documents it.

## 2. Architecture

```
┌─────────────────────── pccx-ide (Tauri) ────────────────────────┐
│                                                                  │
│   Monaco editor  ──▶ tower-lsp client  ──▶ pccx-lsp multiplexer │
│                                                    │              │
│                              ┌─────────────────────┼──────────┐  │
│                              ▼                     ▼          ▼  │
│                     verible-verilog-lsp   rust-analyzer   clangd │
│                                                                  │
│                                     + AI layer (Haiku/Sonnet)   │
│                                       keyed by AST hash          │
└──────────────────────────────────────────────────────────────────┘
```

**pccx-lsp** is the crate that lives between Monaco and the per-language
servers.  It exposes three traits (`CompletionProvider`, `HoverProvider`,
`LocationProvider`) and an in-process multiplexer that fans the query
out to the right backend per language.

### 2.1 Backends

| Language | Backend | Binary |
|---|---|---|
| SystemVerilog | verible | `verible-verilog-lsp` |
| Rust | rust-analyzer | `rust-analyzer` |
| C / C++ | clangd | `clangd` |
| Python | pylsp | `pylsp` |
| Sail | in-house (no upstream) | pccx-lsp internal (tree-sitter) |
| MyST Markdown | tree-sitter + esbonio | `esbonio` for RST |

`Language::from_extension` already maps file extensions to these buckets.

### 2.2 AI layer — two-tier latency budget

| Tier | Model | Latency budget | Purpose |
|---|---|---|---|
| Hot path | fast cloud LLM | < 40 ms | Ghost-text completion while typing |
| Cold path | deep cloud LLM | < 2 s (async) | "Why is this slow?" explanation, refactor proposals |
| Cache | AST-hash LRU | 0 ms | Dedup identical queries within a session |

Cache key: `(language, file_path, AST_hash_of_cursor_subtree, cursor_col)`.
AST is recomputed on debounce (300 ms after typing stops).

### 2.3 Cross-artifact go-to-def (M2.3 killer feature)

The registry that makes "click opcode in RTL → jump to Sail spec row"
work is a flat index built at project-open time:

```
project-open
  ├── scan RTL   (verible AST) ──▶ extract opcode symbols
  ├── scan Sail  (sail parser) ──▶ extract spec rows
  ├── scan docs  (MyST walker) ──▶ extract anchors / headings
  └── build joint index:  symbol -> [(artefact, file, range), ...]
```

The index sits in `pccx-core` (Phase 1 has it scaffolded in `plugin::`).
`LocationProvider::definitions` consults the index first, then asks the
language server if no match.

## 3. Milestones

### M2.1 — LSP multiplexer (Week 6)

- tower-lsp client wrapper in pccx-ide.
- `CompletionProvider` impl for each external LSP.
- Smoke test: type `GEMM_` in a .sv file, receive verible completions.

### M2.2 — AI completion layer (Week 7)

- Haiku ghost-text provider behind `CompletionProvider` (source = AiFast).
- Sonnet refactor provider behind a separate command palette entry
  (source = AiDeep).
- Prompt cache (AST-hash LRU) in pccx-core.

### M2.3 — Cross-artifact navigation (Week 8)

- Joint index builder (scans RTL + Sail + docs).
- `LocationProvider::definitions` walks the joint index first.
- Demo: click `OP_GEMV` in `isa_pkg.sv` → jump to `pccx_decode.sail`
  → jump to `docs/v002/ISA/encoding.rst`.

### M2.4 — Real-time lint (Week 8)

- Verible lint results surfaced as diagnostics.
- Surrogate timing hints (M5A surrogate backend, if landed) shown as
  info-level diagnostics on clock-boundary modules.

### M2.5 — "Why is this slow?" panel (Week 9)

- Right-click trace event → Sonnet-narrated explanation panel.
- Uses `pccx-verification` + `pccx-reports` to fetch context.

### M2.6 — Target-aware parameter suggestions (Week 9)

- Detect FPGA target from `conf/target.toml` (KV260 / ZCU104 / ASIC-22nm).
- Presets surface as completions when a parameter is blank.
- Backed by a curated table in `pccx-lsp`.

## 4. Token budget (ties into Phase 0 M0.3)

- Hot-path completion: Haiku.  Typical response ~150 tokens.
  Session ceiling: 5,000 completions/day × 150 = 750 K tokens/day.
- Cold-path refactor: Sonnet.  Typical response ~1-2 K tokens.
  Session ceiling: 200 refactor calls/day × 1.5 K = 300 K tokens/day.
- Cache hits save 100% of the above.  Warm cache target: 60 % hit rate.

## 5. Out of scope

- Full IntelliSense on the React TypeScript side.  Keep Monaco + TS
  language service; AI layer only on Rust / SV / Sail / docs.
- LSP-over-WebSocket for remote sessions — Phase 3 problem.
- Semantic refactoring of test fixtures — Phase 4 reporting problem.

## 6. Dependencies

- `tower-lsp = "0.20"` — LSP server framework (pccx-lsp will pull in Phase 2 proper).
- `tree-sitter = "0.22"` — fast parser for Sail + MyST (ditto).
- `lsp-types = "0.95"` — matches tower-lsp's version.
- Haiku / Sonnet API access — shares `pccx-ai-copilot`.

_All left out of pccx-lsp's `Cargo.toml` today; added during Phase 2 proper
when implementation lands._
