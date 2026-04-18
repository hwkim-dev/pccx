NPU Controller
===============

The controller is the **front-end + scheduler** half of the NPU. It
accepts 64-bit VLIW instructions over AXI-Lite, decodes them, pushes
the resulting micro-ops into per-engine FIFOs, and exposes an
status-register back to the host. All compute cores operate strictly
downstream of the controller's FIFOs.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      Instruction layout and opcode table consumed by the decoder below.

Topology
---------

::

   Host (AXI-Lite) ──► AXIL_CMD_IN ──► ctrl_npu_decoder ─┐
                                                        ▼
   ┌── GEMV FIFO ── GEMM FIFO ── CVO FIFO ── MEM FIFO ── MEMSET FIFO ──┐
   │                                                                    │
   │            ctrl_npu_dispatcher (per-engine pop)                     │
   │                                                                    │
   └────────────► Global_Scheduler ◄────────────────────────────────────┘
                                                                        │
                                        NPU_fsm_out_Logic ──► AXIL_STAT_OUT

Frontend (AXI-Lite surface)
----------------------------

* ``ctrl_npu_frontend.sv`` — container for the AXIL surface; hosts the
  interface slaves.
* ``AXIL_CMD_IN.sv`` — AXI-Lite write slave. Latches 64-bit instructions
  from 32-bit-at-a-time writes at ``0x00`` / ``0x04``.
* ``AXIL_STAT_OUT.sv`` — AXI-Lite read slave that exposes the BUSY/DONE
  status register at ``0x08``.
* ``ctrl_npu_interface.sv`` — internal handshake glue between the
  frontend and the Control Unit.

.. dropdown:: ``ctrl_npu_frontend.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv
      :language: systemverilog

.. dropdown:: ``AXIL_CMD_IN.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv
      :language: systemverilog

.. dropdown:: ``AXIL_STAT_OUT.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv
      :language: systemverilog

.. dropdown:: ``ctrl_npu_interface.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_interface.sv
      :language: systemverilog

Control Unit (decode + dispatch)
---------------------------------

* ``ctrl_decode_const.svh`` — decode-stage constants (field widths, masks).
* ``ctrl_npu_decoder.sv`` — strips the 4-bit opcode from a 64-bit VLIW
  instruction and routes the 60-bit body to the correct FIFO.
* ``ctrl_npu_dispatcher.sv`` — per-engine local dispatcher: pops a
  queued micro-op and fires the engine when operands are ready.

.. dropdown:: ``ctrl_decode_const.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_decode_const.svh
      :language: systemverilog

.. dropdown:: ``ctrl_npu_decoder.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv
      :language: systemverilog

.. dropdown:: ``ctrl_npu_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv
      :language: systemverilog

Global Scheduler + controller top
----------------------------------

* ``Global_Scheduler.sv`` — cross-engine arbitration: orders memory
  transfers vs. compute, handles ACC / FINDEMAX hazards.
* ``npu_controller_top.sv`` — controller top-level wrapper; instantiates
  frontend + decode/dispatch + scheduler and wires them to the ``npu_if``
  bundle.

.. dropdown:: ``Global_Scheduler.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/Global_Scheduler.sv
      :language: systemverilog

.. dropdown:: ``npu_controller_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/npu_controller_top.sv
      :language: systemverilog

FSM Out Logic (status aggregation)
-----------------------------------

* ``fsmout_npu_stat_collector.sv`` — samples per-engine busy/done flags.
* ``fsmout_npu_stat_encoder.sv`` — encodes collected flags into the
  32-bit status register exposed by ``AXIL_STAT_OUT``.

.. dropdown:: ``fsmout_npu_stat_collector.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_fsm_out_Logic/fsmout_npu_stat_collector.sv
      :language: systemverilog

.. dropdown:: ``fsmout_npu_stat_encoder.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_fsm_out_Logic/fsmout_npu_stat_encoder.sv
      :language: systemverilog
