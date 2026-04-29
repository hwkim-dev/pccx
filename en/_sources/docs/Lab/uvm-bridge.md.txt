# UVM Bridge

_Last revised: 2026-04-29._

The `pccx-uvm-bridge` crate is a **C ABI DPI-C export bundle** that exposes
the `pccx-core` cycle estimator to SystemVerilog UVM testbenches.
The simulator links the shared library (`cdylib`) and calls the Rust
analyzer at runtime via a single `import "DPI-C"` declaration on the SV side.

Source: `crates/uvm_bridge/src/lib.rs`, crate manifest:
`crates/uvm_bridge/Cargo.toml`.

## Role

`pccx-uvm-bridge` connects two layers.

The **pccx-core analyzer layer** instantiates a fixed reference hardware
model (`HardwareModel::pccx_reference()`) and computes cycle counts for
GEMM tile operations and AXI DMA transfers via `CycleEstimator`.
On valid input the result is written to the output pointer and `PCCX_OK(0)`
is returned. On invalid input the output pointer is left untouched and
`PCCX_ERROR(1)` is returned.

The **UVM testbench layer** calls the imported functions directly from
within a simulator environment that has linked the shared library.
A UVM sequence populates the operand fields (`m`, `n`, `k`, `bpe`, etc.),
calls the DPI-C function to receive the cycle estimate, and applies it
as an assertion threshold or a coverage-bucket boundary.

## C ABI surface

Every function declared `#[no_mangle] pub unsafe extern "C"` is exposed
through the C ABI. The table below lists the complete set of DPI-C exports
defined in `crates/uvm_bridge/src/lib.rs`.

```{list-table} DPI-C export functions
:name: tbl-dpi-c-exports
:header-rows: 1
:widths: 35 45 20

* - Function name
  - Arguments
  - Return
* - `pccx_estimate_gemm_cycles`
  - `m: u32, n: u32, k: u32, bpe: u32, out_cycles: *mut u64`
  - `i32` (error code)
* - `pccx_estimate_dma_cycles`
  - `bytes: u32, out_cycles: *mut u64`
  - `i32` (error code)
* - `pccx_estimate_dma_cycles_contended`
  - `bytes: u32, active_cores: u32, out_cycles: *mut u64`
  - `i32` (error code)
* - `pccx_is_compute_bound`
  - `m: u32, n: u32, k: u32, bpe: u32`
  - `i32` (1=compute-bound, 0=memory-bound, PCCX_ERROR=invalid)
* - `pccx_peak_tops_x100`
  - none
  - `u32` (TOPS × 100 integer, e.g. 205 = 2.05 TOPS)
* - `pccx_clock_mhz`
  - none
  - `u32` (MHz)
```

The **`bpe` field** encodes bytes per element: `1` = INT8, `2` = BF16/FP16,
`4` = FP32.

**Error codes** take only two values: `PCCX_OK = 0`, `PCCX_ERROR = 1`.
A null `out_cycles` pointer or a zero-valued size argument causes
`PCCX_ERROR` to be returned immediately.

`pccx_peak_tops_x100` and `pccx_clock_mhz` carry no output pointer and
are therefore declared `pub extern "C"` without `unsafe`.

## TileOperation data flow

The complete path from a UVM testbench query to a returned GEMM cycle
count is as follows.

```
UVM testbench (SV)
  │  import "DPI-C" pccx_estimate_gemm_cycles(m, n, k, bpe, out_cycles)
  │
  ▼
pccx_estimate_gemm_cycles()        [crates/uvm_bridge/src/lib.rs]
  │  construct TileOperation { m, n, k, bytes_per_element: bpe }
  │  instantiate HardwareModel::pccx_reference()
  │  construct CycleEstimator::new(&hw)
  │
  ▼
CycleEstimator::estimate_gemm_cycles(&op)   [crates/core/src/cycle_estimator.rs]
  │  arithmetic model computes cycle count
  │
  ▼
write *out_cycles → return PCCX_OK
  │
  ▼
UVM scoreboard / coverage model
  (applies cycle count to assertion threshold or coverage bucket)
```

`pccx_estimate_dma_cycles_contended` follows the same path but accepts
`active_cores` as an additional argument to model multi-core bus contention.

`pccx_is_compute_bound` returns the compute/memory-bound classification
directly without an `out_cycles` pointer, making it convenient for use
as a branching predicate in UVM sequences.

## SV-side import contract

When the simulator links the shared library (`libpccx_uvm_bridge.so`),
a SV package declares the imports as follows.

```systemverilog
package pccx_dpi_pkg;

  import "DPI-C" function int pccx_estimate_gemm_cycles(
    input  int unsigned m,
    input  int unsigned n,
    input  int unsigned k,
    input  int unsigned bpe,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_estimate_dma_cycles(
    input  int unsigned bytes,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_estimate_dma_cycles_contended(
    input  int unsigned bytes,
    input  int unsigned active_cores,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_is_compute_bound(
    input int unsigned m,
    input int unsigned n,
    input int unsigned k,
    input int unsigned bpe
  );

  import "DPI-C" function int unsigned pccx_peak_tops_x100();
  import "DPI-C" function int unsigned pccx_clock_mhz();

endpackage
```

The `longint unsigned` ↔ Rust `u64` and `int unsigned` ↔ Rust `u32`
mappings follow the IEEE 1800-2017 DPI-C standard.

An **output argument** (`output longint unsigned cycles`) is only valid
after the call returns. The return code must be checked for `PCCX_OK(0)`
before `cycles` is consumed.

The crate type includes both `cdylib` and `rlib`
(see `crates/uvm_bridge/Cargo.toml`). The `rlib` surface serves Rust
unit tests and the high-level wrapper functions `estimate_gemm` and
`estimate_dma`.

## Cite this page

```bibtex
@misc{pccx_uvm_bridge_2026,
  title        = {pccx-lab UVM Bridge: DPI-C adapter exposing the pccx cycle estimator to SystemVerilog testbenches},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/uvm-bridge.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
