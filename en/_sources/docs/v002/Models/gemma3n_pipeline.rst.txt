==============================================================
Gemma 3N E4B — Operator-Level Pipeline
==============================================================

Complete operation specification of Gemma 3N E4B. Every tensor has its
shape and dtype annotated so that each step can be mapped one-to-one to
a pccx v002 instruction (see :doc:`gemma3n_execution`).

**Base dimensions**
  :math:`D=2048`, :math:`D_{ffn}=16384`, :math:`D_{patch}=256`,
  :math:`D_{router}=4`, :math:`Vocab=262400`.

**Attention**
  8 Q heads / 2 KV heads, :math:`d_{head}=256`,
  :math:`N_{layers}=35`.

----

0. Core Function Definitions
==============================

**Embedding** — row lookup by integer id.

.. math::

   Output = W_{embed}[token\_id,\ :]

**RMSNorm**

.. math::

   RMS = \sqrt{\frac{1}{N}\sum_{i=1}^{N}x_i^2 + 10^{-6}},
   \qquad Output = \frac{x}{RMS} \times \gamma

**GELU**

.. math::

   Output = 0.5\,x\,\bigl(1 + \tanh(\sqrt{2/\pi}\,(x + 0.044715\,x^3))\bigr)

**RoPE (Rotary Position Embedding)**

.. math::

   Output_{2i}   &= x_{2i}\cos\theta - x_{2i+1}\sin\theta \\
   Output_{2i+1} &= x_{2i}\sin\theta + x_{2i+1}\cos\theta

**INT4 Dequantization** — unpack two W4 values from a byte:

.. math::

   w_0 = W_{packed} \land \mathtt{0x0F},
   \quad w_0 \mathrel{-}= 16 \text{ if } w_0 > 7

.. math::

   w_1 = W_{packed} \gg 4,
   \quad w_1 \mathrel{-}= 16 \text{ if } w_1 > 7

.. math::

   Output = [w_0,\ w_1] \times Scale

**GQA (Grouped-Query Attention)** — groups the 8 Q heads with the 2 KV
heads in a 4:1 ratio. For group :math:`g \in \{0, 1\}`:

.. math::

   Q_g &= Q[4g:4g+4,\ :] \in \mathbb{R}^{4 \times d_{head}} \\
   \mathrm{scores}_g &= \frac{Q_g \cdot K_g^{T}}{\sqrt{d_{head}}}
                        \in \mathbb{R}^{4 \times L} \\
   \mathrm{out}_g &= \mathrm{softmax}(\mathrm{scores}_g)\cdot V_g
                     \in \mathbb{R}^{4 \times d_{head}}

.. math::

   GQA_{out} = \mathrm{concat}(\mathrm{out}_0, \mathrm{out}_1)
              \in \mathbb{R}^{8 \times d_{head}}
              \xrightarrow{\text{flatten}} \mathbb{R}^{1 \times D}

:math:`L` is the current sequence length; :math:`K_g`, :math:`V_g` come
from the KV cache.

----

1. Token Embedding
===================

.. math::

   x_0 = Embedding(token\_id, W_{embed}) \times \sqrt{2048}

.. note::

   ``token_id`` is clipped to ``min(token_id, 262143)`` so it stays
   within the PLE vocab range.

.. code-block:: text

   W_embed  [262400 × 2048]  INT4
   ─────────────────────────────────
   x₀       [1 × 2048]       float32

----

2. AltUp Initial Projections
=============================

Inserts :math:`x_0` into row 0 of the stream matrix ``xs``; rows 1–3 are
filled by dot-producting :math:`x_0` with the AltUp projection matrices.

.. math::

   xs[0] &= x_0 \\
   xs[k+1] &= x_0 \cdot altup\_projs[k], \quad k=0,1,2

.. code-block:: text

   altup_projs[k]  [2048 × 2048]  float32  (k = 0, 1, 2)
   ─────────────────────────────────────────────────────
   xs              [4 × 2048]     float32

----

3. PLE Setup (Pre-Compute)
===========================

Pre-compute the auxiliary ``pli_all`` vector once so it can be shared
across all 35 layers.

**Step 1 — Linear projection and normalization.**

.. math::

   x_{proj} = \frac{x_0 \cdot W_{ple\_proj}^{T}}{\sqrt{2048}}
              \xrightarrow{\text{reshape}} [35 \times 256]

.. math::

   x_{proj\_normed} = \frac{x_{proj}}{RMS(x_{proj})} \times norm_{ple}

