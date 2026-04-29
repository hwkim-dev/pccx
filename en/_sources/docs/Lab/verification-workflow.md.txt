# Verification Workflow

_Last revised: 2026-04-29._

The pccx-lab verification pipeline converts RTL xsim output to `.pccx` traces,
then runs correctness judgements through the UI Verify tab and the
`pccx_golden_diff` CLI.  Two repositories divide the work:

| Repo | Role |
|------|------|
| `pccx-FPGA-NPU-LLM-kv260` | RTL + testbenches + `hw/sim/run_verification.sh` |
| `pccx-lab` | `.pccx` format, Tauri shell, IPC commands, UI |

## Verification flow

The pipeline consists of five steps: compile and run xsim testbenches, convert
the log via `from_xsim_log`, load into the UI through IPC, inspect in the
Verify tab, and gate with `pccx_golden_diff`.

```
hw/tb/*.sv
    │  xvlog + xelab + xsim
    ▼
xsim.log
    │  from_xsim_log --log <xsim.log> --output <tb>.pccx
    ▼
hw/sim/work/<tb>/<tb>.pccx
    │  IPC: run_verification / load_pccx
    ▼
pccx-lab UI  →  Verify tab  →  pccx_golden_diff --check
```

### Step 1 — xsim execution

From the RTL repo root:

```bash
hw/sim/run_verification.sh
```

The script compiles RTL dependencies declared in the `TB_DEPS` associative
array, then runs xvlog → xelab → xsim in sequence.
Each testbench must emit one of the two canonical patterns at exit:

```systemverilog
$display("PASS: %0d cycles, both channels match golden.", N_CYCLES);
$display("FAIL: %0d mismatches over %0d cycles.", errors, N_CYCLES);
```

These are the exact strings the `from_xsim_log` parser matches.

### Step 2 — from_xsim_log conversion

`from_xsim_log` (owned by `crates/core`) parses the log and writes a `.pccx` file.

| Log pattern | Emitted events |
|-------------|----------------|
| `PASS: <N> cycles, …` | `N × MAC_COMPUTE` on `--core-id` |
| `FAIL: <E> mismatches over <N> cycles.` | `N × MAC_COMPUTE` + `E × SYSTOLIC_STALL` |

Output path: `hw/sim/work/<tb>/<tb>.pccx`.

### Step 3 — IPC load

The `run_verification` IPC command shells out to `run_verification.sh` and
returns a structured summary (per-step PASS/FAIL, timing-met verdict, list of
`.pccx` paths).  Individual traces are cached via `load_pccx` IPC; the Tauri
backend emits a `trace-loaded` event that the Timeline component subscribes to,
causing the canvas to refresh automatically.

### Step 4 — UI Verify tab

Three widgets in the Verify tab:

- **Run Verification Suite** — invokes `run_verification` IPC.  Renders a per-step result table.
- **Per-row Open buttons** — load each testbench's `.pccx` via `load_pccx`.  Timeline canvas refreshes automatically.
- **Synth Status card** — parses `hw/build/reports/{utilization,timing_summary}_post_synth.rpt` and surfaces LUT / FF / RAMB / URAM / DSP counts plus WNS and timing-met verdict.

### Step 5 — pccx_golden_diff CLI

The regression gate is `pccx_golden_diff` (see [CLI reference](cli.md) for flags).

```bash
# Generate a reference profile from a known-good trace
pccx_golden_diff --emit-profile hw/sim/work/tb_gemm/tb_gemm.pccx > ref.jsonl

# Compare a candidate trace against the reference — exits 1 on any tolerance breach
pccx_golden_diff --check ref.jsonl hw/sim/work/tb_gemm/tb_gemm.pccx
```

## golden_diff

`crates/verification/src/golden_diff.rs` implements the correctness gate that
compares a `.pccx` trace against a `.ref.jsonl` reference profile.

### RefProfileRow schema

The reference file is a JSONL stream where each row corresponds to one decode
step (or prefill step):

