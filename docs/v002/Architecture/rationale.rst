===================================================
Design Rationale: v001 → v002
===================================================

pccx v001 reached the brink of implementation before being moved to
``docs/archive/experimental_v001/`` rather than taped out. This page
documents which architectural weaknesses pushed us to that decision and
how v002 resolves each of them.

1. Core Flaws in v001
=====================

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flaw
     - Symptom
   * - **Ambiguous core roles**
     - The boundaries between Matrix, Vector, and CVO cores were fuzzy.
       Some operations were redundantly supported across multiple cores,
       and others fit none of them cleanly.
   * - **Too many buses**
     - Weights, activations, and intermediate results each had their own
       bus, crossing the fabric in different directions. The result was
       routing congestion and poor timing.
   * - **L2 and Global Cache overlap**
     - The two cache levels covered overlapping responsibilities, so the
       same data ended up duplicated on both sides and coherence logic
       added a constant tax.
   * - **Inefficient HP port layout**
     - A single systolic array was served by a single HP port. The
       external 250 MHz limit capped the internal 400 MHz consumption rate.
   * - **Under-utilized systolic array**
     - The 1-DSP-per-1-MAC structure left most of DSP48E2's bit space
       unused.

2. v002's Response
===================

Each flaw maps to a specific design decision in v002.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Response
     - Description
   * - **Three-core organization**
     - **GEMV, GEMM, and SFU** are cleanly separated. Each core is wired
       to the L2 cache, the weight buffer, and the pipeline registers /
       FIFOs that suit its access pattern — no more overlapping roles.
   * - **Bus simplification**
     - Everything collapses onto two orthogonal axes: ``WEIGHT BUS`` and
       ``ACTIVATION BUS``. The two buses are physically perpendicular to
       avoid routing contention.
   * - **Centralized L2**
     - Global Cache responsibilities are folded into L2, and L2 is placed
       in the middle of the floorplan. The upper and lower slices see it
       symmetrically.
   * - **Distributed HP ports**
     - HP2 and HP3 are assigned to independent slices, eliminating the
       weight-supply bottleneck.
   * - **Dual-channel bit packing**
     - 1 DSP = **2 MAC** (:doc:`dsp48e2_w4a8`). Across the whole systolic
       array this works out to **2,048 multiplies + 2,048 accumulates per
       clock cycle**.

3. Speedup Analysis — 3.125×
=============================

The theoretical throughput gain over v001 comes from three independent
levers, multiplied together.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Lever
     - Factor
     - Justification
   * - **Higher internal clock**
     - × 400 / 250 = **1.6**
     - External AXI 250 MHz decoupled from internal core 400 MHz.
   * - **Dual HP ports**
     - (already consumed at 400 MHz)
     - 2 of 4 HP ports (HP2 / HP3) are independently assigned to the upper
       and lower slices, doubling weight-supply bandwidth.
   * - **Bit packing**
     - × **2**
     - 1 DSP now executes 2 MACs simultaneously.

Multiplying the three levers gives
**1.6 × 2 × (bottleneck removed) ≈ 3.125×** effective throughput.

3.1 Load-Side Derivation
-------------------------

v001: 250 MHz × 1 HP × 1 MAC/DSP = **250 units of throughput**.
v002: HP2 + HP3 stack weights at 250 MHz into a buffer, which is then
consumed by the internal 400 MHz domain at 2 MACs per DSP, giving
**800 units of internal consumption rate**.

.. math::

   \frac{800}{250} \;=\; \mathbf{3.125\,\times}

The external port rate didn't change. The win is structural: **buffer
externally, drain quickly internally, and perform two MACs per cycle**.
The effective throughput seen by the systolic array is 3.125× higher.

3.2 Per-Cycle Internal Throughput
----------------------------------

.. mermaid::

   flowchart LR
     subgraph ext[External 250 MHz Domain]
       HP2[AXI HP2] --> BUF[Weight Buffer<br/>CDC FIFO]
       HP3[AXI HP3] --> BUF
     end
     subgraph core[Internal 400 MHz Domain]
       BUF -->|broadcast| SA1[Systolic Array #1<br/>32×16, 1 DSP = 2 MAC]
       BUF -->|broadcast| SA2[Systolic Array #2<br/>32×16, 1 DSP = 2 MAC]
       SA1 --> ACC[Result Accumulator<br/>819 GMAC/s peak]
       SA2 --> ACC
     end

Each systolic array performs **32 × 16 × 2 = 1,024 MAC/clk**. Combined,
2,048 MAC/clk × 400 MHz yields a **819 GMAC/s theoretical peak**.

4. New Trade-offs
==================

The speed gain is not free. v002 accepts the following constraints.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Constraint
     - Description
   * - **Weight precision ceiling**
     - Beyond W4, guard bits run out and ``N_max`` collapses. W5/W6
       support would require a separate mode.
   * - **K-split required**
     - Layers with K > 4,096 must be tiled by the driver / compiler.
   * - **Sign-recovery post-processing**
     - Each PE gains a 1-bit adder and 23-bit split logic. No throughput
       impact, but extra area.
   * - **CDC complexity**
     - Asynchronous 250 MHz ↔ 400 MHz FIFOs need careful design and
       verification.

5. Summary vs. Archived v001
=============================

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Aspect
     - v001 (Archived)
     - v002
   * - Design bias
     - GEMM-centric (prefill-optimized)
     - Three-core layout: GEMM · GEMV · SFU
   * - L2 cache placement
     - Peripheral
     - **Central**, symmetric interconnect on both sides
   * - Global Cache
     - Separate block
     - Absorbed into L2
   * - Quantization
     - W4A16 (BF16 activations)
     - **W4A8 (INT8 activations)**
   * - HP port
     - One per SA
     - HP2 / HP3 distributed (upper / lower slices)
   * - DSP utilization
     - 1 DSP = 1 MAC
     - **1 DSP = 2 MAC**
   * - Peak throughput (400 MHz)
     - ~320 GMAC/s
     - **819 GMAC/s (~2.56× measured improvement expected)**

.. seealso::

   - v001 details: :doc:`../../archive/experimental_v001/index`
   - Bit packing details: :doc:`dsp48e2_w4a8`
   - KV cache strategy: :doc:`kv_cache`
