============================================
KV Cache Optimization Strategy
============================================

The real performance wall in autoregressive decoding is **KV cache
memory bandwidth**, not compute. This page summarizes how pccx v002
handles the KV cache on Gemma 3N E4B and the three guidelines that apply
at the RTL and driver layers.

1. GEMV Dominance and the Memory Wall
======================================

During a single decoding step, **85–98% of FLOPs are GEMV** — only the
GQA Attention block contributes GEMMs that scale with sequence length
``L``. So GEMV's effective utilization directly drives TPS.

The KV cache, in contrast, grows linearly: each layer accumulates and
reuses its entries, and **every new token must read back the entire
history**.

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - Sequence length L
     - Per-token KV
     - Cumulative KV size
     - Headroom vs. KV260 DDR4 (10–12 GB/s)
   * - 1 K
     - ~40 KB
     - ~40 MB
     - Plenty — MAC is the bottleneck
   * - 8 K
     - ~40 KB
     - ~320 MB
     - Tight — bandwidth contention begins
   * - 32 K
     - ~40 KB
     - **~1.31 GB**
     - **Bandwidth saturated — MACs idle**

At 32 K context the cache hits 1.31 GB per token. Against an effective
~10 GB/s DDR4 bandwidth, that's ~131 ms of memory transfer time per
token alone — enough to drag TPS below 8.

.. note::

   Even with Gemma 3N's **Cross-Layer Sharing** optimization (only
   20 of 35 layers actually store KV entries), the per-token footprint
   is still ~40 KB. This is the fundamental reason edge devices like
   KV260 cannot accommodate ``L = 32 K`` directly.

2. Three Hardware-Level Guidelines
===================================

pccx v002 prioritizes three techniques across the RTL, the NPU memory
controller, and the driver. The KV cache is managed as a **circular ring
buffer** within the L2 cache / DDR address space.

.. pccx-memory-layout::
   :banks: 8
   :depth: 4
   :title: KV Cache Ring Buffer Layout (L2/DDR)

*Figure KV-Layout: KV entries are stored in tiled banks. As the sequence
length grows, the ring buffer wraps around, preserving only the
Attention Sink and the most recent Window tokens.*

2.1 KV Cache Quantization
--------------------------

- **What**: store KV entries as **INT8** or **INT4** in DRAM instead of
  FP16.
- **Why it works**:

  - FP16 → INT8: 2×, FP16 → INT4: 4× savings in both bandwidth and
    capacity.
  - The format lines up with the W4A8 compute pipeline, so the existing
    dequantize paths can be reused.

- **Implementation path**:

  - ``MEMCPY from_device=1, to_device=1`` inserts in-line quantization
    on the KV write path (sharing the activation scale).
  - Per-head / per-channel scales are preloaded into the Constant Cache
    via MEMSET.

2.2 Compression and Eviction
-----------------------------

- The driver retains only the **Attention Sink** (the first few tokens of
  the prompt) and a **Local Window** (recent tokens). Middle tokens are
  **evicted** on a schedule.
- Combined with Google **Turbo Quant**-style live requantization, the
  effective KV footprint shrinks even further.
- Eviction is encoded as an update to the KV ring index in the driver.
  The hardware only tracks "which indices are valid" — there is no
  physical erase, just a logical cutoff.

2.3 Maximum Size Limit
-----------------------

- The driver hard-codes a ring-buffer ceiling at init time, e.g.
  ``KV_MAX_TOKENS = 8192``.
- On overflow the oldest entries are overwritten per the eviction policy.
- Purpose:

  - Prevents OOM on boards with ≲ 4 GB of RAM.
  - Makes bandwidth use predictable and bounded.

3. Instruction Mapping
=======================

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Technique
     - Primary Instruction
     - Notes
   * - KV quantization
     - ``MEMCPY``, ``CVO_SCALE``
     - Dequantize / requantize pairs on the dest / src paths.
   * - Eviction
     - Driver-only
     - ``pccx_kv_evict(handle, upto_idx)`` — no hardware state change.
   * - Size limit
     - Driver-only
     - ``pccx_kv_init(handle, max_tokens)`` — sets ring-buffer base and
       capacity.

4. Performance Impact Summary
==============================

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Scenario
     - Bandwidth Pressure
     - MAC Utilization
     - Notes
   * - FP16 KV, 32 K
     - **Severe**
     - ~10 %
     - Memory-wall bound
   * - INT8 KV, 32 K
     - Medium
     - ~35 %
     - Default recommended config
   * - INT4 KV + Eviction, 32 K
     - Relaxed
     - ~70 %
     - With Attention Sink + Window policy
   * - INT4 KV + Turbo Quant, 32 K
     - Relaxed
     - **~85 %+**
     - Extra compression reaches the cold path

5. Open Questions
==================

- **Accuracy impact**: quantifying the task-level accuracy drop of INT4
  KV on Gemma 3N's eval suite is still to be done.
- **Model-specific eviction tuning**: Attention Sink count and window
  size are per-model hyperparameters that need to be exposed through
  driver configuration.
- **Dynamic requantization latency**: Turbo Quant-style periodic
  requantization eats into the ``CVO_SCALE`` scheduling budget — we
  need to reserve slots for it.

Driver APIs for KV management are covered in the KV section of
:doc:`../Drivers/api`.
