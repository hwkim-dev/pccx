# PREPROCESS RTL Reference

The PREPROCESS subdirectory contains five SystemVerilog modules.
`barrel_shifter_BF16.sv` is not present in the current working tree.

## `preprocess_fmap`

```{literalinclude} ../../../codes/v002/hw/rtl/PREPROCESS/preprocess_fmap.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/preprocess_fmap.sv
:start-at: module preprocess_fmap
:end-before: // ===| Bridge & Alignment
```

Receives a 128-bit BF16 stream from the ACP `S_AXIS_ACP_FMAP` interface,
buffers it into 256-bit words through an XPM block FIFO, and runs
exponent caching and mantissa alignment in parallel. The aligned 432-bit
output is written to `fmap_cache`; `o_fmap_broadcast` and `o_cached_emax`
are driven to MAT_CORE.

`fmap_width` defaults to `` `DEVICE_ACP_WIDTH_BIT ``.
`ARRAY_SIZE_H` controls the lane count for both output arrays.

## `preprocess_bf16_fixed_pipeline`

```{literalinclude} ../../../codes/v002/hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
:start-at: module preprocess_bf16_fixed_pipeline
:end-before: // ===| Stage 1
```

Accepts a 256-bit AXI-Stream slave (16 × BF16) and produces a 432-bit
master (16 × 27-bit fixed-point). The conversion spans **3 registered
pipeline stages**.

- **Stage 1** (`phase / buffer_low / block_valid`): On the even beat,
  stores the lower sixteen BF16 words and their local `e_max`. On the
  odd beat, combines both halves into a 32-element block and computes
  the block-global `e_max`.
- **Stage 2** (`shift_phase / shift_trigger / shift_target_data`):
  Processes the block over two clocks, sixteen lanes at a time. Each
  lane inserts the hidden bit into a 27-bit container and right-shifts
  by `(e_max - e_val)`. Two's-complement negation is applied when
  the BF16 sign bit is set. A `delta_e ≥ 27` check flushes the lane
  result to zero.
- **Stage 3** (`m_axis_tvalid / m_axis_tdata` output register):
  Latches the 432-bit result only on cycles where `shift_trigger` is
  asserted.

`s_axis_tready` is hardwired to `1`; the module never asserts backpressure
to the upstream FIFO.

## `bf16_to_INT8_pipeline_power_of_two_scale`

`hw/rtl/PREPROCESS/bf16_to_INT8_pipeline_power_of_two_scale.sv` is the
placeholder module for the Option A (power-of-two scale) INT8 quantizer.
The port declaration accepts 256-bit input and emits 256-bit output
(32 × INT8), but the body contains an incomplete `always_ff` block
with an empty index expression (`buffer_low[]`) and does not synthesize.
The internal logic is a copy of `preprocess_bf16_fixed_pipeline` carried
over as scaffolding. Full implementation follows the scale-policy decision
in `TODO.md` §A-1; the file is currently untracked in the RTL repo.

## `bf16_to_INT8_pipeline_true_symmetric_INT8`

`hw/rtl/PREPROCESS/bf16_to_INT8_pipeline_true_symmetric_INT8.sv` is the
placeholder module for the Option B (true symmetric INT8) quantizer.
Port structure and body state are identical to
`bf16_to_INT8_pipeline_power_of_two_scale`. The `max_abs`-based real-valued
scale path is intended to be implemented with driver-computed `S_a`
stored in the Constant Cache via `MEMSET`; implementation requirements
are specified in `TODO.md` §A-1. The file is currently untracked in the
RTL repo as well.

## `fmap_cache`

```{literalinclude} ../../../codes/v002/hw/rtl/PREPROCESS/fmap_cache.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/fmap_cache.sv
:start-at: module fmap_cache
:end-before: // ===| SRAM Instantiation
```

Receives the `preprocess_bf16_fixed_pipeline` output, stages it in a
2048-deep BRAM, and broadcasts one word per clock to MAT_CORE.

Four parameters govern geometry: `DATA_WIDTH` (default 27),
`WRITE_LANES` (default 16), `CACHE_DEPTH` (default 2048), and
`LANES` (default 32). The write port maps to `xpm_memory_sdpram`
Port A (7-bit address, 432-bit data); the read port maps to Port B
(11-bit address, 27-bit data). `READ_LATENCY_B = 2` is set for
400 MHz operation; the read-valid signal is delayed through a 3-stage
shift chain (`rd_valid_pipe_1 → rd_valid_pipe_2 → rd_valid`) to align
with BRAM output.

The read FSM initialises `rd_addr` to zero on `rd_start` and
de-asserts `is_reading` after the address reaches `CACHE_DEPTH - 1`.
The broadcast assignment updates all `LANES` outputs simultaneously on
every cycle where `rd_valid_pipe_2` is asserted.

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
