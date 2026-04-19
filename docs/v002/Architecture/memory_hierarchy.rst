======================
Memory Hierarchy
======================

The pccx v002 memory subsystem is a four-level hierarchy:
**host DDR4 → Weight Buffer / L2 Cache → L1 / Constant Cache → PE
registers**. Each level is sized to **match bandwidth** with the next and
to **prevent data starvation** in the compute cores.

.. mermaid::

   flowchart TB
     DDR[("Host DDR4<br/>19.2 GB/s")]
     subgraph ext["External 250 MHz"]
       HP["AXI HP2 / HP3<br/>256 bit/clk × 2"]
     end
     subgraph core["Internal 400 MHz"]
       WB["Weight Buffer<br/>BRAM FIFO"]
       L2[("L2 Cache<br/>URAM ~1.75 MB")]
       L1["L1 Cache<br/>per-core BRAM"]
       CC["Constant Cache<br/>BRAM"]
       L0["L0 Accumulator<br/>DSP48E2 P-reg"]
     end
     DDR --> HP
     HP -->|weights| WB
     HP -->|activations| L2
     WB --> L1
     L2 --> L1
     L2 --> CC
     L1 --> L0

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
     - BRAM (FIFO)
     - ~128 KB
     - 256 bit / clk × 2 HP ports
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

- Systolic array: **32 × 16 × 2 = 1,024 DSP** at 400 MHz.
- With W4A8 dual-channel packing, **1 DSP = 2 MAC**, so 2,048 MAC/clk.
- Weight demand: 2,048 × 4 bit = **8,192 bit/clk @ 400 MHz**.
- Supply: 256 bit/clk each on HP0 / HP1 at 250 MHz, i.e., about
  **128 bit/clk @ 400 MHz** equivalent.

The gap is closed by **weight reuse (Weight Stationary)**: the GEMM
systolic array preloads weights once and reuses them for hundreds to
thousands of cycles; the Weight Buffer only prefetches. See
:doc:`gemm_core` for the exact reuse pattern.

2.2 Activation Path
-------------------

**Goal**: L2 cache must satisfy concurrent activation reads from GEMM,
GEMV, and SFU.

- L2 cache ports: each slice owns independent read / write ports
  (**dual-port URAM**).
- Peak slice-side demand: GEMV 32×1 × 4 cores = 128 INT8 element/clk. A
  256 bit/clk port supplies this comfortably.

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
instruction stream (``MEMCPY dest_addr``, ``GEMM src_addr``). Benefits:

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

- **GEMM activations**: ping-pong buffers between L2 and PE.
- **GEMV activations**: bank-split L1 cache for simultaneous read/write.
- **Weights**: ping-pong FIFO inside the Weight Buffer.

The design targets **100% busy-rate** for every compute core under ideal
conditions. Measured utilization will be reported in the Implementation
section once synthesis results come in.
