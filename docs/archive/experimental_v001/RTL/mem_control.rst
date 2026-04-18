Memory Control
================

All path-plumbing between the host DDR, the L2 URAM cache, the per-core
L1 caches, and the CVO stream ingest. A dedicated dispatcher arbitrates
the eight enumerated ``data_route_e`` routes (see the ISA §5) and the
two constant-memory arrays feed the Matrix / Vector cores with shape
and size descriptors.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      ``OP_MEMCPY`` / ``OP_MEMSET`` encodings and the routing enum.

Top-level plumbing
-------------------

* ``mem_dispatcher.sv`` — central arbiter: picks one of eight routes per
  cycle and drives the corresponding source / destination pair.
* ``mem_L2_cache_fmap.sv`` — L2 URAM cache dedicated to feature maps
  (114,688 × 128-bit).
* ``mem_HP_buffer.sv`` — double-buffered queue between the HP-AXI
  slaves and the compute-core weight FIFOs.
* ``mem_CVO_stream_bridge.sv`` — bridge from the L2 cache into the CVO
  core's streaming input.

.. dropdown:: ``mem_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/top/mem_dispatcher.sv
      :language: systemverilog

.. dropdown:: ``mem_L2_cache_fmap.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/top/mem_L2_cache_fmap.sv
      :language: systemverilog

.. dropdown:: ``mem_HP_buffer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/top/mem_HP_buffer.sv
      :language: systemverilog

.. dropdown:: ``mem_CVO_stream_bridge.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/top/mem_CVO_stream_bridge.sv
      :language: systemverilog

Memory modules
---------------

* ``mem_GLOBAL_cache.sv`` — parameterized global cache block used as
  the physical backing for the L2 URAM.
* ``mem_BUFFER.sv`` — generic ping-pong buffer used by the HP buffer
  and CVO bridge.

.. dropdown:: ``mem_GLOBAL_cache.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
      :language: systemverilog

.. dropdown:: ``mem_BUFFER.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/memory/mem_BUFFER.sv
      :language: systemverilog

Constant memory (shape / size)
-------------------------------

* ``fmap_array_shape.sv`` — small constant-memory array holding feature
  map shape descriptors referenced by ``shape_ptr_addr``.
* ``weight_array_shape.sv`` — same structure, for weight shapes.

.. dropdown:: ``fmap_array_shape.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/memory/Constant_Memory/fmap_array_shape.sv
      :language: systemverilog

.. dropdown:: ``weight_array_shape.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/memory/Constant_Memory/weight_array_shape.sv
      :language: systemverilog

IO
----

* ``mem_IO.svh`` — AXI / ACP pin-level types and parameters.
* ``mem_u_operation_queue.sv`` — micro-op queue between the controller
  and the memory dispatcher.

.. dropdown:: ``mem_IO.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/IO/mem_IO.svh
      :language: systemverilog

.. dropdown:: ``mem_u_operation_queue.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MEM_control/IO/mem_u_operation_queue.sv
      :language: systemverilog
