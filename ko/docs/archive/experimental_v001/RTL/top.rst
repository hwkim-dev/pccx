최상위
=======

v001 RTL 트리의 최상위 래퍼입니다. ``NPU_top`` 은 컨트롤러, 세 개의
컴퓨트 코어, 메모리 계층, 전처리 스테이지를 인스턴스화한 뒤 공유
AXI 서피스(``S_AXIL_CTRL``, 4 개의 HP master, 1 개의 ACP master) 로
라우팅합니다. BF16 barrel shifter 는 normalizer 와 SFU 가 공유하는
순수 조합회로 유틸리티입니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      이 최상위 신호들이 어떻게 연결되는지 보여주는 블록도.

모듈
----

* ``NPU_top.sv`` — NPU 전체를 엮어 AXI-Lite 제어 + 4 HP + 1 ACP 노출.
* ``barrel_shifter_BF16.sv`` — 순수 조합 BF16 좌·우 시프터. 누산기 →
  BF16 정규화와 SFU 의 Emax 정렬 수학에서 사용.

소스
----

.. dropdown:: ``NPU_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_top.sv
      :language: systemverilog

.. dropdown:: ``barrel_shifter_BF16.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/barrel_shifter_BF16.sv
      :language: systemverilog
