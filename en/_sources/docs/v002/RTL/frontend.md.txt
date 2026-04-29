---
rtl_source: hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv,
            hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv,
            hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv,
            hw/rtl/NPU_Controller/npu_interfaces.svh
---

# NPU Frontend Modules

## Role

The NPU frontend is the AXI-Lite entry point at the PS↔PL boundary on the NPU side,
complementing the host driver HAL.
The host driver writes ISA words to address `0x000` and a kick token to `0x008`,
then polls completion status over the same interface's read channel.
`AXIL_CMD_IN` receives host write transactions and enqueues command words in a FIFO.
`AXIL_STAT_OUT` returns engine completion status to the host through a FIFO-backed
read path.
In the hierarchy, `ctrl_npu_frontend` sits above the AXI-Lite bus and below the
controller's decoder and dispatcher ({doc}`/docs/v002/RTL/controller`).

## AXIL_CMD_IN

`AXIL_CMD_IN` accepts AXI-Lite write transactions from the host and stores command
words in a synchronous FIFO.
The parameter `FIFO_DEPTH` (default 8) sets the FIFO capacity in command-word entries.
When the FIFO is full, `s_awready` deasserts, stalling the host at the AW channel.
Two register addresses are decoded: `0x000` inserts a raw ISA word directly into the
FIFO; `0x008` inserts a kick marker with `bit63 = 1`.
The kick marker signals a batch boundary to the downstream dispatcher.
A pop occurs each cycle that both `OUT_valid` and `IN_decoder_ready` are asserted.

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv (AXI4-Lite Write Path)
:start-at: "  /*─────────────────────────────────────────────"
:end-before: "  /*─────────────────────────────────────────────"
```

## AXIL_STAT_OUT

The upper module asserts `IN_valid` alongside `IN_data` to push a status word into
the STAT_OUT FIFO after each engine completion.
The parameter `FIFO_DEPTH` (default 8) applies.
When the FIFO is full, pushes are dropped silently.
Completion words carry idempotent information, so a dropped entry is recovered by
the host's next poll cycle.
On an AR-channel handshake the FIFO head is latched into `rdata_r` and `s_rvalid` is
asserted. The response is held until the host acknowledges with `s_rready`.
`s_arready` deasserts when the FIFO is empty or when an R response is still in progress.

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv (AXI4-Lite Read Path)
:start-at: "  /*─────────────────────────────────────────────"
:end-before: "endmodule"
```

## ctrl_npu_frontend

`ctrl_npu_frontend` is a wrapper that routes the `axil_if.slave` signals to
`AXIL_CMD_IN` (write channels) and `AXIL_STAT_OUT` (read channels).
The CMD_IN outputs `cmd_data` and `cmd_valid` are forwarded as `OUT_RAW_instruction`
and `OUT_kick` to the downstream controller.
`OUT_kick` is combinational: `cmd_valid & IN_fetch_ready`.
The status path accepts `IN_enc_stat` and `IN_enc_valid` directly from the encoder FSM.
`ctrl_npu_interface.sv` is currently a placeholder for future per-core interface
aggregation.

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv (instance wiring)
:start-at: "  AXIL_CMD_IN #("
:end-before: "endmodule"
```

## Interface Specification

`npu_interfaces.svh` defines two interfaces: `axil_if` and `axis_if`.
`axil_if` defaults to ADDR_W=12 and DATA_W=64, covering all five AXI-Lite channels
(AW, W, B, AR, R), with `slave` and `master` modports.
`ctrl_npu_frontend` binds the `axil_if.slave` modport.
`axis_if` provides an AXI-Stream interface carrying tdata, tvalid, tready, tlast,
and tkeep; it is used by data-path modules that transfer activation and weight streams.

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: hw/rtl/NPU_Controller/npu_interfaces.svh (axis_if)
:start-at: "interface axis_if"
:end-before: "// axil_if.sv"
```

```{literalinclude} ../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: hw/rtl/NPU_Controller/npu_interfaces.svh (axil_if)
:start-at: "// axil_if.sv"
:end-before: "`endif"
```

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
