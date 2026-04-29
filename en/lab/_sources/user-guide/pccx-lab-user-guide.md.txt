# pccx-lab User Guide

**Version**: pccx v002  
**Target Hardware**: Xilinx KV260 (ZU5EV)  
**Audience**: Hardware Engineers, RTL Designers, Verification Engineers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Interface Overview](#3-interface-overview)
4. [Core Analysis Views](#4-core-analysis-views)
   - [4.1 Timeline Analysis](#41-timeline-analysis)
   - [4.2 Flame Graph](#42-flame-graph)
   - [4.3 System Simulator](#43-system-simulator)
   - [4.4 Waveform Viewer](#44-waveform-viewer)
   - [4.5 Memory Dump](#45-memory-dump)
   - [4.6 Data Flow](#46-data-flow)
   - [4.7 Roofline Analysis](#47-roofline-analysis)
5. [Development Tools](#5-development-tools)
   - [5.1 SV Editor](#51-sv-editor)
   - [5.2 Testbench Author](#52-testbench-author)
   - [5.3 3D View](#53-3d-view)
6. [Verification Suite](#6-verification-suite)
7. [Report Generation](#7-report-generation)
8. [Scenario Flow](#8-scenario-flow)
9. [AI Copilot](#9-ai-copilot)
10. [Keyboard Shortcuts](#10-keyboard-shortcuts)
11. [Theme and Localization](#11-theme-and-localization)
12. [CLI Tools](#12-cli-tools)
13. [Architecture Reference](#13-architecture-reference)
- [Appendix A: .pccx File Format](#appendix-a-pccx-file-format)
- [Appendix B: Supported Event Types](#appendix-b-supported-event-types)

---

## 1. Introduction

pccx-lab is a Tauri v2 desktop application for NPU (Neural Processing Unit) architecture profiling, verification, and development. It consumes `.pccx` binary traces emitted by the pccx-FPGA-NPU-LLM-kv260 xsim testbench suite and presents them through an integrated analysis environment combining cycle-accurate timing visualization, hardware block diagram simulation, UVM-integrated verification, and AI-assisted RTL development.

The primary target hardware is the **Xilinx KV260 (ZU5EV)** FPGA platform running the pccx v002 systolic array architecture. pccx-lab serves as the single workbench for the full NPU development loop: trace ingestion, performance diagnosis, RTL editing, functional verification, and report generation.

### Key Capabilities

| Capability | Description |
|---|---|
| Cycle-accurate trace analysis | Multi-core event timeline with sub-cycle granularity |
| Hardware simulation | Interactive block diagram with module inspector and playback |
| RTL development | Monaco-based SystemVerilog editor with UVM template library |
| Verification integration | ISA validation, API integrity, UVM coverage, and synthesis status |
| Roofline analysis | Arithmetic intensity and memory-bound/compute-bound classification |
| 3D MAC array visualization | Real-time 32x32 utilization heat map |
| Report generation | Configurable PDF reports auto-populated from trace data |
| AI assistance | Context-aware bottleneck analysis and UVM sequence generation |

---

## 2. Getting Started

### 2.1 System Requirements

| Component | Requirement |
|---|---|
| Operating system | Ubuntu 24.04 LTS (primary); macOS and Windows are not officially supported |
| Rust toolchain | Stable, current edition (see `rust-toolchain.toml`) |
| Node.js | LTS release compatible with Vite 7 |
| Display | X11 session (Wayland compositing is not supported; see §2.4) |
| Hardware | KV260 (ZU5EV) for live trace generation; pre-recorded `.pccx` files may be loaded on any host |

### 2.2 Installation

Clone the repository and install both Rust and frontend dependencies:

```bash
# Install frontend dependencies
cd src/ui
npm install

# Build the desktop application (release mode)
cargo build --release
```

To launch the application in development mode with hot-reload:

```bash
cd src/ui
npm run tauri dev
```

### 2.3 First Launch

On first launch, pccx-lab opens to the Timeline view with no trace loaded. The status bar displays `No trace loaded`. To load a trace:

1. Select **File > Open Trace** from the menu bar.
2. Navigate to a `.pccx` file produced by the xsim testbench (`hw/sim/work/<tb>/<tb>.pccx`).
3. The Timeline, Flame Graph, and Roofline views populate automatically from the loaded trace data.

To connect to a live trace stream from a running simulation, use **Trace > Connect to Server** and provide the `pccx-server` host address (default port: 9400).

### 2.4 Linux Display Note

On Linux, pccx-lab sets `WEBKIT_DISABLE_DMABUF_RENDERER=1` and `GDK_BACKEND=x11` at startup to prevent a compositor freeze caused by the interaction between Three.js, Monaco, and WebKitGTK 2.50 DMA-BUF rendering. An active X11 session is required. Wayland-native sessions are not supported in the current release.

---

## 3. Interface Overview

![Timeline view — interface overview](images/01-timeline-overview.png)

The pccx-lab window is organized into the following regions:

### 3.1 Menu Bar

| Menu | Contents |
|---|---|
| File | Open Trace, Open VCD, Save, Export, Preferences |
| Edit | Undo, Redo, Find, Command Palette |
| View | Panel visibility toggles, theme, zoom |
| Trace | Connect to Server, Disconnect, Replay, Trace Settings |
| Analysis | Roofline, Bottleneck Report, Flame Graph |
| Verify | Run ISA Check, API Integrity, UVM Coverage |
| Run | Start, Pause, Stop, Step, Reload |
| Tools | IPC Benchmark, CLI Launcher, Telemetry |
| Window | Layout management, panel docking |
| Help | Documentation, About |

### 3.2 Main Toolbar

The toolbar beneath the menu bar provides quick access to simulation controls and global actions:

| Button | Function |
|---|---|
| Start | Begin simulation or trace replay |
| Pause | Pause at current cycle |
| Stop | Halt simulation and reset cycle counter |
| Step | Advance one clock cycle |
| Reload | Reload the current trace file from disk |
| Telemetry | Toggle live telemetry panel |
| Report | Open Report Builder |

### 3.3 Tab Bar

The tab bar provides access to 14 analysis views. Each tab corresponds to a distinct analysis or development surface. Views are described in detail in Sections 4 through 8.

### 3.4 Panel Docks

Three dockable panel positions are available: left dock, right dock, and bottom dock. The AI Copilot panel (Section 9) may be docked to any of these positions. The bottom dock hosts the Log, Console, and Live Telemetry sub-panels.

### 3.5 Status Bar

The status bar at the bottom of the window displays:

- Current trace status (loaded file path, or `No trace loaded`)
- Active view name
- Application version
- Current theme (Dark / Light)
- Active UI language (EN / 한)

### 3.6 Activity Bar

Two toggle buttons on the right edge of the window control the AI Copilot panel visibility and the Live Telemetry panel visibility.

---

## 4. Core Analysis Views

### 4.1 Timeline Analysis

![Timeline Analysis view](images/01-timeline-overview.png)

The Timeline view presents a cycle-accurate event timeline across all recorded cores. Each row corresponds to one core; each horizontal segment represents one recorded event, color-coded by type.

#### Event Color Coding

| Event Type | Color | Description |
|---|---|---|
| MAC_COMPUTE | Cyan | Systolic array active — matrix multiply in progress |
| DMA_READ | Green | DMA transfer from external memory to on-chip buffer |
| DMA_WRITE | Yellow | DMA transfer from on-chip buffer to external memory |
| SYSTOLIC_STALL | Purple | Systolic array pipeline stalled (data hazard or backpressure) |
| BARRIER_SYNC | Red | Cross-core synchronization barrier active |

#### Controls

| Control | Action |
|---|---|
| Fit All | Rescale the time axis to show the entire trace |
| Clear Markers | Remove all user-placed cycle markers |
| Go to Cycle | Jump the viewport to a specific cycle number |
| Filter | Toggle individual event types on or off |
| Snap to Cycle | Align the viewport origin to the nearest cycle boundary |

#### Navigation Shortcuts

| Input | Action |
|---|---|
| Ctrl+Scroll | Zoom the cycle axis in or out |
| Drag | Pan the viewport horizontally |
| Shift+Drag | Select a cycle range |
| Shift+Click | Place or remove a cycle marker |
| Arrow keys | Step to the next or previous event edge |
| Shift+Arrow | Step exactly one cycle forward or backward |

#### Trace Stats Panel

The Trace Stats panel (right side of the Timeline view) reports the following metrics for the loaded trace or the current visible window:

- **Total events**: count of all recorded events across all cores
- **Total cycles**: elapsed cycles from trace start to end
- **Avg duration**: mean event duration in cycles
- **Live rate**: event throughput when connected to a live trace stream

---

### 4.2 Flame Graph

![Flame Graph view](images/02-flamegraph.png)

The Flame Graph view presents a hierarchical performance breakdown derived from the loaded trace. Wider bars indicate longer cumulative time at a given call or execution stage. The depth axis represents the call hierarchy from top-level kernel dispatch down to individual operation types.

#### Features

**Find Bottleneck**: One-click analysis that identifies the single deepest, widest bar in the current flame graph and highlights its ancestors. The result is presented as a bottleneck report in the right panel, identifying the execution stage consuming the most cycles.

**Compare Run**: Loads a second `.pccx` file and renders an A/B differential flame graph. Segments that grew between runs are colored red; segments that shrank are colored blue. This facilitates regression analysis between optimization iterations.

---

### 4.3 System Simulator

![System Simulator view](images/03-system-simulator.png)

The System Simulator provides an interactive hardware model of the full pccx v002 KV260 ZU5EV module hierarchy.

#### Module Hierarchy Panel (Left)

The left panel lists all modules in the pccx v002 design hierarchy as a collapsible tree. Selecting a module in the tree highlights it in the block diagram and populates the Inspector panel.

#### Block Diagram (Center)

The center canvas renders the pccx v002 architecture as a data flow block diagram, with directed edges representing bus connections and data paths. Module color conveys real-time simulation state:

| Color | State |
|---|---|
| Blue | Active (busy, executing operations) |
| Red | Stalled (backpressure, data hazard, or pipeline stall) |
| Green | Done (operation complete, output valid) |
| Gray | Idle (no activity, waiting for stimulus) |

#### Inspector Panel (Right)

Selecting any module in the tree or block diagram populates the Inspector panel with the following information:

- **Module name**: RTL instance identifier
- **RTL path**: full hierarchical path within the design (`pccx_top.mat_core.…`)
- **Purpose**: description of the module's architectural role
- **Ports**: port list with direction, width, and current driven value
- **Activity timeline**: miniature timeline showing this module's event history within the current trace window
- **Sub-modules**: direct children in the hierarchy

#### Playback Controls

| Control | Action |
|---|---|
| Play / Pause | Begin or pause cycle-by-cycle simulation advance |
| Step | Advance one clock cycle |
| Speed | Multiplier for simulation playback rate |
| Cycle Counter | Displays current simulation cycle; accepts direct entry |

---

### 4.4 Waveform Viewer

The Waveform Viewer renders VCD (Value Change Dump) format signal waveforms. To open a waveform file, select **File > Open VCD** and choose a `.vcd` file produced by the xsim testbench or any compatible simulator.

Each signal occupies one row. Logic signals render as a two-level waveform; bus signals render with hex value annotations at each transition. The time axis is aligned to the Timeline view cycle scale when a `.pccx` trace is also loaded.

---

### 4.5 Memory Dump

The Memory Dump view provides direct inspection of DDR memory state captured within a trace. Addresses are displayed in the left column; contents are rendered in both hexadecimal and ASCII representation. Navigation controls accept a hex address for direct jump. Binary view mode displays raw bit patterns alongside the hex columns.

---

### 4.6 Data Flow

The Data Flow view provides a node-based graph editor for constructing and inspecting data transformation pipelines. Nodes represent operations or hardware modules; edges represent data dependencies. The interaction model follows a standard node editor: drag nodes to reposition, click edges to inspect signal properties, and use the toolbar to add or delete nodes.

---

### 4.7 Roofline Analysis

The Roofline view plots operations from the loaded trace on the standard roofline model: arithmetic intensity (operations per byte transferred) on the horizontal axis and achieved throughput (operations per second) on the vertical axis.

The roofline ceiling and memory bandwidth ridge point are derived from the KV260 ZU5EV hardware parameters. Each kernel or operation segment from the trace appears as a labeled data point. Points below the memory bandwidth line are classified as **memory-bound**; points approaching the compute ceiling are classified as **compute-bound**.

---

## 5. Development Tools

### 5.1 SV Editor

![SV Editor view](images/04-sv-editor.png)

The SV Editor provides a full-featured SystemVerilog development environment built on the Monaco editor (the same engine used in Visual Studio Code), with a custom Monarch-based syntax grammar for SystemVerilog.

#### Features

**Syntax Highlighting**: Keywords, module declarations, always blocks, port lists, macro invocations, and UVM macros are highlighted with the project's JetBrains Mono font.

**UVM Template Library**: Six ready-to-insert templates are available from the toolbar:

| Template | Generated Artifact |
|---|---|
| Driver | UVM driver class skeleton with run_phase and seq_item handling |
| Monitor | UVM monitor class with analysis port and transaction capture |
| Environment | UVM environment class with agent and scoreboard instantiation |
| DMA Test Sequence | Parameterized DMA transfer sequence with address and length fields |
| NPU Interface | SystemVerilog interface definition for NPU bus connections |
| Scoreboard | UVM scoreboard with expected/actual comparison logic |

**Ask AI**: Opens the AI Copilot panel pre-focused on code generation for the current file context. The copilot receives the visible editor content as context.

**Run SV Test**: Invokes the integrated simulation console directly from the editor. Compilation errors are reported inline as Monaco editor markers.

**File Management**: Files open via **File > Open** or by drag-and-drop onto the editor surface. Unsaved changes are indicated by a dot next to the filename in the tab. **Ctrl+S** saves the current file.

---

### 5.2 Testbench Author

The Testbench Author view generates UVM testbench scaffolding from a module definition. Provide the top-level DUT port list and select the desired verification components; the tool produces a complete directory structure including the agent, sequences, environment, and test class, ready for integration with the xsim flow in `pccx-FPGA-NPU-LLM-kv260`.

---

### 5.3 3D View

![3D View — 32x32 MAC array](images/05-3d-view.png)

The 3D View renders the 32x32 MAC (Multiply-Accumulate) array of the pccx v002 systolic core as an interactive three-dimensional grid using Three.js.

#### Visualization

Each cell in the grid corresponds to one Processing Element (PE). Cell color encodes real-time utilization derived from the loaded trace:

- **Bright cyan / pulsing**: high utilization, active MAC operation in progress
- **Dark blue**: PE present but idle in the current cycle window
- **No emission**: stalled or inactive

The pulse animation runs at the trace playback rate, providing an immediate visual impression of spatial utilization distribution across the array.

#### Navigation

| Input | Action |
|---|---|
| Mouse drag | Orbit the camera around the array |
| Scroll | Zoom in or out |
| Right-click drag | Pan the camera laterally |

---

## 6. Verification Suite

![Verification Suite view](images/06-verification.png)

The Verification Suite consolidates four verification disciplines into a single tabbed view.

### ISA Dashboard

The ISA Dashboard presents a cycle-accurate validation matrix for the pccx ISA. Each instruction type executed within the loaded trace is cross-referenced against the specification. The matrix shows pass, fail, or not-exercised status for each opcode. Clicking a failing cell opens the specific event in the Timeline view at the cycle where the discrepancy occurred.

### API Integrity

The API Integrity tab verifies interface contracts between modules. Each declared bus protocol (AXI-Lite command interface, HP port data paths, ACP latency-critical paths) is checked for handshake correctness, valid/ready alignment, and out-of-range address detection. Violations are listed with cycle numbers and signal values.

### UVM Coverage

The UVM Coverage tab imports functional coverage data from `.ucdb` or compatible coverage database files and renders a hierarchy of cover groups with hit percentages. Groups that have not reached the closure threshold are highlighted. Coverage data may also be streamed from a live simulation session.

### Synth Status

The Synth Status tab displays post-synthesis resource utilization and timing analysis data from Vivado implementation reports. Supported metrics include LUT count, DSP48E2 utilization, BRAM/URAM utilization, FF count, and worst-case setup slack (WNS). Reports are imported via **Verify > Import Synth Report**.

---

## 7. Report Generation

![Report Builder view](images/08-report-builder.png)

The Report Builder generates structured PDF reports from the loaded trace and verification data. Reports are auto-populated; all sections draw their data directly from the active pccx-lab session.

### Available Sections

| Section | Content |
|---|---|
| Executive Summary | High-level performance metrics, pass/fail status, key findings |
| Methodology | Trace acquisition method, simulation configuration, tool versions |
| Hardware Configuration | Target device, clock frequencies, memory topology |
| Timeline Analysis | Annotated timeline screenshots with event statistics |
| Core Utilisation | Per-core utilization breakdown and idle-cycle analysis |
| Bottleneck Analysis | Top bottlenecks identified by the Flame Graph engine |
| Roofline Analysis | Roofline chart with kernel operating points |
| Per-Kernel Breakdown | Individual cycle counts and utilization for each kernel |
| Verification Status | ISA Dashboard and API Integrity summary |
| Glossary | Project-standard terminology definitions |

Sections are enabled or disabled using the checkboxes in the Report Builder left panel. The section order is adjustable via drag-and-drop.

### Output

Select **File > Export Report** or click the **Generate** button to produce the PDF. Output resolution is 300 DPI. The output path defaults to the directory of the loaded trace file.

---

## 8. Scenario Flow

![Scenario Flow view](images/07-scenario-flow.png)

The Scenario Flow view renders the transformer decode step as a directed graph of execution sub-stages, built with React Flow. Each node represents one sub-stage of the decode pipeline; directed edges represent data dependencies and execution order.

The default scenario displays the **Gemma 3N E4B pccx v002** decode step with the following sub-stages:

| Sub-stage | Description |
|---|---|
| embed_lookup | Token embedding table lookup |
| Attention | Multi-head attention computation (Q, K, V projections and score) |
| FFN+LAuReL | Feed-forward network with LAuReL regularization |
| lm_head | Language model head projection to vocabulary logits |

### Per-Stage Profiling

Each node displays its cycle count and a criticality classification:

| Classification | Meaning |
|---|---|
| FAST | Sub-stage duration is within expected bounds |
| MEDIUM | Sub-stage duration is moderately elevated; monitor across runs |
| SLOW | Sub-stage duration is above threshold; optimization recommended |
| CRITICAL | Sub-stage is the current end-to-end bottleneck |

Clicking a node opens the corresponding cycle range in the Timeline view for detailed inspection.

---

## 9. AI Copilot

The AI Copilot is a context-aware assistant integrated into pccx-lab via a dockable panel (left, right, or bottom). Its functions span performance analysis and RTL code generation.

### Bottleneck Analysis

The Copilot receives the current trace context — active cycle window, event histogram, and Flame Graph summary — and returns a natural-language bottleneck diagnosis with cycle-level supporting evidence. Analysis does not require an external API connection; the local context-compression engine produces results from trace data alone.

### UVM Sequence Generation

The Copilot generates complete UVM sequence objects for five predefined optimization strategies:

| Strategy | Description |
|---|---|
| l2_prefetch | Prefetch weight tiles into L2 cache ahead of the systolic array's demand window |
| barrier_reduction | Coalesce cross-core barriers to reduce synchronization overhead |
| dma_double_buffer | Interleave DMA transfers with compute using alternating on-chip buffers |
| systolic_pipeline_warmup | Insert priming transactions to fill the systolic array pipeline before the critical path |
| weight_fifo_preload | Pre-populate weight FIFOs during the preceding DMA_READ phase |

Generated sequence code is inserted directly into the SV Editor at the cursor position.

### OpenAI API Integration

For extended reasoning tasks, the Copilot optionally forwards requests to the OpenAI API. Configure the API key under **Tools > Copilot Settings**. All trace data transmitted to the API is summarized by the local context-compression engine; raw binary trace data is never transmitted.

---

## 10. Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+P | Open Command Palette |
| F1 | Switch to Timeline view |
| F2 | Switch to Data Flow view |
| F3 | Switch to SV Editor view |
| F4 | Switch to Report Builder view |
| F5 | Start simulation |
| F7 | Pause simulation |
| Shift+F5 | Stop simulation |
| F10 | Step over (one clock cycle) |
| Ctrl+B | Run IPC benchmark |
| Ctrl+S | Save current file |
| Ctrl+G | Go to cycle (opens cycle number input) |
| Arrow keys | Step to next or previous event edge in Timeline |
| Shift+Arrow | Step exactly one cycle forward or backward in Timeline |
| Ctrl+Scroll | Zoom Timeline cycle axis |

---

## 11. Theme and Localization

### Theme

pccx-lab supports two display themes selectable from **View > Theme** or from the status bar:

- **Dark** (default): high-contrast dark background optimized for extended hardware analysis sessions
- **Light**: light background theme for print-friendly screenshot capture

![Light mode theme](images/09-light-mode.png)

All color tokens are defined in `ThemeContext.tsx`; no hex values are hard-coded outside that file.

### Localization

The UI language is selectable from the status bar or **View > Language**:

| Code | Language |
|---|---|
| EN | English |
| 한 | Korean |

Switching language takes effect immediately without restarting the application.

---

## 12. CLI Tools

pccx-lab includes a set of command-line tools for headless operation and CI integration. These tools are built from the same `pccx-core` workspace crates as the desktop application and produce identical results.

### pccx-cli

Headless trace analysis. Operates on `.pccx` files without launching the desktop UI.

```bash
# Print per-core utilization summary
pccx-cli --util path/to/trace.pccx

# Compute roofline operating points
pccx-cli --roofline path/to/trace.pccx

# Identify top bottlenecks
pccx-cli --bottleneck path/to/trace.pccx

# Export a Markdown analysis report
pccx-cli --report-md path/to/trace.pccx > report.md
```

### pccx-golden-diff

CI gate verification. Compares a candidate `.pccx` trace against a reference (golden) trace and exits non-zero if performance metrics fall outside configured thresholds. Integrate with continuous integration pipelines to catch regressions before merge.

```bash
pccx-golden-diff golden.pccx candidate.pccx
```

### from-xsim-log

Imports Vivado xsim simulation logs and converts them to `.pccx` format for analysis in pccx-lab or `pccx-cli`.

```bash
from-xsim-log hw/sim/work/tb_gemm/tb_gemm.log -o tb_gemm.pccx
```

### pccx-server

Remote backend server for streaming live trace data to a pccx-lab instance over the network. The server listens on port 9400 by default.

```bash
pccx-server --port 9400 --trace-dir hw/sim/work/
```

Connect the desktop application via **Trace > Connect to Server** with the server hostname and port.

---

## 13. Architecture Reference

### Frontend Stack

| Component | Technology |
|---|---|
| Application framework | Tauri v2 |
| UI library | React 19 + TypeScript |
| Build tool | Vite 7 |
| 3D rendering | Three.js |
| Charts | ECharts (echarts-for-react) |
| Graph editor | React Flow (@xyflow/react) |
| Code editor | Monaco (VS Code engine) |
| Layout | react-resizable-panels v4 |

### Rust Workspace Crates

The backend is organized as a 10-crate Rust workspace:

| Crate | Responsibility |
|---|---|
| `pccx-core` | Trace parsing, analytics, hardware model, roofline, bottleneck detection |
| `pccx-reports` | Report generation and PDF export |
| `pccx-verification` | ISA validation, API integrity checking, coverage import |
| `pccx-authoring` | UVM testbench scaffolding and template rendering |
| `pccx-evolve` | Self-evolution cycle management |
| `pccx-remote` | Network server and client for remote trace streaming |
| `pccx-lsp` | Language server protocol integration for the SV Editor |
| `pccx-ai-copilot` | Context compression and AI copilot backend |
| `pccx-uvm-bridge` | UVM scoreboard hooks and coverage data import |
| `pccx-ide` | Tauri IPC command handlers (30+ `invoke_handler` commands) |

### IPC Pattern

The frontend invokes backend functionality through Tauri's typed IPC mechanism:

```typescript
const result = await invoke("command_name", { arg1: value1 });
```

Binary payloads (trace data, waveform buffers) are returned as `Vec<u8>` on the Rust side and mapped to `TypedArray` on the JavaScript side. This pattern avoids serialization overhead for large trace windows.

---

## Appendix A: .pccx File Format

`.pccx` is a binary trace format produced by the pccx-FPGA-NPU-LLM-kv260 xsim testbench suite. It consists of a fixed-size file header followed by a contiguous array of fixed-width event records.

### File Header

The file header encodes metadata including trace format version, hardware configuration, total event count, and clock frequency. The exact header layout is defined in `src/core/src/pccx_format.rs`.

### Event Record Structure

Each event occupies exactly **24 bytes** and contains the following fields:

| Offset | Field | Type | Description |
|---|---|---|---|
| 0 | `core_id` | u32 | Index of the core that recorded this event |
| 4 | `start` | u64 | Start cycle (absolute, from trace epoch) |
| 12 | `duration` | u64 | Duration in clock cycles |
| 20 | `type_id` | u32 | Event type identifier (see Appendix B) |

All multi-byte fields are little-endian. The record array immediately follows the file header with no padding or alignment gaps between records.

### Loading a Trace

The `pccx-core` crate exposes a `Trace::from_file(path)` function that memory-maps the file and returns a validated `Trace` struct. Validation checks the header magic bytes and verifies that the file length is consistent with the declared event count.

---

## Appendix B: Supported Event Types

The following event type identifiers are defined in `src/core/src/pccx_format.rs`. The `type_id` field in each event record carries one of these values.

| Event Name | type_id | Color (Timeline) | Description |
|---|---|---|---|
| MAC_COMPUTE | `<TODO: fill>` | Cyan | Systolic array is actively executing a matrix multiply operation |
| DMA_READ | `<TODO: fill>` | Green | DMA engine is transferring data from external memory (DDR) to an on-chip buffer |
| DMA_WRITE | `<TODO: fill>` | Yellow | DMA engine is transferring data from an on-chip buffer to external memory (DDR) |
| SYSTOLIC_STALL | `<TODO: fill>` | Purple | Systolic array pipeline is stalled due to a data hazard or downstream backpressure |
| BARRIER_SYNC | `<TODO: fill>` | Red | A cross-core synchronization barrier is active; one or more cores are waiting for peers |

Type ID numeric values are assigned during trace file generation and are defined in the `EventType` enum in `src/core/src/pccx_format.rs`. Refer to that file for the authoritative mapping.
