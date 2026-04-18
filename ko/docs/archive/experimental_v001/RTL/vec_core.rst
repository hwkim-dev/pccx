벡터 코어 (GEMV)
===================

4 개의 병렬 μV-core. 각 코어는 자기 L1 캐시 슬라이스에서 활성화를,
HP2/HP3 (포트당 32 INT4/clk) 에서 가중치를 읽습니다. 부분곱은 3 단
reduction tree 로, 이후 Emax 정렬 BF16 누산기로 들어갑니다. 단일
토큰 디코드 경로가 가중치 대역폭에 제한되는 자기회귀 디코딩에서
이 엔진이 주역입니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      μV-core 위치를 보여주는 v001 블록도.

모듈
-----

* ``GEMV_top.sv`` — μV-core 래퍼. 4 레인을 인스턴스화하고 가중치
  FIFO + L1 캐시 슬라이스에 연결.
* ``GEMV_generate_lut.sv`` — 레인별 LUT 로 INT4 가중치 디코드 / 부호
  확장.
* ``GEMV_Vec_Matrix_MUL.svh`` — multiply-reduce 단계용 매개변수 헤더.
* ``GEMV_reduction_branch.sv`` — reduction tree 의 한 가지 (부분곱 쌍
  합산).
* ``GEMV_reduction.sv`` — 4 가지를 스칼라로 합치는 최상위 reduction
  tree.
* ``GEMV_accumulate.sv`` — 최종 스칼라를 받는 Emax 정렬 BF16 누산기.

소스
-----

.. dropdown:: ``GEMV_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_top.sv
      :language: systemverilog

.. dropdown:: ``GEMV_generate_lut.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_generate_lut.sv
      :language: systemverilog

.. dropdown:: ``GEMV_Vec_Matrix_MUL.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_Vec_Matrix_MUL.svh
      :language: systemverilog

.. dropdown:: ``GEMV_reduction_branch.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_reduction_branch.sv
      :language: systemverilog

.. dropdown:: ``GEMV_reduction.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_reduction.sv
      :language: systemverilog

.. dropdown:: ``GEMV_accumulate.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/VEC_CORE/GEMV_accumulate.sv
      :language: systemverilog
