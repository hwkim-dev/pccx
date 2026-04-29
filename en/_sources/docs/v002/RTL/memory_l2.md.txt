# L2 Cache (URAM)

Three modules form the v002 1.75 MiB UltraRAM L2 cache:
`mem_GLOBAL_cache` (top wrapper), `mem_L2_cache_fmap` (URAM array), and
`mem_BUFFER` (ACP CDC bridge). `mem_GLOBAL_cache` drives the state machines
for both the ACP port and the NPU port, and instantiates the other two
internally.

## Role

The L2 cache is a True Dual-Port URAM block resident in the NPU clock domain
(400 MHz). Port A performs DDR4 ↔ L2 DMA over the PS ACP path. Port B is
accessed directly by the compute engines (GEMM, GEMV, CVO). Both fmap and
weight data occupy the same address space; the address ranges assigned to each
are determined by software convention and the shape constant RAM managed by
`mem_dispatcher`. The hardware makes no distinction between the two regions.

## Storage Layout

`mem_L2_cache_fmap` is instantiated with `Depth = 114_688` and a data width
of 128 bits.

$$\text{Total capacity} = 114{,}688 \times 128\ \text{bit} = 14{,}680{,}064\ \text{bit} = 1.75\ \text{MiB}$$ (eq-l2-capacity-en)

The address unit is a 128-bit word. Word address $N$ corresponds to byte
offset $[16N,\ 16N+15]$. The 17-bit address bus can address up to 131,072
words; the current capacity of 114,688 words falls within that range.

URAM read latency is 3 clock cycles. The Port A read path tracks data validity
with a 3-bit shift register `acp_rd_valid_pipe`; `OUT_acp_rdata` is valid 3 cycles
after the address is presented, and `core_acp_tx_bus.tvalid` is asserted
simultaneously. Port B reads carry the same 3-cycle latency characteristic.

## Port Interface

The Port A (ACP) and Port B (NPU) control signals are:

```{literalinclude} ../../../codes/v002/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
:language: systemverilog
:start-at: // ===| Port A — ACP DMA control |
:end-before: // ===| Port B — NPU compute direct access |
```

```{literalinclude} ../../../codes/v002/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
:language: systemverilog
:start-at: // ===| Port B — NPU compute direct access |
:end-before: );
```

Port contract:

- Asserting `IN_acp_rx_start` or `IN_npu_rx_start` starts a sequential
  transfer from `base_addr` through `end_addr - 1` on the respective port.
- `write_en = 1` transfers data into L2 (external source to L2);
  `write_en = 0` transfers data out of L2 (L2 to external sink).
- While `OUT_acp_is_busy` or `OUT_npu_is_busy` is asserted, the port does not
  accept a new command. Command queuing is handled by `mem_u_operation_queue`.

The two ports have independent state machines and can operate concurrently.
Port B arbitration is performed by `mem_dispatcher`; when `mem_CVO_stream_bridge`
is active it preempts Port B. NPU DMA commands hold in the operation queue
during preemption and resume after the bridge completes.

## Submodules

```{table} L2 cache submodules
:name: tbl-l2-submodules-en

| Module | Role |
|---|---|
| `mem_L2_cache_fmap` | 114,688 × 128-bit URAM array. Provides Port A and Port B read/write interfaces. |
| `mem_BUFFER` | ACP CDC bridge: AXI 250 MHz ↔ Core 400 MHz. Two `xpm_fifo_axis` instances (depth 32, BRAM) for RX and TX. |
| `mem_GLOBAL_cache` | Top wrapper containing both modules. Drives Port A and Port B state machines. |
```

```{admonition} Last verified against
:class: note
Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
```
