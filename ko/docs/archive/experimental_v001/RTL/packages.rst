패키지와 상수
===============

컴파일 우선순위로 정렬된 SystemVerilog 패키지와 ``.svh`` 헤더들.
전체 RTL 이 사용하는 글로벌 타입 시스템, 디바이스 상수, 파이프라인
설정, ISA 레이아웃, SystemVerilog ``interface`` 객체를 정의합니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      아래 ``isa_pkg`` 를 뒷받침하는 ISA 사양.

Tier A — 원시 상수 헤더 (``.svh``)
-----------------------------------

``Constants/compilePriority_Order/A_const_svh/`` — 모든 하위 패키지가
소비하는 기본 ``define`` 모음.

* ``GLOBAL_CONST.svh`` — 교차 공통 ``parameter``.
* ``NUMBERS.svh`` — 숫자 포맷 매개변수화.
* ``DEVICE_INFO.svh`` — 디바이스 패밀리 플래그 추상화.
* ``kv260_device.svh`` — KV260 전용 리소스 카운트 (DSP/BRAM/URAM).
* ``npu_arch.svh`` — NPU 아키텍처 상위 knob (레인 수, 시스톨릭 치수,
  FIFO 깊이).

.. dropdown:: ``GLOBAL_CONST.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/GLOBAL_CONST.svh
      :language: systemverilog

.. dropdown:: ``NUMBERS.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/NUMBERS.svh
      :language: systemverilog

.. dropdown:: ``DEVICE_INFO.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/DEVICE_INFO.svh
      :language: systemverilog

.. dropdown:: ``kv260_device.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/kv260_device.svh
      :language: systemverilog

.. dropdown:: ``npu_arch.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/A_const_svh/npu_arch.svh
      :language: systemverilog

Tier B — 디바이스 패키지
--------------------------

* ``device_pkg.sv`` — Tier A define 을 ``import device_pkg::*;`` 로
  쓸 수 있는 타입 뷰로 감쌈.

.. dropdown:: ``device_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
      :language: systemverilog

Tier C — 타입 패키지
----------------------

* ``dtype_pkg.sv`` — 스칼라 데이터 타입 (BF16, INT48, flags) typedef.
* ``mem_pkg.sv`` — 메모리 인터페이스 타입 (주소, 포인터 enum).

.. dropdown:: ``dtype_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/C_type_pkg/dtype_pkg.sv
      :language: systemverilog

.. dropdown:: ``mem_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/C_type_pkg/mem_pkg.sv
      :language: systemverilog

Tier D — 파이프라인 패키지
----------------------------

* ``vec_core_pkg.sv`` — GEMV 파이프라인 stage count 와 struct.

.. dropdown:: ``vec_core_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Constants/compilePriority_Order/D_pipeline_pkg/vec_core_pkg.sv
      :language: systemverilog

ISA 패키지
-----------

모든 오피코드 · 마이크로 옵 · 명령어 레이아웃의 권위 있는 정의.
모든 컨트롤러 모듈 상단에서 import 합니다.

.. dropdown:: ``isa_pkg.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
      :language: systemverilog

.. dropdown:: ``isa_memctrl.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_memctrl.svh
      :language: systemverilog

.. dropdown:: ``isa_x32.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x32.svh
      :language: systemverilog

.. dropdown:: ``isa_x64.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh
      :language: systemverilog

인터페이스 정의
-----------------

* ``npu_interfaces.svh`` — 블록 간 typed handle 로 쓰이는 SystemVerilog
  ``interface`` 블록들.

.. dropdown:: ``npu_interfaces.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/NPU_Controller/npu_interfaces.svh
      :language: systemverilog
