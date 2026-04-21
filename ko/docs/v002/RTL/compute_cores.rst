:rtl_source: hw/rtl/MAT_CORE/GEMM_systolic_top.sv,
             hw/rtl/VEC_CORE/GEMV_top.sv,
             hw/rtl/CVO_CORE/CVO_top.sv,
             hw/rtl/MAT_CORE/GEMM_dsp_unit.sv

============================
컴퓨트 코어 모듈
============================

1. 행렬 코어 — Systolic Top
=============================

``GEMM_systolic_top.sv``\ 는 32 × 32 시스톨릭 어레이 (cascade 가 16 행
에서 끊겨 32 × 16 서브체인 2 개로 나뉨) 를 감싸는 래퍼입니다. HP0/HP1
에서 가중치 타일을, L2 캐시에서 활성화 행을 수신하고 누산 결과를
후처리기 (post-processor) 로 스트리밍합니다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
   :language: systemverilog
   :caption: hw/rtl/MAT_CORE/GEMM_systolic_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/gemm_core`

2. 벡터 코어 — GEMV Top
=========================

``GEMV_top.sv``\ 는 4 개의 병렬 GEMV 코어를 인스턴스화합니다. 각 코어는
32-wide LUT 기반 MAC 과 5 단 reduction tree (Stage 1: DSP48E2 16 슬라이스,
Stage 2–5: LUT 가산기) 를 가지며, HP2/HP3 에서 가중치를 스트리밍합니다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/VEC_CORE/GEMV_top.sv
   :language: systemverilog
   :caption: hw/rtl/VEC_CORE/GEMV_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/gemv_core`

3. CVO / SFU 코어
==================

``CVO_top.sv``\ 는 비선형 연산(Softmax, GELU, RMSNorm, RoPE)을 위한
CORDIC + LUT 하이브리드 함수 유닛을 조율합니다.
모든 연산에서 정밀도는 BF16/FP32로 승격됩니다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/CVO_CORE/CVO_top.sv
   :language: systemverilog
   :caption: hw/rtl/CVO_CORE/CVO_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/sfu_core`

4. DSP48E2 MAC 유닛
====================

``GEMM_dsp_unit.sv``\ 는 단일 DSP48E2 슬라이스를 사용한 듀얼 채널 W4A8 MAC을
구현합니다. 비트 패킹 유도 과정은 :doc:`/docs/v002/Architecture/dsp48e2_w4a8`
를 참조하세요.

.. literalinclude:: ../../../../codes/v002/hw/rtl/MAT_CORE/GEMM_dsp_unit.sv
   :language: systemverilog
   :caption: hw/rtl/MAT_CORE/GEMM_dsp_unit.sv

.. admonition:: 마지막 검증 대상
   :class: note

   커밋 ``773bd82`` @ ``hwkim-dev/pccx-FPGA-NPU-LLM-kv260`` (2026-04-21).
