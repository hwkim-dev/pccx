CVO Core (SFU)
================

The Complex Vector Operation core handles every non-linear activation
the Transformer workload needs — Softmax, GELU, RMSNorm, RoPE — using
a pair of μCVO-cores. Each μCVO-core contains both a CORDIC unit
(rotation-based sin / cos) and an SFU (LUT + piecewise polynomial for
exp / sqrt / GELU / reciprocal).

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      ``OP_CVO`` encoding and function-code table (§3.4).

Modules
--------

* ``CVO_top.sv`` — top-level orchestrator. Accepts the decoded
  ``cvo_control_uop_t`` from the dispatcher, routes the request to the
  CORDIC or SFU unit based on ``cvo_func``, and handles ``sub_emax``
  and ``accm`` flags.
* ``CVO_cordic_unit.sv`` — CORDIC rotation pipeline for sin/cos and
  other trigonometric primitives needed by RoPE.
* ``CVO_sfu_unit.sv`` — LUT + polynomial engine for exp, sqrt, GELU,
  reciprocal, and reduction-sum.

Source
-------

.. dropdown:: ``CVO_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/CVO_CORE/CVO_top.sv
      :language: systemverilog

.. dropdown:: ``CVO_cordic_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/CVO_CORE/CVO_cordic_unit.sv
      :language: systemverilog

.. dropdown:: ``CVO_sfu_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/CVO_CORE/CVO_sfu_unit.sv
      :language: systemverilog
