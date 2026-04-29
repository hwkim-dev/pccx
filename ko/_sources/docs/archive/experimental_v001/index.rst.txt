아카이브: v001 실험적 아키텍처
================================

.. warning::

   이 아키텍처는 예비(v001) 실험적 설계입니다. 구조적으로는 우수하지만,
   GEMM(행렬) 연산에 과도하게 집중되어 설계되었습니다. 로컬 LLM 환경은 주로
   GEMV(벡터) 연산에 의해 제한되므로, 이 브랜치는 최적화된 구조를 위해
   현재 아카이브되었습니다.

|Status Archived| |SystemVerilog RTL| |Target Hardware| |Quantization Precision|

.. toctree::
   :hidden:
   :maxdepth: 1

   Architecture/v001_architecture
   Drivers/ISA
   Drivers/ISA_Spreadsheet
   Drivers/v001_API
   RTL/index

--------------

프로젝트 개요
-------------

**pccx** (이전 명칭 uXC) 는 베어메탈 Xilinx Kria KV260 FPGA(400 MHz)에서
양자화된 **Gemma 3N E4B** 대규모 언어 모델을 가속하기 위해 처음부터
맞춤 설계된 SystemVerilog 기반 신경망 처리 장치(NPU)입니다. 이 아키텍처는
KV260 플랫폼의 1,248 개 DSP48E2 슬라이스와 144 개 BRAM 을 기능적 한계까지
활용하도록 세밀하게 설계되었습니다.

-  **소프트웨어 기준선**:
   `llm-lite <https://github.com/hkimw/llm-lite>`__ (x64 CPU 참조 구현)
-  **풀스택 공동 설계**: 하드웨어 가속기(SystemVerilog), 추적 기반 검증
   모델(Python), AXI DMA 메모리 파이프라인.

--------------

빠른 메뉴
---------

.. container:: grid cards

   -  :doc:`아키텍처 개요 <Architecture/v001_architecture>`

      NPU 내부 아키텍처, 3 계층 코어 시스템의 분리형 모델, 메모리 전이
      계층 레이아웃을 설명합니다.

   -  :doc:`ISA 사양 <Drivers/ISA>`

      64-bit VLIW 코어, Opcode 라우팅 설계, 레지스터 매핑, 파이프라인
      스케줄링 방법론을 설명합니다.

   -  :doc:`ISA 스프레드시트 <Drivers/ISA_Spreadsheet>`

      전체 모듈형 ISA 구조의 스프레드시트 뷰 breakdown 을 제공합니다.

   -  :doc:`C API 상세 <Drivers/v001_API>`

      활성 NPU 호스트 컨트롤러를 타게팅하는 ``pccx_v1_api.c`` /
      ``pccx_v1_api.h`` 의 주요 래핑 인터페이스를 다룹니다.

   -  :doc:`RTL 소스 레퍼런스 <RTL/index>`

      코어별 SystemVerilog 심층 해부. ``codes/v001/`` 의 모든 모듈을
      syntax highlighting 과 접을 수 있는 dropdown 으로 인라인 표시.

--------------

양자화 전략: W4A16 + BF16 활성화
---------------------------------

기본 코어 연산 경로는 **W4A16 정밀도** 로 엄격하게 동작합니다:

.. list-table::
   :header-rows: 1
   :widths: 18 12 12 58

   * - 데이터
     - 타입
     - 비트 폭
     - 비고
   * - **가중치**
     - INT4
     - 4 비트
     - HP 포트를 통해 스트리밍되며 순수 INT4 레이어로 소비
   * - **피처맵**
     - BF16
     - 16 비트
     - BF16 :math:`\rightarrow` 27 비트 고정소수점으로 변환 후 네이티브 MAC 연산
   * - **누산기**
     - INT48
     - 48 비트
     - DSP48E2 블록의 P-레지스터를 통해 재귀적으로 누산
   * - **SFU I/O**
     - BF16
     - 16 비트
     - 정규화 후 비선형 연산을 위해 BF16 으로 재구성

정밀도 승격 흐름
~~~~~~~~~~~~~~~~~

.. mermaid::

   graph TD
       A[Weight: INT4] --> MAC[DSP48E2 MAC]
       B[FMap: BF16 → 27-bit fixed-pt] --> MAC
       MAC -->|Accumulator| C[INT48]
       C -->|Barrel Shift + LOD| D[Normalization: BF16]
       D -->|SFU / CORDIC| E[Non-Linear Ops: exp, RMSNorm, Softmax...]
       E --> F[Output: BF16 to next layer]

비선형 연산(Complex Vector Operation) 루프로 진입하는 전이 구간에서
연산은 정확히 **BF16** 으로 승격됩니다.

--------------

컴퓨트 엔진
-----------

.. list-table::
   :header-rows: 1
   :widths: 12 22 22 26 18

   * - 엔진
     - 연산
     - 가중치 입력
     - 활성화 페치
     - 누산기
   * - **행렬 코어**
     - GEMM (프리필, 프로젝션)
     - HP0/1 (32 INT4/clk)
     - BF16 :math:`\rightarrow` 27 비트 고정소수점
     - INT48 (DSP48E2)
   * - **벡터 코어**
     - GEMV (자기회귀 디코드)
     - HP2/3 (32 INT4/clk each)
     - BF16 :math:`\rightarrow` 27 비트 고정소수점
     - INT48 (DSP48E2)
   * - **CVO 코어**
     - 비선형 연산 (Softmax, GELU, RoPE)
     - N/A
     - L2 경유 BF16 스트림
     - BF16

..

   구조적 **분리형 데이터플로우** 설계 원칙을 적용하면 연산 명령어가
   비동기적으로 실행됩니다. 글로벌 파이프라인에서 별개의 모듈로 분산되어
   아키텍처 스톨을 완전히 방지하고 수학적 하드웨어 처리량을 최고점까지
   밀어붙입니다.

.. |Status Archived| image:: https://img.shields.io/badge/Status-Archived-red
.. |SystemVerilog RTL| image:: https://img.shields.io/badge/RTL-SystemVerilog-green
.. |Target Hardware| image:: https://img.shields.io/badge/Target-Kria_KV260-orange
.. |Quantization Precision| image:: https://img.shields.io/badge/Precision-W4A16_BF16-green
