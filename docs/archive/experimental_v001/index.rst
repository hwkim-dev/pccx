Archive: v001 Experimental Architecture
=======================================

   [!WARNING] This architecture is a preliminary (v001) experimental
   design. Although structurally superior, it was engineered with a
   heavy inclination toward GEMM (Matrix) computations. Because local
   LLM environments are predominantly bound by GEMV (Vector) operations,
   this branch has been currently archived in favor of an optimized
   structure.

|Status Archived| |SystemVerilog RTL| |Target Hardware| |Quantization
Precision|

.. toctree::
   :hidden:
   :maxdepth: 1

   Architecture/v001_architecture
   Drivers/ISA
   Drivers/ISA_Spreadsheet
   Drivers/v001_API

--------------

Project Overview
----------------

**pccx** (formerly uXC) is a customized SystemVerilog-based Neural Processing Unit (NPU)
engineered fundamentally from the ground up to accelerate the quantized
**Gemma 3N E4B** Large Language Model on the bare-metal Xilinx Kria
KV260 FPGA (400 MHz). The architecture is meticulously designed to push
the absolute physical constraints of the KV260 platform, exploiting its
1,248 DSP48E2 slices and 144 BRAMs to their functional ceiling.

-  **Software Baseline**:
   `llm-lite <https://github.com/hwkim-dev/llm-lite>`__ (x64 CPU
   reference implementation)
-  **Full-Stack Co-Design**: Hardware accelerator (SystemVerilog),
   Trace-Driven validation model (Python), and an AXI DMA memory
   pipeline.

--------------

Quick Menu
----------

.. container:: grid cards

   -  `Architecture Overview <Architecture/v001_architecture.md>`__

      --------------

      Illustrates the internal NPU architecture, the 3-tier core system
      decoupled model, and the memory transition layer layout.

   -  `ISA Specification <Drivers/ISA.md>`__

      --------------

      Explains the 64-bit VLIW core, Opcode routing design, register
      mappings, and pipeline scheduling methodologies.

   -  `ISA Spreadsheet <Drivers/ISA_Spreadsheet.md>`__

      --------------

      Provides an internal spreadsheet-view breakdown of the overall
      modular ISA structure.

   -  `C API Detail <Drivers/v001_API.md>`__

      --------------

      Focuses on the primary wrapping interfaces of ``pccx_v1_api.c`` and
      ``pccx_v1_api.h`` targeting the active NPU host controller.

   -  `Agents Architecture <agents.md>`__

      --------------

      Concept logic on the autonomous agent micro-scheduling model
      operating inside the decoupled dataflow pipeline.

--------------

Quantization Strategy: W4A16 with BF16 Activations
--------------------------------------------------

The primary core computational path operates strictly at **W4A16
precision**:

+---------------+---------------+------------------+------------------+
| Data          | Type          | Width            | Notes            |
+===============+===============+==================+==================+
| **Weight**    | INT4          | 4-bit            | Streamed through |
|               |               |                  | HP Ports and     |
|               |               |                  | consumed purely  |
|               |               |                  | as an INT4 layer |
+---------------+---------------+------------------+------------------+
| **Feature     | BF16          | 16-bit           | Undergoes        |
| Map**         |               |                  | conversion from  |
|               |               |                  | BF16             |
|               |               |                  | :ma              |
|               |               |                  | th:`\rightarrow` |
|               |               |                  | 27-bit           |
|               |               |                  | Fixed-Point for  |
|               |               |                  | native MAC       |
|               |               |                  | arithmetic       |
+---------------+---------------+------------------+------------------+
| **            | INT48         | 48-bit           | Accumulated      |
| Accumulator** |               |                  | recursively      |
|               |               |                  | through the      |
|               |               |                  | P-Register of    |
|               |               |                  | the DSP48E2      |
|               |               |                  | blocks           |
+---------------+---------------+------------------+------------------+
| **SFU I/O**   | BF16          | 16-bit           | Reconstructed as |
|               |               |                  | BF16             |
|               |               |                  | Po               |
|               |               |                  | st-Normalization |
|               |               |                  | heading for      |
|               |               |                  | Non-Linear       |
|               |               |                  | operations       |
+---------------+---------------+------------------+------------------+

Precision Promotion Flow
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: mermaid

   graph TD
       A[Weight: INT4] --> MAC[DSP48E2 MAC]
       B[FMap: BF16 → 27-bit fixed-pt] --> MAC
       MAC -->|Accumulator| C[INT48]
       C -->|Barrel Shift + LOD| D[Normalization: BF16]
       D -->|SFU / CORDIC| E[Non-Linear Ops: exp, RMSNorm, Softmax...]
       E --> F[Output: BF16 to next layer]

At the transition segment toward the Non-Linear operations loop (Complex
Vector Operation), the computation elevates precisely into **BF16**.

--------------

Compute Engines
---------------

+-----------+----------------+--------------+--------------+-----------+
| Engine    | Operation      | Weights      | Activation   | Ac        |
|           |                | Input        | Fetch        | cumulator |
+===========+================+==============+==============+===========+
| **Matrix  | GEMM (prefill, | HP0/1 (32    | BF16         | INT48     |
| Core**    | projections)   | INT4/clk)    | :math:`      | (DSP48E2) |
|           |                |              | \rightarrow` |           |
|           |                |              | 27-bit       |           |
|           |                |              | fixed-pt     |           |
+-----------+----------------+--------------+--------------+-----------+
| **Vector  | GEMV           | HP2/3 (32    | BF16         | INT48     |
| Core**    | (              | INT4/clk     | :math:`      | (DSP48E2) |
|           | autoregressive | each)        | \rightarrow` |           |
|           | decode)        |              | 27-bit       |           |
|           |                |              | fixed-pt     |           |
+-----------+----------------+--------------+--------------+-----------+
| **CVO     | Non-linear ops | N/A          | BF16 Stream  | BF16      |
| Core**    | (Softmax,      |              | via L2       |           |
|           | GELU, RoPE)    |              |              |           |
+-----------+----------------+--------------+--------------+-----------+

..

   Applying a structural **Decoupled Dataflow** design principle ensures
   operation instructions execute asynchronously. Distributed from the
   Global Pipeline across distinct modules, it completely prevents
   architectural stalling and pushes mathematical hardware throughput to
   its peak.

.. |Status Archived| image:: https://img.shields.io/badge/Status-Archived-red
.. |SystemVerilog RTL| image:: https://img.shields.io/badge/RTL-SystemVerilog-green
.. |Target Hardware| image:: https://img.shields.io/badge/Target-Kria_KV260-orange
.. |Quantization Precision| image:: https://img.shields.io/badge/Precision-W4A16_BF16-green
