=============================
GEMM Core (Systolic Array)
=============================

The GEMM core handles the large matrix-matrix multiplications that
dominate the **prefill** stage of a Transformer. pccx v002 places **two
32 × 16 2D systolic arrays** side by side, yielding a theoretical peak of
**819 GMAC/s at 400 MHz**.

.. note::

   GEMM is used mainly in prefill (long-prompt initial processing) and in
   Attention's ``Q·Kᵀ`` and ``score·V``. For the decoding-dominant GEMV
   operation, see :doc:`gemv_core`.

1. Operands
============

GEMM computes the product of a **Weight (N × N)** matrix and an
**Activation (N × N)** matrix.

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMM_3_v002.png
   :align: center
   :width: 80%
   :alt: GEMM operands — weight and activation matrices

   **Figure GEMM-Operands.** GEMM takes two 2D tensors (weight and
   activation) and produces a partial-sum result. Both operands are
   defined as Row × Col; tile shapes are chosen by the software layer.

2. Array Configuration
=======================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Value
   * - Array dimensions
     - **32 (M) × 16 (K)**
   * - Number of arrays
     - **2** (dual array)
   * - DSP per PE
     - **1** (DSP48E2)
   * - MAC / clk per PE
     - **2** (dual-channel bit packing, see :doc:`dsp48e2_w4a8`)
   * - Total MAC / clk per array
     - **32 × 16 × 2 = 1,024**
   * - Total MAC / clk (× 2 arrays)
     - **2,048**
   * - Peak throughput
     - **2,048 × 400 MHz = 819 GMAC/s**

3. Array Structure and Dataflow
================================

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMM_1_v002.png
   :align: center
   :width: 92%
   :alt: GEMM systolic array block diagram

   **Figure GEMM-Array.** The systolic array is a **Weight Stationary**
   structure: weights enter from the left, activations from the top, and
   partial sums collect in the Result Accumulator at the bottom. The
   zoomed-in green box shows the internals of a single PE.

3.1 Weight Stationary Reuse
----------------------------

During GEMM, the same weights are reused across many activation tiles.
Rather than re-reading weights from the HP ports for every tile, we
**preload them into the flip-flops inside each PE**.

1. The Weight Buffer pulls a tile's worth of INT4 weights from the HP
   ports.
2. The Weight Dispatcher staggers the loads and places them on each PE's
   Port A.
3. Port A is packed as **{W₁ | 19-bit guard | W₂}** for dual-channel
   packing (:doc:`dsp48e2_w4a8` §2).
4. The same weights are reused for the full activation tile sweep.

3.2 Activation Streaming
-------------------------

1. The relevant INT8 activation tile is streamed from the L2 cache into
   the top of the systolic array.
2. A per-column **fmap staggered delay** keeps pipeline timing aligned.
3. Activations propagate top-to-bottom through the array; the output row
   axis maps onto the array's column direction.

.. mermaid::

   flowchart LR
     subgraph Host[Host DDR4]
       W[Weights INT4]
     end
     WB[Weight Buffer<br/>BRAM FIFO] -->|staggered| PE[(PE Grid<br/>32×16)]
     L2[L2 Cache<br/>URAM] -->|activations INT8| PE
     PE -->|partial sums| RA[Result Accumulator]
     RA -->|scale / requant| L2
     W --> WB
     classDef cache fill:#e8f0fe,stroke:#4c6ef5,color:#1a2e66;
     classDef mem fill:#fff4e0,stroke:#f08c00,color:#663c00;
     class WB,L2 cache
     class Host mem

3.3 Accumulation
-----------------

- Partial sums accumulate into the DSP48E2's 48-bit P register across K
  depth.
- Dual-channel bit packing caps safe accumulation at
  ``N_max = 2²² / 2¹⁰ = 4,096`` cycles.
- For K > 4,096, software tiles the layer (K-split).

3.4 Result Extraction & Sign Recovery
--------------------------------------

Once accumulation finishes, a **single post-processing cycle** separates
the upper and lower channels and restores the borrow caused by a negative
lower accumulator. The math and the Verilog implementation live in
:doc:`dsp48e2_w4a8`.

4. PE Microarchitecture
========================

.. figure:: ../../../assets/images/Architecture/v002/Processing_Elements_GEMM_2_v002.png
   :align: center
   :width: 70%
   :alt: GEMM PE internals

   **Figure GEMM-PE.** A single PE consists of the weight / activation
   input flip-flops, the DSP48E2 multiplier, the P register, the
   accumulator, and on/off control signals. The ``Instruction`` port
   carries μops extracted from the instruction (enable / flush /
   accumulate-done), and ``P_OUT`` is active only when accumulation
   completes, routing into the Result Accumulator.

Every DSP48E2 pipeline register is enabled to hit 400 MHz timing closure.

.. list-table::
   :header-rows: 1
   :widths: 10 25 65

   * - Stage
     - Logic
     - Description
   * - S0
     - Weight Register
     - Latches both 4-bit weights in the 27-bit packed form. Stable
       during reuse.
   * - S1
     - Activation Register
     - Receives an INT8 activation from the upstream neighbor PE.
   * - S2
     - DSP48E2 M stage
     - Port A × Port B (27 × 18-bit) multiply.
   * - S3
     - DSP48E2 P stage (ACC)
     - 48-bit P register accumulation. ON/OFF control handles flush / hold.
   * - S4
     - Propagate
     - Forwards the activation to the next PE. ``P_OUT`` asserts only on
       accumulate-done.

5. Post-Processing
===================

Beyond the Result Accumulator, data flows through the following stages.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Stage
     - Function
   * - **Result Accumulator**
     - Collects PE results at the array boundary and performs the
       upper/lower channel split with sign recovery.
   * - **Post-Process**
     - ``flags.w_scale`` applies the weight scale, then the activation
       scale; ``flags.findemax`` updates the e_max register; finally an
       INT8 requantization.
   * - **L2 Writeback**
     - Writes to the L2 cache address named by the ISA ``dest_reg`` field.

Relevant ISA flags are detailed in the GEMM section of
:doc:`../ISA/instructions`.

6. Scalability
===============

The array dimensions are exposed as SystemVerilog ``generate``
parameters.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - KV260 default
     - Meaning
   * - ``MAT_ROWS``
     - 32
     - Number of PEs in the systolic array's M direction.
   * - ``MAT_COLS``
     - 16
     - Number of PEs in the K direction. Physical size, independent of the
       safe-accumulation limit.
   * - ``MAT_INSTANCES``
     - 2
     - Number of array instances. Placed on the right side of the
       floorplan.

On KV260 the 32 × 16 × 2 configuration consumes 1,024 DSP48E2 slices —
about 82% of the device's 1,248-slice budget.
