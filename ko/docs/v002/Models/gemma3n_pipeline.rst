==============================================================
Gemma 3N E4B — 연산자 수준 파이프라인
==============================================================

Gemma 3N E4B 의 전체 연산 사양. 각 텐서에 shape / dtype 을 표기하여,
각 단계가 pccx v002 의 명령어와 1:1 로 매핑되도록 했습니다
(:doc:`gemma3n_execution` 참고).

**기본 차원**
  :math:`D=2048`, :math:`D_{ffn}=16384`, :math:`D_{patch}=256`,
  :math:`D_{router}=4`, :math:`Vocab=262400`.

**어텐션**
  Q 8 / KV 2, :math:`d_{head}=256`, :math:`N_{layers}=35`.

----

0. 핵심 함수 정의
=================

**Embedding** — 정수 id 로 행 조회.

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

**INT4 역양자화** — 한 바이트에서 W4 두 개 풀어내기:

.. math::

   w_0 = W_{packed} \land \mathtt{0x0F},
   \quad w_0 \mathrel{-}= 16 \text{ if } w_0 > 7

.. math::

   w_1 = W_{packed} \gg 4,
   \quad w_1 \mathrel{-}= 16 \text{ if } w_1 > 7

.. math::

   Output = [w_0,\ w_1] \times Scale

**GQA (Grouped-Query Attention)** — Q 8 헤드와 KV 2 헤드를 4:1 로 묶음.
:math:`g \in \{0, 1\}` 에 대해:

.. math::

   Q_g &= Q[4g:4g+4,\ :] \in \mathbb{R}^{4 \times d_{head}} \\
   \mathrm{scores}_g &= \frac{Q_g \cdot K_g^{T}}{\sqrt{d_{head}}}
                        \in \mathbb{R}^{4 \times L} \\
   \mathrm{out}_g &= \mathrm{softmax}(\mathrm{scores}_g) \cdot V_g
                     \in \mathbb{R}^{4 \times d_{head}}

.. math::

   GQA_{out} = \mathrm{concat}(\mathrm{out}_0, \mathrm{out}_1)
              \in \mathbb{R}^{8 \times d_{head}}
              \xrightarrow{\text{flatten}} \mathbb{R}^{1 \times D}

:math:`L` 은 현재 시퀀스 길이, :math:`K_g`, :math:`V_g` 는 KV 캐시에서
가져옵니다.

----

1. 토큰 임베딩
===============

.. math::

   x_0 = Embedding(token\_id, W_{embed}) \times \sqrt{2048}

.. note::

   ``token_id`` 는 PLE vocab 범위를 초과하지 않도록
   ``min(token_id, 262143)`` 로 clip 합니다.

.. code-block:: text

   W_embed  [262400 × 2048]  INT4
   ─────────────────────────────────
   x₀       [1 × 2048]       float32

----

2. AltUp 초기 Projection
=========================

``xs`` 의 0 번 행에 :math:`x_0` 를 넣고, 1~3 행은 :math:`x_0` 와
AltUp projection 행렬의 내적으로 채웁니다.

.. math::

   xs[0] &= x_0 \\
   xs[k+1] &= x_0 \cdot altup\_projs[k], \quad k = 0, 1, 2

.. code-block:: text

   altup_projs[k]  [2048 × 2048]  float32  (k = 0, 1, 2)
   ─────────────────────────────────────────────────────
   xs              [4 × 2048]     float32

----

3. PLE 사전 계산
==================

보조 벡터 ``pli_all`` 을 토큰 진입 시 1 회만 계산해 35 레이어가 공유합니다.

**Step 1 — Linear projection & normalization.**

.. math::

   x_{proj} = \frac{x_0 \cdot W_{ple\_proj}^{T}}{\sqrt{2048}}
              \xrightarrow{\text{reshape}} [35 \times 256]

.. math::

   x_{proj\_normed} = \frac{x_{proj}}{RMS(x_{proj})} \times norm_{ple}

.. code-block:: text

   W_ple_proj  [8960 × 2048]  INT4    →  x_proj         [35 × 256]  float32
   norm_ple    [256]          float32 →  x_proj_normed  [35 × 256]  float32

**Step 2 — Patch 임베딩 추출.**

.. math::

   y = Embedding(token\_id, W_{ple})
       \xrightarrow{\text{reshape}} [35 \times 256]
       \times \sqrt{256}

.. code-block:: text

   W_ple  [262144 × 8960]  INT4   →  y  [35 × 256]  float32

**Step 3 — 합성.**

.. math::

   pli\_all = (x_{proj\_normed} + y) \times \frac{1}{\sqrt{2}}

.. code-block:: text

   pli_all  [35 × 256]  float32

----

4. Transformer 레이어 (×35)
============================

루프 인덱스 :math:`i = 0, 1, \ldots, 34`.

4.A AltUp Router & Prediction
------------------------------

4 개의 modality 벡터를 혼합해 :math:`xs_{pred}` 를 만듭니다.

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

헤드 단위 RMSNorm (256 차원).

.. math::

   Q^{head}_i &= \frac{Q^{head}_i}{RMS(Q^{head}_i)} \times \gamma_q,
   \quad i = 0, \ldots, 7 \\
   K^{head}_j &= \frac{K^{head}_j}{RMS(K^{head}_j)} \times \gamma_k,
   \quad j = 0, 1

.. code-block:: text

   gamma_q  [256]  float32  (Q 8 헤드에 공유)
   gamma_k  [256]  float32  (K 2 헤드에 공유)
   ──────────────────────────────────────────
   Q_norm   [8 × 256]  float32
   K_norm   [2 × 256]  float32

