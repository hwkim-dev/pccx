==================
C API Overview
==================

This page documents the v002 driver's public C API. The implementation
lives under ``codes/v002/sw/driver/`` (``uCA_v1_api.h`` + ``uCA_v1_hal.h``).

The stack is organized into two layers.

1. **HAL** (``uca_hal_*``) — direct access to AXI-Lite / AXI-HP registers
   and the CMD_IN / STAT_OUT FIFOs. Applications should not call this
   layer directly.
2. **Public API** (``uca_*``) — "CUDA-equivalent" compute/memory
   primitives. Every call assembles a 64-bit VLIW instruction
   (:doc:`../ISA/encoding`) and issues it through the HAL.

.. note::

   The API is named ``uca_*`` (micro Compute Architecture), not
   ``pccx_*``. pccx is the architecture / documentation project; uCA is
   the RTL + software contract it exposes.

1. Initialization and Lifecycle
================================

.. code-block:: c

   #include "uCA_v1_api.h"

   // Bring the NPU up and verify the status register responds.
   // Returns 0 on success, -1 on failure.
   int  uca_init(void);

   // Park the NPU and release the HAL.
   void uca_deinit(void);

The API does **not** take a context pointer — a single process talks to
a single NPU instance, so the HAL keeps its state in a file-scope
singleton.

2. Compute Primitives
======================

Every compute call **returns immediately** after writing the instruction
into the CMD_IN FIFO. Use ``uca_sync`` (§5) to wait for completion.

2.1 Vector Core — ``uca_gemv``
-------------------------------

.. code-block:: c

   // y = W · x  (INT4 weight × BF16/INT8 activation → BF16 result)
   void uca_gemv(uint32_t dest_reg,   // 17-bit L2 destination
                 uint32_t src_addr,   // 17-bit L2 source (activation)
                 uint8_t  flags,      // OR of UCA_FLAG_* (see §4.1)
                 uint8_t  size_ptr,   // 6-bit size descriptor pointer
                 uint8_t  shape_ptr,  // 6-bit shape descriptor pointer
                 uint8_t  lanes);     // 5-bit parallel-lane mask (1–4)

2.2 Matrix Core — ``uca_gemm``
-------------------------------

.. code-block:: c

   // Y = W · X on the 32 × 32 systolic array.
   // Identical field layout to uca_gemv; differs only in the opcode
   // routed into the dispatcher.
   void uca_gemm(uint32_t dest_reg,
                 uint32_t src_addr,
                 uint8_t  flags,
                 uint8_t  size_ptr,
                 uint8_t  shape_ptr,
                 uint8_t  lanes);

2.3 CVO / SFU — ``uca_cvo``
----------------------------

.. code-block:: c

   // Complex vector operations:
   //   Softmax     (EXP, REDUCE_SUM, SCALE)
   //   RMSNorm     (SQRT, RECIP, SCALE)
   //   Activation  (GELU)
   //   RoPE        (SIN / COS)
   void uca_cvo(uint8_t  cvo_func,    // UCA_CVO_* (see §4.3)
                uint32_t src_addr,    // 17-bit L2 source
                uint32_t dst_addr,    // 17-bit L2 destination
                uint16_t length,      // element count
                uint8_t  flags,       // OR of UCA_CVO_FLAG_*
                uint8_t  async);      // 1 = fire-and-forget, 0 = block

3. Memory Primitives
=====================

3.1 ``uca_memcpy``
-------------------

.. code-block:: c

   // Route-encoded DMA. The route enum combines source and destination
   // (see §4.4). Typical use: load a weight tile from host DDR4 into
   // L2 before a GEMM/GEMV.
   void uca_memcpy(uint8_t  route,       // UCA_ROUTE_*
                   uint32_t dest_addr,   // 17-bit destination
                   uint32_t src_addr,    // 17-bit source
                   uint8_t  shape_ptr,   // 6-bit shape descriptor
                   uint8_t  async);

3.2 ``uca_memset``
-------------------

.. code-block:: c

   // Write a shape / size descriptor (up to three 16-bit values) into
   // one of the two descriptor caches.
   void uca_memset(uint8_t  dest_cache,  // 0 = fmap_shape, 1 = weight_shape
                   uint8_t  dest_addr,   // 6-bit pointer slot
                   uint16_t a,           // usually M
                   uint16_t b,           // usually N
                   uint16_t c);          // usually K

4. Constants
=============

The header exposes named constants for every ISA field so application
code never hard-codes bit patterns.

4.1 GEMV / GEMM flags (6-bit)
------------------------------

.. code-block:: c

   UCA_FLAG_FINDEMAX   // bit 5 — record e_max of the output (softmax)
   UCA_FLAG_ACCM       // bit 4 — accumulate into dest (do not overwrite)
   UCA_FLAG_W_SCALE    // bit 3 — apply the weight scale during MAC

