# Shared Library

The v002 RTL isolates common numeric operations and data structures under the
`Library/` directory. In the compile ordering recorded by `filelist.f`, these
files appear immediately after the package tier (A–D) and before `isa_pkg`.
Compute cores depend on this shared library to prevent duplicate implementations
of the same operation.

## Algorithms Package

**`algorithms_pkg`** (`Library/Algorithms/Algorithms.sv`)
Defines the QUEUE status struct `queue_stat_t`, a two-field packed struct
containing `empty` and `full`. External logic that needs to inspect queue state
uses this type rather than reading the raw signals directly. A STACK entry is
reserved as a commented stub.

```{literalinclude} ../../../codes/v002/hw/rtl/Library/Algorithms/Algorithms.sv
:language: systemverilog
:caption: Library/Algorithms/Algorithms.sv
:start-at: package algorithms_pkg;
:end-before: endpackage
```

**`bf16_math_pkg`** (`Library/Algorithms/BF16_math.sv`)
Provides BF16 arithmetic as a SystemVerilog package. The file header documents
the bit layout: `[15]=sign`, `[14:7]=exp(8b)`, `[6:0]=mantissa(7b)`. The hidden
bit (implicit leading 1) is not stored.

Exposed types and functions:

- `bf16_t` — Packed struct with a 1-bit sign, 8-bit exponent, and 7-bit mantissa.
- `bf16_aligned_t` — Packed struct holding an 8-bit `emax` and a 24-bit
  two's-complement aligned value.
- `to_bf16(raw[15:0])` — Automatic function that casts a raw 16-bit value to
  `bf16_t`.
- `align_to_emax(val, emax)` — Aligns a BF16 value to a given `emax` and
  returns a 24-bit two's-complement integer. Shifts the mantissa right by
  `diff = emax - val.exp` before sign extension.
- `bf16_add(a[15:0], b[15:0])` — Adds two packed BF16 values and returns a
  packed BF16 result. Aligns both operands to the larger exponent, performs a
  24-bit signed addition, then renormalises by locating the leading 1. Denormal,
  NaN, and Inf handling are not included; the autoregressive decode path operates
  exclusively on normalised BF16 operands.

```{literalinclude} ../../../codes/v002/hw/rtl/Library/Algorithms/BF16_math.sv
:language: systemverilog
:caption: Library/Algorithms/BF16_math.sv
:start-at: package bf16_math_pkg;
:end-before: endpackage
```

## QUEUE Interface

The QUEUE primitive is split across two files: an interface (`IF_queue`) and a
module (`QUEUE`).

**`IF_queue`** (`Library/Algorithms/QUEUE/IF_queue.sv`)
A parameterised SystemVerilog interface with `DATA_WIDTH` (default 32) and
`DEPTH` (default 8). The interface itself takes `clk` and `rst_n` as ports.
Pointer width `PTR_W = $clog2(DEPTH)` is derived internally. The storage array
`mem[0:DEPTH-1]` and pointers `wr_ptr`/`rd_ptr` are declared inside the
interface. The `empty` and `full` flags are assigned combinationally.

Three modports:

- `producer` — Imports the `push()` task only. Drives `push_data`/`push_en`;
  reads `empty`/`full`.
- `consumer` — Imports the `pop()` task only. Reads `pop_data`/`empty`/`full`;
  drives `pop_en`.
- `owner` — Used by the QUEUE module itself. Receives all handshake signals as
  inputs; drives `wr_ptr`/`rd_ptr` and references `mem` via `ref`.

```{literalinclude} ../../../codes/v002/hw/rtl/Library/Algorithms/QUEUE/IF_queue.sv
:language: systemverilog
:caption: Library/Algorithms/QUEUE/IF_queue.sv
:start-at: modport producer
:end-before: endinterface
```

**`QUEUE`** (`Library/Algorithms/QUEUE/QUEUE.sv`)
A module with a single port `IF_queue.owner q`. It re-derives the pointer width
as `PTR_W = $clog2($size(q.mem))` because modports cannot export parameters.
The `always_ff` block initialises both pointers to zero on reset, writes a word
when `push_en && !full`, and advances the read pointer when `pop_en && !empty`.

## Quantizations

**`Quantize_BF16.sv`** (`Library/Quantizations/BF16/Quantize_BF16.sv`)
The file is an empty placeholder. It marks the intended location for BF16
quantization helpers that will provide a common conversion path between the
offline quantization pipeline and the RTL datapath.

## Usage Patterns

The table reflects `import` statements and interface instantiations confirmed
directly in each source file.

```{list-table} Library dependencies by compute core
:name: tbl-lib-usage
:header-rows: 1
:widths: 32 22 22 12 12

* - Module (core)
  - `algorithms_pkg`
  - `bf16_math_pkg`
  - `IF_queue`
  - `QUEUE`
* - `CVO_top` (CVO_CORE)
  - —
  - o
  - —
  - —
* - `AXIL_CMD_IN` (sub-module of ctrl_npu_frontend)
  - o
  - —
  - o
  - o
```

`o` = import or instantiation confirmed in source. `—` = not present in that file.

`CVO_top` declares `import bf16_math_pkg::*;` directly. Per the source comment,
the `FLAG_SUB_EMAX` path (the sub-emax stage of the CVO softmax) uses this
package's BF16 arithmetic. `algorithms_pkg`, `IF_queue`, and `QUEUE` are
instantiated inside `AXIL_CMD_IN`, which buffers AXI4-Lite commands into a FIFO
and is itself instantiated by `ctrl_npu_frontend`. `GEMM_systolic_top`,
`GEMV_top`, and the PREPROCESS modules do not import any library package; they
use only `` `define `` headers.

---

```{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
```
