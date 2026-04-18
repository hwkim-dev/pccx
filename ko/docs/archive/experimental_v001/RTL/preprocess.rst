전처리
=======

전처리 스테이지는 ACP 로 호스트에서 들어오는 원시 BF16 피처맵을 받아
DSP48E2 MAC 이 이해하는 27 비트 고정소수점 표현으로 변환하고, 코어별
L1 캐시에 올립니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      최상위 다이어그램의 ``preprocess_fmap`` 박스.

모듈
-----

* ``preprocess_fmap.sv`` — 행렬·벡터 코어 양쪽에 공급하는 전처리
  최상위 래퍼.
* ``fmap_cache.sv`` — L1 피처맵 캐시. 소비자당 1 슬라이스.
* ``preprocess_bf16_fixed_pipeline.sv`` — BF16 → 27 비트 고정소수점
  변환 파이프라인 (Emax 정렬 포함).

소스
-----

.. dropdown:: ``preprocess_fmap.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/PREPROCESS/preprocess_fmap.sv
      :language: systemverilog

.. dropdown:: ``fmap_cache.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/PREPROCESS/fmap_cache.sv
      :language: systemverilog

.. dropdown:: ``preprocess_bf16_fixed_pipeline.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
      :language: systemverilog
