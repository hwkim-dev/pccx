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

.. admonition:: Download the offline guidebook (PDF)
   :class: tip

   A signoff-ready typeset version of this ISA reference — same tables,
   same numbers, offline-readable — is downloadable as a PDF:

   :download:`pccx v002 ISA Guidebook (PDF) <../../../_static/downloads/pccx-isa-v002.pdf>`

   The PDF is regenerated from ``main.tex`` at the repository root; the
   LaTeX source is the single authoring entry point for the offline
   book, while this HTML portal remains the living reference for the
   web.

.. note::

   The authoritative ISA type definitions live in the v002 RTL repo at
   :file:`hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv`
   (external: `hkimw/pccx-FPGA-NPU-LLM-kv260
   <https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260>`_). Encoding
   tables on the pages below must stay in sync with that package — see
   :doc:`../RTL/isa_pkg`.
