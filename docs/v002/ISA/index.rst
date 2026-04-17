==================================
Instruction Set Architecture (ISA)
==================================

The pccx v002 ISA is a **fixed-length, VLIW-style 64-bit format** with
five opcodes: GEMV, GEMM, MEMCPY, MEMSET, and CVO. The design follows
three principles:

- **Hardware independence**: the encoding is decoupled from any specific
  device's resource budget.
- **CISC-style macros**: one instruction kicks off thousands of MAC
  cycles.
- **Dispatch-centric**: instructions are decoded into control μops and
  memory μops as soon as they land, and those are handed off to the
  back end.

.. toctree::
   :maxdepth: 1

   encoding
   instructions
   dataflow

.. note::

   The current ISA type definitions live in the v001 codebase
   (:file:`codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv`)
   as a SystemVerilog package. They will be migrated and finalized as
   part of v002.
