# Compile-Priority Packages

The v002 RTL organises packages and headers into a compile-priority hierarchy
(`Constants/compilePriority_Order/`). Each tier depends only on the tier above
it, allowing `xvlog` and the Vivado compiler to process them in order without
forward references. The canonical ordering is recorded in
`hw/vivado/filelist.f`.

## Compile Priority

Compilation proceeds in tiers A → B → C → D.

**A — Pure `` `define `` headers (`A_const_svh/`)**: Added to the include search
path via the `xvlog -i` flag; they are not compiled directly.

- `NUMBERS.svh` — Primitive bit-width constants.
  `` `N_SIZEOF_INT4 = 4 ``, `` `N_BF16_SIZE = 16 ``, `` `N_FP32_SIZE = 32 ``.
- `npu_arch.svh` — NPU architectural macros. Holds values that must be
  `` `define `` rather than `localparam` because they appear in port declarations
  and `generate` ranges. Key constants: `` `ARRAY_SIZE_H = 32 ``,
  `` `ARRAY_SIZE_V = 32 ``, `` `ISA_WIDTH = 64 ``, `` `ISA_BODY_WIDTH = 60 ``,
  `` `SYSTOLIC_TOTAL_LATENCY = 64 ``, `` `FMAP_CACHE_DEPTH = 2048 ``,
  `` `FIXED_MANT_WIDTH = 27 ``.
- `kv260_device.svh` — Physical hardware constants for the Kria KV260 target.
  HP port count 4, HP single-port width 128 bits, DSP48E2 A/B/P port widths
  30/18/48 bits, XPM FIFO depths 512/16.
- `GLOBAL_CONST.svh` — **Deprecated shim.** Re-includes `NUMBERS.svh`,
  `kv260_device.svh`, and `npu_arch.svh` in sequence, then adds legacy aliases
  (`HP_PORT_MAX_WIDTH`, `DSP48E2_POUT_SIZE`, etc.). New code must include the
  source headers directly rather than using this file.
- `DEVICE_INFO.svh` — **Deprecated shim.** Re-includes `kv260_device.svh` and
  provides legacy aliases (`DEVICE_HP_SINGLE_LANE_MAX_IN_BIT`, `DEVICE_HP_CNT`).
  Do not use in new code.

**B — `device_pkg.sv` (`B_device_pkg/`)**: Depends on A headers. The first
SystemVerilog package; holds algorithm-level type choices.

**C — `dtype_pkg.sv`, `mem_pkg.sv` (`C_type_pkg/`)**: Depend on B. Separate
numeric-type constants from memory-architecture parameters.

**D — `vec_core_pkg.sv` (`D_pipeline_pkg/`)**: Depends on A + B + C. Defines
the Vector Core configuration struct and default values.

## Core Packages

**`device_pkg`** (`B_device_pkg/device_pkg.sv`)
Fixes the feature-map (activation) port precision at BF16 (16 bits) and the
internal accumulation precision at FP32 (32 bits). Declares pipeline instance
counts `VecPipelineCnt = 4` and `MatPipelineCnt = 1`. All downstream packages
reference these values, making this file the first edit point for any
architecture-level change.

```{literalinclude} ../../../codes/v002/hw/rtl/Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
:language: systemverilog
:caption: Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
:start-at: package device_pkg;
:end-before: endpackage
```

**`dtype_pkg`** (`C_type_pkg/dtype_pkg.sv`)
Exposes BF16 (`Bf16Width = 16`, `Bf16ExpWidth = 8`, `Bf16MantWidth = 7`),
fixed-point mantissa width `FixedMantWidth = 27`, INT4 (`Int4Width = 4`),
INT8 (`Int8Width = 8`), FP32 (`Fp32Width = 32`), and DSP48E2 P-register width
`DspPWidth = 48` as `localparam` constants. No units or semantics are embedded,
so the file remains valid across synthesis targets.

