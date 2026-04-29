# Memory Dispatch

`mem_dispatcher` translates uops received from the scheduler into L2 cache
commands and routes them across three channels: the ACP DMA path, the NPU
burst path, and the CVO stream path. This page covers the dispatch path, the
uop ABI, the CDC weight buffer, and the CVO stream bridge.

## Dispatch Path

The scheduler delivers three uop types to `mem_dispatcher`.

- `memory_control_uop_t` (`IN_LOAD_uop`) — decoded output of a MEMCPY
  instruction. The `data_dest` field (`data_route_e`) determines whether the
  uop is converted to an ACP channel command or an NPU channel command before
  being pushed into `mem_u_operation_queue`.
- `memory_set_uop_t` (`IN_mem_set_uop`) — decoded output of a MEMSET
  instruction. Written directly into the fmap or weight shape constant RAM
  (`fmap_array_shape` / `weight_array_shape`), bypassing any FIFO.
- `cvo_control_uop_t` (`IN_CVO_uop`) — decoded output of a CVO instruction.
  Monitored directly by `mem_CVO_stream_bridge`; does not pass through the
  dispatcher's operation queues.

When a command is popped from `mem_u_operation_queue`, `IN_acp_rx_start` or
`IN_npu_rx_start` on `mem_GLOBAL_cache` is asserted and the L2 state machine
begins a sequential 128-bit-word transfer. Port B is preempted by the CVO
bridge when `OUT_busy` is asserted; otherwise the NPU DMA state machine drives it.

## uop ABI

`acp_uop_t` and `npu_uop_t` are 35-bit packed structs that define the transfer
ABI between the scheduler and the memory subsystem. Both types share an
identical field layout.

```{table} acp_uop_t / npu_uop_t fields (35 bits)
:name: tbl-uop-fields-en

| Bits | Width | Signal | Meaning |
|---|---|---|---|
| [34] | 1 | `write_en` | 1 = write to L2, 0 = read from L2 |
| [33:17] | 17 | `base_addr` | Transfer start word address |
| [16:0] | 17 | `end_addr` | Transfer end word address (exclusive) |
```

RTL definition:

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
:language: systemverilog
:start-at: // ===| ACP / NPU Transfer uops (used by mem_dispatcher) |
:end-before: endpackage
```

Two independent FIFO channels (`xpm_fifo_sync`, depth 128, width 35 bits)
buffer ACP and NPU commands separately. When either FIFO reaches
`PROG_FULL_THRESH = 100`, `OUT_fifo_full` is asserted, propagating backpressure
to the scheduler.

## CDC Weight Buffer

`mem_HP_buffer` crosses the PS HP0–HP3 weight streams from the AXI 250 MHz
domain into the NPU core 400 MHz domain.

- One `xpm_fifo_axis` (depth 4096, width 128 bits, BRAM) per HP port, four in total.
- Slave side clocked by `clk_axi` (250 MHz); master side by `clk_core` (400 MHz).
- Uses `axis_if` interfaces named `S_AXI_HP{0..3}_WEIGHT` →
  `M_CORE_HP{0..3}_WEIGHT`.

GEMM weights arrive on HP0/HP1; GEMV weights arrive on HP2/HP3 (see CLAUDE.md §4).
Each FIFO's depth of 4096 × 128 bits = 64 KiB is sufficient to buffer one weight tile batch.

## CVO Stream Bridge

`mem_CVO_stream_bridge` connects the 128-bit L2 Port B interface to the
16-bit BF16 streaming interface of the CVO engine. It operates as a four-state
FSM (IDLE / READ / WRITE / DONE).

**Phase 1 — READ**: sequential 128-bit word bursts are read from L2 starting at
`src_addr` through `src_addr + ceil(length/8) - 1`. Each word is deserialized
into eight 16-bit slices and fed to the CVO engine. The 3-cycle URAM read
latency is tracked by a 3-bit shift register `rd_lat_pipe`. CVO outputs are
buffered in an internal `xpm_fifo_sync` (depth 2048, width 16 bits, maximum
32 KiB).

**Phase 2 — WRITE**: 16-bit elements are drained from the FIFO, serialized
eight at a time into 128-bit words, and written sequentially to L2 starting at
`dst_addr`.

Address conversion: `src_addr` and `dst_addr` are element (16-bit) addresses;
a 3-bit right shift (`>> 3`) converts them to 128-bit word addresses. Maximum
vector length is 2048 elements (32 KiB at 16 bits per element).

```{admonition} Last verified against
:class: note
Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
```
