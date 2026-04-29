:rtl_source: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv

============================
ISA 타입 패키지
============================

``isa_pkg.sv``\ 는 모든 명령어 인코딩, 오피코드 열거형, 마이크로 옵(μop) 구조체의
단일 진실 원천(Single Source of Truth)입니다. 모든 RTL 모듈은
``import isa_pkg::*;``\ 로 이 패키지를 가져오며, 별도의 헤더 include가 필요없습니다.

패키지 구성 순서:

1. 기본 주소·제어 타입 (``dest_addr_t``, ``src_addr_t`` 등)
2. 디바이스 방향 열거형 (``from_device_e``, ``to_device_e``, ``async_e``)
3. GEMV/GEMM 플래그 구조체
4. 오피코드 열거형 (``opcode_e``)
5. 명령어별 인코딩 구조체 (60비트 바디)
6. CVO 함수 코드·플래그
7. 메모리 라우팅 열거형 (``data_route_e``)
8. 각 명령어에서 디코딩되는 마이크로 옵 구조체

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv

인코딩 테이블 헤더
------------------

``isa_pkg.sv`` 옆에 동반하는 세 개의 ``.svh`` 헤더가 호스트 드라이버가
미러링하는 비트 레이아웃 테이블을 정의한다.

- ``isa_x32.svh`` — 32-bit 필드 레이아웃 (레거시 + control-plane 오피코드).
- ``isa_x64.svh`` — 64-bit VLIW 필드 레이아웃 (현재 활성 오피코드 집합).
- ``isa_memctrl.svh`` — 메모리 컨트롤러 오피코드 본문 (MEMSET / LOAD /
  STORE / CVO).

호스트 C 드라이버의 ``uCA_v1_api.h`` 는 자신의 비트 레이아웃이
``isa_x64.svh`` 의 오피코드와 1:1 일치한다고 명시하므로, 필드 폭이
바뀔 때마다 SV 헤더와 드라이버 헤더가 함께 이동한다.

.. literalinclude:: ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh
   :language: systemverilog
   :caption: hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_x64.svh

.. admonition:: 마지막 검증 대상
   :class: note

   커밋 ``8c09e5e`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260`` (2026-04-29).

.. seealso::

   :doc:`/docs/v002/ISA/encoding` — 동일 인코딩의 사람이 읽기 쉬운 설명.
   :doc:`/docs/v002/ISA/instructions` — 명령어별 필드 표.
