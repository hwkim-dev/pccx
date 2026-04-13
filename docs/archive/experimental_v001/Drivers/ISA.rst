uCA ISA Specification
=====================

**uCA**: micro Compute Architecture — the FPGA NPU instruction set.

Target: Kria KV260 \| Word width: **64-bit** \| Encoding: **VLIW**

RTL source: ``hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/``

--------------

1. Instruction Format
---------------------

Every instruction is 64 bits wide.

::

    [63:60]   [59:0]
    OPCODE    BODY (60 bits, layout depends on opcode)

The top-level decoder (``ctrl_npu_decoder.sv``) strips the 4-bit opcode
and routes the remaining 60-bit body to the appropriate execution
engine.

--------------

2. Opcode Table
---------------

+-------+------------+-------+---------------------------------------+
| O     | Mnemonic   | Value | Target Engine                         |
| pcode |            |       |                                       |
+=======+============+=======+=======================================+
| `     | Vec        | ``4   | Vector Core (μV-Cores)                |
| `OP_G | tor–Matrix | 'h0`` |                                       |
| EMV`` | Multiply   |       |                                       |
+-------+------------+-------+---------------------------------------+
| `     | Mat        | ``4   | Matrix Core (Systolic Array)          |
| `OP_G | rix–Matrix | 'h1`` |                                       |
| EMM`` | Multiply   |       |                                       |
+-------+------------+-------+---------------------------------------+
| ``O   | Memory     | ``4   | MEM Dispatcher                        |
| P_MEM | Copy       | 'h2`` |                                       |
| CPY`` |            |       |                                       |
+-------+------------+-------+---------------------------------------+
| ``O   | Memory Set | ``4   | MEM Dispatcher                        |
| P_MEM |            | 'h3`` |                                       |
| SET`` |            |       |                                       |
+-------+------------+-------+---------------------------------------+
| ``OP_ | Complex    | ``4   | CVO Core (μCVO-Cores)                 |
| CVO`` | Vector Op  | 'h4`` |                                       |
+-------+------------+-------+---------------------------------------+
| —     | Reserved   | ``    | —                                     |
|       |            | 4'h5` |                                       |
|       |            | `–``4 |                                       |
|       |            | 'hF`` |                                       |
+-------+------------+-------+---------------------------------------+

--------------

3. Instruction Encoding
-----------------------

3.1 GEMV / GEMM (``OP_GEMV``, ``OP_GEMM``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both share the same body layout.

::

   [59:43]  dest_reg       17-bit  Destination register / address
   [42:26]  src_addr       17-bit  Source address
   [25:20]  flags           6-bit  Control flags (see §4)
   [19:14]  size_ptr_addr   6-bit  Pointer to size descriptor
   [13:8]   shape_ptr_addr  6-bit  Pointer to shape descriptor
   [7:3]    parallel_lane   5-bit  Number of active parallel lanes
   [2:0]    reserved        3-bit

3.2 MEMCPY (``OP_MEMCPY``)
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   [59]     from_device     1-bit  0=FROM_NPU, 1=FROM_HOST
   [58]     to_device       1-bit  0=TO_NPU,   1=TO_HOST
   [57:41]  dest_addr      17-bit  Destination address
   [40:24]  src_addr       17-bit  Source address
   [23:7]   aux_addr       17-bit  Auxiliary address (reserved)
   [6:1]    shape_ptr_addr  6-bit  Pointer to shape descriptor
   [0]      async           1-bit  0=sync, 1=async transfer

3.3 MEMSET (``OP_MEMSET``)
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   [59:58]  dest_cache      2-bit  0=fmap_shape, 1=weight_shape
   [57:52]  dest_addr       6-bit  Destination pointer address (ptr_addr_t)
   [51:36]  a_value        16-bit  Value A
   [35:20]  b_value        16-bit  Value B
   [19:4]   c_value        16-bit  Value C
   [3:0]    reserved        4-bit

3.4 CVO (``OP_CVO``)
~~~~~~~~~~~~~~~~~~~~

Dispatched to the CVO Core (2× μCVO-Cores). Each μCVO-Core contains a
CORDIC unit (sin/cos) and an SFU (exp, sqrt, GELU). Required for
Transformer softmax, RMSNorm, and activation functions.

::

   [59:56]  cvo_func        4-bit  Function code (see §3.4.1)
   [55:39]  src_addr       17-bit  Source address in L2 cache
   [38:22]  dst_addr       17-bit  Destination address in L2 cache
   [21:6]   length         16-bit  Number of elements (vector length)
   [5:1]    flags           5-bit  Control flags (see §3.4.2)
   [0]      async           1-bit  0=sync, 1=async

3.4.1 CVO Function Codes
^^^^^^^^^^^^^^^^^^^^^^^^

+------+-----------+--------------------------------------+-----------+
| Code | Mnemonic  | Description                          | Hardware  |
|      |           |                                      | Unit      |
+======+===========+======================================+===========+
| ``4' | ``        | Element-wise exp(x)                  | SFU       |
| h0`` | CVO_EXP`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``C       | Element-wise sqrt(x)                 | SFU       |
| h1`` | VO_SQRT`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``C       | Element-wise GELU(x)                 | SFU       |
| h2`` | VO_GELU`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``        | Element-wise sin(x)                  | CORDIC    |
| h3`` | CVO_SIN`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``        | Element-wise cos(x)                  | CORDIC    |
| h4`` | CVO_COS`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``CVO_RED | Sum all elements → scalar at         | SFU +     |
| h5`` | UCE_SUM`` | dst_addr                             | Adder     |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``CV      | Element-wise multiply by scalar at   | SFU       |
| h6`` | O_SCALE`` | src_addr+0                           |           |
+------+-----------+--------------------------------------+-----------+
| ``4' | ``CV      | Element-wise 1/x                     | SFU       |
| h7`` | O_RECIP`` |                                      |           |
+------+-----------+--------------------------------------+-----------+
| `    | —         | Reserved                             | —         |
| `4'h |           |                                      |           |
| 8``– |           |                                      |           |
| ``4' |           |                                      |           |
| hF`` |           |                                      |           |
+------+-----------+--------------------------------------+-----------+

