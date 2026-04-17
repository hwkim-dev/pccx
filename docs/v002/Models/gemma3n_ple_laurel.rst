=======================================================
Gemma 3N — LAuReL and PLE Calibration Modules
=======================================================

Gemma 3N uses two calibration paths that sit outside the main attention
/ FFN stack: **LAuReL** (a parallel low-rank branch combined with the
attention output) and **PLE** (a per-layer depth embedding injected
into the shadow streams). Both have very specific scaling and routing
rules; getting them wrong means the model still *runs* but the output
distribution drifts silently.

1. LAuReL: Parallel Attention Calibration
==========================================

LAuReL processes the input concurrently with Attention, and its output
is merged with the Attention output **before** the first residual
connection.

1.1 Math
---------

.. math::

   x_{out} = \frac{\text{Attention}(x) + \text{LAuReL}(x_{norm})}{\sqrt{2.0}}

Important: LAuReL sees :math:`x_{norm}` (the RMSNormed input),
**not** the raw :math:`x`. See :doc:`gemma3n_pipeline` §4.C for the
full formula including the post-attention RMSNorm and the residual add.

1.2 Diagram
------------

.. mermaid::

   graph TD
       X["Input x"] --> N["RMSNorm (input_ln)"]
       N --> Attn["Attention block"]
       N --> LAuReL["LAuReL block<br/>(2 tiny GEMVs: D×64, 64×D)"]
       Attn --> AddOp((+))
       LAuReL --> AddOp
       AddOp --> ScaleOp["× 1/sqrt(2)"]
       ScaleOp --> FinalOut["Attention + LAuReL output"]
       style Attn fill:#c8e6c9,stroke:#388e3c
       style LAuReL fill:#ffccbc,stroke:#d84315
       style ScaleOp fill:#bbdefb,stroke:#1976d2

1.3 Hardware Mapping on pccx v002
----------------------------------

LAuReL is two low-rank GEMVs plus a trivial scale:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Operation
     - pccx Instruction
     - Notes
   * - :math:`x_{norm} \cdot W_{laurel\_left}^{T}` (2048 → 64)
     - ``GEMV``
     - Tiny matrix; latency < Attention GEMV, so it runs in parallel.
   * - :math:`\ldots \cdot W_{laurel\_right}^{T}` (64 → 2048)
     - ``GEMV``
     -
   * - Scale by :math:`1/\sqrt{2}`
     - ``CVO_SCALE`` with flags.recip_scale=0
     - Constant scalar preloaded via MEMSET.
   * - Final sum with ``attn_output``
     - ``GEMV`` with ``flags.accm=1``
     - Fused into the output projection write-back.

Because LAuReL's two GEMVs are so small (``[2048 × 64]`` and
``[64 × 2048]``), they can share a GEMV lane with the main projection
and add negligible latency.

2. PLE (Per-Layer Embedding): Shadow-Stream Injection
======================================================

PLE injects depth-aware positional context, but only into the shadow
streams. This is the single easiest Gemma 3N detail to get wrong.

2.1 Injection Point Constraint
-------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Behavior
     - Wrong
     - Correct
   * - Stream
     - main ``xs[0]``
     - shadow ``xs[1..3]`` only
   * - Timing
     - start of layer
     - end of layer, after AltUp correction
   * - Affected tensors
     - all 4 rows of ``xs``
     - rows 1, 2, 3 only

In code (refer to :doc:`gemma3n_pipeline` §4.E step 4):

.. math::

   xs_{new}[1:] \mathrel{+}= RMSNorm(gate\_ple \cdot W_{ple\_proj},
                                   W_{ple\_post\_ln})

``xs[0]`` is deliberately excluded from the addition. The main stream
stays a clean residual path.

2.2 Diagram
------------

.. mermaid::

   graph TD
       subgraph "Layer Processing"
         X0["Main stream xs[0]"] --> MainComputation["Attn · LAuReL · FFN"]
         X1["Shadow streams xs[1..3]"] --> Wait["(bypass)"]
       end
       MainComputation --> X0_Out["Updated main stream xs[0]"]
       Wait --> AddPLE((+))
       PLE["Per-Layer Embedding<br/>(depth context)"] --> AddPLE
       AddPLE --> X1_Out["Updated shadow streams xs[1..3]"]
       X0_Out --> NextLayer["Next layer"]
       X1_Out --> NextLayer
       style X0 fill:#a5d6a7,stroke:#2e7d32
       style MainComputation fill:#a5d6a7,stroke:#2e7d32
       style X1 fill:#ce93d8,stroke:#6a1b9a
       style AddPLE fill:#ce93d8,stroke:#6a1b9a
       style PLE fill:#ffe082,stroke:#ff8f00

2.3 Hardware Mapping
---------------------

PLE has two compute phases:

- **Pre-compute (once per token, before layer 0).** Section
  :doc:`gemma3n_pipeline` §3 computes ``pli_all[35][256]`` from
  ``W_ple_proj`` and ``W_ple``. This is one GEMV + one embedding
  lookup + two CVO operations. Both tables land in L2 by ``MEMCPY``
  at token entry.

- **Per-layer injection (end of each layer).** Compute ``gate_ple``
  (GEMV + GELU), multiply element-wise with ``pli``, expand back to
  ``D`` with ``W_ple_proj`` (GEMV), RMSNorm, and add into
  ``xs_new[1..3]``. The final add uses ``GEMV flags.accm=1`` so the
  shadow-stream L2 rows are updated in place.

The main stream is never touched by any of this activity, so a GEMV
lane assigned to the main stream can run the next layer's AltUp
pre-computation while the shadow-stream lanes are busy with PLE.

3. Why These Details Matter
============================

Both modules exist to stabilize deep residual dynamics. Misrouting them
breaks the calibration without producing an obvious runtime error — the
model still emits plausible tokens, just miscalibrated. pccx v002
therefore has **hard rules** in the scheduler:

- LAuReL output path is always scaled by :math:`1/\sqrt{2}` before the
  residual add; the scale is a reserved MEMSET slot.
- PLE writes the shadow streams by a GEMV with an explicit mask that
  refuses to target row 0 of ``xs``. This mask is part of the
  per-layer uop emitted by the Global Scheduler.

.. seealso::

   - Operator spec: :doc:`gemma3n_pipeline` §4.C, §4.E.
   - Full instruction set: :doc:`../ISA/instructions`.
