# UI Panel Catalogue

_Refreshed 2026-04-29 to match pccx-lab HEAD. Panel files under `ui/src/`._

The pccx-lab UI (`ui/src/`) mounts purpose-specific panel components on
a flexlayout-react tab shell.  Each panel is lazy-imported from
`App.tsx` and communicates with the backend via `invoke(...)` calls or
Tauri events.

---

## Trace visualisation

### `Timeline.tsx` — `Timeline`

Receives the `trace-loaded` event and renders the `.pccx` flat buffer
onto a canvas.  When the event count exceeds `MMAP_EVENT_THRESHOLD`
(50,000) the panel automatically switches to the mmap streaming path
(`mmap_open_trace` → `mmap_viewport`), allowing large traces to render
without exhausting memory.  Viewport fetch calls during pan/zoom are
coalesced behind a 100 ms debounce and the `useRafScheduler` hook.
Rows are keyed by core ID; the horizontal axis is clock cycles.
`useCycleCursor` synchronises the cursor position across panels.

- Feed commands: `fetch_trace_payload`, `mmap_open_trace`, `mmap_viewport`
- Event: `trace-loaded` (Tauri emit)

### `FlameGraph.tsx` — `FlameGraph`

Bins the flat buffer into canonical layers (Fetch / Decode / MAC / DMA /
Retire) and renders them as a flame graph.  In compare mode the second
trace loaded via `load_pccx_alt` (the `trace_b` slot) is fetched with
`fetch_trace_payload_b` and rendered as a differential flame graph
following the Gregg 2018 IEEE SW §III-D contract.  The RAF scheduler
reduces 120 Hz mouse-move events to one paint per vsync.

- Feed commands: `fetch_trace_payload`, `fetch_trace_payload_b`
- Compare path: `load_pccx_alt`

### `WaveformViewer.tsx` — `WaveformViewer`

Multi-channel waveform viewer for IEEE 1364-2005 VCD files.  Consumes
the `WaveformDump` returned by `parse_vcd_file`; binary-search per
signal provides O(log n) value-at-tick lookup.  Radix display switches
between `bin` / `oct` / `hex` / `dec` / `ascii`.  The `useLiveWindow`
hook overlays live-window samples.  Cursor is synchronised with
Timeline via `useCycleCursor`.  The `export_vcd` command converts the
currently-cached `.pccx` trace into a VCD file.

- Feed commands: `parse_vcd_file`, `export_vcd`

### `MemoryDump.tsx` — `MemoryDump`

Renders pccx v002 KV260 memory-map access patterns (BRM, weight SRAM,
AXI HP ports) as a hex grid and access heatmap.  A precomputed 256-entry
HEX LUT (`HEX_LUT`) minimises per-cell string work.  `useCycleCursor`
highlights read/write accesses at the current cycle.  Access records are
parsed from the flat buffer rather than fetched via a dedicated command.

- Feed commands: `fetch_trace_payload` (indirect)

---

## Analysis

### `Roofline.tsx` — `Roofline`

ECharts-based roofline chart.  Renders both the single-tier
`RooflinePoint` from `analyze_roofline` and the multi-tier
`RooflineBand` list from `analyze_roofline_hierarchical` (Cache-Aware
Roofline — Ilic 2014 DOI 10.1109/L-CA.2013.6, Yang 2020
arXiv:2009.02449).  Each memory tier is drawn as a dashed ceiling plus
a trajectory segment showing where the workload dwells across the pccx
memory hierarchy.  `useVisibilityGate` + `useRafScheduler` pause the
ECharts instance when the tab is hidden.

- Feed commands: `analyze_roofline`, `analyze_roofline_hierarchical`

### `RooflineCard.tsx` — `RooflineCard`

Compact roofline summary card embedded inside `VerificationSuite.tsx`.
Consumes the `RooflinePoint` from `analyze_roofline` and displays
arithmetic intensity, achieved GOPS, and the compute/memory-bound
verdict as single-line badges.  Degrades gracefully to a warning banner
in browser-only builds where the Tauri IPC bridge is absent.

- Feed commands: `analyze_roofline`

### `BottleneckCard.tsx` — `BottleneckCard`

Bottleneck summary card embedded inside `VerificationSuite.tsx`.
Consumes the `BottleneckInterval` array from `detect_bottlenecks`
and renders DMA read / write / systolic stall / barrier-sync intervals
as proportion bars.

- Feed commands: `detect_bottlenecks`

### `OccupancyCalculator.tsx` — `OccupancyCalculator`

Takes MAC array size (N×N, range 4–16), activation SRAM, weight SRAM,
pipeline depth, and DMA channel count as parameters and computes
occupancy (%), INT4 TOPS throughput, and required memory bandwidth in
real time against the KV260 PL fabric at 300 MHz.  Entirely frontend
arithmetic; no Tauri commands.

- Feed commands: none (independent calculator)

### `PipelineDiagram.tsx` — `PipelineDiagram`

