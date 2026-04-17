====================
개요
====================

|Status| |Architecture| |Target| |Precision|

.. |Status| image:: https://img.shields.io/badge/Status-Active_Development-yellow
.. |Architecture| image:: https://img.shields.io/badge/Architecture-Heterogeneous_NPU-purple
.. |Target| image:: https://img.shields.io/badge/Target-Kria_KV260-orange
.. |Precision| image:: https://img.shields.io/badge/Precision-W4A8-green

1. 프로젝트 목표
================

**pccx (Parallel Compute Core eXecutor) v002** 는 Xilinx Kria KV260 SoM을
1차 타겟으로 하여, 베어메탈 환경에서 양자화된 Transformer 기반 LLM 을
가속하는 범용 NPU 아키텍처입니다.

핵심 설계 철학
--------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - 원칙
     - 설명
   * - **범용성 (Generality)**
     - 특정 모델(Gemma 3N E4B)에 종속되지 않고, 다양한 Transformer 계열
       모델을 지원할 수 있도록 **디바이스-독립적인 명령어 세트(ISA)** 와
       **분리형(Decoupled) 데이터플로우** 를 제공합니다.
   * - **확장성 (Scalability)**
     - 시스톨릭 어레이의 크기, GEMV·SFU 코어의 수, 로컬 캐시 용량 등
       주요 파라미터가 **generate 파라미터** 로 노출되어, 타겟 디바이스의
       리소스 예산에 맞게 재합성 가능합니다.
   * - **메모리 중심 설계**
     - 물리적으로 L2 캐시를 아키텍처의 중심에 배치하여, GEMM·GEMV·CVO 가
       **동일한 액티베이션 소스** 를 공유하도록 합니다. 이를 통해 레이어
       간 재배치(shuffle) 비용을 제거합니다.

2. 타겟 워크로드
================

타겟 모델의 디코딩 단계는 배치 크기 1, 시퀀스 길이 1 의 **GEMV 지배적
(GEMV-dominated)** 워크로드입니다. 반면 프리필(Prefill) 단계는 GEMM
지배적입니다. pccx v002 는 두 단계 모두를 단일 아키텍처 상에서 효율적으로
실행하도록 **행렬 코어(GEMM)** 와 **벡터 코어(GEMV)** 를 물리적으로 분리
배치하고, **Complex Vector Operation(CVO)** 을 담당하는 **SFU** 를 별도로
두어 파이프라인 스톨을 방지합니다.

성능 목표
---------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - 항목
     - 목표
     - 근거
   * - 디코딩 처리량
     - **20 tok/s (Gemma 3N E4B)**
     - L2 캐시 — GEMV 코어 사이 bandwidth 매칭
   * - 코어 동작 주파수
     - **400 MHz**
     - DSP48E2 타이밍 한계
   * - 양자화 정밀도
     - **W4A8 (INT4 × INT8)**
     - KV260 DSP48E2 의 정수형 연산 최적화
   * - SFU 정밀도
     - **BF16 / FP32 승격**
     - 비선형 연산(Softmax, RMSNorm, GELU)의 수치 안정성

3. v001 과의 주요 차이점
==========================

v001 → v002 전환 배경과 3.125 배 처리량 향상 분석은
:doc:`Architecture/rationale` 에서 상세히 다룹니다. 요약:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - 항목
     - v001 (Archived)
     - v002
   * - 설계 편중
     - GEMM 중심 (프리필 최적화)
     - GEMM · GEMV · SFU 3 코어 체제
   * - L2 캐시 배치
     - 외곽, Global Cache 와 역할 중복
     - **중심 배치**, Global Cache 통합, 양측 대칭 인터커넥트
   * - 양자화
     - W4A16 (BF16 activation)
     - **W4A8 (INT8 activation)**
   * - 코어 구성
     - Matrix + Vector + CVO (경계 모호)
     - Matrix + **GEMV 32×1 × 4** + **SFU 32×1 × 4**
   * - HP 포트
     - 단일 SA 에 1 개 (250 MHz 상한)
     - HP2 / HP3 분산 + 400 MHz 내부 소비
   * - DSP 활용
     - 1 DSP = 1 MAC
     - **1 DSP = 2 MAC (듀얼 채널 비트 패킹)**
   * - 이론 처리량 개선
     - —
     - **× 3.125** (1.6 × 2)

.. seealso::

   - 속도 향상 근거와 설계 트레이드오프: :doc:`Architecture/rationale`
   - KV 캐시 대역폭 전략: :doc:`Architecture/kv_cache`
   - v001 아카이브: :doc:`../archive/experimental_v001/index`

4. 에코시스템 계층
===================

pccx 는 이식성을 보장하기 위해 세 개의 엄격히 분리된 레이어로 구성됩니다.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - 레이어
     - 위치
     - 역할
   * - **Architecture**
     - ``codes/v002/hw/rtl/``
     - 핵심 RTL 로직과 generate 파라미터. ISA, 파이프라인, 스케줄링을
       정의하며 하드웨어 벤더와 무관.
   * - **Device**
     - ``codes/v002/hw/device/``
     - 특정 타겟(예: KV260) 에 리소스 예산을 매핑. 시스톨릭 어레이 크기,
       AXI 인터페이스, URAM 구성을 결정.
   * - **Driver**
     - ``codes/v002/sw/``
     - C/C++ 하드웨어 추상화 레이어(HAL) 와 고수준 API. 명령어 디스패칭,
       메모리 매핑, 호스트-디바이스 동기화 담당.

5. 문서 구성
=============

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 섹션
     - 내용
   * - :doc:`Architecture/index`
     - 탑레벨 블록 다이어그램, 플로어플랜, GEMM·GEMV·SFU 코어 마이크로아키텍처,
       메모리 계층, DSP48E2 W4A8 비트 패킹 기법.
   * - :doc:`ISA/index`
     - 64-bit 명령어 포맷, 5개 오피코드(GEMV/GEMM/MEMCPY/MEMSET/CVO) 인코딩,
       명령어별 데이터플로우.
   * - :doc:`Drivers/index`
     - C API 개요, 명령어 디스패치 플로우.
