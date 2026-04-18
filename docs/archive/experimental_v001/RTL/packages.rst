Packages and Constants
=======================

Compile-order-ordered SystemVerilog packages and ``.svh`` headers that
establish the global type system, device-specific constants, pipeline
configuration, ISA layout, and SystemVerilog ``interface`` objects used
across the rest of the RTL.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      Human-readable ISA specification backing ``isa_pkg`` below.

Tier A — Raw constant headers (``.svh``)
-----------------------------------------

The ``Constants/compilePriority_Order/A_const_svh/`` directory — primitive
defines consumed by every downstream package.

* ``GLOBAL_CONST.svh`` — cross-cutting ``parameter`` set.
* ``NUMBERS.svh`` — numeric-format parameterization.
* ``DEVICE_INFO.svh`` — abstract device-family flags.
* ``kv260_device.svh`` — KV260-specific resource counts (DSP / BRAM / URAM).
* ``npu_arch.svh`` — top-level NPU architecture knobs (lane counts,
  systolic dimensions, FIFO depths).

.. dropdown:: ``GLOBAL_CONST.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/GLOBAL_CONST.svh
      :language: systemverilog

.. dropdown:: ``NUMBERS.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/NUMBERS.svh
      :language: systemverilog

.. dropdown:: ``DEVICE_INFO.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/DEVICE_INFO.svh
      :language: systemverilog

.. dropdown:: ``kv260_device.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/kv260_device.svh
      :language: systemverilog

.. dropdown:: ``npu_arch.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/npu_arch.svh
      :language: systemverilog

Tier B — Device package
------------------------

* ``device_pkg.sv`` — typed views of the Tier A defines suitable for
  `import device_pkg::*;`.

.. dropdown:: ``device_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
      :language: systemverilog

Tier C — Type packages
-----------------------

* ``dtype_pkg.sv`` — scalar data-type typedefs (BF16, INT48, flags).
* ``mem_pkg.sv`` — memory-interface types (addresses, ptr enums).

.. dropdown:: ``dtype_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/C_type_pkg/dtype_pkg.sv
      :language: systemverilog

.. dropdown:: ``mem_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/C_type_pkg/mem_pkg.sv
      :language: systemverilog

Tier D — Pipeline package
--------------------------

* ``vec_core_pkg.sv`` — GEMV pipeline stage counts / structs.

.. dropdown:: ``vec_core_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/D_pipeline_pkg/vec_core_pkg.sv
      :language: systemverilog

ISA package
------------

The authoritative definition of every opcode, micro-op, and instruction
layout. Imported at the top of every controller module.

.. dropdown:: ``isa_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
      :language: systemverilog

.. dropdown:: ``isa_memctrl.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_memctrl.svh
      :language: systemverilog

.. dropdown:: ``isa_x32.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x32.svh
      :language: systemverilog

.. dropdown:: ``isa_x64.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh
      :language: systemverilog

Interface definitions
----------------------

* ``npu_interfaces.svh`` — SystemVerilog ``interface`` blocks used as
  typed handles between blocks.

.. dropdown:: ``npu_interfaces.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_Controller/npu_interfaces.svh
      :language: systemverilog
