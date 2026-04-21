:rtl_source: hw/rtl/NPU_Controller/npu_controller_top.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv,
             hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv,
             hw/rtl/NPU_Controller/Global_Scheduler.sv

============================
NPU 컨트롤러 모듈
============================

1. 컨트롤러 최상위
===================

``npu_controller_top.sv``\는 AXI-Lite 프론트엔드, 명령어 디코더,
디스패처, 글로벌 스케줄러를 하나의 단위로 통합한다.

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

3. 명령어 디스패처
===================

``ctrl_npu_dispatcher.sv``\는 Constant Cache 포인터 조회(shape/size/scale)를
수행하고, 주소 및 리소스 해저드를 검사하며, 각 코어(GEMM, GEMV, CVO,
mem_dispatcher)에 제어 μop을 발행한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv

4. 글로벌 스케줄러
===================

``Global_Scheduler.sv``\는 in-flight 비동기 명령어를 추적하고,
의존성 스코어보드를 유지하며, 해저드 감지 시 새 디스패치를 게이팅한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/Global_Scheduler.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/Global_Scheduler.sv

.. admonition:: 마지막 검증 대상
   :class: note

   커밋 ``773bd82`` @ ``hwkim-dev/pccx-FPGA-NPU-LLM-kv260`` (2026-04-21).

.. seealso:: :doc:`/docs/v002/ISA/dataflow` — 의존성·완료 추적.