```rust
pub struct RefProfileRow {
    pub step:              u32,
    pub api_name:          Option<String>,  // e.g. "uca_iter_0"
    pub expect_mac:        u64,
    pub expect_dma_read:   u64,
    pub expect_dma_write:  u64,
    pub expect_barrier:    u64,
    // cycle_budget: maximum cycles allowed for this step
}
```

### Match / mismatch determination

The diff is deterministic, framework-free — pure `serde_json` over a stable
schema, so CI reports identical numbers across machines.
Tolerances live on reference rows, not on CLI flags: the reference producer
(PyTorch pipeline — not yet landed) controls strictness without touching
pccx-lab.

- A step whose measured MAC / DMA event counts fall within the reference
  row's tolerance is **PASS**.
- Any field that drifts outside the tolerance makes the step a **MISMATCH** —
  that step appears in the diff report.
- The gate passes (`GateVerdict.passed = true`) only when `report.is_clean()`
  returns `true`.

### GoldenDiffGate — VerificationGate trait

`GoldenDiffGate` implements the `VerificationGate` trait so the IDE Verify tab
and CI pipelines can swap gate backends behind a single interface.  Current
implementation:

```rust
impl VerificationGate for GoldenDiffGate {
    fn check(&self, trace: &NpuTrace) -> GateVerdict {
        let report = golden_diff::diff(trace, &self.reference);
        let passed = report.is_clean();
        let summary = format!("{} / {} steps pass",
            report.pass_count, report.step_count);
        // ...
    }
    fn name(&self) -> &'static str { "golden-diff" }
}
```

Future gate kinds: Sail refinement verification, UVM coverage, formal property
checks.

## robust_reader

`crates/verification/src/robust_reader.rs` implements the 4-level parsing
policy that ISA / API config readers share.  It applies uniformly to every
config-shaped read (TOML, JSON, JSONL).

```rust
pub enum Policy {
    /// Fail the read on any unknown field.  CI default.
    Strict,
    /// Accept but surface unknown fields in `RobustReport::warnings`.
    /// CLI default — noisy enough to notice, not enough to block.
    Warn,
    /// Accept silently.  For tests or disposable scripts only.
    Lenient,
    /// Accept AND emit a "fixed" source string with unknown fields stripped —
    /// the UI's "auto-repair" button.
    Fix,
}
```

All helpers are pure (no I/O), so the UI's unknown-field modal dialog and CI
gates reuse the same logic.

Additional utilities:

- `sanitize_whitespace` — drops trailing whitespace, normalises BOM + line
  endings so Windows-edited files round-trip cleanly.
- `strip_trailing_commas` — forgives JSON's trailing-comma rejection (a common
  editor paste artefact).

## UI integration

The Verify tab renders `run_verification` IPC results in the following order:

1. When the IPC returns a `VerificationResult` struct, the per-step PASS/FAIL
   table is drawn.
2. A row's **Open** button calls `load_pccx` → the Tauri backend caches the
   trace and broadcasts `trace-loaded` → the Timeline component subscribes and
   refreshes the canvas.
3. The `pccx_golden_diff --check` verdict appears as a separate status badge;
   the detailed diff tree expands `GateVerdict.details` JSON as a collapsible
   tree.
4. The Synth Status card displays the `SynthReport` parsed from Vivado reports
   independently.

IPC command reference:

| Command | Input | Output |
|---------|-------|--------|
| `run_verification` | `repoPath: String` | per-step results + synth status |
| `load_pccx` | `path: String` | `PccxHeader` (+ `trace-loaded` event) |
| `fetch_trace_payload` | — | flat binary buffer (24 B/event) |
| `list_pccx_traces` | `repoPath: String` | list of generated `.pccx` artefacts |

## Cite this page

```bibtex
@misc{pccx_lab_verification_workflow_2026,
  title        = {pccx-lab Verification Workflow: RTL to .pccx to golden-diff gate},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/verification-workflow.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

Source lives under the `crates/verification/` crate at
[hkimw/pccx-lab](https://github.com/hkimw/pccx-lab).
