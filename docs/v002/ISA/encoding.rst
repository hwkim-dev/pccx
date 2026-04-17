=====================
Instruction Encoding
=====================

1. Format Overview
===================

Every pccx v002 instruction is **fixed 64 bits long** and follows this
top-level layout.

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Bits
     - Field
     - Description
   * - ``[63:60]``
     - opcode
     - 4 bits. Up to 16 opcodes; 5 in use today.
   * - ``[59:0]``
     - instruction body
     - 60 bits. Per-opcode layouts are detailed in §3.

2. Opcode Table
================

.. list-table::
   :header-rows: 1
   :widths: 15 15 30 40

   * - Opcode
     - Mnemonic
     - Function
     - Primary fields
   * - ``4'h0``
     - **GEMV**
     - Matrix × vector
     - dest_reg, src_addr, flags, shape_ptr, size_ptr, parallel_lane
   * - ``4'h1``
     - **GEMM**
     - Matrix × matrix
     - Identical layout to GEMV
   * - ``4'h2``
     - **MEMCPY**
     - Device-to-device data movement
     - from_device, to_device, dest_addr, src_addr, aux_addr, shape_ptr, async
   * - ``4'h3``
     - **MEMSET**
     - Constant Cache write
     - dest_cache, dest_addr, a/b/c_value
   * - ``4'h4``
     - **CVO**
     - Complex Vector Op (SFU)
     - cvo_func, src_addr, dst_addr, length, flags, async
   * - ``4'h5`` – ``4'hF``
     - *reserved*
     - —
     - Reserved for future extensions

3. Decode Flow
===============

The host writes instructions into the AXI-Lite CMD_IN FIFO. The decode
path is:

.. mermaid::

   flowchart TB
     CMD[[AXI-Lite<br/>CMD_IN FIFO]] --> DEC["Decoder<br/>(ctrl_npu_decode)<br/>opcode[63:60] branch"]
     DEC -->|control μop<br/>memory μop<br/>CVO μop| DISP["Dispatcher<br/>(ctrl_dispatcher)"]
     GS[[Global Scheduler<br/>dependency / hazard check]] -.-> DISP
     DISP --> GEMM[GEMM ctrl]
     DISP --> GEMV[GEMV ctrl]
     DISP --> MC[MEMCTRL<br/>ACP / NPU]
     DISP --> MS[MEMSET<br/>Constant]
     DISP --> CVO[CVO ctrl]

4. μop Decomposition
=====================

Inside the dispatcher, each opcode decomposes into the following μops.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - μop type
     - Fields
   * - ``gemm_control_uop_t``
     - flags (6 bit) + size_ptr_addr (6 bit) + parallel_lane (5 bit)
   * - ``GEMV_control_uop_t``
     - Same layout as ``gemm_control_uop_t``
   * - ``memory_control_uop_t`` (49 bit)
     - data_route (8 bit) + dest_addr + src_addr + shape_ptr + async
   * - ``memory_set_uop_t``
     - dest_cache (2 bit) + dest_addr + a/b/c_value (16 bit × 3)
   * - ``cvo_control_uop_t``
     - cvo_func (4 bit) + src_addr + dst_addr + length + flags + async

5. Memory Routing Encoding
===========================

The ``from_device`` + ``to_device`` pair in MEMCPY is expanded inside the
Control Unit into an 8-bit route enum (``data_route_e``).

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Route
     - Encoding
     - Path
   * - ``from_host_to_L2``
     - ``8'h01``
     - Host DDR4 → L2 cache
   * - ``from_L2_to_host``
     - ``8'h10``
     - L2 cache → host DDR4
   * - ``from_L2_to_L1_GEMM``
     - ``8'h12``
     - L2 → GEMM L1
   * - ``from_L2_to_L1_GEMV``
     - ``8'h13``
     - L2 → GEMV L1
   * - ``from_L2_to_CVO``
     - ``8'h14``
     - L2 → SFU
   * - ``from_GEMM_res_to_L2``
     - ``8'h21``
     - GEMM result → L2
   * - ``from_GEMV_res_to_L2``
     - ``8'h31``
     - GEMV result → L2
   * - ``from_CVO_res_to_L2``
     - ``8'h41``
     - SFU result → L2

6. Pointer / Parameter Registers
=================================

The ISA uses 6-bit pointers to index small entries in the Constant
Cache.

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Pointer
     - Width
     - Content
   * - ``shape_ptr_addr``
     - 6 bit
     - Tensor shape metadata (M, N, K).
   * - ``size_ptr_addr``
     - 6 bit
     - Tile sizes, loop bounds, etc.
   * - ``ptr_addr_t`` (shared)
     - 6 bit
     - Index into the 64-entry Constant Cache.

Pointer entries are preloaded by **MEMSET** (see the MEMSET section of
:doc:`dataflow`).

7. Address Space
=================

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Width
     - Address space
   * - ``dest_addr`` / ``src_addr``
     - 17 bit
     - 128 K entries (indexed by L2 cache block).
   * - ``aux_addr``
     - 17 bit
     - MEMCPY auxiliary address (e.g., host DDR offset).

Entry size is defined at the device layer (128 bit per word on KV260),
so 17 bit × 16 byte yields a **2 MB** linear L2 address space.
