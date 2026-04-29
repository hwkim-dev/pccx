# CLI Reference

_Page in flux.  Refreshed 2026-04-24 to match pccx-lab HEAD._

The single `pccx_analyze` umbrella binary described in the
pre-Phase-1 revision of this page was **not re-landed** when the
workspace split moved code into `crates/`.  Today pccx-lab ships four
smaller Rust binaries, spread across the crates that own each
surface.  Each one covers a piece of what `pccx_analyze` used to
multiplex; the rest (research-list export, analyzer-id explain,
`--compare` regression gate, synth runner) awaits re-landing inside
the appropriate crate.

## Binaries distributed across crates

| Binary              | Source crate        | Build command                         |
|---------------------|---------------------|---------------------------------------|
| `pccx_cli`          | `pccx-reports`      | `cargo build -p pccx-reports`         |
| `generator`         | `pccx-core`         | `cargo build -p pccx-core`            |
| `from_xsim_log`     | `pccx-core`         | `cargo build -p pccx-core`            |
| `pccx_golden_diff`  | `pccx-verification` | `cargo build -p pccx-verification`    |

Release artefacts still land in the workspace-wide
`target/release/` directory.

## `pccx_cli`

Headless trace-inspection CLI — the surface any CI pipeline that only
needs per-core utilisation, bottleneck windows, roofline verdicts, or
a Markdown summary should target today.

### Synopsis

```text
pccx_cli <path/to/trace.pccx>
         [--util]
         [--roofline]
         [--bottleneck <ratio>]
         [--windows <cycles>]
         [--threshold <ratio>]
         [--report-md]
         [--source <script>]
```

### Flag reference

| Flag                    | Behaviour                                                        |
|-------------------------|------------------------------------------------------------------|
| `--util`                | Print per-core MAC utilisation bar chart.                        |
| `--roofline`            | Print arithmetic intensity + compute/memory-bound verdict.       |
| `--bottleneck <ratio>`  | Legacy per-event DMA hotspot filter (default `0.5`).             |
| `--windows <cycles>`    | Sliding-window size for the new bottleneck detector (default 256). |
| `--threshold <ratio>`   | Share-of-window threshold (default `0.5`).                       |
| `--report-md`           | Emit a `pccx-reports::render_markdown` summary to stdout.        |
| `--source <script>`     | Run a `pccx_tcl`-style batch script (headless mode).             |

There are no `--json`, `--compare`, `--research-list`, `--explain`,
or `--run-synth` modes today.  The previous documentation described
those flags as part of a unified `pccx_analyze` binary that was
deferred — they are tracked for re-landing but are not callable in the
current tree.

### Example — pretty trace inspection

```bash
pccx_cli ./dummy_trace.pccx --util --roofline --report-md
```

The `--report-md` output is the same Markdown document
`pccx-reports::render_markdown` produces; consumers that just want the
Rust API should skip the binary and call it directly.

## `generator`

Generates a demo `.pccx` trace for development and testing.  Used by
the UI's first-run flow and by CI smoke tests.

### Synopsis

```text
generator [output_path] [tiles] [cores]
```

Defaults: `dummy_trace.pccx`, `tiles=100`, `cores=32`.  Constructs an
`NpuTrace` via `pccx_core::simulator::generate_realistic_trace`,
wraps it in a `PccxFile` with the current `HardwareModel::pccx_reference()`
metadata, and writes it to disk.

## `from_xsim_log`

Converts a Xilinx `xsim` simulation log into a `.pccx` trace the UI
can load.  Invoked automatically by `hw/sim/run_verification.sh` in
the RTL repo; not normally run by hand.

### Synopsis

```text
from_xsim_log --log <xsim.log> --output <out.pccx>
              [--core-id <u32>] [--testbench <name>]
```

Recognised patterns (emitted by the pccx-FPGA testbenches):

| Log pattern                                    | Emitted events                                   |
|------------------------------------------------|--------------------------------------------------|
| `PASS: <N> cycles, ...`                        | `N × MAC_COMPUTE` on `--core-id`.                |
| `FAIL: <E> mismatches over <N> cycles.`        | `N × MAC_COMPUTE` + `E × SYSTOLIC_STALL`.        |

## `pccx_golden_diff`

End-to-end correctness gate that compares a candidate `.pccx`
trace against a JSONL reference profile.

### Synopsis

```text
pccx_golden_diff --emit-profile <trace.pccx> [--tolerance-pct N] > ref.jsonl
pccx_golden_diff --check        ref.jsonl <trace.pccx> [--json]
```

Two modes:

- `--emit-profile` — self-calibration.  Loads a known-good trace,
  buckets it by `API_CALL` boundary, and writes a JSONL reference
  with observed counts + configurable tolerance.
- `--check` — regression gate.  Loads a reference JSONL + candidate
  trace, runs `golden_diff::diff`, prints a one-line verdict + per-step
  metric table, exits 1 if any step drifts outside its tolerance.

Tolerances live on the reference rows so the PyTorch-side reference
pipeline (forthcoming) controls strictness without flag explosion on
the pccx-lab side.

## Board bringup scripts (RTL repo)

Under `pccx-FPGA-NPU-LLM-kv260/scripts/board/` — independent of
pccx-lab, listed here for convenience:

| Script               | Purpose                                              |
|----------------------|------------------------------------------------------|
| `health_check.sh`    | SSH reachability + kernel + fpga_manager + free RAM. |
| `load_bitstream.sh`  | scp .bit to `/lib/firmware/`, then program PL.       |
| `run_inference.sh`   | Run `pccx_host` on board, optionally emit a trace.   |
| `capture_trace.sh`   | Pull a `.pccx` from the board back to the host.      |
| `bringup.sh`         | Orchestrates the above four in sequence.             |

## Surfaces not yet re-landed

Tracked for future re-landing in whichever crate makes the most sense
(likely a combination of `pccx-reports` and a new analytics crate):

- `--json` adjacently-tagged structured output.
- `--compare BASE CAND` regression gate with `--threshold-pct`.
- `--run-synth`, `--dry-run`, `--parse-only` Vivado wrapper
  (the RTL repo's `hw/vivado/build.sh` still works standalone).
- `--research-list` citation-registry exporter (see
  [research lineage](research.md) for why this is pending).
- `--explain <id>` long-form analyzer / strategy documentation.

## Exit codes

The four binaries follow the conventional Rust shape: `0` on success,
non-zero on runtime failure.  `pccx_golden_diff --check` exits `1`
when any row drifts outside its tolerance — the canonical CI regression
gate for now.

## Cite this page

```bibtex
@misc{pccx_lab_cli_2026,
  title        = {pccx-lab command-line binaries after the Phase 1 workspace split: pccx\_cli, generator, from\_xsim\_log, pccx\_golden\_diff},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/cli.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

Each binary's source lives under its owning crate at
<https://github.com/hkimw/pccx-lab>.
