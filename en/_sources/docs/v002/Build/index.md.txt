# Vivado Build

This page documents the Vivado build flow for the pccx v002 NPU core.
All build scripts reside under `hw/vivado/`; `build.sh` is the single
entry point. Source files are managed in the
`hkimw/pccx-FPGA-NPU-LLM-kv260` repository.

## Build Flow

`build.sh` is a thin wrapper around Vivado batch-mode invocations.
The first argument selects one of four stages.

```{code-block} bash
./hw/vivado/build.sh project   # create project only
./hw/vivado/build.sh synth     # create project + OOC synthesis
./hw/vivado/build.sh impl      # full implementation + bitstream
./hw/vivado/build.sh clean     # remove build/ directory
```

The script first searches `PATH` for `vivado`; if not found it falls
back through `/tools/Xilinx/2025.2`, `2024.1`, `2023.2` in that order.
Vivado 2023.2 or later is required.

**Stage descriptions:**

1. **`create_project.tcl`** — Creates a Vivado project targeting part
   `xck26-sfvc784-2LV-c` (KV260 ZU5EV) at `build/pccx_v002_kv260/`.
   Parses `filelist.f` to populate the `sources_1` fileset, then adds
   every `*.xdc` from `hw/constraints/` to `constrs_1`.
2. **`synth.tcl`** — Runs `synth_design -mode out_of_context
   -flatten_hierarchy rebuilt`. On completion, writes
   `utilization_post_synth.rpt`, `clocks_post_synth.rpt`,
   `timing_summary_post_synth.rpt`, and `drc_post_synth.rpt` to
   `build/reports/`. Check WNS in the timing summary before
   proceeding to implementation.
3. **`impl.tcl`** — Verifies that `synth_1` progress is `100%`, then
   launches `impl_1 -to_step write_bitstream -jobs 4`. On success,
   the bitstream is copied to `build/pccx_v002_kv260.bit`.
   Implementation is an hour-scale job; run it only after OOC synthesis
   is clean.

The OOC mode is required because `NPU_top` uses SystemVerilog interface
ports (`axil_if` / `axis_if`). Out-of-context synthesis leaves those
ports unbound, allowing the core to be synthesised and checked in
isolation before a block-design wrapper is available.

## SV Interface Wrapper

`hw/vivado/npu_core_wrapper.sv` converts `NPU_top`'s SystemVerilog
interface ports into plain AXI4-Lite and AXI4-Stream signal bundles so
the core can be packaged as a Vivado IP and placed alongside the Zynq PS
in a block design. The wrapper contains no registers and no CDC logic;
it performs one-to-one signal expansion only.

```{literalinclude} ../../../codes/v002/hw/vivado/npu_core_wrapper.sv
:language: systemverilog
:start-at: module npu_core_wrapper
:end-before: // ---------------------------------------------------------------------------
:caption: npu_core_wrapper — port declarations
:name: lst-npu-core-wrapper-ports
```

The external interface exposed by the wrapper is as follows.

```{list-table} npu_core_wrapper external interfaces
:header-rows: 1
:name: tbl-wrapper-interfaces

* - Port group
  - Direction
  - Width
  - Description
* - `clk_core` / `rst_n_core`
  - Input
  - 1-bit
  - Core-domain clock and active-low reset
* - `clk_axi` / `rst_axi_n`
  - Input
  - 1-bit
  - AXI-domain clock and active-low reset
* - `s_axil_*`
  - Slave
  - 32-bit
  - AXI4-Lite control channel (CMD_IN / STAT_OUT)
* - `s_axis_hp0` .. `hp3`
  - Slave
  - 128-bit
  - AXI4-Stream HP ports × 4 (weight streaming)
* - `s_axis_acp_fmap`
  - Slave
  - 128-bit
  - AXI4-Stream ACP FMap input
* - `m_axis_acp_result`
  - Master
  - 128-bit
  - AXI4-Stream ACP result output
```

The Vivado IP packager auto-infers AXI interfaces from plain signal
ports, so this wrapper allows `NPU_top` to be placed directly into a
block design alongside the Zynq PS.

## Constraints

`hw/constraints/pccx_timing.xdc` is a timing-only constraint file.
Pin and IO constraints are absent; they are delegated to the block
design that wraps this core.

Two clock domains are declared.

```{list-table} Clock domain definitions
:header-rows: 1
:name: tbl-clock-domains

* - Clock name
  - Period
  - Frequency
  - Scope
* - `axi_clk`
  - 4.000 ns
  - 250 MHz
  - AXI-Lite MMIO, CDC FIFO drain sides, DMA path
* - `core_clk`
  - 2.500 ns
  - 400 MHz
  - DSP48E2 array, GEMV lanes, CVO SFU
```

The two domains are genuinely asynchronous. `set_clock_groups
-asynchronous` is applied; every domain crossing uses a CDC FIFO or a
properly-staged reset synchroniser.

Additional path exceptions are set.

- **False paths** — Reset bridge first-flop paths and `XPM_FIFO_ASYNC`
  gray-coded pointer crossings.
- **Multicycle path (setup 2, hold 1)** — From DSP48E2 P-registers
  inside the GEMM systolic array to `mat_result_normalizer`. The
  controller stalls new MACs during accumulator flush, so the drain
  path tolerates two cycles.

## File Manifest

`hw/vivado/filelist.f` is the source list for both OOC synthesis and
`xvlog` lint. `create_project.tcl` parses this file to add sources to
the Vivado project.

Compile order follows the declaration order in the file. Packages and
interfaces must appear before the modules that import them.

```{literalinclude} ../../../codes/v002/hw/vivado/filelist.f
:language: text
:start-at: B_device_pkg/device_pkg.sv
:end-before: Library/Algorithms/BF16_math.sv
:caption: filelist.f — package compile order (leading section)
:name: lst-filelist-packages
```

The full file is organized into the following sections.

```{list-table} filelist.f section structure
:header-rows: 1
:name: tbl-filelist-sections

* - Section
  - Contents
* - A (comment only)
  - `` `include `` headers (`*.svh`); picked up via `-i`, not compiled
* - B
  - `device_pkg.sv` — device parameters
* - C
  - `dtype_pkg.sv`, `mem_pkg.sv` — data and memory types
* - D
  - `vec_core_pkg.sv` — Vector Core pipeline parameters
* - Library
  - BF16 math library, algorithms, QUEUE interface
* - ISA
  - `isa_pkg.sv` — 64-bit VLIW encoding package
* - MAT_CORE
  - GEMM systolic array and result packer
* - VEC_CORE
  - GEMV core (accumulate, LUT generation, reduction, top)
* - CVO_CORE
  - CORDIC unit, SFU, CVO top
* - PREPROCESS
  - BF16↔fixed-point pipeline, fmap cache
* - MEM_control
  - L2 cache, HP buffer, CVO bridge, dispatcher
* - NPU_Controller
  - AXI-Lite decoder, dispatcher, front-end, Global Scheduler, top
* - Top level
  - `NPU_top.sv` — always last
```

When adding a new `.sv` file, insert it in dependency order inside
`filelist.f`.

## Related Pages

```{toctree}
:maxdepth: 1
```

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
:::
