:rtl_source: hw/rtl/NPU_top.sv

============================
NPU Top-Level
============================

``NPU_top.sv`` is the top integration wrapper. It exposes:

- ``S_AXIL_CTRL`` — AXI-Lite control (HPM port, 250 MHz)
- ``S_AXI_HP{0,1}_WEIGHT`` — 128-bit weight streams for the GEMM systolic array
- ``S_AXI_HP{2,3}_WEIGHT`` — 128-bit weight streams for the GEMV core
- ``S_AXIS_ACP_FMAP`` / ``M_AXIS_ACP_RESULT`` — ACP feature-map input and result output

All four sub-cores (GEMM, GEMV, CVO, mem_dispatcher) are instantiated
here and connected through the shared L2 cache bus.

.. literalinclude:: ../../../codes/v002/hw/rtl/NPU_top.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_top.sv

.. seealso::

   :doc:`/docs/v002/Architecture/top_level` — block diagram and design rationale.
