행렬 코어 (GEMM)
===================

DSP48E2 기반 MAC 으로 구성된 32×32 시스톨릭 어레이입니다. HP0/HP1
(128 비트/clk) 으로 가중치 타일을, L2 캐시에서 활성화 행을 받아
양 방향으로 multiply-accumulate 를 순환시키고, 패킹된 INT48 결과
벡터를 ``mat_result_normalizer`` 에 넘겨 writeback 전에 BF16 barrel
shift 로 정규화합니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      GEMM 이 3 코어 아키텍처 내 어디 위치하는지.

어레이 쉘
----------

* ``GEMM_systolic_top.sv`` — 컨트롤러가 보는 래퍼. 디스패치된
  ``gemm_control_uop_t`` 수신 후 done 어서트.
* ``GEMM_systolic_array.sv`` — 32×32 PE 격자 본체.
* ``GEMM_Array.svh`` — 어레이와 주변 feeder 가 공유하는 매개변수 헤더.

.. dropdown:: ``GEMM_systolic_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_top.sv
      :language: systemverilog

.. dropdown:: ``GEMM_systolic_array.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_systolic_array.sv
      :language: systemverilog

.. dropdown:: ``GEMM_Array.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_Array.svh
      :language: systemverilog

DSP MAC 유닛
--------------

* ``GEMM_dsp_unit.sv`` — 단일 row PE. 피드백 P-레지스터를 가진
  DSP48E2 MAC.
* ``GEMM_dsp_unit_last_ROW.sv`` — 누산기 체인을 종결하고 partial sum
  을 내보내는 최하단 row 변형.

.. dropdown:: ``GEMM_dsp_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_dsp_unit.sv
      :language: systemverilog

.. dropdown:: ``GEMM_dsp_unit_last_ROW.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_dsp_unit_last_ROW.sv
      :language: systemverilog

공급단
-------

* ``GEMM_weight_dispatcher.sv`` — HP0/HP1 스트림을 column 별 가중치
  타일로 분해.
* ``GEMM_fmap_staggered_delay.sv`` — 활성화 행을 어레이에 삼각형
  주입하도록 단계 지연시키는 shift register bank.
* ``GEMM_accumulator.sv`` — 다중 타일 동안 DSP P-레지스터 체인 뒤로
  따라가는 partial sum 누산기.

.. dropdown:: ``GEMM_weight_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_weight_dispatcher.sv
      :language: systemverilog

.. dropdown:: ``GEMM_fmap_staggered_delay.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_fmap_staggered_delay.sv
      :language: systemverilog

.. dropdown:: ``GEMM_accumulator.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/GEMM_accumulator.sv
      :language: systemverilog

결과 경로
----------

* ``FROM_mat_result_packer.sv`` — INT48 누산기 row 를 AXI beat 로 패킹.
* ``mat_result_normalizer.sv`` — 패킹된 INT48 벡터를 Emax 정렬과 함께
  BF16 으로 barrel shift 다운.

.. dropdown:: ``FROM_mat_result_packer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/FROM_mat_result_packer.sv
      :language: systemverilog

.. dropdown:: ``mat_result_normalizer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MAT_CORE/mat_result_normalizer.sv
      :language: systemverilog
