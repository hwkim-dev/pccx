:rtl_source: hw/rtl/NPU_Controller/npu_controller_top.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv,
             hw/rtl/NPU_Controller/Global_Scheduler.sv

============================
NPU 컨트롤러 모듈
============================

1. 컨트롤러 최상위
===================

``npu_controller_top.sv``\는 AXI-Lite 프론트엔드, 명령어 디코더,
글로벌 스케줄러를 단일 컨트롤러 경계로 통합한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/npu_controller_top.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/npu_controller_top.sv

2. 명령어 디코더
=================

``ctrl_npu_decoder.sv``\는 64비트 VLIW 명령어를 파싱한다: 4비트 오피코드를
분리하고 60비트 바디를 적절한 타입 구조체
(``GEMV_op_x64_t``, ``memcpy_op_x64_t`` 등)로 라우팅한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv

3. 글로벌 스케줄러
===================

``Global_Scheduler.sv``\는 디코더에서 전달된 명령어 필드를 받아 각 코어에
대한 제어 μop을 발행하고, in-flight 비동기 명령어를 추적하며, 의존성
스코어보드를 유지하고, 해저드 감지 시 새 디스패치를 게이팅한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/Global_Scheduler.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/Global_Scheduler.sv

.. admonition:: 마지막 검증 대상
   :class: note

   문서 CI가 사용하는 공개 ``pccx-FPGA-NPU-LLM-kv260`` ``main`` 클론을
   기준으로 한다. 컨트롤러 소스 참조는 해당 공개 RTL 트리에 존재하는
   파일과 일관성을 유지해야 한다.

.. seealso:: :doc:`/docs/v002/ISA/dataflow` — 의존성·완료 추적.
