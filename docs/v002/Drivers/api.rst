==================
C API Overview
==================

This page sketches the design of the v002 driver's C API. The API is
organized into three layers.

1. **Low-level HAL** — direct access to AXI-Lite / AXI-HP registers.
2. **ISA Encoder** — helpers that assemble 64-bit instructions.
3. **High-level Ops** — convenience wrappers around GEMM / GEMV / CVO /
   MEMCPY.

1. Initialization and Lifecycle
================================

.. code-block:: c

   typedef struct pccx_ctx pccx_ctx_t;

   // Open the device
   int  pccx_open(pccx_ctx_t **ctx, const char *device_path);

   // Close the device
   void pccx_close(pccx_ctx_t *ctx);

   // Reset the hardware registers
   int  pccx_reset(pccx_ctx_t *ctx);

2. Instruction Encoding
========================

One encoder helper per opcode.

.. code-block:: c

   // GEMM / GEMV
   uint64_t pccx_encode_gemm(
       uint32_t dest_reg,
       uint32_t src_addr,
       uint8_t  flags,
       uint8_t  size_ptr,
       uint8_t  shape_ptr,
       uint8_t  parallel_lane);

   uint64_t pccx_encode_gemv( /* same signature */ );

   // MEMCPY
   uint64_t pccx_encode_memcpy(
       bool     from_host,
       bool     to_host,
       uint32_t dest_addr,
       uint32_t src_addr,
       uint32_t aux_addr,
       uint8_t  shape_ptr,
       bool     async);

   // MEMSET
   uint64_t pccx_encode_memset(
       uint8_t  dest_cache,
       uint8_t  dest_addr,
       uint16_t a,
       uint16_t b,
       uint16_t c);

   // CVO
   uint64_t pccx_encode_cvo(
       uint8_t  func,       // CVO_EXP, CVO_GELU, ...
       uint32_t src_addr,
       uint32_t dst_addr,
       uint16_t length,
       uint8_t  flags,
       bool     async);

3. Dispatch and Synchronization
================================

.. code-block:: c

   // Push a single instruction into the CMD_IN FIFO
   int pccx_dispatch(pccx_ctx_t *ctx, uint64_t instr);

   // Batch dispatch
   int pccx_dispatch_batch(pccx_ctx_t *ctx,
                           const uint64_t *instrs,
                           size_t n);

   // Wait for all async instructions to complete (polling)
   int pccx_wait_idle(pccx_ctx_t *ctx, uint32_t timeout_ms);

   // Read the STAT_OUT register
   uint32_t pccx_read_status(pccx_ctx_t *ctx);

4. High-Level Helpers
======================

Common sequences — such as presetting shape / size at the start of a
layer — are wrapped as helpers.

.. code-block:: c

   // Preset a shape entry in the Constant Cache
   int pccx_set_shape(pccx_ctx_t *ctx,
                      uint8_t idx,
                      uint16_t M, uint16_t N, uint16_t K);

   // Host → L2 weight load
   int pccx_load_weights(pccx_ctx_t *ctx,
                         uint32_t l2_dest_addr,
                         const void *host_src,
                         size_t nbytes);

   // L2 → Host result fetch
   int pccx_fetch_result(pccx_ctx_t *ctx,
                         void *host_dest,
                         uint32_t l2_src_addr,
                         size_t nbytes);

5. Example: a Transformer FFN Block
====================================

A minimal FFN (``y = W_down · GELU(W_up · x)``) looks like this:

.. code-block:: c

   // 1) Preset shapes
   pccx_set_shape(ctx, /*idx*/ 0, M=1, N=4096, K=4096);   // W_up
   pccx_set_shape(ctx, /*idx*/ 1, M=1, N=4096, K=4096);   // W_down

   // 2) W_up · x  (GEMV)
   uint64_t i0 = pccx_encode_gemv(
       /*dest*/  0x0100, /*src*/ 0x0000,
       /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 0,
       /*lane*/  0);
   pccx_dispatch(ctx, i0);

   // 3) GELU
   uint64_t i1 = pccx_encode_cvo(
       CVO_GELU,
       /*src*/  0x0100, /*dst*/ 0x0200,
       /*len*/  4096, /*flags*/ 0, /*async*/ false);
   pccx_dispatch(ctx, i1);

   // 4) W_down · activation (GEMV)
   uint64_t i2 = pccx_encode_gemv(
       /*dest*/  0x0300, /*src*/ 0x0200,
       /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 1,
       /*lane*/  0);
   pccx_dispatch(ctx, i2);

   pccx_wait_idle(ctx, /*timeout_ms*/ 100);

6. Error Handling
==================

Every driver function returns ``0`` on success or a negative
errno-compatible code on failure.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Error
     - Meaning
   * - ``-EBUSY``
     - CMD_IN FIFO is full.
   * - ``-ETIMEDOUT``
     - ``pccx_wait_idle`` timed out.
   * - ``-EINVAL``
     - Encode failed (for example, a field overflowed).
   * - ``-EIO``
     - AXI transaction failed.

.. note::

   The driver implementation will eventually live under
   ``codes/v002/sw/``. The current docs describe the API contract
   up-front.
