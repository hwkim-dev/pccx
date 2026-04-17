==================================================
Gemma 3N — FFN Gaussian Top-K Sparsity
==================================================

Gemma 3N's early FFN layers use **Gaussian Top-K Sparsity** to zero out
95 % of the gate activations. Because the mechanism replaces a sort with
two reductions, it maps cleanly to the pccx v002 SFU.

1. What the Rule Does
======================

For layers 0 through 9 (10 layers total), the gate-projection output is
thresholded so that only the top **5 %** of activations survive:

.. math::

   cutoff = Mean(gate\_raw) + 1.6448536 \times Std(gate\_raw)

.. math::

   sparse\_gate = \max(gate\_raw - cutoff,\ 0)

.. math::

   hidden = GELU(sparse\_gate) \times up\_out

The constant ``1.6448536`` is the Z-score for the 95th percentile of a
standard normal distribution; the rule assumes the gate outputs are
approximately Gaussian, which empirically holds for FFN pre-activations
in practice.

Layers 10–34 skip this step and use the standard GELU gate:

.. math::

   hidden = GELU(gate\_raw) \times up\_out

2. Why It's Done This Way
==========================

- **Sorting is expensive on parallel hardware.** A real "top 5 %"
  requires a sort over 16 384 elements — not a good shape for an NPU.
- **Reductions are cheap.** ``Mean`` and ``Std`` are two ``CVO_REDUCE_SUM``
  calls on the same buffer, plus a pair of ``CVO_SCALE`` calls. Total
  cost: a handful of cycles, negligible compared to a
  ``16 384 × 2048`` ``GEMV``.
- **A Gaussian approximation is accurate enough.** The 5 % boundary
  isn't sharp; small misclassifications at the edge don't hurt
  downstream accuracy.

3. Pipeline View
=================

.. mermaid::

   flowchart TD
       X["Input x_n2"] --> GateOp(("x · W_gate^T"))
       GateOp --> GateOut["gate_raw (16384)"]
       GateOut --> CalcStats["Reduce-sum × 2<br/>→ Mean and Std"]
       CalcStats --> Threshold["cutoff = Mean + 1.6448·Std"]
       GateOut --> FilterOp
       Threshold --> FilterOp["max(gate_raw - cutoff, 0)"]
       FilterOp --> SparseGate["sparse_gate<br/>(~95% zeros)"]
       SparseGate --> GELU["GELU"]
       GELU --> MultOp(("element-wise ×"))
       X --> UpOp(("x · W_up^T"))
       UpOp --> UpOut["up_out (16384)"]
       UpOut --> MultOp
       MultOp --> FFN_Mid["hidden → W_down"]
       style FilterOp fill:#ffcc80,stroke:#e65100,stroke-width:2px
       style SparseGate fill:#c8e6c9,stroke:#388e3c

4. Mapping onto pccx v002
==========================

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Operation
     - Instruction
     - Notes
   * - :math:`\mathrm{Mean}(gate\_raw)`
     - ``CVO_REDUCE_SUM`` followed by ``CVO_SCALE`` with
       :math:`1/16384`
     - Scale preloaded via ``MEMSET``.
   * - :math:`\mathrm{Var}(gate\_raw)`
     - ``CVO_SCALE`` (square) → ``CVO_REDUCE_SUM`` →
       ``CVO_SCALE`` (:math:`1/16384`) → ``CVO_SQRT``
     - Four CVO calls. Can overlap with the ``W_up`` GEMV.
   * - ``cutoff = μ + 1.645·σ``
     - Scalar compute done in the SFU's ALU
     - Single cycle.
   * - ``max(gate_raw - cutoff, 0)``
     - Custom CVO fused with GELU? **No** — currently realized as
       ``CVO_SCALE`` + ReLU masking inside the GELU kernel
     - The SFU's GELU path includes a configurable bias-and-clip front
       end for exactly this reason.
   * - Elementwise multiply with ``up_out``
     - Direct FIFO inside the GEMV / SFU pair
     - No L2 round-trip.

5. Throughput Impact
=====================

With 95 % of ``sparse_gate`` equal to zero, the downstream
``W_down`` GEMV can skip masked rows entirely. The pccx v002 driver
emits a sparse ``GEMV`` variant for layers 0–9: the weight streamer
compares each row mask and skips DSP cycles when the mask is zero.

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Layer range
     - Gate density
     - FFN GMAC/s (effective)
     - Notes
   * - Layers 0–9
     - ~5 %
     - ~40 GMAC/s per token
     - Dominated by ``W_gate`` + ``W_up``; ``W_down`` is nearly free.
   * - Layers 10–34
     - 100 %
     - ~130 GMAC/s per token
     - Full dense FFN.

.. note::

   The sparsity mask is computed **on the fly** from the gate output of
   the current token — it is not learned. The driver must therefore
   issue the ``MEMCPY`` for the skip mask from L2 back into the weight
   streamer after the cutoff is known; on pccx v002 this is done with
   ``MEMCPY async=1`` overlapped with the ``W_up`` GEMV.

.. seealso::

   - Full FFN spec: :doc:`gemma3n_pipeline` §4.D.
   - SFU function codes: :doc:`../ISA/instructions` §4.