4.B-3 동적 θ RoPE
~~~~~~~~~~~~~~~~~~

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

자세한 θ 주기 시각화 및 scaling / softcap 제거 근거는
:doc:`gemma3n_attention_rope` 참고.

4.B-4 KV 캐시 저장과 레이어 간 공유
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KV 캐시는 float32 를 **float16** 으로 downcast 해서 저장합니다.

Shape: ``K_cache[20, max_seq, 512]``, ``V_cache[20, max_seq, 512]``.

고유 엔트리를 가지는 레이어:

.. math::

   i < 20:\quad K\_cache[i, pos, :] = K_{rope},
   \quad V\_cache[i, pos, :] = V

상위 캐시를 재사용하는 레이어:

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

4.B-5 GQA & Output Projection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

4.C LAuReL + Attention Residual 합성
-------------------------------------

LAuReL 의 residual 에는 원본이 아니라 **정규화된 입력**
(:math:`x_{norm}`) 이 더해집니다:

.. math::

   laurel\_x &= (x_{norm} \cdot W_{laurel\_left}^{T})
                \cdot W_{laurel\_right}^{T} \\
   laurel\_out &= x_{norm} + RMSNorm(laurel\_x, W_{laurel\_norm})

.. math::

   attn\_output &= RMSNorm(attn\_output, W_{post\_attn\_ln}) + x_{input}

.. math::

   x_{attn} = (attn\_output + laurel\_out) \times \frac{1}{\sqrt{2}}

.. code-block:: text

   laurel_left   [64   × 2048]  INT4    →  laurel_x (중간) [1 × 64]    float32
   laurel_right  [2048 × 64  ]  INT4    →  laurel_x        [1 × 2048]  float32
   laurel_norm   [2048]         float32
   post_attn_ln  [2048]         float32
   ──────────────────────────────────────────────────────────────────
   x_attn        [1 × 2048]     float32

:math:`1/\sqrt{2}` 스케일의 근거는 :doc:`gemma3n_ple_laurel` 참고.

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

**:math:`i \ge 10` — 표준 GELU 게이트.**

.. math::

   gate\_out = GELU(gate\_raw),
   \quad hidden = gate\_out \times up\_out

**:math:`i < 10` — 희소 게이트 (Gaussian Top-K,
:doc:`gemma3n_ffn_sparsity` 참고).**

.. math::

   cutoff = Mean(gate\_raw) + Std(gate\_raw) \times 1.6448536

.. math::

   sparse\_gate = \max(gate\_raw - cutoff, 0),
   \quad hidden = GELU(sparse\_gate) \times up\_out

.. code-block:: text

   hidden  [1 × 16384]  float32

**FFN 출력.**

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

**Step 1 — Scale 과 innovation.**

.. math::

   activated &= outputs \times W_{altup\_scale} \\
   innovation &= activated - xs_{pred}[0]

.. code-block:: text

   altup_scale  [2048]       float32
   activated    [1 × 2048]   float32
   innovation   [1 × 2048]   float32

**Step 2 — 보정 계수.**

.. math::

   x_{n3} &= \frac{RMSNorm(activated, W_{altup\_rn})}{2048} \\
   mod\_corr &= \tanh(x_{n3} \cdot W_{altup\_router}) \\
   corr\_coefs &= W_{altup\_corr} \cdot mod\_corr + 1.0

.. code-block:: text

   altup_rn      [2048]      float32  →  x_n3        [1 × 2048]  float32
   altup_router  [2048 × 4]  float32  →  mod_corr    [4]         float32
   altup_corr    [4 × 4]     float32  →  corr_coefs  [4]         float32

**Step 3 — Modality 업데이트 (broadcasting).**

.. math::

   xs_{new} = xs_{pred} + corr\_coefs_{[:,1]} \times innovation_{[1,:]}

.. code-block:: text

   corr_coefs[:, np.newaxis]  [4 × 1]    × innovation  [1 × 2048]  →  [4 × 2048]
   xs_new                     [4 × 2048]  float32

**Step 4 — PLE mixing (shadow stream 전용).**

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

**Step 1 — Magnitude 매칭과 unprojection.**

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

**Step 2 — 평균과 최종 projection.**

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

6. 생성 및 샘플링
==================

**반복 페널티** (:math:`\rho = 1.15`):

.. math::

   Logits_t = \begin{cases}
     Logits_t \times \rho & Logits_t < 0 \\
     Logits_t / \rho      & Logits_t \ge 0
   \end{cases}

**Temperature softmax.** :math:`T = 0` 이면
:math:`next\_token = \arg\max(Logits)`. :math:`T > 0` 이면:

.. math::

   Logits_{safe} = \frac{Logits}{T} - \max\!\left(\frac{Logits}{T}\right)

.. math::

   probs_i = \frac{\exp(Logits_{safe, i})}{\sum_j \exp(Logits_{safe, j})}

**Top-P 샘플링** (:math:`p = 0.9`):

.. math::

   sorted\_idx = \mathrm{argsort}(probs)[::-1]

.. math::

   \mathrm{keep} = \{i : \mathrm{cumsum}(probs[sorted\_idx])_i
                       - probs[sorted\_idx_i] < p\}

.. math::

   probs = \frac{probs_{filtered}}{\sum probs_{filtered}},
   \qquad next\_token \sim \mathrm{Categorical}(probs)

샘플링 (§5 Step 3 이후) 은 pccx 레퍼런스 드라이버에서 호스트 CPU 가
처리합니다. NPU 는 soft-cap 후 logits 를 반환합니다.

.. seealso::

   - 명령어 수준 매핑: :doc:`gemma3n_execution`.
   - KV 캐시 전략: :doc:`../Architecture/kv_cache`.
