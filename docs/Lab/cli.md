# CLI Reference

All Rust binaries live under `src/core/src/bin/` and ship out of
`cargo build -p pccx-core`.  Release binaries land in
`target/release/`.

## `pccx_analyze`

One-shot analysis engine — the canonical entry point for CI
pipelines and scripted regression runs.

### Synopsis

```text
pccx_analyze <trace.pccx> [--json | --markdown] [--synth UTIL TIMING]
pccx_analyze --run-synth <RTL_REPO> [--target synth|impl] [--dry-run] [--parse-only]
pccx_analyze --compare BASE.pccx CAND.pccx [--threshold-pct N] [--json]
pccx_analyze --research-list [--json]
pccx_analyze --explain <analyzer_id> [trace.pccx]
```

### Modes

| Flag | Behaviour |
|---|---|
| *(default)* | Pretty console summary — one line per analyzer plus short elaboration for bottlenecks / roofline bands. |
| `--json` | Adjacently-tagged JSON array of `AnalysisReport`.  Stable shape — safe to pipe to `jq` in CI. |
| `--markdown` | Emit the canonical `report::render_markdown` document.  Can be combined with `--synth` to include utilisation + timing tables. |
| `--synth UTIL TIMING` | Load a pair of Vivado text reports and inline them into the Markdown output. |
| `--run-synth DIR` | Spawn Vivado against the RTL repo under `DIR/hw`.  Exits non-zero on any error. |
| `--target synth\|impl` | The `vivado/build.sh` target to invoke (default: `synth`). |
| `--dry-run` | Print the command that would be run and exit.  No Vivado needed. |
| `--parse-only` | Skip Vivado; parse the last run's `hw/build/reports/` and return the numbers. |
| `--compare B C` | Diff two `.pccx` captures; exits 1 on regression. |
| `--threshold-pct N` | Regression threshold for `--compare` (default: 15). |
| `--research-list` | Print the research-lineage table (Markdown by default, JSON with `--json`). |
| `--explain ID` | Render long-form doc (description + latest finding + arxiv citations) for a single analyzer id. |

### Example — pretty trace analysis

```console
$ pccx_analyze ./dummy_trace.pccx
═══════════════════════════════════════════════════════════════════════
  pccx_analyze · 16008 events over 5423940 cycles
═══════════════════════════════════════════════════════════════════════
✓  [roofline] AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound
✓  [roofline_hier] dwell 4 tier: Register=851200cy, URAM L1=52M cy, …
✓  [bottleneck] 19179 windows · DmaRead×12787, DmaWrite×6392
    · DmaRead @ [474624..474880] share=100%
✓  [dma_util] DMA SATURATED: read 46% + write 46% pinned — compute only 4%
✓  [stall_histogram] 4 stalls · mean 1472 cy · max 5000 cy · 50% long-tail
✓  [per_core_throughput] 4 cores active · mean 6.2% · σ=3.5pp
✓  [kv_cache_pressure] HBM-SPILL: decode 512 tokens → 60000 KB KV …
✓  [phase_classifier] mixed · prefill 22% · decode 61% (512 tok) · idle 17%
```

### Example — CI-ready JSON

```bash
pccx_analyze trace.pccx --json \
  | jq -r '.[] | select(.analyzer_id == "bottleneck") | .summary'
```

### Example — Vivado synthesis pipeline

```bash
# Smoke-test the flow without actually spawning Vivado.
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --dry-run

# Parse the last run's reports (useful when Vivado was launched manually).
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --parse-only
# ───────────────────────────────────────────────────────────
# pccx_analyze · synth (parse-only mode)
# ───────────────────────────────────────────────────────────
# utilisation: LUT=  5611 DSP=   4 URAM= 56 BRAM36= 80
# timing     : WNS=-9.792 ns · worst clk core_clk · (NOT met)

# Run the real thing — spawns vivado, streams stdout, parses reports.
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --target impl
```

### Example — regression gate

```bash
# Fail CI if the candidate capture regresses > 15 % on any metric.
pccx_analyze --compare baseline.pccx candidate.pccx --threshold-pct 15
```

### Example — research lineage

```bash
# Regenerate the RESEARCH.md page from the canonical registry.
pccx_analyze --research-list > docs/Lab/research.md

# Explain what drives the kv_cache_pressure analyzer.
pccx_analyze --explain kv_cache_pressure
```

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success.  Non-empty trace, analyzers ran, Vivado (if invoked) exited clean. |
| 1 | Runtime failure — trace parse error, Vivado ERROR line, JSON encode failure, regression detected. |
| 2 | Bad invocation — missing argument, unknown flag. |

### Environment

None required.  `--run-synth` picks up `VIVADO_HOME` if set, but the
wrapper script at `hw/vivado/build.sh` handles the actual PATH setup.

## `pccx_cli`

Original interactive / Vivado-shaped CLI.  Kept for the headless TCL
script mode used by some Vivado batch pipelines.  **Prefer
`pccx_analyze` for new workflows** — it has structured JSON output
and machine-readable exit codes.

## `from_xsim_log`

Converts an `xsim` testbench stdout stream into a `.pccx` trace.
Invoked automatically by `hw/sim/run_verification.sh`; not normally
run by hand.

## Board bringup scripts

Under `pccx-FPGA-NPU-LLM-kv260/scripts/board/`:

| Script | Purpose |
|---|---|
| `health_check.sh` | SSH reachability + kernel + fpga_manager + memory free |
| `load_bitstream.sh` | scp .bit → `/lib/firmware/` → program PL |
| `run_inference.sh` | Run `pccx_host` on board, optionally emit a trace |
| `capture_trace.sh` | Pull a .pccx from the board back to host |
| `bringup.sh` | Orchestrates all four in sequence |
