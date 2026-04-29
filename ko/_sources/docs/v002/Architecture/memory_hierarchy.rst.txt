======================
Memory Hierarchy
======================

The pccx v002 memory subsystem is a four-level hierarchy:
**host DDR4 → Weight Buffer / L2 Cache → L1 / Constant Cache →
registers inside each PE**. Each level is sized to match the bandwidth
of the next and to prevent data starvation in the compute cores.

.. _v002-memory-hierarchy-fig:
.. figure:: ../../../../_static/diagrams/v002_memory_hierarchy.svg
   :align: center
   :width: 600px
   :name: fig-memory-hierarchy

   pccx v002 Memory Hierarchy & Interconnect Architecture. Weights and
   activations are staged from host DDR4 through URAM-based L2 and
   Weight Buffers to the compute-local BRAM caches.

1. Hierarchy
=============

.. list-table::
   :header-rows: 1
   :widths: 18 14 18 20 30

   * - Level
     - Media
     - Capacity (KV260)
     - Peak Bandwidth
     - Purpose
   * - **L0 Register**
     - FF
     - Inside DSP48E2
     - 48 bit / clk / DSP
     - Accumulator
   * - **L1 Cache**
     - BRAM
     - A few KB per core
     - 32 element / clk
     - GEMV activation / result staging
   * - **Constant Cache**
     - BRAM
     - A few KB per core
     - 16 bit × N / clk
     - ISA shape/size pointers, scale factors
   * - **L2 Cache**
     - URAM
     - **1.75 MB** (114,688 × 128-bit; ~50 of 64 URAM)
     - 256 bit × 2 / clk (both slices)
     - Activations, KV cache, intermediate results
   * - **Weight Buffer**
     - URAM (FIFO)
     - 4 × 64 KB (4 HP ports, 4096 deep each)
     - 128 bit/clk per HP port @ 250 MHz
     - INT4 weight stream
   * - **Host DDR4**
     - External DRAM
     - 4 × 512 Mb × 16-bit
     - **19.2 GB/s**
     - Model weights, inputs, token outputs

2. Bandwidth Matching
======================

2.1 Weight Path
---------------

**Goal**: the HP ports must deliver enough weight bandwidth to feed the
GEMM systolic array each cycle.

- Systolic array: **32 × 32 = 1,024 DSP** at 400 MHz (one grid, cascade
  split at row 16 into two 32 × 16 sub-chains).
- With W4A8 dual-channel packing, **1 DSP = 2 MAC**, so 2,048 MAC/clk.
- Weight demand: 2,048 × 4 bit = **8,192 bit/clk @ 400 MHz**.
- Supply: HP0 + HP1 deliver **2 × 128 bit/clk @ 250 MHz** (64 Gbit/s
  total raw), which normalizes to **~160 bit/clk @ 400 MHz** downstream
  of the CDC FIFO.

The gap is closed by **weight reuse (Weight Stationary)**: the GEMM
systolic array preloads weights once and reuses them for hundreds to
thousands of cycles; the Weight Buffer only prefetches. See
:doc:`gemm_core` for the exact reuse pattern.

2.2 Activation Path
-------------------

**Goal**: L2 cache must satisfy concurrent activation reads from GEMM,
GEMV, and SFU.

- L2 cache ports: **dual-port URAM** — ACP DMA on Port A, NPU compute
  on Port B, both 128-bit wide per cycle.
- Peak per-slice activation demand from the GEMV cores: 4 cores ×
  32 INT8 elements per clock = 128 INT8 elements per clock total.
  A single 128-bit URAM read supplies 16 INT8 elements per cycle,
  so the GEMV broadcast path (the same activation is reused across
  all four cores) fits within a single port.

2.3 Host ↔ Device Path
----------------------

**Goal**: load model weights during prefill, and support KV cache updates
plus token output during decoding.

- DMA via AXI ACP port. Capped by host DDR4's 19.2 GB/s.
- At ~20 tokens/s the host ↔ device traffic is dominated by KV cache
  updates and new token writes — well within the budget.

3. Cache Operating Policy
==========================

3.1 L2 Cache: Central Shared Buffer
------------------------------------

L2 cache runs as a **software-managed scratchpad** — there is no
hardware replacement policy. Addresses are named directly in the
instruction stream (``MEMCPY dest_addr``, ``GEMM src_addr``).

The 1.75 MB L2 capacity is partitioned into 8 banks of dual-port URAM to
support concurrent access from multiple cores.

.. pccx-memory-layout::
   :banks: 8
   :depth: 4
   :title: L2 Shared Buffer Bank Organization (URAM)

Benefits:

- Predictable latency (no tag matching, no miss handling).
- The compiler can lay out data statically and route around interconnect
  contention.

3.2 Constant Cache: ISA Pointer Backing Store
----------------------------------------------

The ISA references shape / size metadata through 6-bit
``shape_ptr_addr`` and ``size_ptr_addr`` fields. These pointers index
into the Constant Cache's 64 entries, which are preloaded by MEMSET. See
:doc:`../ISA/instructions` for the encoding.

3.3 Weight Buffer: Streaming FIFO
----------------------------------

The Weight Buffer is implemented as a circular FIFO that absorbs the
timing difference between HP port prefetch and core consumption. It
supports both GEMM's Weight Stationary reuse and GEMV's Weight Streaming
pattern via bank-level interleaving.

4. Preventing Data Starvation
==============================

Pipeline stalls are avoided with **double-buffering** throughout:

- **GEMM activations**: ping-pong buffers between L2 and the PEs.
- **GEMV activations**: L1 cache partitioned across banks so that
  reads and writes proceed in parallel.
- **Weights**: ping-pong FIFO inside the Weight Buffer.

The design targets 100% utilization on every compute core under ideal
conditions. Measured utilization will be reported in the Implementation
section once synthesis results are in.