.. code-block:: text

   W_ple_proj  [8960 × 2048]  INT4    →  x_proj         [35 × 256]  float32
   norm_ple    [256]          float32 →  x_proj_normed  [35 × 256]  float32

**Step 2 — Patch embedding extraction.**

.. math::

   y = Embedding(token\_id, W_{ple})
       \xrightarrow{\text{reshape}} [35 \times 256]
       \times \sqrt{256}

.. code-block:: text

   W_ple  [262144 × 8960]  INT4   →  y  [35 × 256]  float32

**Step 3 — Composition.**

.. math::

   pli\_all = (x_{proj\_normed} + y) \times \frac{1}{\sqrt{2}}

.. code-block:: text

   pli_all  [35 × 256]  float32

----

4. Transformer Layer (×35)
===========================

Loop index :math:`i = 0, 1, \ldots, 34`.

4.A AltUp Router & Prediction
------------------------------

Mix the four modality vectors to generate :math:`xs_{pred}`.

.. math::

   x_n &= \frac{RMSNorm(xs[0], W_{altup\_rn})}{2048} \\
   modalities &= \tanh(x_n \cdot W_{altup\_router}) \\
   coef\_mat &= (W_{altup\_pred} \cdot modalities)
               \xrightarrow{\text{reshape}} [4 \times 4] \\
   xs_{pred} &= xs + coef\_mat \cdot xs

.. code-block:: text

   altup_rn     [2048]      float32  →  x_n         [1 × 2048]  float32
   altup_router [2048 × 4]  float32  →  modalities  [4]         float32
   altup_pred   [16 × 4]    float32  →  coef_mat    [4 × 4]     float32
   ──────────────────────────────────────────────────────────────────────
   xs_pred      [4 × 2048]  float32

4.B Attention — Q / K / V Projection
--------------------------------------

.. math::

   x_{input} &= xs_{pred}[0],
   \quad x_{norm} = RMSNorm(x_{input}, W_{input\_ln}) \\
   Q &= x_{norm} \cdot W_q^{T},
   \quad K = x_{norm} \cdot W_k^{T},
   \quad V = x_{norm} \cdot W_v^{T}

.. code-block:: text

   input_ln  [2048]           float32
   W_q       [2048 × 2048]    INT4    →  Q  [1 × 2048]  →  [8 × 256]  float32
   W_k       [512  × 2048]    INT4    →  K  [1 × 512]   →  [2 × 256]  float32
   W_v       [512  × 2048]    INT4    →  V  [1 × 512]   →  [2 × 256]  float32

4.B-2 Head-wise QK-Norm
~~~~~~~~~~~~~~~~~~~~~~~~

RMSNorm per head (256 dims).

.. math::

   Q^{head}_i &= \frac{Q^{head}_i}{RMS(Q^{head}_i)} \times \gamma_q,
   \quad i = 0, \ldots, 7 \\
   K^{head}_j &= \frac{K^{head}_j}{RMS(K^{head}_j)} \times \gamma_k,
   \quad j = 0, 1

.. code-block:: text

   gamma_q  [256]  float32  (shared across the 8 Q heads)
   gamma_k  [256]  float32  (shared across the 2 K heads)
   ──────────────────────────────────────────────────────
   Q_norm   [8 × 256]  float32
   K_norm   [2 × 256]  float32

4.B-3 Dynamic-θ RoPE
~~~~~~~~~~~~~~~~~~~~

.. math::

   \theta = \begin{cases}
     1{,}000{,}000 & i \bmod 5 = 4 \\
     10{,}000     & \text{otherwise}
   \end{cases}

.. math::

   Q_{rope} = RoPE(Q_{norm}, pos, \theta),
   \quad K_{rope} = RoPE(K_{norm}, pos, \theta)

.. code-block:: text

   Q_rope  [8 × 256]  float32
   K_rope  [2 × 256]  float32

See :doc:`gemma3n_attention_rope` for the theta cycle visualization and
why scaling / softcap are removed.

4.B-4 KV Cache Storage and Cross-Layer Sharing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KV cache stores **float16** (downcast from float32).

Shape: ``K_cache[20, max_seq, 512]``, ``V_cache[20, max_seq, 512]``.

For layers that own a cache entry:

.. math::

   i < 20:\quad K\_cache[i, pos, :] = K_{rope},
   \quad V\_cache[i, pos, :] = V

For layers that reuse an upstream cache:

