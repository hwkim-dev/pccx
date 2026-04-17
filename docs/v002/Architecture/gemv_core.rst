==================
GEMV Core
==================

The GEMV core handles the dominant operation during **autoregressive
decoding** — the matrix-vector product ``y = W x``. In batch-1,
sequence-1 decoding, 85 – 98% of the FLOPs come from GEMV, which makes
GEMV throughput **directly proportional to tokens-per-second**.

.. important::

   Running decoding on a 2D systolic array alone drops effective
   utilization to ``1/32`` (only a single row is active). pccx v002 fixes
   this with a dedicated **1D GEMV core** placed alongside the GEMM
   array; both paths share the same L2 cache, giving the architecture its
   heterogeneous character.

1. Operands
============

GEMV's inputs are an **activation vector of length N** and an **N × N
weight matrix**.

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMV_2_v002.png
   :align: center
   :width: 80%
   :alt: GEMV operands — activation vector × weight matrix

   **Figure GEMV-Operands.** Activation is a 1 × N row vector, Weight is
   an N × N matrix. Their inner product produces a new length-N output
   vector. Both Attention's ``Q·Kᵀ`` and FFN projections follow this
   same shape.

2. Configuration
=================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Value
   * - Per-core dimensions
     - **32 (K) × 1 (M)**
   * - Number of cores
     - **4** (per slice; 2 slices total — upper and lower)
   * - Pipeline width
     - **8 MAC** (8 DSP48E2 lanes)
   * - Reduction tree
     - **3 stages** (8 → 4 → 2 → 1)
   * - Peak throughput
     - **32 MAC × 4 cores × 400 MHz = 51.2 GMAC/s**

3. Core Internals
==================

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMV_1_v002.png
   :align: center
   :width: 90%
   :alt: GEMV core pipeline and reduction tree

   **Figure GEMV-Core.** The **Pre-Process** block dequantizes one
   activation row and one weight column, then fans the data out to 8
   pipelined DSP lanes. Each lane's result feeds a 3-stage reduction
   adder tree that collapses to a scalar; the **Post-Process** block then
   applies scale and bias and writes back to the REGISTER.

3.1 Weight Streaming
---------------------

During decoding each layer's weights are used **exactly once per token**
— there is no reuse. GEMV therefore uses **Weight Streaming** rather
than Weight Stationary.

- Weights stream continuously from HP2 / HP3.
- They pass through the Weight Buffer into each core's **W-side
  Pre-Process** stage.
- The Weight Buffer is just a circular FIFO; no residency required.

3.2 Activation Reuse
--------------------

The activation vector ``x`` lives in the L2 cache, and the four GEMV
cores **broadcast** the same vector among themselves.

1. Preload an activation tile from L2 into the per-core L1 cache.
2. **Pre-Process** dequantizes INT8 → BF16 and applies the scale.
3. 8 MAC units execute ``W × A`` in parallel.

3.3 Reduction Tree
-------------------

The 8 MAC results collapse through a 3-stage adder tree, with pipeline
registers between stages for timing closure.

.. mermaid::

   flowchart TB
     M0([MAC₀]) --> R0a((+))
     M1([MAC₁]) --> R0a
     M2([MAC₂]) --> R0b((+))
     M3([MAC₃]) --> R0b
     M4([MAC₄]) --> R0c((+))
     M5([MAC₅]) --> R0c
     M6([MAC₆]) --> R0d((+))
     M7([MAC₇]) --> R0d
     R0a --> R1a((+))
     R0b --> R1a
     R0c --> R1b((+))
     R0d --> R1b
     R1a --> R2((+))
     R1b --> R2
     R2 --> OUT[/Scalar/]

The implementation inherits from v001's ``GEMV_reduction.sv`` and
``GEMV_reduction_branch.sv``.

3.4 Accumulation & Post-Processing
-----------------------------------

- The reduction result lands in a **Result Accumulator** and is summed
  with subsequent weight columns to complete a full row's partial sum.
- Post-Process applies weight-scale / activation-scale / bias.
- The final INT8-requantized result goes back to either the L2 cache or
  the direct FIFO to the SFU.

4. Parallelization Strategy
============================

The four GEMV cores support two parallelization modes. The ISA's
``parallel_lane`` (5-bit) field selects the number of active cores and
the partition axis.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Mode
     - Description
   * - **Row Parallelism**
     - Four cores each compute a different subset of output rows. The
       weight matrix is striped along the row axis; the activation is
       shared.
   * - **Head Parallelism**
     - Four cores handle different Multi-Head Attention heads. Both
       activation (Q) and weights are partitioned along the head axis.

5. Embedded Lookup Table
=========================

Each GEMV core embeds a **16-entry LUT** dedicated to W4 dequantization.

- Reuses ``GEMV_generate_lut.sv`` from v001.
- Maps a 4-bit weight directly to its BF16 real value.
- Scale factors are indexed from the Constant Cache.

6. Interaction with Softmax / Normalize
========================================

GEMV's output is consumed mainly by two patterns.

1. **Attention**: ``Q·Kᵀ`` → ``CVO_EXP`` / ``REDUCE_SUM`` (SFU) →
   ``V·softmax`` (back to GEMV)
2. **FFN projection**: GEMV → ``CVO_GELU`` / ``CVO_SCALE`` (SFU) → next
   GEMV

The GEMV ↔ SFU path bypasses the L2 cache via a **direct FIFO**, cutting
round-trip latency. See :doc:`sfu_core` for details.
