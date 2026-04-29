# Phase 1 — Workspace / Crate Split Proposal

**Status:** draft (2026-04-24) — awaiting user approval before implementation
**Scope:** PCCX-Lab roadmap §Phase 1 (M1.1 Workspace split + M1.2 stable API contracts)
**Prior art:** `docs/design/rationale.md` (why pccx-lab is one repo, not five)

## 1. Current state

```
pccx-lab/  (Cargo workspace — 3 members)
├── src/core          pccx-core       30 files   7,375 LOC     monolith
├── src/ai_copilot    pccx-ai-copilot  1 file      297 LOC     skeleton
├── src/uvm_bridge    pccx-uvm-bridge  1 file      134 LOC     skeleton
└── src/ui/src-tauri  "srcui"          3 files     706 LOC     orphan (not in workspace)
```

**Pain points**

1. **`pccx-core` is overloaded.** 24 `pub mod` declarations span unrelated concerns:
   trace parsing, .pccx format, hardware model, roofline, report generation,
   golden diff, VCD / chrome-trace writers, Vivado timing, ISA authoring,
   API authoring, speculative decoding primitives. Compile times scale with
   the crate; so does the blast radius of any change.
2. **`src/ui/src-tauri` carries the default scaffold name `srcui`** and is
   not a workspace member. Cargo lockfile / dependency resolution happens
   in isolation.
3. **Roadmap gaps:** Phase 3 needs a `pccx-remote` daemon, Phase 4 needs
   a dedicated `pccx-reports`, Phase 5 needs a `pccx-evolve` crate —
   none exist yet.

## 2. Target layout

```
pccx-lab/  (Cargo workspace — 7 members)
├── crates/
│   ├── pccx-core/          core types + .pccx format + trace + analytics (slim)
│   ├── pccx-reports/       Markdown / PDF / HTML report generator
│   ├── pccx-verification/  golden_diff + robust_reader + step_snapshot reference logic
│   ├── pccx-authoring/     isa_spec + api_spec (ISA / API TOML compilers)
│   ├── pccx-agents/        cloud LLM orchestration (was ai_copilot)
│   ├── pccx-uvm-bridge/    UVM scoreboard hooks (unchanged)
│   ├── pccx-remote/        NEW — backend daemon (Phase 3 scaffold)
│   ├── pccx-evolve/        NEW — DSE + surrogate + PRM loop (Phase 5 scaffold)
│   └── pccx-ide/           Tauri shell (was src/ui/src-tauri, renamed)
└── ui/                     React + Vite frontend (Node.js, outside Cargo workspace)
```

Rename `src/` → `crates/` to match idiomatic Rust workspace conventions.
The React frontend moves to top-level `ui/` because it is not a Cargo
member and merging it under `crates/` would be misleading.

### Module -> crate mapping (`pccx-core` breakup)

| Current `pccx-core` module | Destination crate |
|---|---|
| `pccx_format`, `trace`, `event_type_id`, `fnv1a_64` | `pccx-core` (retained) |
| `simulator`, `license`, `hw_model`, `cycle_estimator` | `pccx-core` (retained) |
| `roofline`, `bottleneck`, `coverage`, `live_window`, `step_snapshot` | `pccx-core` (retained — these are core analytics) |
| `vcd`, `vcd_writer`, `chrome_trace`, `isa_replay`, `api_ring` | `pccx-core` (retained — trace I/O) |
| `synth_report`, `vivado_timing` | `pccx-core` (retained — synth is core workflow) |
| **`report`** | **`pccx-reports`** |
| **`golden_diff`, `robust_reader`** | **`pccx-verification`** |
| **`isa_spec`, `api_spec`** | **`pccx-authoring`** |
| **`speculative`** | **`pccx-evolve`** (primitives for EAGLE-family strategies) |

After split, `pccx-core` drops from 24 modules to 19 — still the largest
crate but no longer a dumping ground.

## 3. Dependency graph (target)

```
pccx-ide  ──depends──▶  pccx-core, pccx-reports, pccx-verification, pccx-agents
pccx-remote  ──────▶   pccx-core, pccx-reports, pccx-verification, pccx-agents
pccx-agents  ──────▶   pccx-core
pccx-reports  ─────▶   pccx-core
pccx-verification ─▶   pccx-core
pccx-authoring  ───▶   pccx-core          (shared TOML parse / codegen helpers)
pccx-evolve  ──────▶   pccx-core, pccx-verification  (surrogate + PRM use ref traces)
pccx-uvm-bridge ───▶   pccx-core
```

