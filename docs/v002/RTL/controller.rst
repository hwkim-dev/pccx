:rtl_source: hw/rtl/NPU_Controller/npu_controller_top.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv,
             hw/rtl/NPU_Controller/Global_Scheduler.sv

============================
NPU Controller Modules
============================

1. Controller Top
==================

``npu_controller_top.sv`` integrates the AXI-Lite frontend, instruction
decoder, dispatcher, and global scheduler into a single unit.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/npu_controller_top.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/npu_controller_top.sv

2. Instruction Decoder
=======================

``ctrl_npu_decoder.sv`` parses the 64-bit VLIW instruction word: strips
the 4-bit opcode and routes the 60-bit body into the appropriate
typed struct (``GEMV_op_x64_t``, ``memcpy_op_x64_t``, etc.).

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv

3. Instruction Dispatcher
==========================

``ctrl_npu_dispatcher.sv`` resolves Constant Cache pointer lookups
(shape / size / scale), checks for address and resource hazards, and
issues per-core control μops to GEMM, GEMV, CVO, and mem_dispatcher.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv

4. Global Scheduler
====================

``Global_Scheduler.sv`` tracks in-flight async instructions, maintains
the dependency scoreboard, and gates new dispatches when a hazard is
detected.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/Global_Scheduler.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/Global_Scheduler.sv

.. admonition:: Last verified against
   :class: note

   Commit ``773bd82`` @ ``hwkim-dev/pccx-FPGA-NPU-LLM-kv260`` (2026-04-21).

.. seealso:: :doc:`/docs/v002/ISA/dataflow` — dependency and completion tracking.
