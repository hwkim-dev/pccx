Developer Reference for uCA v001 Host API
=========================================

   [!NOTE] This document covers the High-Level C API used by the host
   application to control the NPU. It is designed for the v001 NPU
   architecture and directly wraps the Hardware Abstraction Layer (HAL).

API Architecture Overview
-------------------------

The current API layer pursues an experience similar to CUDA. Developers
can utilize the asynchronous hardware accelerator by simply making
``uca_*`` C function calls without needing to understand the 64-bit VLIW
instruction assembly.

-  **Non-blocking (Asynchronous)**: All computation functions simply
   queue the instructions into the NPU FIFO via the HAL and return
   immediately.
-  **Sync Point**: The host execution flow stops and synchronizes with
   the hardware state only when the ``uca_sync()`` function is
   explicitly called.

--------------

API Reference
-------------

1. Initialization and Shutdown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These fundamental functions initialize the NPU device handles and
release the resources. They ensure the NPU is responsive before
proceeding.

=== “Header (uCA_v1_api.h)”

::

   ```c
   int  uca_init(void);

   void uca_deinit(void);
   ```

=== “Implementation (uCA_v1_api.c)”

::

   ```c
   int uca_init(void) {
       return uca_hal_init();
   }

   void uca_deinit(void) {
       uca_hal_deinit();
   }
   ```

2. Matrix Core and Vector Core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Executes Vector Core (GEMV) and Matrix Core (GEMM) operations. When the
Host passes arguments using C types, the API internally builds them into
a 64-bit VLIW format and pushes it to the hardware FIFO.

**Parameters:** - ``dest_reg`` : Destination register or L2 memory
address (17-bit). - ``src_addr`` : Starting location of the Source
Feature Map buffer (17-bit). - ``flags`` : Configuration flags
(``UCA_FLAG_FINDEMAX``, ``UCA_FLAG_ACCM``, etc). - ``size_ptr`` :
Pointer to the size descriptor inside the shape cache (6-bit). -
``shape_ptr`` : Pointer to the shape descriptor inside the shape cache
(6-bit). - ``lanes`` : The number of parallel μV-Core lanes to utilize
(1 to 4).

=== “Header (uCA_v1_api.h)”

::

   ```c
   void uca_gemv(uint32_t dest_reg,   uint32_t src_addr,
                 uint8_t  flags,      uint8_t  size_ptr,
                 uint8_t  shape_ptr,  uint8_t  lanes);

   void uca_gemm(uint32_t dest_reg,   uint32_t src_addr,
                 uint8_t  flags,      uint8_t  size_ptr,
                 uint8_t  shape_ptr,  uint8_t  lanes);
   ```

=== “Implementation (uCA_v1_api.c)”

::

   ```c
   static uint64_t build_compute_instr(...) {
       uint64_t instr = 0;
       instr |= ((uint64_t)(opcode    & 0xF)     << 60);
       instr |= ((uint64_t)(dest_reg  & 0x1FFFF) << 43);
       instr |= ((uint64_t)(src_addr  & 0x1FFFF) << 26);
       instr |= ((uint64_t)(flags     & 0x3F)    << 20);
       instr |= ((uint64_t)(size_ptr  & 0x3F)    << 14);
       instr |= ((uint64_t)(shape_ptr & 0x3F)    <<  8);
       instr |= ((uint64_t)(lanes     & 0x1F)    <<  3);
       return instr;
   }

   void uca_gemv(...) {
       uint64_t instr = build_compute_instr(UCA_OP_GEMV, dest_reg, src_addr, flags, size_ptr, shape_ptr, lanes);
       uca_hal_issue_instr(instr);
   }
   ```

3. CVO (Complex Vector Operations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Controls the non-linear math functions (SFU and CORDIC) utilized for
attention weight scaling such as Softmax, RMSNorm, GELU, and RoPE.

**Parameters:** - ``cvo_func`` : The function code constant, such as
``UCA_CVO_EXP``, ``UCA_CVO_SQRT``. - ``src_addr`` : Source cache
address. - ``dst_addr`` : Destination cache address. - ``length`` : The
number of vector operations to process sequentially.

=== “Header (uCA_v1_api.h)”

::

   ```c
   void uca_cvo(uint8_t  cvo_func,  uint32_t src_addr,
                uint32_t dst_addr,  uint16_t length,
                uint8_t  flags,     uint8_t  async);
   ```

=== “Implementation (uCA_v1_api.c)”

::

   ```c
   static uint64_t build_cvo_instr(...) {
       uint64_t instr = 0;
       instr |= ((uint64_t)(UCA_OP_CVO & 0xF)   << 60);
       instr |= ((uint64_t)(cvo_func  & 0xF)    << 56);
       instr |= ((uint64_t)(src_addr  & 0x1FFFF)<< 39);
       instr |= ((uint64_t)(dst_addr  & 0x1FFFF)<< 22);
       instr |= ((uint64_t)(length    & 0xFFFF) <<  6);
       instr |= ((uint64_t)(flags     & 0x1F)   <<  1);
       instr |= ((uint64_t)(async     & 0x1)    <<  0);
       return instr;
   }

   void uca_cvo(...) {
       uint64_t instr = build_cvo_instr(cvo_func, src_addr, dst_addr, length, flags, async);
       uca_hal_issue_instr(instr);
   }
   ```

4. Memory Control (DMA Transfers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pipelines the data routing and bus transfers between the Host DDR, NPU
L2 Cache, and L1 engine local caches.

**DMA Transfer Parameters:** - ``route`` : The routing bus constant
identifying flow source and destination. - ``dest_addr`` : Transfer
target local address. - ``src_addr`` : Source buffer address.

=== “Header (uCA_v1_api.h)”

::

   ```c
   void uca_memcpy(uint8_t route, uint32_t dest_addr, uint32_t src_addr, uint8_t shape_ptr, uint8_t async);

   void uca_memset(uint8_t dest_cache, uint8_t dest_addr, uint16_t a, uint16_t b, uint16_t c);
   ```

=== “Implementation (uCA_v1_api.c)”

::

   ```c
   void uca_memcpy(...) {
       uint8_t from_dev = (route >> 4) & 0xF;
       uint8_t to_dev   = (route >> 0) & 0xF;

       uint64_t instr = 0;
       instr |= ((uint64_t)(UCA_OP_MEMCPY & 0xF) << 60);
       instr |= ((uint64_t)(from_dev  & 0x1)      << 59);
       instr |= ((uint64_t)(to_dev    & 0x1)      << 58);
       instr |= ((uint64_t)(dest_addr & 0x1FFFF)  << 41);
       instr |= ((uint64_t)(src_addr  & 0x1FFFF)  << 24);
       instr |= ((uint64_t)(shape_ptr & 0x3F)     <<  1);
       instr |= ((uint64_t)(async     & 0x1)      <<  0);
       uca_hal_issue_instr(instr);
   }
   ```

5. Synchronization
~~~~~~~~~~~~~~~~~~

Wait using a blocking behavior until all asynchronous NPU pipelines
registered in the FIFO queue have completed their tasks.

**Parameters:** - ``timeout_us`` : Threshold timeout in microseconds
before returning an error state.

=== “Header (uCA_v1_api.h)”

::

   ```c
   int uca_sync(uint32_t timeout_us);
   ```

=== “Implementation (uCA_v1_api.c)”

::

   ```c
   int uca_sync(uint32_t timeout_us) {
       return uca_hal_wait_idle(timeout_us);
   }
   ```
