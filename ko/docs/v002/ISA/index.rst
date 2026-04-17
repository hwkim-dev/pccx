===============================
명령어 세트 아키텍처 (ISA)
===============================

pccx v002 의 ISA 는 **고정 길이 64-bit VLIW 스타일** 이며, 5 개의 오피코드
(GEMV, GEMM, MEMCPY, MEMSET, CVO) 로 구성됩니다. 설계 원칙은 다음과 같습니다:

- **하드웨어 독립성**: 명령어 인코딩은 특정 디바이스 리소스 예산과 무관.
- **CISC 스타일 매크로**: 단일 명령어가 수천 사이클의 MAC 시퀀스를 기동.
- **디스패치 중심**: 명령어 디코딩 즉시 제어 μop, 메모리 μop 로 분해되어
  백엔드에 전달.

.. toctree::
   :maxdepth: 1

   encoding
   instructions
   dataflow

.. note::

   현재 ISA 타입 정의는 v001 코드베이스
   (:file:`codes/v001/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv`)
   의 SystemVerilog 패키지에 정의되어 있으며, v002 로 이전되며 안정화될
   예정입니다.
