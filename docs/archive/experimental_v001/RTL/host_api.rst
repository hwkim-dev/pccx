Host API (C driver)
=====================

The host-side C library that builds VLIW instructions and writes them
to the NPU's AXI-Lite control surface. Split into a thin HAL (MMIO
register accessors + IRQ-free ``wait_idle`` polling) and a public API
that mirrors the ISA 1:1.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/v001_API`
      Human-readable developer reference for the same API.

Public API
-----------

* ``uCA_v1_api.h`` — public function prototypes (``pccx_init``,
  ``pccx_gemv``, ``pccx_gemm``, ``pccx_cvo``, ``pccx_memcpy``,
  ``pccx_memset``, ``pccx_sync``).
* ``uCA_v1_api.c`` — implementation: per-opcode ``build_*_instr``
  helpers that pack arguments into 64-bit VLIWs and hand them to the
  HAL.

.. dropdown:: ``uCA_v1_api.h``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/sw/driver/uCA_v1_api.h
      :language: c

.. dropdown:: ``uCA_v1_api.c``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/sw/driver/uCA_v1_api.c
      :language: c

Hardware Abstraction Layer
---------------------------

* ``uCA_v1_hal.h`` — HAL prototypes: ``pccx_hal_init`` / ``deinit`` /
  ``issue_instr`` / ``wait_idle``.
* ``uCA_v1_hal.c`` — MMIO implementation: opens ``/dev/mem`` (or a
  device-tree handle), maps the AXI-Lite region, and writes VLIWs as
  paired 32-bit stores at ``0x00`` / ``0x04``.

.. dropdown:: ``uCA_v1_hal.h``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/sw/driver/uCA_v1_hal.h
      :language: c

.. dropdown:: ``uCA_v1_hal.c``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/sw/driver/uCA_v1_hal.c
      :language: c
