아카이브: v001 실험적 아키텍처
================================

.. warning::
   이 아키텍처는 예비(v001) 실험적 설계입니다. 구조적으로는 우수하지만,
   GEMM(행렬) 연산에 과도하게 집중되어 설계되었습니다. 로컬 LLM 환경은 주로
   GEMV(벡터) 연산에 의해 제한되므로, 이 브랜치는 최적화된 구조를 위해
   현재 아카이브되었습니다.

|Status Archived| |SystemVerilog RTL| |Target Hardware| |Quantization Precision|

--------------

프로젝트 개요
-------------

**pccx** 는 베어메탈 Xilinx Kria KV260 FPGA(400 MHz)에서 양자화된
**Gemma 3N E4B** 대규모 언어 모델을 가속하기 위해 처음부터 맞춤 설계된
SystemVerilog 기반 신경망 처리 장치(NPU)입니다. 이 아키텍처는 KV260 플랫폼의
1,248개 DSP48E2 슬라이스와 144개 BRAM을 기능적 한계까지 활용하도록 세밀하게 설계되었습니다.

-  **소프트웨어 기준선**: `llm-lite <https://github.com/hwkim-dev/llm-lite>`__ (x64 CPU 참조 구현)
-  **풀스택 공동 설계**: 하드웨어 가속기(SystemVerilog), 추적 기반 검증 모델(Python), AXI DMA 메모리 파이프라인.

--------------

양자화 전략: W4A16 + BF16 활성화
---------------------------------

기본 코어 연산 경로는 **W4A16 정밀도** 로 엄격하게 동작합니다:

.. list-table::
   :header-rows: 1
   :widths: 15 10 10 65

   * - 데이터
     - 타입
     - 비트 폭
     - 비고
   * - 가중치
     - INT4
     - 4비트
     - HP 포트를 통해 스트리밍되며 순수 INT4 레이어로 소비됨
   * - 피처맵
     - BF16
     - 16비트
     - BF16 → 27비트 고정소수점으로 변환 후 네이티브 MAC 연산 수행
   * - 누산기
     - INT48
     - 48비트
     - DSP48E2 블록의 P-레지스터를 통해 재귀적으로 누산
   * - SFU I/O
     - BF16
     - 16비트
     - 정규화 후 비선형 연산을 위해 BF16으로 재구성

--------------

컴퓨트 엔진
-----------

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 20 25

   * - 엔진
     - 연산
     - 가중치 입력
     - 활성화 페치
     - 누산기
   * - 행렬 코어
     - GEMM (프리필, 프로젝션)
     - HP0/1 (32 INT4/클럭)
     - BF16 → 27비트 고정소수점
     - INT48 (DSP48E2)
   * - 벡터 코어
     - GEMV (자기회귀 디코딩)
     - HP2/3 (32 INT4/클럭, 각 포트)
     - BF16 → 27비트 고정소수점
     - INT48 (DSP48E2)
   * - CVO 코어
     - 비선형 연산 (Softmax, GELU, RoPE)
     - N/A
     - L2 경유 BF16 스트림
     - BF16

**분리형 데이터플로우** 설계 원칙을 적용하면 연산 명령어가 비동기적으로 실행됩니다.
글로벌 파이프라인에서 별개의 모듈로 분산되어 아키텍처 스톨을 완전히 방지하고
수학적 하드웨어 처리량을 최대로 끌어올립니다.

.. |Status Archived| image:: https://img.shields.io/badge/Status-Archived-red
.. |SystemVerilog RTL| image:: https://img.shields.io/badge/RTL-SystemVerilog-green
.. |Target Hardware| image:: https://img.shields.io/badge/Target-Kria_KV260-orange
.. |Quantization Precision| image:: https://img.shields.io/badge/Precision-W4A16_BF16-green
