========================
Gemma 3N E4B — Overview
========================

pccx v002 is sized to run **Gemma 3N E4B** at 20 tok/s on a bare-metal
Kria KV260. Before diving into the operator-level pipeline, this page
fixes the key dimensions and enumerates the deviations from a "standard"
decoder-only Transformer that the hardware has to accommodate.

1. Model Dimensions
===================

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Notes
   * - Hidden dim ``D``
     - **2048**
     - Main residual stream width.
   * - FFN intermediate ``D_ffn``
     - **16384**
     - 8× expansion.
   * - Number of layers
     - **35**
     - 35 decoder blocks.
   * - Attention heads
     - **8 Q / 2 KV**
     - Grouped-Query Attention, 4:1 ratio.
   * - Head dim ``d_head``
     - **256**
     - ``D / 8``.
   * - Vocab size
     - **262,400**
     - ``logits = x · W_lm_head``.
   * - Patch/router dims
     - ``D_patch = 256``, ``D_router = 4``
     - PLE patch embedding and AltUp router.
   * - Streams (AltUp)
     - **4**
     - ``xs[0]`` main stream + 3 shadow streams.

2. What Makes Gemma 3N Non-standard
====================================

Gemma 3N departs from the textbook decoder in five places. Each one has
a direct consequence for how pccx v002 schedules its instructions.

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - Feature
     - Behavior
     - Hardware Consequence
   * - **AltUp 4-stream**
     - Four parallel residual streams; the shadow streams receive
       depth-dependent updates, the main stream stays clean.
     - Four copies of ``xs`` live in L2. All GEMV/GEMM operands are
       sourced from the relevant stream slice.
   * - **Alternating RoPE θ**
     - 5-layer cycle ``[Local, Local, Local, Local, Global]`` with
       θ = 10 000 / 1 000 000.
     - θ is a per-layer constant preloaded via ``MEMSET`` before each
       RoPE ``CVO_SIN`` / ``CVO_COS`` pair.
   * - **No attention scaling / softcap**
     - Attention score is ``Q · Kᵀ`` with no ``/sqrt(d_head)`` and no
       softcap before softmax.
     - One fewer ``CVO_SCALE`` per attention block; softmax starts
       straight after ``GEMV``.
   * - **LAuReL parallel branch**
     - Low-rank side path combined with the attention output, then
       divided by ``sqrt(2)``.
     - Two tiny GEMVs (``D × 64`` and ``64 × D``) plus a single
       ``CVO_SCALE`` merged with the residual.
   * - **PLE shadow injection**
     - Per-Layer Embedding is injected **only** into ``xs[1..3]`` at the
       *end* of each layer.
     - Main stream path is never polluted by PLE; the scheduler keeps
       PLE activity off the critical path.

Full math for each of these is in the following pages:

- :doc:`gemma3n_attention_rope` — scaling removal and dynamic θ.
- :doc:`gemma3n_ple_laurel` — LAuReL scaling and PLE injection rules.
- :doc:`gemma3n_ffn_sparsity` — Gaussian Top-K gate on early layers.

3. Cross-Layer KV Sharing
==========================

Gemma 3N does **not** store a KV entry in every layer. Of the 35
layers:

- Layers **0–19** store their own ``K`` / ``V`` in cache.
- Layers **20–34** reuse the caches of layer 18 (local RoPE) or layer 19
  (global RoPE) depending on the 5-layer cycle.

Concretely, ``K_cache`` and ``V_cache`` are sized ``[20, max_seq, 512]``
rather than ``[35, max_seq, 512]``. This is the main reason the KV
footprint budget in :doc:`../Architecture/kv_cache` lists **~40 KB per
token**, not 70 KB.

4. Datatype Map
================

How each tensor type lands on pccx v002 compute:

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 30

   * - Tensor
     - Storage
     - Compute path
     - Notes
   * - Weights (Q / K / V / O / FFN)
     - **INT4 packed**
     - Systolic Array (GEMM) or GEMV Core
     - W4 + per-channel scale.
   * - Activations (hidden, Q / K / V)
     - **INT8** on L2
     - Same, after preprocess
     - Promoted to BF16 only through the SFU.
   * - KV cache
     - **FP16** (baseline), **INT8/INT4** recommended
     - MEMCPY host ↔ L2
     - See :doc:`../Architecture/kv_cache`.
   * - AltUp / LAuReL / PLE scales
     - **FP32** (host) → **BF16** (device)
     - SFU
     - Small vectors, amortized.
   * - Logits
     - **FP32** on host
     - Post-processing on CPU
     - Top-P / temperature happen outside the NPU.

5. Where to Go Next
====================

- Full operator-level spec (embedding → sampling): :doc:`gemma3n_pipeline`.
- Instruction-level mapping and scheduling: :doc:`gemma3n_execution`.
- Baseline x64 CPU reference: `llm-lite
  <https://github.com/hwkim-dev/llm-lite>`_.
