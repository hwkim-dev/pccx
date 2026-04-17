===============================================
Gemma 3N — Attention and RoPE Constraints
===============================================

Gemma 3N makes two decisions about the attention block that diverge
sharply from the standard Transformer recipe. Both of them simplify the
pccx v002 instruction stream, so they are worth stating explicitly.

1. No Attention Scaling, No Softcap
====================================

In a textbook attention block, the ``Q · Kᵀ`` result is divided by
:math:`\sqrt{d_{head}}`. Earlier Gemma revisions additionally applied a
**softcap** (usually ``50.0``) on both the attention logits and the
final logits.

**Gemma 3N drops both of these.**

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * -
     - Standard Transformer
     - Gemma 3N
   * - Attention score
     - :math:`Q \cdot K^{T} / \sqrt{d_{head}}`
     - :math:`Q \cdot K^{T}`
   * - Softcap
     - :math:`50 \cdot \tanh(x / 50)` before softmax
     - None
   * - Final-logit cap
     - optional
     - :math:`30 \cdot \tanh(x / 30)` once, at the very end

.. code-block:: python

   # Wrong (old recipe):
   # attn_weights = np.dot(Q, K.T) / np.sqrt(256)
   # attn_weights = softcap(attn_weights, 50.0)

   # Gemma 3N:
   attn_weights = np.dot(Q, K.T)

.. note::

   **Hardware consequence on pccx v002.** The softmax sequence collapses
   from four CVO invocations to three:

   .. code-block:: text

      GEMV   flags.findemax=1            ; Q · Kᵀ, track e_max
      CVO    CVO_EXP  flags.sub_emax=1   ; exp(score - e_max)
      CVO    CVO_REDUCE_SUM              ; Σ exp → scalar
      CVO    CVO_SCALE flags.recip_scale=1  ; divide each exp by the sum

   No extra ``CVO_SCALE`` before ``CVO_EXP``, no softcap ``tanh`` in the
   middle.

2. Dynamic Alternating RoPE θ
==============================

Rotary Position Embedding normally uses a fixed ``theta_base`` (10 000 or
1 000 000) for every layer. Gemma 3N alternates per layer in a 5-layer
cycle.

2.1 The 5-Layer Pattern
------------------------

``[Local, Local, Local, Local, Global]``, repeated.

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Layer slot
     - Role
     - ``theta_base``
     - Receptive field
   * - 0, 1, 2, 3, 5, 6, 7, 8, …
     - Local
     - **10 000**
     - Short-range syntax
   * - 4, 9, 14, 19, 24, 29, 34
     - Global
     - **1 000 000**
     - Long-range semantic

2.2 Visualization
------------------

.. mermaid::

   block-beta
       columns 5
       L0["Layer 0\nLocal\n(10,000)"]
       L1["Layer 1\nLocal\n(10,000)"]
       L2["Layer 2\nLocal\n(10,000)"]
       L3["Layer 3\nLocal\n(10,000)"]
       L4["Layer 4\nGlobal\n(1,000,000)"]
       L5["Layer 5\nLocal\n(10,000)"]
       L6["Layer 6\nLocal\n(10,000)"]
       L7["Layer 7\nLocal\n(10,000)"]
       L8["Layer 8\nLocal\n(10,000)"]
       L9["Layer 9\nGlobal\n(1,000,000)"]
       E1["..."]
       E2["..."]
       E3["..."]
       E4["..."]
       E5["..."]
       style L0 fill:#e3f2fd,stroke:#1e88e5
       style L1 fill:#e3f2fd,stroke:#1e88e5
       style L2 fill:#e3f2fd,stroke:#1e88e5
       style L3 fill:#e3f2fd,stroke:#1e88e5
       style L4 fill:#ffe0b2,stroke:#f57c00
       style L5 fill:#e3f2fd,stroke:#1e88e5
       style L6 fill:#e3f2fd,stroke:#1e88e5
       style L7 fill:#e3f2fd,stroke:#1e88e5
       style L8 fill:#e3f2fd,stroke:#1e88e5
       style L9 fill:#ffe0b2,stroke:#f57c00

2.3 Hardware Consequence on pccx v002
--------------------------------------

- The ``theta_base`` is a **per-layer constant**, not per-token. It can
  be preloaded into the Constant Cache with a single ``MEMSET`` at the
  start of each layer.
- The ``CVO_SIN`` / ``CVO_COS`` kernels only need the phase
  :math:`pos \cdot \omega_j` where
  :math:`\omega_j = \theta^{-2j/d_{head}}`. These frequency tables are
  precomputed on host and ``MEMCPY``'d once at boot for both θ values.
- ``target_K`` / ``target_V`` are pulled from the correct cache slot
  (layer 19 for global θ, layer 18 for local θ) in the cross-layer
  sharing regime — see :doc:`gemma3n_pipeline` §4.B-4.

3. Combined Effect on Tokens per Second
========================================

The two simplifications together remove **one CVO_SCALE** and
**one CVO_TANH** per attention block per layer. Over the 35 layers of
Gemma 3N E4B, that is 70 CVO invocations saved per decode step. At the
decoding target of 20 tok/s, the SFU budget saves roughly 2–3 %
wall-clock time.

.. seealso::

   - Operator spec: :doc:`gemma3n_pipeline` §4.B.
   - CVO function codes: :doc:`../ISA/instructions` §4.
