:rtl_source: hw/rtl/MAT_CORE/GEMM_systolic_top.sv,
             hw/rtl/VEC_CORE/GEMV_top.sv,
             hw/rtl/CVO_CORE/CVO_top.sv,
             hw/rtl/MAT_CORE/GEMM_dsp_unit.sv

============================
Compute Core Modules
============================

1. Matrix Core — Systolic Top
==============================

``GEMM_systolic_top.sv`` wraps the 32 × 32 systolic array (cascade
split at row 16 into two 32 × 16 sub-chains). It receives weight tiles
from HP0/HP1 and activation rows from the L2 cache, and streams
accumulated results to the post-processor.

.. literalinclude:: ../../../codes/v002/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
   :language: systemverilog
   :caption: hw/rtl/MAT_CORE/GEMM_systolic_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/gemm_core`

2. Vector Core — GEMV Top
==========================

``GEMV_top.sv`` instantiates 4 parallel GEMV cores. Each core has a
32-wide LUT-based MAC and a 5-stage reduction tree (Stage 1 uses 16
DSP48E2 slices; Stages 2–5 are LUT adders). Weights stream from HP2/HP3.

.. literalinclude:: ../../../codes/v002/hw/rtl/VEC_CORE/GEMV_top.sv
   :language: systemverilog
   :caption: hw/rtl/VEC_CORE/GEMV_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/gemv_core`

3. CVO / SFU Core
==================

``CVO_top.sv`` orchestrates the CORDIC + LUT hybrid units for
non-linear operations: ``exp``, ``sqrt``, ``gelu``, ``sin``, ``cos``,
``reduce_sum``, ``scale``, ``recip``. Precision is promoted to BF16/FP32
for all computations.

.. literalinclude:: ../../../codes/v002/hw/rtl/CVO_CORE/CVO_top.sv
   :language: systemverilog
   :caption: hw/rtl/CVO_CORE/CVO_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/sfu_core`

4. DSP48E2 MAC Unit
====================

``GEMM_dsp_unit.sv`` implements the dual-channel W4A8 MAC using a single
DSP48E2 slice. See :doc:`/docs/v002/Architecture/dsp48e2_w4a8` for the
bit-packing derivation.

.. literalinclude:: ../../../codes/v002/hw/rtl/MAT_CORE/GEMM_dsp_unit.sv
   :language: systemverilog
   :caption: hw/rtl/MAT_CORE/GEMM_dsp_unit.sv

.. admonition:: Last verified against
   :class: note

   Commit ``773bd82`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260`` (2026-04-21).
