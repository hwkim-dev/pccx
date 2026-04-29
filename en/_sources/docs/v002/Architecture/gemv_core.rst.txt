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
     - **4 total** (``VecPipelineCnt = 4`` in ``device_pkg.sv``; split 2
       per slice across upper / lower halves of the floorplan)
   * - Per-core multiply width
     - **32 MAC / clk** (INT4 × BF16, LUT-based pre-computation)
   * - Stage-1 accumulator DSPs
     - **16 DSP48E2** per core (32 partial products → 16 pair-sums)
   * - Reduction tree
     - **5 stages** (32 → 16 → 8 → 4 → 2 → 1)
   * - Peak throughput
     - **32 MAC × 4 cores × 400 MHz = 51.2 GMAC/s**

3. Core Internals
==================

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMV_1_v002.png
   :align: center
   :width: 90%
   :alt: GEMV core pipeline and reduction tree

   **Figure GEMV-Core.** The **Pre-Process** block dequantizes one
   activation row and one weight column, then 32 LUT-based multipliers
   compute ``W × A`` in a single cycle. The 32 partial products feed a
   5-stage reduction adder tree (Stage 1: 16 DSP48E2 slices; Stages 2–5:
   LUT adders) that collapses to a scalar. The **Post-Process** block
   finally applies scale / bias and writes the result into the REGISTER.

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
3. 32 LUT-based multipliers execute ``W × A`` in parallel in a single
   clock. Because ``W`` is INT4, the 16 possible ``A × w`` products are
   pre-computed in the LUT; the actual weight bits only *select* the
   matching entry.

3.3 Reduction Tree
-------------------

Each core's 32 partial products collapse to a single scalar through a
5-stage adder tree, with a pipeline register between every stage for
400 MHz closure.

.. _v002-gemv-reduction-fig:
.. figure:: /_static/diagrams/v002_gemv_reduction.svg
   :align: center
   :width: 600px
   :name: fig-gemv-reduction

   **Figure GEMV-Reduction.** GEMV uses a 32-lane reduction tree to
   collapse partial products into a single scalar. Stage 1 uses DSP48E2
   slices for high-speed addition; subsequent stages use LUT-based
   FP/Int adders.

Stage 1 uses the DSP48E2 ``A:B + C`` (ONE48) mode purely to add two
...
adjacent partial products (16 DSP slices per core). Stages 2–5 use
LUT-based adders to keep the DSP budget small. The implementation
inherits from v001's ``GEMV_reduction.sv`` and
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

The GEMV core fuses W4 dequantization and the multiply into a single LUT
pre-computation.

- ``GEMV_generate_lut.sv`` (inherited from v001) produces, for each BF16
  activation ``A``, all **16 pre-computed products** ``A × w`` for the
  possible INT4 weight values (-8 to +7).
- This runs in parallel across all 32 activation positions, so each core
  has **32 × 16 = 512 pre-computed products** ready every clock.
- When the actual weight arrives, the 4-bit pattern just *indexes* the
  LUT — the matching value flows straight into the Stage-1 accumulator
  DSP.
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