Renders the nine-stage pccx pipeline (Fetch → Decode → Dispatch → MAC →
Accumulate → Activation → DMA_Write / DMA_Read_Weights / DMA_Read_Acts)
as an SVG flow diagram.  Each stage visualises `utilization` (0.0–1.0)
by colour and `stalled` state with a red border.  Clicking a stage opens
a side panel of detailed metrics.  The `useLiveWindow` hook drives
live stall-state updates.

- Feed commands: `fetch_live_window` (via hook)

### `MetricTree.tsx` — `MetricTree`

Hierarchical metric-tree inspector with collapsible root groups
(throughput, memory, pipeline, verification).  Leaf nodes carry unit,
range, and warn/error thresholds; badge colour flips when the value
crosses a threshold.  Does not consume trace data directly; metric
values are injected via props from the parent (VerificationSuite or
App).

- Feed commands: none (props injection)

---

## Hardware view

### `HardwareVisualizer.tsx` — `HardwareVisualizer`

ELK.js auto-layout block diagram of the pccx v002 KV260 module hierarchy
(reflecting `hw/rtl/` structure).  Modules are colour-coded by kind
(`ctrl` / `mat` / `vec` / `sfu` / `mem` / `bus` / `io`); clicking a
module shows its port list and RTL path.  `step_to_cycle` supplies the
register and MAC-array state at the cursor cycle so active modules are
highlighted.  An ECharts mini-chart overlays per-module utilisation.
`useRafScheduler` + `useVisibilityGate` suspend rendering when the tab
is hidden.

- Feed commands: `step_to_cycle`, `analyze_roofline`, `fetch_trace_payload`

### `CanvasView.tsx` — `CanvasView`

Three.js instanced-mesh 3D heatmap of the 32×32 MAC array.  Each cell
maps a [0,1] utilisation value to an HSL colour (blue=idle, green=active,
red=hot).  The `ResourceHeatmap` JSON returned by `synth_heatmap` is
uploaded to the instanced colour buffer, minimising GPU draw calls.
`useVisibilityGate` halts the Three.js animation loop when the tab is
hidden.

- Feed commands: `synth_heatmap`

### `SynthStatusCard.tsx` — `SynthStatusCard`

Parses Vivado `report_utilization` + `report_timing_summary` output and
displays LUT / FF / DSP / BRAM usage counts and WNS/TNS slack as a card.
Requires at least one of `load_synth_report` (utilisation+timing) or
`load_timing_report` (timing only) to render.  Timing-met renders a
green badge; timing-not-met renders red.

- Feed commands: `load_synth_report`, `load_timing_report`, `synth_heatmap`

### `NodeEditor.tsx` — `NodeEditor`

React Flow (`@xyflow/react`) visual node editor.  Provides a
drag-and-drop interactive canvas for connecting pccx pipeline stages,
with custom node types (compute, memory, I/O, sequencer).  Not currently
wired to trace commands; receives node-graph state via props from
ScenarioFlow or App.

- Feed commands: none (graph editor)

---

## Verification / reporting

### `VerificationSuite.tsx` — `VerificationSuite`

Container panel that unifies the verification workflow under five tabs
(ISA / API / UVM / Synth / Golden).  Calls `run_verification` to invoke
`hw/sim/run_verification.sh` and parses `PASS`/`FAIL` lines into a
per-testbench result table.  `merge_coverage` merges xsim coverage JSONL
files; the resulting bin-hit table renders via `@tanstack/react-virtual`.
Embeds `SynthStatusCard`, `VerificationRunner`, `RooflineCard`, and
`BottleneckCard` as sub-components.

- Feed commands: `run_verification`, `merge_coverage`, `list_api_calls`,
  `validate_isa_trace`

### `VerificationRunner.tsx` — `VerificationRunner`, `GoldenDiffCard`, `SanitizeCard`

Three components embedded inside `VerificationSuite`.

- `VerificationRunner`: renders `run_verification` output as a
  testbench-row table; clicking an individual `.pccx` path loads it into
  the Timeline.
- `GoldenDiffCard`: calls `verify_golden_diff` to compare a candidate
  trace against a reference JSONL, then forwards the `verify_report`
  Markdown output to DiffView.
- `SanitizeCard`: calls `verify_sanitize` to clean input content (NUL
  removal, BOM/CRLF normalisation, trailing-comma forgiveness) and
  displays the list of fixups applied.

- Feed commands: `run_verification`, `verify_golden_diff`, `verify_report`,
  `verify_sanitize`

### `DiffView.tsx` — `DiffView`

Side-by-side text diff viewer.  Computes a line-level Myers diff
internally without a library dependency.  `@tanstack/react-virtual`
handles large files.  Rows are classified as `equal` / `added` /
`removed` / `modified` and colour-coded accordingly.  `GoldenDiffCard`
forwards `verify_golden_diff` results to this component.

- Feed commands: none (string injection from parent)

### `ReportBuilder.tsx` — `ReportBuilder`

