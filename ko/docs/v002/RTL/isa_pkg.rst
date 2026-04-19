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

.. seealso::

   :doc:`/docs/v002/ISA/encoding` — 동일 인코딩의 사람이 읽기 쉬운 설명.
   :doc:`/docs/v002/ISA/instructions` — 명령어별 필드 표.
