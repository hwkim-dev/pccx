:rtl_source: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv

============================
ISA Type Package
============================

``isa_pkg.sv`` is the single source of truth for all instruction types,
opcode enums, and micro-op structs. Every RTL module does
``import isa_pkg::*;`` — no header includes are needed downstream.

The package is organized in compilation order:

1. Basic address and control typedefs
2. Device-direction enums (``from_device_e``, ``to_device_e``, ``async_e``)
3. GEMV/GEMM flags struct
4. Opcode enum (``opcode_e``)
5. Per-instruction encoding structs (60-bit bodies)
6. CVO function codes and flags
7. Memory routing enums (``data_route_e``)
8. Micro-op structs decoded from each instruction

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv

Encoding-table headers
----------------------

Three companion ``.svh`` files sit next to ``isa_pkg.sv`` and define
the bit-layout tables the host driver mirrors:

- ``isa_x32.svh`` — 32-bit field layouts (legacy + control-plane opcodes).
- ``isa_x64.svh`` — 64-bit VLIW field layouts (the active opcode set).
- ``isa_memctrl.svh`` — memory-controller opcode bodies (MEMSET / LOAD /
  STORE / CVO).

The host C driver's ``uCA_v1_api.h`` claims its bit layout matches
``isa_x64.svh`` opcode-by-opcode; whenever a field width changes the
SV header and the driver header must move together.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh

.. admonition:: Last verified against
   :class: note

   Commit ``8c09e5e`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260`` (2026-04-29).

.. seealso::

   :doc:`/docs/v002/ISA/encoding` — human-readable description of the same encoding.
   :doc:`/docs/v002/ISA/instructions` — per-instruction field tables.
