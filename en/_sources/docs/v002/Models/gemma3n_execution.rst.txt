=================================================================
Gemma 3N E4B on pccx v002 — Execution and Scheduling
=================================================================

This page explains *how* a single decode token of Gemma 3N E4B runs
end-to-end on pccx v002 — which tensor lives where, which instruction
fires which core, and how the scheduler keeps all three compute engines
busy.

For the math, see :doc:`gemma3n_pipeline`. For the instruction encodings
themselves, see :doc:`../ISA/instructions`.

1. Memory Layout at Steady State
=================================

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 40

   * - Region
     - Backing store
     - Unit
     - Contents
   * - **Host DDR4**
     - 4 GB shared with PS
     - byte
     - All weights (INT4 + per-channel scales), KV cache ring buffer,
       embedding / LM head tables.
   * - **L2 cache** (URAM)
     - 1.75 MB, 128-bit words
     - 128-bit word
     - Current ``xs[0..3]``, ``x_norm``, ``Q/K/V``, ``attn_output``,
       ``gate_raw``, ``up_out``, ``hidden``, ``mlp_out``, ``pli_all``,
       e_max, reduction accumulators.
   * - **Weight Buffer** (BRAM/URAM FIFO)
     - ~512 KB
     - 128-bit word
     - Burst buffer between HP2/HP3 (250 MHz) and the 400 MHz compute
       cores. Holds at most one GEMV/GEMM's worth of weights.
   * - **Constant Cache** (BRAM)
     - 64 entries × 48-bit
     - shape / scale tuple
     - RMSNorm scales, attention shapes, RoPE θ, sparsity cutoff ``μ +
       1.645·σ``, the :math:`1/\sqrt{2}` LAuReL scalar.

2. Host Setup (Once, at Model Load)
====================================

The driver performs these steps before any token is generated:

1. ``pccx_open(&handle)`` — maps the AXI-Lite control window and opens
   the HP/ACP DMA channels.
2. **Load immutable weights** (host DDR → L2 is too small; weights stay
   on DDR and stream on demand via HP ports).

   - Embedding table (``W_embed``), PLE tables, AltUp projections,
     LM head — these do land on L2 for the first and last layer
     respectively, via ``MEMCPY from_device=1 to_device=0 async=1``.
3. **Preload constants** via a sequence of ``MEMSET`` instructions:

   - Attention / FFN shape tuples.
   - Per-layer RoPE ``theta_base`` (10 000 or 1 000 000 depending on
     the 5-layer cycle).
   - FFN sparsity z-score ``1.6448536``.
   - LAuReL :math:`1/\sqrt{2}` scalar, attention+LAuReL merged scale.
4. **Initialize the KV ring buffer**:
   ``pccx_kv_init(handle, max_tokens=8192)``. The hardware treats KV
   cache as a ring with an explicit hard cap — see
   :doc:`../Architecture/kv_cache`.
5. ``pccx_start(handle)`` — raises ``core_enable`` and unblocks the
   dispatcher FIFO.

3. Per-Token Decode Flow
=========================

One decode token executes Sections 1 → 6 of :doc:`gemma3n_pipeline`. The
high-level dataflow, annotated with instructions:

.. mermaid::

   flowchart TB
       A["Host: read token id"] --> B["MEMCPY host → L2<br/>W_embed row + pli_all"]
       B --> C["GEMV: xs[k+1] = x0 · altup_projs[k]"]
       C --> L["Layer loop (i = 0 ... 34)"]
       L --> L1["GEMV/CVO: AltUp router + pred"]
       L1 --> L2["GEMV: Q/K/V projection"]
       L2 --> L3["CVO: QK-Norm + RoPE"]
       L3 --> L4["GEMV: Q · Kᵀ<br/>flags.findemax = 1"]
       L4 --> L5["CVO: softmax sequence"]
       L5 --> L6["GEMV: scores · V"]
       L6 --> L7["GEMV: W_o projection<br/>(+ LAuReL GEMVs in parallel)"]
       L7 --> L8["GEMV: FFN gate + up"]
       L8 --> L9["CVO: sparsity / GELU / merge"]
       L9 --> L10["GEMV: W_down + residual add"]
       L10 --> L11["GEMV/CVO: AltUp correction + PLE shadow inject"]
       L11 --> L
       L --> D["GEMV: Mean magnitude + unprojections"]
       D --> E["GEMV: LM head projection"]
       E --> F["CVO: softcap tanh"]
       F --> G["MEMCPY L2 → host: logits"]
       G --> H["Host: sampling"]

