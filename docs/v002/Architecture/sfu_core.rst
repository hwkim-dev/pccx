======================================
SFU Core (Complex Vector Operations)
======================================

The SFU (Special Function Unit) handles the Transformer's non-linear
operations — **Softmax**, **GELU**, **RMSNorm**, and **RoPE**. In the
ISA, these appear under the **CVO (Complex Vector Operation)** opcode
family.

1. Configuration
=================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Value
   * - Unit dimensions
     - **32 × 1 (per instance)**
   * - Instances
     - **4** per slice (upper + lower = 2 slices)
   * - Internal precision
     - **BF16 / FP32** (dynamic promotion)
   * - Supported functions
     - **EXP, SQRT, GELU, SIN, COS, REDUCE_SUM, SCALE, RECIP**

2. Precision Promotion Strategy
================================

**Inputs and outputs** stay in INT8 or BF16 to keep L2 bandwidth usage
reasonable, but **internal computation** is promoted as follows.

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - Function
     - Input
     - Internal
     - Rationale
   * - ``CVO_EXP``
     - BF16
     - FP32
     - Overflow protection (softened further by the ``sub_emax`` flag in
       softmax).
   * - ``CVO_SQRT``
     - BF16
     - FP32
     - Numerical stability for RMSNorm's ``1/sqrt(var + ε)``.
   * - ``CVO_GELU``
     - BF16
     - BF16
     - Approximation (tanh or rational) suffices.
   * - ``CVO_SIN / COS``
     - BF16
     - FP32
     - Prevents phase drift in RoPE.
   * - ``CVO_REDUCE_SUM``
     - BF16 / INT8
     - FP32
     - Minimizes long-running accumulation error.
   * - ``CVO_SCALE``
     - INT8 / BF16
     - BF16
     - Dequantize × scalar.
   * - ``CVO_RECIP``
     - BF16
     - FP32
     - Softmax denominator, layer-norm divisor.

3. Implementation Techniques
=============================

3.1 CORDIC + LUT Hybrid
------------------------

Inherits from v001's ``CVO_cordic_unit.sv`` and ``CVO_sfu_unit.sv``:

- **CORDIC**: iterative-convergence operators — ``SIN``, ``COS``,
  ``SQRT``, ``RECIP``. 15–20 pipeline stages.
- **LUT + polynomial correction**: ``EXP`` and ``GELU``. The LUT produces
  a coarse estimate; a 2nd- or 3rd-order polynomial refines it.

3.2 Reduction
--------------

``CVO_REDUCE_SUM`` folds 32 lanes through a 5-stage adder tree. It's the
building block for softmax's denominator.

3.3 Softmax Fast Path
----------------------

Softmax decomposes into a 3-instruction sequence.

.. mermaid::

   sequenceDiagram
     autonumber
     participant D as Dispatcher
     participant S as SFU
     participant E as e_max reg
     D->>S: CVO_REDUCE_SUM (flags.findemax)
     S->>E: update e_max
     D->>S: CVO_EXP (flags.sub_emax)
     S->>S: exp(x − e_max)
     D->>S: CVO_RECIP × CVO_SCALE
     S-->>D: softmax(x)

The ``findemax`` and ``sub_emax`` flags perform **online
max-normalization** in hardware, so the software layer never has to run
a separate scan pass.

4. Pipeline Integration
========================

The SFU is wired to the GEMV core through a **direct FIFO**, enabling
two tight loops.

- GEMV → SFU: Attention's ``Q·K^T → softmax`` and the FFN's GEMV → GELU
  hand-offs skip the L2 round trip.
- SFU → GEMV: the softmax output is multiplied with V immediately, again
  without going through L2.

The SFU supports **async execution** (the ``async_e`` ISA field) so the
controller can dispatch the next instruction without waiting for
completion. Completion notifications are handled by
``fsmout_npu_stat_collector`` (inherited from v001).

5. Physical Placement
======================

On the floorplan (:doc:`floorplan`) the SFU appears four times per
slice, for a total of eight units. They sit adjacent to the GEMV cores
so the direct FIFO stays short.

6. Scalability
===============

Adding a function to the CVO table (``cvo_func_e`` in
:doc:`../ISA/instructions`) requires:

1. Extending the ``cvo_func_e`` enum (4 bits total, 8 of 16 used so far).
2. Adding the corresponding CORDIC / LUT block inside the SFU.
3. Updating the Dispatcher's decode table.

The hardware function slots are gated by a generate parameter
``SFU_ENABLE_MASK``, letting you drop unused functions from synthesis to
save LUTs.
