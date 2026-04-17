==========================
Per-Instruction Encoding
==========================

Every instruction consists of ``opcode[3:0]`` plus a 60-bit body. This
page details the body layout and field semantics for each opcode.

1. GEMV / GEMM (opcode = 0x0 / 0x1)
====================================

GEMV and GEMM share an identical body layout.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - Bits
     - Width
     - Field
     - Description
   * - [59:43]
     - 17
     - ``dest_reg``
     - L2 address where the result is written.
   * - [42:26]
     - 17
     - ``src_addr``
     - L2 address of the activation source.
   * - [25:20]
     - 6
     - ``flags``
     - See :ref:`gemm-flags`.
   * - [19:14]
     - 6
     - ``size_ptr_addr``
     - Constant Cache index for the size entry.
   * - [13:8]
     - 6
     - ``shape_ptr_addr``
     - Constant Cache index for the shape entry.
   * - [7:3]
     - 5
     - ``parallel_lane``
     - Number of core lanes to activate (0 = all).
   * - [2:0]
     - 3
     - reserved
     - Must be zero.

.. _gemm-flags:

1.1 Flags Field (6 bit)
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Bit
     - Name
     - Description
   * - [5]
     - ``findemax``
     - Update the e_max register for output normalization (used in
       softmax).
   * - [4]
     - ``accm``
     - Accumulate into ``dest`` (default is overwrite).
   * - [3]
     - ``w_scale``
     - Apply the weight scale factor during MAC.
   * - [2:0]
     - reserved
     - Must be zero.

2. MEMCPY (opcode = 0x2)
========================

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - Bits
     - Width
     - Field
     - Description
   * - [59]
     - 1
     - ``from_device``
     - 0 = NPU, 1 = Host.
   * - [58]
     - 1
     - ``to_device``
     - 0 = NPU, 1 = Host.
   * - [57:41]
     - 17
     - ``dest_addr``
     - Destination address.
   * - [40:24]
     - 17
     - ``src_addr``
     - Source address.
   * - [23:7]
     - 17
     - ``aux_addr``
     - Auxiliary address (e.g., a host DDR offset).
   * - [6:1]
     - 6
     - ``shape_ptr_addr``
     - Shape pointer for the transfer.
   * - [0]
     - 1
     - ``async``
     - 0 = wait for completion, 1 = fire-and-forget.

3. MEMSET (opcode = 0x3)
========================

Writes to the Constant Cache's shape / size / scale registers.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - Bits
     - Width
     - Field
     - Description
   * - [59:58]
     - 2
     - ``dest_cache``
     - 0 = fmap_shape, 1 = weight_shape.
   * - [57:52]
     - 6
     - ``dest_addr``
     - Constant Cache index.
   * - [51:36]
     - 16
     - ``a_value``
     - First 16-bit value.
   * - [35:20]
     - 16
     - ``b_value``
     - Second 16-bit value.
   * - [19:4]
     - 16
     - ``c_value``
     - Third 16-bit value.
   * - [3:0]
     - 4
     - reserved
     - Must be zero.

.. tip::

   The three slots (a / b / c) let a single MEMSET write an entire
   (M, N, K) tuple in one shot.

4. CVO (opcode = 0x4)
=====================

Complex Vector Operation — the instruction sent to the SFU.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - Bits
     - Width
     - Field
     - Description
   * - [59:56]
     - 4
     - ``cvo_func``
     - Function code (table below).
   * - [55:39]
     - 17
     - ``src_addr``
     - L2 address of the input vector.
   * - [38:22]
     - 17
     - ``dst_addr``
     - L2 address for the result.
   * - [21:6]
     - 16
     - ``length``
     - Number of elements to process.
   * - [5:1]
     - 5
     - ``flags``
     - See :ref:`cvo-flags`.
   * - [0]
     - 1
     - ``async``
     - 0 = synchronous, 1 = asynchronous.

4.1 CVO Function Codes
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Function
     - Code
     - Description
   * - ``CVO_EXP``
     - ``4'h0``
     - `exp(x)` — softmax.
   * - ``CVO_SQRT``
     - ``4'h1``
     - `sqrt(x)` — RMSNorm.
   * - ``CVO_GELU``
     - ``4'h2``
     - `gelu(x)` — FFN non-linearity.
   * - ``CVO_SIN``
     - ``4'h3``
     - `sin(x)` — RoPE.
   * - ``CVO_COS``
     - ``4'h4``
     - `cos(x)` — RoPE.
   * - ``CVO_REDUCE_SUM``
     - ``4'h5``
     - Sum of vector elements.
   * - ``CVO_SCALE``
     - ``4'h6``
     - Scalar × vector.
   * - ``CVO_RECIP``
     - ``4'h7``
     - `1/x`.
   * - ``4'h8`` – ``4'hF``
     - —
     - Reserved for future extensions.

.. _cvo-flags:

4.2 CVO Flags (5 bit)
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Bit
     - Name
     - Description
   * - [4]
     - ``sub_emax``
     - Subtract e_max before computing (softmax stabilization).
   * - [3]
     - ``recip_scale``
     - Use the reciprocal of the scalar (turns multiplication into
       division).
   * - [2]
     - ``accm``
     - Accumulate into ``dst``.
   * - [1:0]
     - reserved
     - Must be zero.

5. Summary
===========

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Opcode
     - Primary use case
   * - **GEMM**
     - Prefill. Q/K/V projection, FFN up / down projection.
   * - **GEMV**
     - Decoding. Every projection in the autoregressive step.
   * - **CVO**
     - Softmax, RMSNorm, RoPE, GELU.
   * - **MEMCPY**
     - Host ↔ device weight loads, KV cache updates, token output.
   * - **MEMSET**
     - Preset shape / size pointers at layer start, inject scale factors.