3.1 Who Does What
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Pipeline stage
     - Systolic Array
     - GEMV ×4
     - SFU ×4
   * - Embedding row fetch + AltUp init (×4)
     - —
     - 4 GEMV (one per ``altup_projs[k]``)
     - —
   * - PLE pre-compute
     - —
     - 1 GEMV
     - 2 (RMSNorm + scale)
   * - Attention Q/K/V
     - —
     - 3 GEMV
     - 2 (Q-norm, K-norm per head)
   * - RoPE
     - —
     - —
     - 2 (sin, cos) per Q, K
   * - Attention score + softmax + context
     - —
     - 2 GEMV
     - 3 (exp, reduce_sum, scale)
   * - Output + LAuReL merge
     - —
     - 3 GEMV (W_o + 2 LAuReL)
     - 1 (× 1/sqrt 2)
   * - FFN gate + up
     - —
     - 2 GEMV (16384 × 2048 each)
     - —
   * - FFN sparsity (layers 0–9) or GELU only
     - —
     - —
     - 4 (reduce × 2, gate compute, GELU)
   * - FFN down + residual
     - —
     - 1 GEMV (2048 × 16384)
     - 1 (RMSNorm)
   * - AltUp correction + PLE inject
     - —
     - 3 GEMV (ple_gate, ple_proj, shadow-only add)
     - 2 (tanh, RMSNorm)

The Systolic Array is **idle** during decode. It wakes up only for the
prefill stage, where ``Q · Kᵀ`` across the full context is a real GEMM.

3.2 Overlap Strategy
---------------------

Three rules keep the cores busy:

1. **Weight prefetch from HP2/HP3 starts the moment the previous GEMV
   launches.** The Weight Buffer is deep enough to hold one full GEMV
   worth of weights, so weight DMA and compute always overlap.
2. **SFU runs ahead of its consumer.** Once a GEMV finishes, its result
   is written to L2 and immediately picked up by the SFU through a
   direct-connect FIFO. The SFU result goes back to L2 in parallel with
   the next GEMV starting.
3. **PLE pre-compute lives off the critical path.** ``pli_all`` is
   computed on token entry, not per-layer. Per-layer PLE injection is
   also kept off the main stream (see
   :doc:`gemma3n_ple_laurel`), so it overlaps with the next layer's
   AltUp router on the main stream lane.

4. KV Cache Management
=======================

KV cache is the single biggest bandwidth consumer. Two driver-level
behaviors apply:

1. **Cross-layer sharing.** Only layers 0–19 write their own KV entries.
   Layers 20–34 reuse the cache from layer 18 (local θ) or layer 19
   (global θ). The scheduler therefore issues the GEMV that produces
   ``K`` / ``V`` only for ``i < 20`` and re-reads ``target_K`` /
   ``target_V`` from the cache for ``i >= 20``.
2. **Hard-cap ring buffer.** ``max_tokens`` is set at init time and
   cannot grow. When the ring wraps, the **oldest** entries are
   overwritten according to the attention-sink + local-window policy.
3. **Optional INT4 / INT8 quantization** on the KV write path (see
   :doc:`../Architecture/kv_cache` §2.1). Recommended default for
   context length > 4 K.

5. Error and Completion Handling
=================================

- Every instruction carries a 1-bit ``async`` field. The driver treats
  all intra-layer instructions as async and only waits (via the
  ``done`` status register) once per layer, at the AltUp correction
  step where the previous layer's results must be visible.
- A ``CVO_SCALE`` with ``flags.recip_scale=1`` returns ``0`` when the
  scalar is ``0``; the driver is responsible for not issuing such an
  instruction (it is a programmer error, not a hardware fault).
- The Global Scheduler exposes an **error interrupt** on the AXI-Lite
  control bank when an instruction fails decode (reserved bits
  nonzero, unknown opcode, out-of-range addresses). The driver logs
  the instruction and halts.

6. Performance Budget (Target)
===============================

Under the baseline configuration (W4A8 compute path, INT4 KV cache,
``L = 8192`` hard cap), the end-to-end decode target is:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Metric
     - Target
     - Source of bottleneck
   * - Decode throughput
     - **20 tok/s**
     - GEMV bandwidth at 400 MHz × 4 lanes × 1024 MAC/clk.
   * - L2 activation bandwidth
     - **~1.6 GB/s**
     - ``xs[0..3]``, ``gate_raw``, ``up_out``, ``hidden`` round-trips.
   * - KV cache read bandwidth @ 8 K
     - **~6 GB/s**
     - 20 layers × 512 × INT4 × 2 (K, V) × 8 K / 50 ms.
   * - Weight stream bandwidth
     - **~3 GB/s**
     - Two HP ports at 128-bit × 250 MHz, amortized.

When context length exceeds 4 K, KV bandwidth becomes the limiter — see
the mitigations in :doc:`../Architecture/kv_cache`.

.. seealso::

   - Operator spec: :doc:`gemma3n_pipeline`
   - Pccx v002 ISA: :doc:`../ISA/index`
   - Driver API: :doc:`../Drivers/api`
