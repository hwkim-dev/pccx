---
myst:
  html_meta:
    description lang=en: |
      pccx-core public module reference — live_window, mmap_reader,
      step_snapshot, api_ring, chrome_trace, isa_replay, cycle_estimator,
      vivado_timing, coverage, vcd/vcd_writer, pccx_format.
---

# pccx-core Module Reference

`crates/core/` (`pccx-core`) is the single sink of the workspace
dependency graph. Every other crate — UI, reports, verification, lsp —
imports its public types from here. This page documents the role and
top-level public items of each module declared with `pub mod` in
`lib.rs`.

Implementation files live at `pccx-lab/crates/core/src/<module>.rs`.

```{contents} On this page
:depth: 2
:backlinks: none
```

## live_window

Live-telemetry ring buffer. Modelled on the `perf_event_open(2)` mmap
head/tail ring and the Perfetto SHM producer/consumer API, it bins real
`NpuTrace` events into cycle windows. No synthetic fallbacks: an empty
trace yields an empty snapshot (Yuan OSDI 2014 loud-fallback contract).
Each `LiveSample` carries three utilisation ratios — `mac_util`,
`dma_bw`, `stall_pct` — and a monotonic `ts_ns` derived from
`start_cycle` at the pccx v002 reference clock (200 MHz, 5 ns/cycle).
The Tauri `fetch_live_window` IPC command consumes this module to feed
the frontend BottomPanel, PerfChart, and Roofline views.

**Public items**: `LiveSample`, `LiveWindow`

## mmap_reader

Zero-copy `.pccx` reader for production-scale (100 MB+) traces. Opens
the file with `memmap2`, parses only the fixed-size header at
construction time, and leaves the flat-buffer payload mapped but
untouched until a viewport or tile query arrives. This bypasses the
multi-second heap allocation that `PccxFile::read` incurs on large
traces. Only the `flatbuf` encoding is supported (24-byte fixed-stride
events); a bincode payload (variable-length) is rejected with an error
because binary search cannot be applied to it. Events in the flat
buffer must be sorted by `start_cycle` ascending for viewport binary
search to produce correct results — write files intended for
`MmapTrace` using `NpuTrace::to_flat_buffer_sorted`.

**Public items**: `MmapTrace`

## step_snapshot

Single-cycle register and MAC-array state snapshot. Given a cached
`NpuTrace` and a target cycle, it reduces the flat event stream to a
`RegisterSnapshot`: per-core active event class and remaining span
cycles, plus aggregate MAC/DMA/stall/barrier counts across the whole
NPU at that exact cycle. Cycles outside `[0, trace.total_cycles]`
return a deterministic empty snapshot instead of an error, so the UI
renders "idle" without error handling. When two events on the same core
overlap, the later `start_cycle` wins (latest-dispatch rule). Zero-
duration events fire only on their exact `start_cycle` and never project
into the next cycle (IEEE 1364-2005 §Annex 18 VCD convention).

**Public items**: `step_to_cycle`, `CoreState`, `RegisterSnapshot`

## api_ring

API-integrity ring buffer that records every `uca_*` driver entry/exit
boundary. Following the CUPTI driver-trace pattern, it flushes the
aggregate p99 latency and drop count to a fixed-schema row vector that
the UI's API-Integrity panel renders. The ring is populated exclusively
from `API_CALL` events in the `.pccx` event stream — no synthetic
fallback. A trace that carries no `API_CALL` events returns an empty
`Vec` and logs a warning. The `list_api_calls` function provides the
consumer-facing surface.

**Public items**: `ApiCall`, `NS_PER_CYCLE` (constant: 5 ns/cycle @ 200 MHz)

## chrome_trace

Chromium Trace Event Format exporter. Serialises an `NpuTrace` to a
JSON array of Complete Events (`ph: "X"`) that opens directly in
`ui.perfetto.dev`, `chrome://tracing`, and any Perfetto proto importer.
Event categories map to `"mac"`, `"dma"`, `"stall"`, and `"sync"`;
timestamps are converted to integer microseconds using the pccx v002
reference clock (200 cycles = 1 µs). `pid` maps to the accelerator
instance; `tid` maps to `core_id`.

**Public items**: `write_chrome_trace`, `write_chrome_trace_to`