..

   **Softmax sequence** (one CVO pipeline pass): 1. ``OP_GEMV`` with
   ``FLAG_FINDEMAX`` — find e_max over attention scores 2.
   ``OP_CVO CVO_EXP`` with ``FLAG_SUB_EMAX`` — exp(x − e_max) for each
   score 3. ``OP_CVO CVO_REDUCE_SUM`` — sum of exps (denominator) 4.
   ``OP_CVO CVO_SCALE`` with ``FLAG_RECIP_SCALE`` — divide each exp by
   sum

   **RMSNorm sequence**: 1. ``OP_GEMV`` with ``FLAG_FINDEMAX`` during
   projection (emax already tracked) 2. ``OP_CVO CVO_REDUCE_SUM`` (of
   squares) → then 3. ``OP_CVO CVO_SQRT`` + ``CVO_RECIP`` →
   normalization factor 4. ``OP_CVO CVO_SCALE`` — apply learned weight γ

3.4.2 CVO Flags (5-bit, [5:1] of body)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   [5]  sub_emax      Subtract e_max from input before operation (requires prior FINDEMAX)
   [4]  recip_scale   Use reciprocal of scalar for SCALE (divide instead of multiply)
   [3]  accm          Accumulate into dst (do not overwrite)
   [2:1] reserved

--------------

4. Flags Field for GEMV/GEMM (6-bit, [25:20])
---------------------------------------------

::

   [5]  findemax   Find and register the exponent maximum (e_max) for output normalization
   [4]  accm       Accumulate result into destination register (do not overwrite)
   [3]  w_scale    Apply weight scale factor during MAC
   [2:0] reserved

--------------

5. Memory Routing Table (MEMCPY)
--------------------------------

Defined in ``isa_memctrl.svh`` as ``data_route_e``.

+-----------------+---------------------+------------------------------+
| Route Enum      | Encoding            | Description                  |
|                 | (``sr               |                              |
|                 | c[3:0]\|dst[3:0]``) |                              |
+=================+=====================+==============================+
| ``fr            | ``8'h01``           | Host DDR4 → L2 cache (fmap   |
| om_host_to_L2`` |                     | DMA in via ACP)              |
+-----------------+---------------------+------------------------------+
| ``fr            | ``8'h10``           | L2 cache → Host DDR4 (result |
| om_L2_to_host`` |                     | DMA out via ACP)             |
+-----------------+---------------------+------------------------------+
| ``from_         | ``8'h12``           | L2 → Matrix Core fmap        |
| L2_to_L1_GEMM`` |                     | broadcast                    |
+-----------------+---------------------+------------------------------+
| ``from_         | ``8'h13``           | L2 → Vector Core fmap        |
| L2_to_L1_GEMV`` |                     | broadcast                    |
+-----------------+---------------------+------------------------------+
| ``f             | ``8'h14``           | L2 → CVO Core input stream   |
| rom_L2_to_CVO`` |                     |                              |
+-----------------+---------------------+------------------------------+
| ``from_G        | ``8'h31``           | Vector Core result → L2      |
| EMV_res_to_L2`` |                     | cache                        |
+-----------------+---------------------+------------------------------+
| ``from_G        | ``8'h21``           | Matrix Core result → L2      |
| EMM_res_to_L2`` |                     | cache                        |
+-----------------+---------------------+------------------------------+
| ``from_         | ``8'h41``           | CVO Core result → L2 cache   |
| CVO_res_to_L2`` |                     |                              |
+-----------------+---------------------+------------------------------+

