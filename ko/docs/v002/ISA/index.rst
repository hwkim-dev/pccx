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

.. admonition:: 오프라인 가이드북 (PDF) 다운로드
   :class: tip

   동일한 표·동일한 값으로 조판된 오프라인 가이드북이 PDF 로 제공됩니다.
   HTML 포털과 달리 인쇄·아카이브·사인오프용 용도로 적합합니다.

   :download:`pccx v002 ISA 가이드북 (PDF) <../../../../_static/downloads/pccx-isa-v002.pdf>`

   PDF 는 저장소 루트의 ``main.tex`` 로부터 재생성되며, 오프라인 본은
   해당 LaTeX 소스가 단일 작성 창구입니다. 웹 포털은 계속해서 살아있는
   레퍼런스 역할을 맡습니다.

.. note::

   ISA 타입 정의의 권위 있는 소스는 v002 RTL 리포의
   :file:`hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv`
   입니다 (외부: `hwkim-dev/pccx-FPGA-NPU-LLM-kv260
   <https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260>`_). 아래 페이지의
   인코딩 표는 해당 패키지와 1:1 일치해야 합니다 — :doc:`../RTL/isa_pkg`
   참고.