**`mem_pkg`** (`C_type_pkg/mem_pkg.sv`)
Consolidates memory parameters derived from `device_pkg` and `kv260_device.svh`.
`HpPortCnt = 4`, `HpSingleWidthBit = 128`, `HpTotalWidthBit = 512`,
`HpSingleWeightCnt = 32`, `FmapL2CacheOutCnt = 32` (= `ARRAY_SIZE_H`),
`FmapCacheDepth = 2048`, `XpmFifoDepth = 512`. No magic numbers — all values
are derived from upstream headers.

**`vec_core_pkg`** (`D_pipeline_pkg/vec_core_pkg.sv`)
Defines the packed struct `vec_cfg_t` describing the Vector Core topology, and
the KV260 default `VecCoreDefaultCfg`. Key defaults: `GemvBatch = 512`,
`GemvCycle = 512`, `GemvLineCnt = 32`. The legacy alias `gemv_cfg_t` is retained
until all `GEMV_*.sv` modules migrate to the renamed type.

## Interface Headers

**`npu_interfaces.svh`** (`NPU_Controller/npu_interfaces.svh`)
Includes `GLOBAL_CONST.svh` then defines two SystemVerilog interfaces.

`axis_if #(DATA_WIDTH = 128)` — AXI4-Stream bus. The `slave` modport takes
`tdata`, `tvalid`, `tlast`, `tkeep` as inputs and drives `tready`. The `master`
modport reverses direction.

`axil_if #(ADDR_W = 12, DATA_W = 64)` — AXI4-Lite control bus. The interface
itself takes `clk` and `rst_n` as ports. The `slave` modport takes AW/W/AR
channels as inputs and drives B/R channels.

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: NPU_Controller/npu_interfaces.svh
:start-at: interface axis_if
:end-before: `endif  // NPU_INTERFACES_SVH
```

**`GEMM_Array.svh`** (`MAT_CORE/GEMM_Array.svh`)
A compatibility shim that re-includes `npu_arch.svh` to single-source
`ARRAY_SIZE_H` and `ARRAY_SIZE_V`, eliminating redefinition warnings. Adds two
MAT_CORE-scoped constants: `MINIMUM_DELAY_LINE_LENGTH = 1` and
`gemm_instruction_dispatcher_CLOCK_CONSUMPTION = 1`. New MAT_CORE modules
should include `npu_arch.svh` directly.

## Usage Matrix

The table reflects `import` statements and `` `include `` directives observed
directly in each source file.

```{list-table} Package dependencies by compute core
:name: tbl-pkg-usage
:header-rows: 1
:widths: 28 13 13 13 16 13 14

* - Module (core)
  - `device_pkg`
  - `dtype_pkg`
  - `mem_pkg`
  - `vec_core_pkg`
  - `isa_pkg`
  - Header (include)
* - `GEMM_systolic_top` (MAT_CORE)
  - —
  - —
  - —
  - —
  - —
  - `GEMM_Array.svh`, `GLOBAL_CONST.svh`
* - `GEMV_top` (VEC_CORE)
  - —
  - o
  - —
  - o
  - —
  - `GLOBAL_CONST.svh`
* - `CVO_top` (CVO_CORE)
  - —
  - —
  - —
  - —
  - o
  - `GLOBAL_CONST.svh`
* - `ctrl_npu_frontend` (Controller)
  - —
  - —
  - —
  - —
  - —
  - `npu_interfaces.svh`, `GEMM_Array.svh`
* - `AXIL_CMD_IN` (sub-module of ctrl_npu_frontend)
  - —
  - —
  - —
  - —
  - —
  - `GLOBAL_CONST.svh`
```

`o` = import confirmed in source. `—` = no import in that file.

`GEMM_systolic_top` does not import any package; it uses only `` `define ``
macros from the headers. `GEMV_top` declares `import vec_core_pkg::*;` and
references `dtype_pkg::Bf16ExpWidth` in its port list. `CVO_top` declares
`import isa_pkg::*;` and `import bf16_math_pkg::*;` (`bf16_math_pkg` is a
library package documented on the {doc}`library` page). `ctrl_npu_dispatcher`
is currently an entirely commented-out stub and is excluded from the table.

---

```{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
```
