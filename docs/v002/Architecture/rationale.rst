===================================================
Design Rationale: v001 → v002
===================================================

pccx v001 reached late-stage RTL implementation before being archived
to ``docs/archive/experimental_v001/`` rather than taken through to
tape-out. This page documents the architectural weaknesses that drove
that decision and how v002 addresses each of them.

1. Core Flaws in v001 & v002's Response
=======================================

The table below visualizes how each architectural weakness in v001 directly drove a specific design decision in v002.

.. mermaid::

   flowchart LR
     subgraph v001 ["v001 Flaws"]
       F1[Ambiguous core roles]
       F2[Too many buses]
       F3[L2 / Global Cache overlap]
       F4[Inefficient HP port layout]
       F5[Under-utilized systolic array]
     end

     subgraph v002 ["v002 Responses"]
       R1[Three-core organization]
       R2[Bus simplification]
       R3[Centralized L2 Cache]
       R4[Distributed HP ports]
       R5[Dual-channel bit packing]
     end

     F1 -->|Fuzzy boundaries| R1
     F2 -->|Routing congestion| R2
     F3 -->|Duplicated data| R3
     F4 -->|Bottlenecked weight supply| R4
     F5 -->|1 MAC per DSP| R5

     style v001 fill:#f5edd5,stroke:#dbe1ea,stroke-width:2px,color:#000
     style v002 fill:#dae7f4,stroke:#dbe1ea,stroke-width:2px,color:#000

- **Three-core organization**: GEMV, GEMM, and SFU are cleanly separated. Each core is wired to the L2 cache and weight buffer that suits its access pattern.
- **Bus simplification**: Everything collapses onto two orthogonal axes (WEIGHT BUS and ACTIVATION BUS) to avoid routing contention.
- **Centralized L2**: Global Cache responsibilities are folded into L2, which is placed in the center of the floorplan.
- **Distributed HP ports**: HP2 and HP3 are assigned to independent slices, eliminating the weight-supply bottleneck.
- **Dual-channel bit packing**: 1 DSP = 2 MACs, yielding 2,048 MACs per clock cycle across the systolic array.

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
v002: HP2 and HP3 stream weights at 250 MHz into a shared buffer that
the internal 400 MHz domain drains at 2 MACs per DSP, yielding
**800 units of internal consumption rate**.

.. math::

   \frac{800}{250} \;=\; \mathbf{3.125\,\times}

The external port rate is unchanged. The improvement is structural:
weights are buffered externally at 250 MHz, drained at the higher
internal 400 MHz clock, and each DSP executes two MACs per cycle.
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
       BUF -->|broadcast| SA[Systolic Array<br/>32×32 · 1 DSP = 2 MAC<br/>cascade break @ row 16]
       SA --> ACC[Result Accumulator<br/>819 GMAC/s peak]
     end

The single 32 × 32 grid holds **1,024 PEs × 2 MAC = 2,048 MAC/clk**.
Running at 400 MHz, this yields a **819 GMAC/s theoretical peak**.

4. New Trade-offs
==================

v002 accepts the following constraints in exchange for the throughput gain.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Constraint
     - Description
   * - **Weight precision ceiling**
     - Beyond W4, guard bits are exhausted and the maximum representable
       accumulated value (``N_max``) drops sharply. W5/W6 support would
       require a separate mode.
   * - **K-split required**
     - Layers with K > 4,096 must be tiled by the driver or compiler.
   * - **Sign-recovery post-processing**
     - Each PE adds a 1-bit adder and 23-bit split logic. No throughput
       impact, but additional area cost.
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
