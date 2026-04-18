CVO 코어 (SFU)
=================

Complex Vector Operation 코어는 Transformer 가 요구하는 모든 비선형
활성화 — Softmax, GELU, RMSNorm, RoPE — 를 2 개의 μCVO-core 로
처리합니다. 각 μCVO-core 는 CORDIC 유닛 (회전 기반 sin/cos) 과
SFU (exp / sqrt / GELU / 역수용 LUT + 조각 다항식) 를 동시에 가집니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      ``OP_CVO`` 인코딩과 함수 코드 테이블 (§3.4).

모듈
-----

* ``CVO_top.sv`` — 최상위 오케스트레이터. 디스패처가 보낸
  ``cvo_control_uop_t`` 를 받아 ``cvo_func`` 에 따라 CORDIC 이나 SFU
  유닛으로 라우팅하고, ``sub_emax`` 와 ``accm`` 플래그를 처리.
* ``CVO_cordic_unit.sv`` — RoPE 가 필요로 하는 삼각함수 primitive 와
  sin/cos 를 위한 CORDIC 회전 파이프라인.
* ``CVO_sfu_unit.sv`` — exp, sqrt, GELU, 역수, reduce-sum 을 위한
  LUT + 다항식 엔진.

소스
-----

.. dropdown:: ``CVO_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/CVO_CORE/CVO_top.sv
      :language: systemverilog

.. dropdown:: ``CVO_cordic_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/CVO_CORE/CVO_cordic_unit.sv
      :language: systemverilog

.. dropdown:: ``CVO_sfu_unit.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/CVO_CORE/CVO_sfu_unit.sv
      :language: systemverilog