4.2 CVO flags (5-bit)
----------------------

.. code-block:: c

   UCA_CVO_FLAG_SUB_EMAX     // bit 4 — subtract e_max before the op
   UCA_CVO_FLAG_RECIP_SCALE  // bit 3 — SCALE uses 1 / scalar
   UCA_CVO_FLAG_ACCM         // bit 2 — accumulate into dst

4.3 CVO function codes (4-bit)
-------------------------------

.. code-block:: c

   UCA_CVO_EXP          // 0x0  element-wise exp(x)            [SFU]
   UCA_CVO_SQRT         // 0x1  element-wise sqrt(x)           [SFU]
   UCA_CVO_GELU         // 0x2  element-wise GELU(x)           [SFU]
   UCA_CVO_SIN          // 0x3  element-wise sin(x)            [CORDIC]
   UCA_CVO_COS          // 0x4  element-wise cos(x)            [CORDIC]
   UCA_CVO_REDUCE_SUM   // 0x5  sum-reduction → scalar         [SFU + adder]
   UCA_CVO_SCALE        // 0x6  element-wise × scalar          [SFU]
   UCA_CVO_RECIP        // 0x7  element-wise 1/x               [SFU]

4.4 Memory routes (8-bit)
--------------------------

.. code-block:: c

   UCA_ROUTE_HOST_TO_L2       // 0x01  host DDR4 → L2
   UCA_ROUTE_L2_TO_HOST       // 0x10  L2 → host DDR4
   UCA_ROUTE_L2_TO_L1_GEMM    // 0x12  L2 → GEMM L1 (input stage)
   UCA_ROUTE_L2_TO_L1_GEMV    // 0x13  L2 → GEMV L1 (input stage)
   UCA_ROUTE_GEMM_RES_TO_L2   // 0x21  GEMM output → L2
   UCA_ROUTE_GEMV_RES_TO_L2   // 0x31  GEMV output → L2
   UCA_ROUTE_CVO_RES_TO_L2    // 0x41  SFU / CVO output → L2

5. Synchronization
===================

.. code-block:: c

   // Poll UCA_STAT_BUSY until every issued instruction retires.
   // Returns 0 when idle, -1 on timeout.
   int uca_sync(uint32_t timeout_us);

The pccx controller is fully decoupled — ``uca_init`` configures the
decoder once, after which every ``uca_*`` issue is independent. Call
``uca_sync`` before reading results back to host memory with
``uca_memcpy(UCA_ROUTE_L2_TO_HOST, …)``.

6. Example — One FFN Block
===========================

A minimal FFN ``y = W_down · GELU(W_up · x)`` looks like this:

.. code-block:: c

   // 0) Bring the NPU up
   if (uca_init() != 0) return -1;

   // 1) Preload shape descriptors.
   //    slot 0: W_up   (M, N, K) = (1, 4096, 4096)
   //    slot 1: W_down (M, N, K) = (1, 4096, 4096)
   uca_memset(/*cache*/ 1, /*slot*/ 0, 1, 4096, 4096);
   uca_memset(/*cache*/ 1, /*slot*/ 1, 1, 4096, 4096);

   // 2) W_up · x  → 0x0100 (GEMV)
   uca_gemv(/*dest*/ 0x0100, /*src*/ 0x0000,
            /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 0,
            /*lanes*/ 0x0F);                 // all four cores active

   // 3) GELU at 0x0100 → 0x0200
   uca_cvo(UCA_CVO_GELU,
           /*src*/ 0x0100, /*dst*/ 0x0200,
           /*length*/ 4096,
           /*flags*/ 0, /*async*/ 0);

   // 4) W_down · activation → 0x0300
   uca_gemv(/*dest*/ 0x0300, /*src*/ 0x0200,
            /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 1,
            /*lanes*/ 0x0F);

   // 5) Wait for completion
   uca_sync(/*timeout_us*/ 100000);

7. Error Handling
==================

``uca_init`` and ``uca_sync`` return ``0`` on success and ``-1`` on
failure. All other ``uca_*`` calls return ``void`` — they only push an
instruction into the CMD_IN FIFO, and failure modes surface through the
next ``uca_sync`` (which polls ``UCA_STAT_*``).

Typical failure surfaces:

* ``uca_init`` returns ``-1`` if the NPU STAT register does not read
  the expected boot pattern.
* ``uca_sync`` returns ``-1`` if the ``BUSY`` bit stays asserted past
  ``timeout_us``.
* Field overflows (e.g. address > 17 bits) are silently masked by the
  instruction encoder — keep application code within the documented
  widths.

.. seealso::

   - Instruction encoding: :doc:`../ISA/encoding`
   - Dataflow per opcode: :doc:`../ISA/dataflow`
   - RTL side of the ISA: :doc:`../RTL/isa_pkg`
