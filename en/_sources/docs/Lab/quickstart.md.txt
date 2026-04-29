---
myst:
  html_meta:
    description lang=en: |
      pccx-lab installation and first trace walkthrough — cargo build,
      npm ci, Linux WebKitGTK workaround, loading a sample .pccx, and
      entering the main panels.
---

# pccx-lab Quickstart

The goal of this page is to have a `.pccx` trace open in pccx-lab.
It covers the build, the Linux workaround, and the first panel entry
in the shortest possible path.

```{contents} On this page
:depth: 2
:backlinks: none
```

## Installation

pccx-lab is a Tauri v2 desktop application composed of a Rust workspace
(`crates/`) and a React/Vite frontend (`ui/`). The Rust workspace
contains nine crates: `core`, `reports`, `verification`, `authoring`,
`evolve`, `lsp`, `remote`, `uvm_bridge`, `ai_copilot`. All crates
treat `pccx-core` as the single sink of the dependency graph;
`pccx-ide` (`ui/src-tauri/`) and `pccx-remote` are the only terminal
binaries.

**Prerequisites**

| Item | Requirement |
|---|---|
| OS | Ubuntu 24.04 LTS (primary); macOS and Windows untested |
| Rust | `rustup` stable (see `rust-toolchain.toml`) |
| Node.js | LTS release compatible with Vite 7 |
| Display | X11 session (Wayland is not supported in the current release) |
| Optional | Xilinx KV260 board for live trace capture |

```bash
# 1. Clone the repository
git clone https://github.com/hkimw/pccx-lab.git
cd pccx-lab

# 2. Build the full Rust workspace (includes headless CLI binaries)
cargo build --release

# 3. Install frontend dependencies and start in development mode
cd ui
npm ci
npm run tauri dev
```

`npm run tauri dev` rebuilds the Rust backend and starts Vite hot-reload
simultaneously. For a release binary, use `cargo tauri build` instead.

## Linux WebKitGTK Workaround

On Linux, set the following environment variables before launching the app:

```bash
export WEBKIT_DISABLE_DMABUF_RENDERER=1
export GDK_BACKEND=x11
npm run tauri dev
```

**Reason**: Three.js, Monaco, and WebKitGTK 2.50 interact to trigger a
renderer freeze when DMA-BUF compositing is active for all three
simultaneously. `ui/src-tauri/src/main.rs` sets these variables
automatically at app startup, but an explicit shell export is required
when launching outside the Tauri process tree. A pure Wayland session
without XWayland is not supported in the current release.

If the freeze recurs after applying this workaround, consult the
pccx-lab issue tracker and the five-stage escalation procedure in
`CLAUDE_TASKS_lab.md` §3.

## Loading the First Trace

On launch the status bar shows `No trace loaded`. There are two entry
points for opening a trace.

**Option 1 — Menu**

Select `File ▸ Open .pccx…` (`Ctrl+O`) and choose a `.pccx` file.
On success, a green `trace loaded` badge appears to the right of the
tab strip and the status bar populates `cycles` and `cores`.

**Option 2 — CLI**

```bash
# Using the pre-built binary
./target/release/pccx_cli samples/gemma3n_16tok_smoke.pccx \
    --roofline --report-md

# Or via cargo run
cargo run -p pccx-reports --bin pccx_cli -- \
    samples/gemma3n_16tok_smoke.pccx --roofline --report-md
```

**Sample traces included in the repository**

| File | Size | Events | Use |
|---|---|---|---|
| `samples/gemma3n_16tok_smoke.pccx` | 101 KB | 2,568 | CI smoke |
| `samples/gemma3n_128tok_decode.pccx` | 797 KB | 20,488 | steady-state decode |

To generate a trace from RTL simulation, run the verification script in
the sibling repository:

```bash
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260
./hw/sim/run_verification.sh
# output: hw/sim/work/<tb>/<tb>.pccx
```

## Main Panels

After loading a trace, the following five panels are available from
the tab bar:

| Panel | Tab label | Role |
|---|---|---|
| Timeline | Timeline | Cycle-accurate per-core event timeline |
| FlameGraph | Flame Graph | Hierarchical performance breakdown and bottleneck identification |
| System Simulator | System Simulator | Interactive pccx v002 module hierarchy simulator |
| Verification Suite | Verify | ISA validation, API integrity, UVM coverage, synthesis status |
| Reports | Report | Automated PDF/Markdown analysis report generation |

**Timeline event colour coding**

| Event type | Colour | Meaning |
|---|---|---|
| MAC_COMPUTE | Cyan | systolic array matrix multiply in progress |
| DMA_READ | Green | external memory to on-chip buffer DMA transfer |
| DMA_WRITE | Yellow | on-chip buffer to external memory DMA transfer |
| SYSTOLIC_STALL | Purple | systolic array pipeline stall |
| BARRIER_SYNC | Red | cross-core synchronisation barrier active |

Timeline navigation: `Ctrl+Scroll` to zoom the cycle axis, drag to
pan, `Ctrl+G` to jump to a specific cycle.

For detailed controls in each panel, see {doc}`panels`.

Press `?` or `F1` anywhere in the app to open the full shortcut modal.

## Next Steps

- {doc}`verification-workflow` — end-to-end xsim → `.pccx` → UI verification pipeline.
- {doc}`pccx-format` — `.pccx` binary format specification.
- {doc}`panels` — per-panel reference for all analysis views.
- {doc}`ipc` — Tauri IPC command catalogue and binary payload patterns.
- {doc}`core-modules` — reference for the public modules in `pccx-core`.

## Cite This Page

```bibtex
@misc{pccx_lab_quickstart_2026,
  title        = {pccx-lab Quickstart: installing the profiler and loading the first trace},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/quickstart.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
