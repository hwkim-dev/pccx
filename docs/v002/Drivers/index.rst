==================
Software Stack
==================

The pccx v002 driver is a C/C++ hardware abstraction layer (HAL).
Responsibilities include:

- 64-bit instruction encoding and dispatch
- Preloading pointers and scale factors via MEMSET
- Managing DMA between the host and the L2 cache
- Polling or interrupt handling for async completion

.. toctree::
   :maxdepth: 1

   api

.. note::

   The v002 driver API is still in the design stage. The reference
   implementation draws from v001's
   :file:`docs/archive/experimental_v001/Drivers/uCA_v1_api.h` and
   :file:`uCA_v1_api.c`.
