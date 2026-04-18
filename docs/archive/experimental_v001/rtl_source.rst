================================
RTL Source Reference (v001)
================================

This page embeds the key SystemVerilog source files from the v001 RTL
tree at :file:`codes/v001/hw/rtl/`. All files are read-only archives —
v001 is no longer under active development.

.. note::

   The v002 RTL lives in a separate repository:
   `hwkim-dev/pccx-FPGA-NPU-LLM-kv260
   <https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260>`_.
   For v002 source, see :doc:`/docs/v002/RTL/index`.

1. ISA Type Package
===================

``isa_pkg.sv`` is the authoritative definition of every instruction
encoding, opcode enum, and micro-op struct. All RTL modules
``import isa_pkg::*;``.

.. literalinclude:: ../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
   :language: systemverilog
   :caption: codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv

2. NPU Top-Level
================

``NPU_top.sv`` wires all sub-cores together and exposes the AXI-Lite
control port, four HP weight ports, and the ACP feature-map bus.

.. literalinclude:: ../../../codes/v001/hw/rtl/NPU_top.sv
   :language: systemverilog
   :lines: 1-80
   :caption: codes/v001/hw/rtl/NPU_top.sv (port declaration, first 80 lines)

3. Matrix Core — Systolic Top
==============================

``GEMM_systolic_top.sv`` wraps the 2-D systolic array. It accepts
weight tiles from HP0/HP1 and activation rows from the L2 cache, and
streams results to the normalizer.

.. literalinclude:: ../../../codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
   :language: systemverilog
   :caption: codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_top.sv

4. Vector Core — GEMV Top
==========================

``GEMV_top.sv`` instantiates 4 parallel GEMV lanes. Each lane reads
activations from its own L1 cache slice and weights from HP2/HP3.

.. literalinclude:: ../../../codes/v001/hw/rtl/VEC_CORE/GEMV_top.sv
   :language: systemverilog
   :caption: codes/v001/hw/rtl/VEC_CORE/GEMV_top.sv

5. CVO Core (SFU) Top
======================

``CVO_top.sv`` orchestrates the CORDIC and LUT-based function units
for non-linear operations (Softmax, GELU, RMSNorm, RoPE).

.. literalinclude:: ../../../codes/v001/hw/rtl/CVO_CORE/CVO_top.sv
   :language: systemverilog
   :caption: codes/v001/hw/rtl/CVO_CORE/CVO_top.sv

6. NPU Controller Top
======================

``npu_controller_top.sv`` integrates the AXI-Lite frontend, instruction
decoder, dispatcher, and global scheduler.

.. literalinclude:: ../../../codes/v001/hw/rtl/NPU_Controller/npu_controller_top.sv
   :language: systemverilog
   :caption: codes/v001/hw/rtl/NPU_Controller/npu_controller_top.sv