.. math::

   i \ge 20:\quad
   \begin{cases}
     target\_K = K\_cache[19, :pos+1, :] & i \bmod 5 = 4 \\
     target\_K = K\_cache[18, :pos+1, :] & \text{otherwise}
   \end{cases}

.. code-block:: text

   K_cache   [20 × max_seq × 512]  float16
   V_cache   [20 × max_seq × 512]  float16
   target_K  [L × 512]  →  [L × 2 × 256]  float16   (L = pos + 1)
   target_V  [L × 512]  →  [L × 2 × 256]  float16

4.B-5 GQA and Output Projection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   attn\_raw &= GQA(Q_{rope}, target\_K, target\_V) \\
   attn\_output &= attn\_raw \cdot W_o^{T}

.. code-block:: text

   scores_g     [4 × L]      float32   (g = 0, 1)
   out_g        [4 × 256]    float32
   attn_raw     [1 × 2048]   float32
   W_o          [2048 × 2048]  INT4
   ──────────────────────────────────
   attn_output  [1 × 2048]   float32

4.C LAuReL + Attention Residual Composition
--------------------------------------------

LAuReL's residual adds :math:`x_{norm}`, **not** the raw input:

.. math::

   laurel\_x &= (x_{norm} \cdot W_{laurel\_left}^{T})
                \cdot W_{laurel\_right}^{T} \\
   laurel\_out &= x_{norm} + RMSNorm(laurel\_x, W_{laurel\_norm})

.. math::

   attn\_output &= RMSNorm(attn\_output, W_{post\_attn\_ln}) + x_{input}

.. math::

   x_{attn} = (attn\_output + laurel\_out) \times \frac{1}{\sqrt{2}}

.. code-block:: text

   laurel_left   [64   × 2048]  INT4    →  laurel_x (intermediate) [1 × 64]    float32
   laurel_right  [2048 × 64  ]  INT4    →  laurel_x                [1 × 2048]  float32
   laurel_norm   [2048]         float32
   post_attn_ln  [2048]         float32
   ──────────────────────────────────────────────────────────────────────
   x_attn        [1 × 2048]     float32

See :doc:`gemma3n_ple_laurel` for the rationale behind the
:math:`1/\sqrt{2}` scale.

4.D FFN (Gate-Up-Down)
-----------------------

.. math::

   x_{n2} &= RMSNorm(x_{attn}, W_{pre\_ffn\_ln}) \\
   gate\_raw &= x_{n2} \cdot W_{gate}^{T},
   \quad up\_out = x_{n2} \cdot W_{up}^{T}

.. code-block:: text

   pre_ffn_ln  [2048]           float32
   W_gate      [16384 × 2048]   INT4    →  gate_raw  [1 × 16384]  float32
   W_up        [16384 × 2048]   INT4    →  up_out    [1 × 16384]  float32

**For** :math:`i \ge 10` **— standard GELU gate.**

.. math::

   gate\_out = GELU(gate\_raw),
   \quad hidden = gate\_out \times up\_out

**For** :math:`i < 10` **— sparse gate (Gaussian Top-K, see**
:doc:`gemma3n_ffn_sparsity` **).**

.. math::

   cutoff = Mean(gate\_raw) + Std(gate\_raw) \times 1.6448536

.. math::

   sparse\_gate = \max(gate\_raw - cutoff, 0),
   \quad hidden = GELU(sparse\_gate) \times up\_out

.. code-block:: text

   hidden  [1 × 16384]  float32

**FFN output.**

.. math::

   mlp\_out = hidden \cdot W_{down}^{T}

.. math::

   outputs = RMSNorm(mlp\_out, W_{post\_ffn\_ln}) + x_{attn}

.. code-block:: text

   W_down       [2048 × 16384]  INT4    →  mlp_out  [1 × 2048]  float32
   post_ffn_ln  [2048]          float32
   ───────────────────────────────────────────────────────────────────
   outputs      [1 × 2048]      float32

4.E AltUp Correction + PLE Mixing
----------------------------------

**Step 1 — Scale and innovation.**

.. math::

   activated &= outputs \times W_{altup\_scale} \\
   innovation &= activated - xs_{pred}[0]

.. code-block:: text

   altup_scale  [2048]       float32
   activated    [1 × 2048]   float32
   innovation   [1 × 2048]   float32

**Step 2 — Correction coefficients.**

.. math::

   x_{n3} &= \frac{RMSNorm(activated, W_{altup\_rn})}{2048} \\
   mod\_corr &= \tanh(x_{n3} \cdot W_{altup\_router}) \\
   corr\_coefs &= W_{altup\_corr} \cdot mod\_corr + 1.0

