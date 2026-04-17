=====================
Physical Floorplan
=====================

.. figure:: ../../../assets/images/Architecture/v002/architecture_v002.png
   :align: center
   :width: 95%
   :alt: pccx v002 physical floorplan

   **Figure 2.** Physical floorplan of pccx v002. L2 cache occupies the
   center and feeds activations to the GEMV/SFU banks placed symmetrically
   above and below, as well as to the systolic arrays on the right.

1. Symmetric Placement Strategy
================================

The defining physical feature of pccx v002 is the **centered shared L2
cache flanked by symmetric compute slices**.

- **Central L2 cache**: placed at the geometric center of the floorplan
  so that the upper and lower slices reach activations with identical
  latency.
- **Upper / lower slices**: each slice contains a GEMV 32×1 bank, an SFU
  bank, a constant cache, and an L1 cache. During decoding the two slices
  can run in parallel on different batches, heads, or multi-query streams.
- **Right-side systolic arrays**: two 32×16 systolic arrays sit
  side-by-side to handle the heavy GEMMs in the prefill stage.

2. Bus Structure
================

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Bus
     - Purpose
   * - **WEIGHT BUS**
     - Broadcasts weights from the Weight Buffer into the pipeline
       registers of the GEMM / GEMV cores. A pipeline register
       (*Pipeline REG - WEIGHT BUS*) sits immediately before each bank to
       relax timing.
   * - **ACTIVATION BUS**
     - Connects the L2 cache to GEMV / SFU / systolic array. Runs on the
       vertical axis from the central L2, distributing up and down with
       bidirectional read/write.
   * - **AXI DMA HP Port [2, 3]**
     - Upper and lower slices each own an independent HP port and stream
       weights from host DDR4. Effective bandwidth is
       **256 bit/clk @ 250 MHz**.

3. Cache Bank Layout
=====================

Each slice's caches are **split by function**.

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Cache
     - Purpose
     - Description
   * - **L1 Cache**
     - Core-local
     - Direct access for GEMV operations. Private to each core.
   * - **Constant Cache**
     - Constants
     - Stores ISA shape/size pointers, weight scale factors, etc.
       Preloaded by MEMSET.
   * - **L2 Cache**
     - Shared (central)
     - Activations, KV cache, intermediate results. Accessible
       concurrently from both slices.
   * - **Weight Buffer**
     - Weight stream
     - Circular queue that temporarily holds INT4 weights streamed from
       the HP ports.

4. Physical Design Considerations
==================================

4.1 Routing Symmetry
---------------------

Wire lengths between L2 and each slice are matched to keep activation
latency identical on both sides. This is a prerequisite for the software
stack to schedule **symmetric work partitioning** across the two slices.

4.2 Concentrated DSP Slices
----------------------------

Most of KV260's 1,248 DSP48E2 slices are packed into the right-side
systolic array region. The GEMV and SFU banks keep DSP usage minimal by
favoring LUT / BRAM-based arithmetic. Exact placement will be updated in
the Implementation section once post-synthesis results are available.

4.3 BRAM / URAM Allocation
---------------------------

- **L2 Cache**: URAM-based (~96 blocks).
- **L1 / Constant Cache**: BRAM-based (~140 blocks).
- **Weight Buffer**: BRAMs in FIFO mode.

.. note::

   Resource usage scales with generate parameters. For the recommended
   KV260 configuration see :doc:`../../Devices/kv260`.
