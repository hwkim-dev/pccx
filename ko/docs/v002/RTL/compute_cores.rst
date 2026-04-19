:rtl_source: hw/rtl/MAT_CORE/GEMM_systolic_top.sv,
             hw/rtl/VEC_CORE/GEMV_top.sv,
             hw/rtl/CVO_CORE/CVO_top.sv,
             hw/rtl/MAT_CORE/GEMM_dsp_unit.sv

============================
컴퓨트 코어 모듈
============================

1. 행렬 코어 — Systolic Top
=============================

``GEMM_systolic_top.sv``\ 는 32 × 16 × 2 시스톨릭 어레이를 감싸는 래퍼입니다.
HP0/HP1에서 가중치 타일을, L2 캐시에서 활성화 행을 수신하고
누산 결과를 후처리기(post-processor)로 스트리밍합니다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
   :language: systemverilog
   :caption: hw/rtl/MAT_CORE/GEMM_systolic_top.sv

.. seealso:: :doc:`/docs/v002/Architecture/gemm_core`

2. 벡터 코어 — GEMV Top
=========================

``GEMV_top.sv``\ 는 4개의 병렬 GEMV 레인을 인스턴스화합니다. 각 레인은
8-lane MAC 파이프라인과 3단계 reduction tree를 가지며, HP2/HP3에서
가중치를 스트리밍합니다.

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