.. code-block:: text

   altup_rn      [2048]      float32  →  x_n3        [1 × 2048]  float32
   altup_router  [2048 × 4]  float32  →  mod_corr    [4]         float32
   altup_corr    [4 × 4]     float32  →  corr_coefs  [4]         float32

**Step 3 — Modality update (broadcasting).**

.. math::

   xs_{new} = xs_{pred} + corr\_coefs_{[:,1]} \times innovation_{[1,:]}

.. code-block:: text

   corr_coefs[:, np.newaxis]  [4 × 1]    × innovation  [1 × 2048]  →  [4 × 2048]
   xs_new                     [4 × 2048]  float32

**Step 4 — PLE mixing (shadow-stream only).**

.. math::

   gate\_ple &= GELU(activated \cdot W_{ple\_gate}^{T}) \times pli \\
   mapped    &= RMSNorm(gate\_ple \cdot W_{ple\_proj}, W_{ple\_post\_ln}) \\
   xs_{new}[1:] &\mathrel{+}= mapped

.. code-block:: text

   W_ple_gate   [256  × 2048]  INT4    →  gate_ple (INT4 matmul)  [1 × 256]   float32
   pli          [256]          float32 →  gate_ple (× pli)        [1 × 256]   float32
   W_ple_proj   [256  × 2048]  float32 →  gate_ple · W_ple_proj   [1 × 2048]  float32
   ple_post_ln  [2048]         float32 →  mapped                  [1 × 2048]  float32

.. math::

   xs \leftarrow xs_{new} \quad [4 \times 2048]

----

5. Decode Logits
=================

**Step 1 — Magnitude matching and unprojection.**

.. math::

   target\_mag = \sqrt{Mean(xs[0]^2)}

.. math::

   proj\_x_k = xs[k+1] \cdot altup\_unprojs[k], \quad k = 0, 1, 2

.. math::

   new\_mag_k = \sqrt{Mean(proj\_x_k^2)},
   \quad proj\_x_k \mathrel{\ast}= \frac{target\_mag}{\max(new\_mag_k,\ 10^{-12})}

.. code-block:: text

   altup_unprojs[k]  [2048 × 2048]  float32  (k = 0, 1, 2)
   proj_x_k          [1 × 2048]     float32

**Step 2 — Average and final projection.**

.. math::

   x_{final} = Mean([xs[0], proj\_x_0, proj\_x_1, proj\_x_2])

.. math::

   x_{final\_norm} = RMSNorm(x_{final}, W_{final\_norm})

.. math::

   logits = x_{final\_norm} \cdot W_{lm\_head}^{T}

.. code-block:: text

   W_final_norm  [2048]           float32
   W_lm_head     [262400 × 2048]  INT4
   ─────────────────────────────────────
   x_final_norm  [1 × 2048]       float32
   logits        [1 × 262400]     float32

**Step 3 — Logit soft-capping.**

.. math::

   Logits = 30.0 \times \tanh(logits / 30.0)

----

6. Generation and Sampling
===========================

**Repetition penalty** (:math:`\rho = 1.15`):

.. math::

   Logits_t = \begin{cases}
     Logits_t \times \rho & Logits_t < 0 \\
     Logits_t / \rho      & Logits_t \ge 0
   \end{cases}

**Temperature softmax.** For :math:`T = 0`:
:math:`next\_token = \arg\max(Logits)`. For :math:`T > 0`:

.. math::

   Logits_{safe} = \frac{Logits}{T} - \max\!\left(\frac{Logits}{T}\right)

.. math::

   probs_i = \frac{\exp(Logits_{safe, i})}{\sum_j \exp(Logits_{safe, j})}

**Top-P sampling** (:math:`p = 0.9`):

.. math::

   sorted\_idx = \mathrm{argsort}(probs)[::-1]

.. math::

   \mathrm{keep} = \{i : \mathrm{cumsum}(probs[sorted\_idx])_i
                       - probs[sorted\_idx_i] < p\}

.. math::

   probs = \frac{probs_{filtered}}{\sum probs_{filtered}},
   \qquad next\_token \sim \mathrm{Categorical}(probs)

Sampling (steps 5 step 3 onwards) is done on the host CPU in the pccx
reference driver. The NPU returns logits after the soft-cap.

.. seealso::

   - Instruction-level mapping: :doc:`gemma3n_execution`.
   - KV cache strategy: :doc:`../Architecture/kv_cache`.