## isa_replay

ISA-level replay diff engine. Consumes a Spike `--log-commits` style
commit log and emits per-instruction (expected, actual) cycle pairs.
Expected cycle counts are looked up from an NPU latency table keyed by
mnemonic prefix; actual cycle counts are read from a `;cycles=<N>`
suffix on each log line. Lines without the suffix treat
`actual == expected` as PASS. Within ±10 % of expected is WARN; outside
is FAIL. Unknown mnemonics default to 1 cycle.

**Public items**: `IsaReplayEntry`, `IsaVerdict` (PASS/WARN/FAIL),
`replay_log`

## cycle_estimator

Cycle estimation engine for pre-RTL design-space exploration. Given a
`TileOperation` (tiled GEMM M/N/K/bytes_per_element) or
`AttentionOperation` (MQA/GQA parameters), it queries the
`HardwareModel` for MAC array dimensions, AXI bus configuration, and
BRAM layout to compute arithmetic cycles, DMA transfer cycles, and stall
penalties. Used for Roofline expected-value generation and DSE loops.

**Public items**: `CycleEstimator`, `TileOperation`

## vivado_timing

Parser for Vivado `report_timing_summary -quiet -no_header` text output.
Binds the UG906 section headers — "Design Timing Summary", "Clock
Summary", "Intra Clock Table", "Timing Details" — into a structured
`TimingReport`. The UI's SynthStatusCard consumes this parser in place
of the regex stub in `synth_report.rs`. Supported fields include WNS,
TNS, failing endpoints, and per-clock-domain period for the KV260 ZU5EV
fixture.

**Public items**: `parse_timing_report`, `parse_worst_endpoint`,
`TimingReport`, `ClockDomain`, `FailingPath`, `TimingParseError`

## coverage

UVM functional-coverage JSONL run-dump merger. Consumes per-run `.jsonl`
files and aggregates bin hit counts and cross tuples following
Accellera UCIS merge semantics (count-based bin summation across runs).
The `goal` field is optional; when absent, the largest goal seen across
all runs is carried forward (0 if none was ever supplied). The merged
result is rendered by the UI's VerificationSuite panel with groups below
their closure threshold highlighted.

**Public items**: `merge_coverage_jsonl`, `CovBin`, `CovGroup`,
`CrossTuple`, `MergedCoverage`, `CoverageError`

## vcd / vcd_writer

IEEE 1364 VCD reader/writer pair.

**vcd** — Delegates lexing to the `vcd` crate (MIT) and repackages the
output as a flat, serde-serialisable `WaveformDump`: `Vec<SignalMeta>`
from `$scope/$var` headers and `Vec<VcdChange>` from timestamp and
value-change lines. The UI consumes this via the `parse_vcd_file` Tauri
command; it binary-searches per signal for O(log n) value-at-tick
lookups.

**vcd_writer** — Generates a spec-legal VCD from an `NpuTrace` for
use in GTKWave, Surfer, Verdi, or the built-in Waveform panel. Emits
eight signals: `clk`, `rst_n`, `mac_busy`, `dma_rd`, `dma_wr`,
`stall`, `barrier`, `core_id`. Timescale 1 ns; IEEE 1364-2005 §18
compliant.

**Public items (vcd)**: `parse_vcd_file`, `WaveformDump`, `SignalMeta`,
`VcdChange`, `VcdError`

**Public items (vcd_writer)**: `write_vcd`, `write_vcd_to`

## pccx_format

Binary trace format codec for the `.pccx` container. File layout
(little-endian): magic `PCCX` (4 bytes) → major/minor version (u8
each) → 2 reserved bytes → JSON header length (u64) → UTF-8 JSON
header → binary payload. Current version: `MAJOR_VERSION = 0x01`,
`MINOR_VERSION = 0x01`. A major-version mismatch returns
`UnsupportedMajorVersion`. For the full format specification, see
{doc}`pccx-format`.

**Public items**: `PccxFile`, `PccxHeader`, `PccxError`, `ArchConfig`,
`TraceConfig`, `PayloadConfig`, `fnv1a_64`

## Cite This Page

```bibtex
@misc{pccx_lab_core_modules_2026,
  title        = {pccx-core module reference: public modules of the pccx-lab Rust core crate},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/core-modules.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
