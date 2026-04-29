# Tauri IPC Contract

_Refreshed 2026-04-29 to match pccx-lab HEAD. Sources:
`ui/src-tauri/src/lib.rs`, `crates/schema/src/lib.rs`._

The pccx-lab frontend and Rust backend communicate via the Tauri v2
`invoke` mechanism.  All commands are registered in the
`tauri::generate_handler![]` list inside `ui/src-tauri/src/lib.rs`.
The full catalogue of 48 registered commands follows.

---

## Command catalogue

### Load / trace

| Command | Args | Return | Purpose |
|---|---|---|---|
| `load_pccx` | `path: &str` | `Result<PccxHeader, String>` | Parse a `.pccx` file, cache the trace and flat buffer in AppState, emit `trace-loaded` on success. |
| `load_pccx_alt` | `path: String` | `Result<PccxHeader, String>` | Load a second trace into the `trace_b` slot for FlameGraph differential comparison.  Does not touch the primary trace or flat buffer. |
| `fetch_trace_payload` | — | `Result<Vec<u8>, String>` | Return the cached 24-byte struct-array flat buffer for zero-copy TypedArray mapping on the JS side. |
| `fetch_trace_payload_b` | — | `Result<Vec<u8>, String>` | Return the flat buffer for `trace_b`.  Errors if `load_pccx_alt` has not been called. |
| `list_pccx_traces` | `repo_path: String` | `Result<Vec<TraceEntry>, String>` | Enumerate `.pccx` files under the RTL repo's `hw/sim/work/<tb>/` tree. |

### mmap streaming (large traces)

| Command | Args | Return | Purpose |
|---|---|---|---|
| `mmap_open_trace` | `path: &str` | `Result<MmapTraceInfo, String>` | Open a `.pccx` file via memory-mapping and store the `MmapTrace` handle in AppState.  Returns header metadata and event count. |
| `mmap_viewport` | `start_cycle: u64`, `end_cycle: u64`, `generation_id: u32` | `Result<MmapViewportResponse, String>` | Return events overlapping `[start_cycle, end_cycle)`.  Echoes `generation_id` for stale-discard on the frontend. |
| `mmap_event_count` | — | `Result<usize, String>` | Return the total event count of the mmap trace. |
| `mmap_tile` | `offset: usize`, `count: usize` | `Result<Vec<u8>, String>` | Return a raw byte slice from the mmap payload for zero-copy TypedArray transfer. |

### Analytics

| Command | Args | Return | Purpose |
|---|---|---|---|
| `analyze_roofline` | — | `Result<RooflinePoint, String>` | Run roofline analysis on the cached trace.  Returns a single-tier result. |
| `analyze_roofline_hierarchical` | — | `Result<Vec<RooflineBand>, String>` | Return one `RooflineBand` per memory tier (Ilic 2014 CARM DOI 10.1109/L-CA.2013.6). |
| `detect_bottlenecks` | `window_cycles: Option<u64>`, `threshold: Option<f64>` | `Result<Vec<BottleneckInterval>, String>` | Sliding-window bottleneck detection.  Defaults: 256 cycles / 0.5 threshold. |
| `get_core_utilisation` | — | `Result<serde_json::Value, String>` | Return per-core MAC utilisation percentages, total cycles, total microseconds, and peak TOPS as JSON. |
| `fetch_live_window` | `window_cycles: Option<u64>` | `Result<Vec<LiveSample>, String>` | Reduce the cached trace into a `LiveSample` ring.  Returns an empty Vec when no trace is loaded. |
| `step_to_cycle` | `cycle: u64` | `Result<RegisterSnapshot, String>` | Return the deterministic `RegisterSnapshot` for the requested cycle.  Returns an empty snapshot when no trace is loaded. |
| `compress_trace_context` | — | `Result<String, String>` | Compress the trace into an LLM-friendly context string via `ai_copilot::compress_context`. |

### Reports

| Command | Args | Return | Purpose |
|---|---|---|---|
| `generate_report` | `format: String` | `Result<String, String>` | Render a trace-derived report.  `format` must be `"markdown"` or `"html"`. |
| `generate_report_custom` | `title: String`, `sections: Vec<SectionInput>`, `format: String` | `Result<String, String>` | Build a report from caller-supplied sections and render it. |
| `generate_markdown_report` | `utilization_path: String`, `timing_path: String` | `Result<String, String>` | Render a Markdown report.  Both paths may be empty to omit the synth section. |

### Verification

