:rtl_source: hw/rtl/NPU_Controller/npu_controller_top.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv,
             hw/rtl/NPU_Controller/Global_Scheduler.sv

============================
NPU Controller Modules
============================

1. Controller Top
==================

``npu_controller_top.sv`` integrates the AXI-Lite frontend, instruction
decoder, and global scheduler into a single controller boundary.

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

3. Global Scheduler
====================

``Global_Scheduler.sv`` receives decoded instruction fields, emits
per-core control μops, tracks in-flight async instructions, maintains
the dependency scoreboard, and gates new dispatches when a hazard is
detected.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/Global_Scheduler.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/Global_Scheduler.sv

.. admonition:: Last verified against
   :class: note

   Current public ``pccx-FPGA-NPU-LLM-kv260`` ``main`` clone used by the
   documentation CI. Controller source references should stay aligned with
   files present in that public RTL tree.

.. seealso:: :doc:`/docs/v002/ISA/dataflow` — dependency and completion tracking.
