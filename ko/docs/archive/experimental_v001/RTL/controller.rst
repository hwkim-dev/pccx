NPU 컨트롤러
=============

컨트롤러는 NPU 의 **프론트엔드 + 스케줄러** 반쪽입니다. AXI-Lite 로
64 비트 VLIW 명령어를 받아 디코딩하고, 결과 마이크로 옵을 엔진별
FIFO 로 푸시하며, 상태 레지스터를 호스트에 노출합니다. 모든 컴퓨트
코어는 컨트롤러의 FIFO 뒤에서만 동작합니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      아래 디코더가 처리하는 명령어 레이아웃과 오피코드 표.

토폴로지
---------

::

   Host (AXI-Lite) ──► AXIL_CMD_IN ──► ctrl_npu_decoder ─┐
                                                        ▼
   ┌── GEMV FIFO ── GEMM FIFO ── CVO FIFO ── MEM FIFO ── MEMSET FIFO ──┐
   │                                                                    │
   │            ctrl_npu_dispatcher (엔진별 pop)                         │
   │                                                                    │
   └────────────► Global_Scheduler ◄────────────────────────────────────┘
                                                                        │
                                        NPU_fsm_out_Logic ──► AXIL_STAT_OUT

프론트엔드 (AXI-Lite 서피스)
------------------------------

* ``ctrl_npu_frontend.sv`` — AXIL 서피스 컨테이너. 인터페이스 슬레이브
  호스팅.
* ``AXIL_CMD_IN.sv`` — AXI-Lite 쓰기 슬레이브. ``0x00`` / ``0x04`` 에
  32 비트씩 쓰면 64 비트 명령어를 래치.
* ``AXIL_STAT_OUT.sv`` — ``0x08`` 에 BUSY/DONE 상태 레지스터를 노출하는
  AXI-Lite 읽기 슬레이브.
* ``ctrl_npu_interface.sv`` — 프론트엔드와 Control Unit 간 핸드셰이크
  내부 접착제.

.. dropdown:: ``ctrl_npu_frontend.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv
      :language: systemverilog

.. dropdown:: ``AXIL_CMD_IN.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv
      :language: systemverilog

.. dropdown:: ``AXIL_STAT_OUT.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv
      :language: systemverilog

.. dropdown:: ``ctrl_npu_interface.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_interface.sv
      :language: systemverilog

Control Unit (디코드 + 디스패치)
-----------------------------------

* ``ctrl_decode_const.svh`` — 디코드 단계 상수 (필드 폭, 마스크).
* ``ctrl_npu_decoder.sv`` — 64 비트 VLIW 에서 4 비트 오피코드를 떼고
  60 비트 본문을 해당 FIFO 로 라우팅.
* ``ctrl_npu_dispatcher.sv`` — 엔진별 로컬 디스패처. 큐잉된 마이크로
  옵을 꺼내 오퍼랜드 준비 시 엔진을 발사.

.. dropdown:: ``ctrl_decode_const.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_decode_const.svh
      :language: systemverilog

.. dropdown:: ``ctrl_npu_decoder.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_decoder.sv
      :language: systemverilog

.. dropdown:: ``ctrl_npu_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ctrl_npu_dispatcher.sv
      :language: systemverilog

Global Scheduler + 컨트롤러 최상위
-----------------------------------

* ``Global_Scheduler.sv`` — 엔진 간 중재. 메모리 전송과 연산 순서,
  ACC / FINDEMAX 해저드 처리.
* ``npu_controller_top.sv`` — 컨트롤러 최상위 래퍼. 프론트엔드 + 디코드/
  디스패치 + 스케줄러를 인스턴스화하고 ``npu_if`` 번들에 연결.

.. dropdown:: ``Global_Scheduler.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/Global_Scheduler.sv
      :language: systemverilog

.. dropdown:: ``npu_controller_top.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/npu_controller_top.sv
      :language: systemverilog

FSM Out Logic (상태 집계)
--------------------------

* ``fsmout_npu_stat_collector.sv`` — 엔진별 busy/done 플래그 샘플링.
* ``fsmout_npu_stat_encoder.sv`` — 수집된 플래그를 ``AXIL_STAT_OUT`` 가
  노출하는 32 비트 상태 레지스터로 인코딩.

.. dropdown:: ``fsmout_npu_stat_collector.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_fsm_out_Logic/fsmout_npu_stat_collector.sv
      :language: systemverilog

.. dropdown:: ``fsmout_npu_stat_encoder.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_fsm_out_Logic/fsmout_npu_stat_encoder.sv
      :language: systemverilog