| Command | Args | Return | Purpose |
|---|---|---|---|
| `run_verification` | `repo_path: String` | `Result<VerificationSummary, String>` | Spawn `hw/sim/run_verification.sh`, parse `PASS`/`FAIL` lines, return structured summary including synth timing status. |
| `merge_coverage` | `runs: Vec<String>` | `Result<MergedCoverage, String>` | Merge multiple JSONL coverage-run files.  Empty `runs` returns an empty merge. |
| `verify_sanitize` | `content: String` | `SanitizeResult` | Sanitise input (NUL removal, BOM/CRLF normalisation, trailing-comma forgiveness).  Never fails. |
| `verify_golden_diff` | `expected_path: String`, `actual_path: String` | `Result<GoldenDiffReport, String>` | Compare a candidate `.pccx` trace against a reference JSONL profile. |
| `verify_report` | `report: GoldenDiffReport` | `String` | Render a `GoldenDiffReport` as a Markdown summary. |
| `validate_isa_trace` | `path: String` | `Result<Vec<IsaResult>, String>` | Parse a Spike `--log-commits` style ISA commit log and return one `IsaResult` per retired instruction. |
| `list_api_calls` | — | `Result<Vec<ApiCall>, String>` | Enumerate `uca_*` driver-surface calls from `API_CALL` events in the cached trace.  Returns empty Vec when no trace is loaded. |

### Synthesis / hardware

| Command | Args | Return | Purpose |
|---|---|---|---|
| `load_synth_report` | `utilization_path: String`, `timing_path: String` | `Result<SynthReport, String>` | Parse Vivado `report_utilization` + `report_timing_summary`. |
| `load_timing_report` | `path: String` | `Result<TimingReport, String>` | Parse a Vivado timing-summary text file.  Returns per-clock WNS/TNS/period. |
| `synth_heatmap` | `rows: u32`, `cols: u32` | `Result<String, String>` | Return a `ResourceHeatmap` JSON for the given grid dimensions.  Uses representative KV260 ZU5EV mock figures. |

### LSP (SystemVerilog)

| Command | Args | Return | Purpose |
|---|---|---|---|
| `sv_completions` | — | `Vec<serde_json::Value>` | Return the full SV keyword completion set from `SvKeywordProvider`.  Called once on editor mount. |
| `lsp_hover` | `uri: String`, `line: u32`, `character: u32`, `source: String` | `Result<Option<serde_json::Value>, String>` | Position-aware hover info.  Returns `null` when nothing to show. |
| `lsp_complete` | `uri: String`, `line: u32`, `character: u32`, `source: String` | `Result<Vec<serde_json::Value>, String>` | Position-aware completions combining keyword and user-defined symbol items. |
| `lsp_diagnostics` | `uri: String`, `source: String` | `Result<Vec<serde_json::Value>, String>` | SV source diagnostics mapped to Monaco MarkerSeverity integers (8/4/2/1). |
| `parse_sv_file` | `path: String` | `Result<serde_json::Value, String>` | Parse an SV file and return the structured result as JSON. |
| `generate_block_diagram` | `sv_source: String`, `file_path: String` | `Result<String, String>` | Generate a Mermaid block diagram from parsed module connections. |
| `generate_fsm_diagram` | `sv_source: String`, `file_path: String` | `Result<Vec<FsmDiagramResult>, String>` | Return one Mermaid state diagram per extracted FSM plus dead-state lists. |
| `generate_module_detail` | `sv_source: String`, `module_name: String` | `Result<String, String>` | Return a Mermaid subgraph diagram for the named module. |
| `generate_sv_docs` | `path: String` | `Result<String, String>` | Generate module documentation from SV source. |

### AI copilot

| Command | Args | Return | Purpose |
|---|---|---|---|
| `get_extensions` | — | `Vec<Extension>` | Return the available extension list from `ai_copilot`. |
| `generate_uvm_sequence_cmd` | `strategy: String` | `String` | Generate a SV UVM sequence stub for the named strategy (`l2_prefetch`, `barrier_reduction`). |
| `list_uvm_strategies` | — | `Vec<String>` | Return the strategy names accepted by the UVM sequence generator. |

### File system / utility

| Command | Args | Return | Purpose |
|---|---|---|---|
| `read_file_tree` | `root: String`, `depth: u32` | `Result<Vec<FileNode>, String>` | Recursively read a directory tree from `root` up to `depth` levels. |
| `read_text_file` | `path: String` | `Result<String, String>` | Read a text file for the Monaco editor buffer. |
| `write_text_file` | `path: String`, `content: String` | `Result<(), String>` | Write a text file (Ctrl+S save). |
| `parse_vcd_file` | `path: String` | `Result<WaveformDump, String>` | Parse an IEEE 1364-2005 VCD file.  Returns signal metadata plus the full value-change stream. |
| `export_vcd` | `output_path: String` | `Result<String, String>` | Write the cached trace as a VCD file.  Returns the absolute path. |
| `export_chrome_trace` | `output_path: String` | `Result<String, String>` | Write the cached trace as a Google Trace Event Format JSON. |
| `get_license_info` | — | `String` | Return the Apache-2.0 license string for the status bar. |

