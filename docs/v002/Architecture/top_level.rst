======================
Top-Level Architecture
======================

.. figure:: ../../../assets/images/Architecture/v002/top_level_architecture_GEMM_v002.png
   :align: center
   :width: 80%
   :alt: pccx v002 top-level block diagram

   **Figure 1.** pccx v002 top-level block diagram. Shows the data path
   between host DDR4 and the device-side L2 cache, the clock domain
   crossings, and the placement of each heterogeneous compute core.

1. Design Principles
=====================

The top level is organized around four principles.

1. **Clock domain separation** — The AXI infrastructure (250 MHz) is
   decoupled from the core logic (400 MHz) so that AXI protocol timing
   never constrains the core frequency.
2. **Decoupled dataflow** — Instruction decode (front-end) and execution
   (back-end) are separated by an asynchronous FIFO, eliminating pipeline
   stalls due to dispatch latency.
3. **Separated weight and activation paths** — Weights stream directly
   from host DDR4 into the weight buffer, while activations flow from the
   central L2 cache. The two streams never collide on the interconnect.
4. **Centralized L2 cache** — GEMM, GEMV, and SFU are placed physically
   close to L2, eliminating the cost of reshuffling activations between
   layers.

2. Major Blocks
================

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Block
     - Domain
     - Role
   * - **Host Interface**
     - 250 MHz
     - AXI-Lite (control registers), AXI HP ports (data streaming), AXI
       ACP (host-cache DMA). Bridged to the 400 MHz domain through a CDC
       FIFO.
   * - **Device Interface**
     - 400 MHz
     - Core-side AXI slave. Bridges onto the Weight Bus and the L2 cache
       R/W ports.
   * - **Decoder / Dispatcher**
     - 400 MHz
     - Decodes 64-bit instructions and emits per-opcode control μops.
       See :doc:`../ISA/encoding`.
   * - **Control Unit**
     - 400 MHz
     - Global scheduler. Handles dependency resolution, dispatch ordering,
       and completion notification.
   * - **Weight Buffer**
     - 400 MHz
     - Broadcasts INT4 weights streamed in from the HP ports to the
       GEMM / GEMV cores.
   * - **L2 Cache**
     - 400 MHz
     - Central shared cache. Stores activations, intermediate results, and
       the KV cache.
   * - **Constant Cache**
     - 400 MHz
     - Stores small constants — shape / size pointers, scale factors —
       written by MEMSET.
   * - **Systolic Array (32×16 ×2)**
     - 400 MHz
     - GEMM-only 2D systolic array. See :doc:`gemm_core`.
   * - **GEMV Core (32×1 ×4)**
     - 400 MHz
     - Parallel vector MAC + reduction tree. See :doc:`gemv_core`.
   * - **SFU (32×1 ×4)**
     - 400 MHz
     - Non-linear functions — Softmax, GELU, RMSNorm, and more.
       See :doc:`sfu_core`.

3. Clock Domain Strategy
=========================

3.1 Why Split the Domains
--------------------------

The KV260 AXI interconnect closes timing comfortably at 250 MHz, but the
core logic — when all DSP48E2 pipeline stages are enabled — can reach
400 MHz. Separating the two lets each subsystem run at its natural rate:

- **AXI domain (250 MHz)**: Host, DMA, AXI-Lite control register access.
- **Core domain (400 MHz)**: Dispatcher, Control Unit, every compute core,
  L2 cache.

3.2 CDC (Clock Domain Crossing)
--------------------------------

The domain boundary is crossed through an **asynchronous FIFO**. Each
AXI HP port delivers bursts at ``burst_length × AXI_clock`` bandwidth,
sized so that the 400 MHz core side is never starved. See the bandwidth
matching analysis in :doc:`memory_hierarchy`.

4. Data Path Summary
=====================

.. mermaid::

   flowchart LR
     DDR[(Host DDR4)] -->|HP2/HP3| WB[Weight Buffer]
     DDR -->|ACP DMA| L2[(L2 Cache<br/>Central URAM)]
     WB --> SA[Systolic Array<br/>32×16 ×2]
     WB --> GV[GEMV Core<br/>×4]
     L2 --> SA
     L2 --> GV
     L2 <--> SFU[SFU<br/>×4]
     GV <-. direct FIFO .-> SFU
     SA --> L2
     GV --> L2
     SFU --> L2
     DISP[Decoder / Dispatcher] -->|μop| SA
     DISP -->|μop| GV
     DISP -->|μop| SFU
     DISP -->|MEMSET| CC[Constant Cache]

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Instruction
     - Primary Data Path
     - Notes
   * - **GEMM**
     - Weight Buffer → Systolic Array ← L2
     - Prefill stage. Weights and activations meet inside the array.
   * - **GEMV**
     - Weight Buffer → GEMV Core ← L2
     - Decoding stage. Four GEMV cores partition across batch / head.
   * - **CVO (SFU)**
     - L2 ↔ SFU, with direct GEMV ↔ SFU FIFO
     - Weight path unused. Softmax / GELU / RoPE.
   * - **MEMCPY**
     - Host DDR4 ↔ L2
     - ACP port. Synchronous or asynchronous.
   * - **MEMSET**
     - Dispatcher → Constant Cache
     - Initializes small constants — shape / size pointers and the like.

For per-instruction dataflow detail, see :doc:`../ISA/dataflow`.
