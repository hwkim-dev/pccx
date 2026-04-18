Matrix Core (GEMM)
====================

A 32×32 systolic array of DSP48E2-backed MACs. The array receives
weight tiles over HP0 / HP1 (128 bit/clk) and activation rows from the
L2 cache, cycles through multiply-accumulate across both dimensions,
and hands a packed INT48 result vector to ``mat_result_normalizer``
for BF16 barrel-shift normalization before writeback.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      Where GEMM sits in the tri-core architecture.

Array shell
------------

* ``GEMM_systolic_top.sv`` — controller-visible wrapper: accepts
  dispatched ``gemm_control_uop_t``, asserts done.
* ``GEMM_systolic_array.sv`` — the 32×32 PE grid itself.
* ``GEMM_Array.svh`` — parameter header shared by the array and its
  surrounding feeders.

.. dropdown:: ``GEMM_systolic_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
      :language: systemverilog

.. dropdown:: ``GEMM_systolic_array.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_array.sv
      :language: systemverilog

.. dropdown:: ``GEMM_Array.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_Array.svh
      :language: systemverilog

DSP MAC units
--------------

* ``GEMM_dsp_unit.sv`` — a single-row PE: a DSP48E2 MAC with its
  feedback P-register.
* ``GEMM_dsp_unit_last_ROW.sv`` — bottom-row variant that terminates
  the accumulator chain and exports the partial sum.

.. dropdown:: ``GEMM_dsp_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_dsp_unit.sv
      :language: systemverilog

.. dropdown:: ``GEMM_dsp_unit_last_ROW.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_dsp_unit_last_ROW.sv
      :language: systemverilog

Feeders
--------

* ``GEMM_weight_dispatcher.sv`` — slices the HP0/HP1 stream into
  per-column weight tiles.
* ``GEMM_fmap_staggered_delay.sv`` — clocked shift register bank
  that staggers activation rows for triangular injection into the array.
* ``GEMM_accumulator.sv`` — partial-sum accumulator that rides behind
  the DSP P-register chain during multi-tile runs.

.. dropdown:: ``GEMM_weight_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_weight_dispatcher.sv
      :language: systemverilog

.. dropdown:: ``GEMM_fmap_staggered_delay.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_fmap_staggered_delay.sv
      :language: systemverilog

.. dropdown:: ``GEMM_accumulator.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_accumulator.sv
      :language: systemverilog

Result path
------------

* ``FROM_mat_result_packer.sv`` — packs a row of INT48 accumulators
  into an AXI beat.
* ``mat_result_normalizer.sv`` — barrel-shifts the packed INT48 vector
  down to BF16, applying Emax alignment.

.. dropdown:: ``FROM_mat_result_packer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/FROM_mat_result_packer.sv
      :language: systemverilog

.. dropdown:: ``mat_result_normalizer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/MAT_CORE/mat_result_normalizer.sv
      :language: systemverilog
