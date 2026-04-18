Vector Core (GEMV)
====================

Four parallel μV-cores, each reading activations from its own L1 cache
slice and weights from HP2/HP3 (32 INT4/clk per port). Partial
products feed a three-stage reduction tree, then the Emax-aligned BF16
accumulator. This is the primary engine during autoregressive decoding
because the single-token decode path is weight-bandwidth bound.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      v001 block diagram locating the μV-cores.

Modules
--------

* ``GEMV_top.sv`` — μV-core wrapper; instantiates 4 lanes and wires
  them to the weight FIFO + L1 cache slice.
* ``GEMV_generate_lut.sv`` — generates the per-lane lookup for INT4
  weight decode / sign extension.
* ``GEMV_Vec_Matrix_MUL.svh`` — parameter header for the
  multiply-reduce stage.
* ``GEMV_reduction_branch.sv`` — one branch of the reduction tree
  (adds pairs of partial products).
* ``GEMV_reduction.sv`` — top-level reduction tree that combines the
  four branches into a scalar.
* ``GEMV_accumulate.sv`` — Emax-aligned BF16 accumulator for the final
  scalar.

Source
-------

.. dropdown:: ``GEMV_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_top.sv
      :language: systemverilog

.. dropdown:: ``GEMV_generate_lut.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_generate_lut.sv
      :language: systemverilog

.. dropdown:: ``GEMV_Vec_Matrix_MUL.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_Vec_Matrix_MUL.svh
      :language: systemverilog

.. dropdown:: ``GEMV_reduction_branch.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_reduction_branch.sv
      :language: systemverilog

.. dropdown:: ``GEMV_reduction.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_reduction.sv
      :language: systemverilog

.. dropdown:: ``GEMV_accumulate.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_accumulate.sv
      :language: systemverilog