**Acyclic.** `pccx-core` is the single sink. No crate depends on
`pccx-ide` / `pccx-remote` (they are terminal binaries).

## 4. Stable API contracts (M1.2 scope)

Each non-core crate exposes a **trait** that `pccx-core` (or its
consumers) can depend on without pulling the whole crate:

| Crate | Trait / surface | Caller |
|---|---|---|
| `pccx-reports` | `trait ReportFormat { fn render(...) -> String; }` | pccx-ide, pccx-remote, pccx_analyze CLI |
| `pccx-verification` | `trait VerificationGate { fn check(trace, ref) -> VerdictReport; }` | CI, pccx-ide |
| `pccx-authoring` | `trait IsaCompiler / trait ApiCompiler` + TOML schema | build.rs scripts, docs pipeline |
| `pccx-agents` | `trait ContextCompressor / trait SubagentRunner` | pccx-ide, pccx-remote |
| `pccx-remote` | REST OpenAPI spec + WebSocket event schema | web client (Phase 3.5) |
| `pccx-evolve` | `trait SurrogateModel / trait EvoOperator / trait PRMGate` | pccx-authoring (chip DSE loop) |

All traits start as `#[unstable]`; semver-strict after v0.3 per roadmap.

## 5. Implementation order (ordered by risk, not by milestone number)

1. **pccx-reports extraction** — lowest risk. `report.rs` is self-contained, has
   its own tests (25 existing), no downstream consumer outside the crate yet.
   Move as-is, re-export from `pccx-core` for backward compat in this session.

2. **pccx-verification extraction** — move `golden_diff` + `robust_reader` +
   `pccx_golden_diff` bin. Medium risk: the bin already imports explicitly via
   `pccx_core::golden_diff`, so the import path must change.

3. **pccx-authoring extraction** — move `isa_spec` + `api_spec`. Similar
   medium risk; no downstream consumer in-tree yet, but CLI tools like
   `pccx_analyze` may grow them.

4. **pccx-evolve extraction** — move `speculative` into a new crate with
   room for surrogate / PRM modules. Low risk since speculative is leaf.

5. **pccx-ide rename** — rename `srcui` → `pccx-ide` in
   `src/ui/src-tauri/Cargo.toml` + add to workspace `members`. This breaks
   the Tauri build script's expected path; requires coordination with
   `vite.config.ts` / `package.json` scripts. Medium risk.

6. **pccx-remote scaffold** — new empty crate with `lib.rs` stub and a
   minimal OpenAPI placeholder. Zero risk.

7. **`src/` → `crates/` rename** — last, after all members are
   relocated, because it touches every Cargo.toml path. Use `git mv`
   so history is preserved.

8. **CHANGELOG.md per crate + cargo-release setup** (M1.4) — do after
   crates stabilise; no point versioning a moving target.

## 6. Risk mitigation

- **Each step is its own commit.** `cargo check` + `cargo test` pass between
  every commit. If step N regresses, revert just N.
- **Re-export facade in `pccx-core`** during transition. Downstream code
  keeps importing `pccx_core::report::render_markdown` while the impl
  moves to `pccx-reports`; remove the re-export facade in a follow-up
  commit once consumers have migrated.
- **Tests move with their modules.** 25 existing tests must all pass
  post-move.
- **No Tauri build breakage.** Verify `cargo tauri build` works after
  the `pccx-ide` rename by testing the dev shell locally.

## 7. Out of scope for this proposal

- **Phase 1.3 plugin host** (hot-loadable `.so`). This is a standalone
  mechanism that lands on top of the split structure; does not affect
  the layout.
- **Phase 1.4 cargo-release / CHANGELOG automation.** Documented here
  but postponed to end of Phase 1.
- **React frontend split.** `ui/` stays monolithic for now; splitting
  into sub-packages is a Phase 2 IDE concern.
- **pccx-ai-copilot / pccx-agents merger.** Rename only in this round;
  expanding agent orchestration features is Phase 2 territory.

## 8. Decision requested

Approve to start implementation step 1 (`pccx-reports` extraction)?
Alternative: split steps into their own PRs so each can be reviewed
in isolation — slower but safer.

---

_Drafted 2026-04-24. When approved, update "Status" to "in progress"
and link the first implementation commit below._
