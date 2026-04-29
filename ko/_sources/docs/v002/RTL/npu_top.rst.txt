:rtl_source: hw/rtl/NPU_top.sv

============================
NPU 최상위 모듈
============================

``NPU_top.sv``\ 는 최상위 통합 래퍼입니다. 외부 인터페이스:

- ``S_AXIL_CTRL`` — AXI-Lite 제어 (HPM 포트, 250 MHz)
- ``S_AXI_HP{0,1}_WEIGHT`` — GEMM 시스톨릭 어레이용 128비트 가중치 스트림
- ``S_AXI_HP{2,3}_WEIGHT`` — GEMV 코어용 128비트 가중치 스트림
- ``S_AXIS_ACP_FMAP`` / ``M_AXIS_ACP_RESULT`` — ACP 활성화 입력 및 결과 출력

4개 서브코어 (GEMM, GEMV, CVO, mem_dispatcher) 모두 여기서 인스턴스화되어
중앙 L2 캐시 버스로 연결됩니다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_top.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_top.sv

.. admonition:: 마지막 검증 대상
   :class: note

   커밋 ``773bd82`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260`` (2026-04-21).

.. seealso::

   :doc:`/docs/v002/Architecture/top_level` — 블록 다이어그램 및 설계 근거.
