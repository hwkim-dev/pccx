Top level
==========

The topmost wrapper in the v001 RTL tree. ``NPU_top`` instantiates the
controller, all three compute cores, the memory hierarchy, and the
preprocess stage, then routes them through a shared AXI surface
(``S_AXIL_CTRL``, four HP master ports, one ACP master). The BF16
barrel shifter is a shared combinational utility invoked by the
normalizer and the SFU.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      Block diagram showing how these top-level signals connect.

Modules
-------

* ``NPU_top.sv`` — wires the full NPU together; exports AXI-Lite control
  + four HP + one ACP.
* ``barrel_shifter_BF16.sv`` — pure combinational BF16 left / right
  shifter. Used during accumulator → BF16 normalization and inside
  the SFU for Emax-aligned math.

Source
------

.. dropdown:: ``NPU_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/NPU_top.sv
      :language: systemverilog

.. dropdown:: ``barrel_shifter_BF16.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/barrel_shifter_BF16.sv
      :language: systemverilog