--------------

6. Micro-Op (uop) Structures
----------------------------

After decoding, the Global Scheduler splits the instruction body into
engine-specific micro-ops before dispatch.

6.1 GEMV / GEMM Control uop
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: systemverilog

   typedef struct packed {
       flags_t         flags;           // 6-bit
       ptr_addr_t      size_ptr_addr;   // 6-bit
       parallel_lane_t parallel_lane;   // 5-bit
   } gemv_control_uop_t;  // = gemm_control_uop_t

6.2 Memory Control uop
~~~~~~~~~~~~~~~~~~~~~~

.. code:: systemverilog

   typedef struct packed {
       data_route_e data_dest;      // 8-bit  (source[3:0] | dest[3:0])
       dest_addr_t  dest_addr;      // 17-bit
       src_addr_t   src_addr;       // 17-bit
       ptr_addr_t   shape_ptr_addr; // 6-bit
       async_e      async;          // 1-bit
   } memory_control_uop_t;

6.3 Memory Set uop
~~~~~~~~~~~~~~~~~~

.. code:: systemverilog

   typedef struct packed {
       dest_cache_e dest_cache;  // 2-bit
       ptr_addr_t   dest_addr;   // 6-bit
       a_value_t    a_value;
       b_value_t    b_value;
       c_value_t    c_value;
   } memory_set_uop_t;

6.4 CVO Control uop
~~~~~~~~~~~~~~~~~~~

.. code:: systemverilog

   typedef struct packed {
       cvo_func_e  cvo_func;     // 4-bit
       src_addr_t  src_addr;     // 17-bit
       dst_addr_t  dst_addr;     // 17-bit
       length_t    length;       // 16-bit
       cvo_flags_t flags;        // 5-bit
       async_e     async;        // 1-bit
   } cvo_control_uop_t;

--------------

7. Decoupled Dataflow Pipeline
------------------------------

The front-end and execution engines are strictly decoupled.

::

   Host (AXI-Lite) --> [AXIL_CMD_IN] --> ctrl_npu_decoder
                                               |
                      +----------+------+------+------+-----------+
                      v          v      v             v           v
                 GEMV FIFO  GEMM FIFO  CVO FIFO  MEM FIFO    MEMSET FIFO
                      |          |      |             |           |
                 μV-Core    Systolic  μCVO-Core  mem_dispatcher  mem_set
                (GEMV)    Array(GEMM) (CVO)

The front-end (``ctrl_npu_decoder``) issues instructions into per-engine
FIFOs and immediately returns — it never stalls waiting for execution to
complete. Each engine’s local dispatcher independently pops from its
FIFO and fires when operands are ready.

--------------

8. AXI-Lite Register Map
------------------------

Control is via ``S_AXIL_CTRL`` (HPM port on KV260).

+-----+-----+-------+--------------------------------------------------+
| Off | Wi  | Dire  | Description                                      |
| set | dth | ction |                                                  |
+=====+=====+=======+==================================================+
| ``  | 32- | W     | VLIW instruction [31:0] (write lower word first) |
| 0x0 | bit |       |                                                  |
| 0`` |     |       |                                                  |
+-----+-----+-------+--------------------------------------------------+
| ``  | 32- | W     | VLIW instruction [63:32] (writing this word      |
| 0x0 | bit |       | triggers NPU latch)                              |
| 4`` |     |       |                                                  |
+-----+-----+-------+--------------------------------------------------+
| ``  | 32- | R     | NPU status register (see §9)                     |
| 0x0 | bit |       |                                                  |
| 8`` |     |       |                                                  |
+-----+-----+-------+--------------------------------------------------+

--------------

9. Status Register (``0x08``)
-----------------------------

====== ======== ===============================================
Bit    Name     Description
====== ======== ===============================================
[0]    ``BUSY`` NPU is executing — do not issue new instruction
[1]    ``DONE`` Last operation completed successfully
[31:2] —        Reserved
====== ======== ===============================================