---

## DTO schema

`crates/schema/src/lib.rs` defines the shared Rust-TypeScript wire DTOs.
All types derive `ts-rs`'s `#[derive(TS)]` + `#[ts(export)]`; TypeScript
interfaces are auto-generated under `cargo test`.

```rust
// crates/schema/src/lib.rs (excerpt)

/// Frontend -> backend: request a window of trace data.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct ViewportRequest {
    pub start_cycle:  u64,
    pub end_cycle:    u64,
    pub generation_id: u32,
}

/// A single event inside a viewport tile.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct TileEvent {
    pub core_id:     u32,
    pub start_cycle: u64,
    pub duration:    u64,
    pub type_id:     u32,
}

/// Backend -> frontend: a batch of events for one viewport generation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct ViewportTile {
    pub events:        Vec<TileEvent>,
    pub generation_id: u32,
    pub total_events:  u64,
}

/// Summary of a loaded trace file.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct TraceInfo {
    pub total_cycles: u64,
    pub total_events: u64,
    pub num_cores:    u32,
    pub encoding:     String,
}
```

The `MmapViewportResponse` (defined inline in `lib.rs`) also carries
`generation_id: u32`, which `mmap_viewport` echoes:

```rust
#[derive(serde::Serialize)]
struct MmapViewportResponse {
    events:        Vec<NpuEvent>,
    generation_id: u32,
}
```

The schema crate carries no dependency on `ui/`, `uvm_bridge/`, or
`ai_copilot/`.  Wire DTOs are thin data carriers with no domain logic.

---

## Boundary rules

Rules derived from `CLAUDE.md §5.5` and the `lib.rs` implementation.

### u64 fields

`u64` fields that may exceed 2^53 must be serialised as `String` over
IPC; passing them as JSON numbers loses precision in JavaScript.
Fields in this category include `TileEvent.start_cycle`,
`TileEvent.duration`, `TraceInfo.total_cycles`, and
`TraceInfo.total_events`.  JS code deserialises these string fields
via `BigInt` or a precision-preserving library before arithmetic use.

### generation_id

Every async viewport response must carry a `generation_id: u32`.  The
frontend compares the returned ID against the current generation on
receipt and discards stale responses.  This prevents a slow IPC
round-trip from overwriting newer state during rapid scroll or zoom.

Both `ViewportRequest` and `MmapViewportResponse` carry the field:

```rust
pub struct ViewportRequest {
    pub start_cycle:  u64,
    pub end_cycle:    u64,
    pub generation_id: u32,   // caller-supplied
}

struct MmapViewportResponse {
    events:        Vec<NpuEvent>,
    generation_id: u32,       // echoed back verbatim
}
```

### Large binary

Large binary data is represented as `Vec<u8>` on the Rust side and
mapped to `TypedArray` on the JS side.  `fetch_trace_payload`,
`fetch_trace_payload_b`, and `mmap_tile` all follow this pattern,
serialising a 24-byte struct array or a raw mmap slice respectively:

```rust
#[tauri::command]
async fn fetch_trace_payload(state: State<'_, AppState>) -> Result<Vec<u8>, String> {
    let buf = state.trace_flat_buffer.lock().unwrap().clone();
    Ok(buf)
}
```

The JS receiver wraps the returned value in a `Uint8Array` or
`Float32Array` view and accesses struct fields via byte offsets.

### Raw trace data never crosses IPC

Raw trace data (`NpuTrace`, full `NpuEvent` arrays) does not cross the
IPC boundary directly.  Only the flat buffer returned by
`fetch_trace_payload`, tiled slices from `mmap_viewport`, and
aggregated results from commands such as `analyze_roofline` may cross.
This is a design decision stated in `CLAUDE.md §5.5` and motivated in
`docs/design/architecture_adoption.md` Section 4.

---

## Related

- [Panel catalogue](panels.md) — UI panels that consume each command.
- [CLI reference](cli.md) — headless binaries that use the same pccx-core
  analytics functions.
- [Analyzer API](analyzer_api.md) — the primitive by which backend crates
  register analysis logic as plugins.

---

## Cite this page

```bibtex
@misc{pccx_lab_ipc_2026,
  title        = {pccx-lab Tauri IPC contract: 48 commands, DTO schema,
                  and boundary rules},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/ipc.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

Command source is at
<https://github.com/hkimw/pccx-lab/blob/main/ui/src-tauri/src/lib.rs>;
DTO schema is at
<https://github.com/hkimw/pccx-lab/blob/main/crates/schema/src/lib.rs>.