Section-selection UI that enables/disables report sections (executive
summary, methodology, hardware configuration, timeline analysis, core
utilisation, bottleneck analysis, roofline, per-kernel breakdown) and
calls `generate_markdown_report` (Markdown) or `generate_report` (HTML)
to produce the assembled report.  Uses `useLiveWindow` to populate
section previews with live-window samples.

- Feed commands: `generate_markdown_report`, `generate_report`

### `ReportGenerator.tsx` — `ReportGenerator`

Minimal Radix UI Dialog trigger component.  Calls `generate_report` to
request a report for the currently-cached trace and shows a loading
spinner while the command runs.

- Feed commands: `generate_report`

### `TestbenchAuthor.tsx` — `TestbenchAuthor`

Cross-level authoring tool that displays an ISA instruction sequence in
three synchronised views: ISA assembly, API TOML, and SystemVerilog UVM
sequence.  Editing at the ISA or API level regenerates the SV pane
(reverse direction not implemented).  `generate_uvm_sequence_cmd`
produces SV UVM sequence stubs for named strategies (`l2_prefetch`,
`barrier_reduction`).

- Feed commands: `generate_uvm_sequence_cmd`, `list_uvm_strategies`

---

## Editing / support

### `CodeEditor.tsx` — `CodeEditor`

Monaco (VSCode editor engine) SystemVerilog source editor.  Applies SV
highlighting via the Monarch grammar in `monarch_sv.ts`.  Four LSP
commands — `sv_completions`, `lsp_hover`, `lsp_complete`,
`lsp_diagnostics` — are wired to Monaco's `registerCompletionItemProvider`,
`registerHoverProvider`, and `setModelMarkers` APIs respectively.
File I/O uses `read_text_file` / `write_text_file`.  Static analysis
views use `parse_sv_file`, `generate_block_diagram`, `generate_fsm_diagram`,
`generate_module_detail`, and `generate_sv_docs`.

- Feed commands: `sv_completions`, `lsp_hover`, `lsp_complete`,
  `lsp_diagnostics`, `read_text_file`, `write_text_file`,
  `parse_sv_file`, `generate_block_diagram`, `generate_fsm_diagram`,
  `generate_module_detail`, `generate_sv_docs`

### `ScenarioFlow.tsx` — `ScenarioFlow`

React Flow-based ISA execution scenario visualiser.  Renders ISA events
(cycle / op / body / unit) and data-move edges as a flow graph.
i18n-aware.  Does not invoke Tauri commands directly; receives scenario
data via props or local state.

- Feed commands: none (props or local state)

### `ExtensionManager.tsx` — `ExtensionManager`

Calls `get_extensions` to retrieve the `ai_copilot` extension list and
presents it as a category-grouped card grid (Local LLM, Hardware
Acceleration, Cloud Bridge, Analysis Plugins, Export Plugins).  The
install-progress UI exists; the actual download logic is currently a
stub.

- Feed commands: `get_extensions`

### `BottomPanel.tsx` — `BottomPanel`

Dockable bottom/side panel with Terminal Log, Live Activity, and Info
tabs.  `useLiveWindow` polls at 2 Hz and appends MAC/DMA/stall activity
to the log stream.  Log rows (22 px fixed height) render via
`@tanstack/react-virtual`.  The `dock` prop (`left` / `right` /
`bottom`) switches the panel's placement direction.

- Feed commands: `fetch_live_window` (via hook)

### `MainToolbar.tsx` — `MainToolbar`

Top toolbar exposing play / pause / stop / step / refresh / layers /
debug actions as 14 px icon buttons.  i18n-aware.  Does not call Tauri
commands directly; delegates all events to `App.tsx` via the `onAction`
callback.

- Feed commands: none (App.tsx delegation)

### `MenuBar.tsx` — `MenuBar`

Native-style menu bar with File / View / Analyze / Tools / Help menus.
File actions include opening `.pccx` (`Ctrl+O`), opening VCD
(`Ctrl+Shift+O`), saving sessions, exporting the flat buffer, and
generating a trace.  View actions include theme switching, panel
visibility, and entering the extension manager.  All actions delegate to
`App.tsx` via `onAction`.

- Feed commands: none (App.tsx delegation)

### `StatusBar.tsx` — `StatusBar`

Bottom status bar.  Displays trace-load state, total cycle count, core
count, the license string, and the active tab name.  In debug mode an
rAF frame counter exposes the current FPS.  `get_license_info` is called
at App level and passed as the `license` prop.

- Feed commands: none (props)

### `FileTree.tsx` — `FileTree`

Renders the `FileNode` tree returned by `read_file_tree` as an Explorer
sidebar.  Supports directory collapse/expand, per-type icons (SV, TOML,
JSON, binary, etc.), and an `onFileOpen` callback.  Entries that fail to
read (permissions, broken symlinks) are silently skipped.

- Feed commands: `read_file_tree`

---

## Cite this page

```bibtex
@misc{pccx_lab_panels_2026,
  title        = {pccx-lab UI panel catalogue: trace visualisation, analysis,
                  hardware view, verification, and editing components},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/panels.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

Panel sources live at
<https://github.com/hkimw/pccx-lab/tree/main/ui/src/>.
