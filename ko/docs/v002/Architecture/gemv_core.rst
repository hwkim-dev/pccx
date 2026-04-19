==================
GEMV 코어
==================

GEMV 코어는 LLM **자기회귀 디코딩(Autoregressive Decoding)** 단계의
지배적 연산인 **행렬 × 벡터(``y = W x``)** 를 담당합니다. 배치 1 ·
시퀀스 1 의 디코딩에서는 전체 FLOPs 의 85 ~ 98 % 이상이 GEMV 이므로,
GEMV 처리량이 **초당 토큰 생성률(TPS) 에 직접 비례** 합니다.

.. important::

   2 차원 시스톨릭 어레이 하나만으로 디코딩을 수행하면 유효 가동률이
   ``1 / 32`` (= 단일 행만 활성) 까지 떨어집니다. pccx v002 는 이를 해결하기
   위해 **GEMV 전용 1D 벡터 코어** 를 GEMM 과 병렬로 두고, 두 경로가 동일
   L2 Cache 를 공유하는 이기종(heterogeneous) 구조를 채택했습니다.

1. 연산 대상
=============

GEMV 의 입력은 **길이 N 의 액티베이션 벡터** 와 **N × N 크기의 가중치
행렬** 입니다.

.. figure:: ../../../../assets/images/Architecture/v002/Processing_Elements_GEMV_2_v002.png
   :align: center
   :width: 80%
   :alt: GEMV 연산 대상 — Activation 벡터 × Weight 행렬

   **Figure GEMV-Operands.** Activation 은 1 × N 행 벡터, Weight 는
   N × N 행렬이며 두 피연산자의 내적 결과가 새 길이 N 의 출력 벡터를
   구성합니다. Attention 의 ``Q·Kᵀ``, FFN 의 projection 에 모두 동일한
   형태가 적용됩니다.

2. 구성
========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 파라미터
     - 값
   * - 코어 당 차원
     - **32 (K) × 1 (M)**
   * - 코어 개수
     - **총 4 개** (``device_pkg.sv`` 의 ``VecPipelineCnt = 4``; 플로어
       플랜 상 상·하 슬라이스에 2 개씩 분산)
   * - 코어 당 곱셈 폭
     - **32 MAC / clk** (INT4 × BF16, LUT 기반 사전 계산)
   * - Stage 1 누적 DSP
     - **16 DSP48E2** · 코어당 (32 부분합 → 16 이중합)
   * - Reduction 트리
     - **5 단계** (32 → 16 → 8 → 4 → 2 → 1)
   * - 피크 처리량
     - **32 MAC × 4 코어 × 400 MHz = 51.2 GMAC/s**

3. 코어 내부 구조
=================

.. figure:: ../../../../assets/images/Architecture/v002/Processing_Elements_GEMV_1_v002.png
   :align: center
   :width: 90%
   :alt: GEMV 코어 파이프라인과 reduction tree

   **Figure GEMV-Core.** Activation 1 행과 Weight 1 열을 **Pre-Process**
   블록에서 dequantize 하여, 32 개 LUT 기반 곱셈기가 (W × A) 를 단일
   사이클에 병렬 수행합니다. 32 개의 부분곱은 5 단계 reduction adder
   tree (Stage 1: DSP48E2 16 슬라이스, Stage 2–5: LUT) 를 거쳐 스칼라로
   축약되며, **Post-Process** 블록에서 스케일·bias 를 적용한 뒤
   REGISTER 에 기록됩니다.

3.1 Weight Streaming
---------------------

디코딩 단계에서는 각 레이어 가중치가 **매 토큰마다 한 번만** 사용되어
재사용이 없습니다. 따라서 GEMV 는 GEMM 과 달리 **Weight Streaming** 전략을
적용합니다.

- HP2/HP3 포트에서 가중치를 연속 스트리밍.
- Weight Buffer 를 경유해 각 코어의 **W-side Pre-Process** 에 직접 주입.
- 가중치 재사용이 없으므로 버퍼는 순환 FIFO 형태로만 동작.

3.2 Activation 재사용
---------------------

액티베이션 벡터 ``x`` 는 L2 Cache 에 상주하며, 여러 GEMV 코어가 **동일한
벡터를 브로드캐스트** 해 소비합니다.

1. L2 → L1 Cache 로 액티베이션 타일 프리로드.
2. **Pre-Process** 블록이 INT8 → BF16 dequantize 와 scale 수행.
3. 32 개의 LUT 기반 곱셈 유닛이 ``(W × A)`` 를 한 클럭에 병렬 실행.
   (W 가 INT4 이므로 가능한 16 개 가중치 값에 대한 곱을 먼저 LUT 로
   사전 계산한 뒤, 실제 W 비트 패턴으로 선택만 수행.)

3.3 Reduction Tree
------------------

코어 당 32 개의 부분곱을 아래 5 단계 트리로 스칼라 한 개까지 축약하며,
각 단계마다 파이프라인 레지스터를 삽입해 400 MHz 타이밍을 확보합니다.

.. mermaid::

   flowchart TB
     MAC["32 × partial products<br/>(LUT-based W × A)"]
         --> S1["Stage 1 — DSP48E2<br/>16 × (a + b)<br/>32 → 16"]
     S1  --> S2["Stage 2 — LUT<br/>16 → 8"]
     S2  --> S3["Stage 3 — LUT<br/>8 → 4"]
     S3  --> S4["Stage 4 — LUT<br/>4 → 2"]
     S4  --> S5["Stage 5 — LUT<br/>2 → 1"]
     S5  --> OUT[/Scalar/]

Stage 1 은 ``DSP48E2`` 의 ``A:B + C`` (ONE48) 모드를 써서 인접한 두
부분곱을 더하는 용도로만 사용 (16 개 DSP 슬라이스 / 코어). Stage 2–5
는 LUT 기반 가산기로 구현되어 DSP 예산을 절약. 구현 파일은 v001 의
``GEMV_reduction.sv`` · ``GEMV_reduction_branch.sv`` 를 그대로 계승.

3.4 누적 & 포스트프로세싱
-------------------------

- Reduction 결과는 **Result Accumulator** 에 저장되어, 다음 가중치 열과
  순차적으로 합산되어 행 전체의 부분합을 완성합니다.
- Post-Process 에서 weight-scale / activation-scale / bias 를 적용.
- 최종 INT8 재양자화 결과를 L2 Cache 또는 SFU 직결 FIFO 로 전송.

4. 병렬화 전략
==============

4 개의 GEMV 코어는 두 가지 병렬화 모드를 지원합니다. ISA 의
``parallel_lane`` (5-bit) 필드로 활성 코어 수와 파티션 방향이 지정됩니다.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 모드
     - 설명
   * - **Row Parallelism**
     - 출력 벡터의 서로 다른 행을 4 개 코어가 분할 계산. 가중치 행렬이
       row 방향으로 스트라이프 됨. 액티베이션은 공유.
   * - **Head Parallelism**
     - Multi-Head Attention 의 서로 다른 헤드를 4 개 코어가 독립 처리.
       액티베이션(Q)·가중치가 헤드 축으로 분할됨.

5. 내장 Lookup Table
=====================

GEMV 코어는 W4 dequantize 와 MAC 을 하나의 LUT 사전 연산으로 병합.

- ``GEMV_generate_lut.sv`` (v001 계승) 가 BF16 액티베이션 ``A`` 1 개와
  INT4 가중치의 가능한 16 개 값 (-8 ~ +7) 에 대해 **16 개 사전
  계산된 곱** ``A × w`` 를 만든다.
- 이를 32 개의 액티베이션 위치에 대해 병렬 생성하므로, 코어 당
  **32 × 16 = 512 개의 사전 곱** 이 매 클럭 준비된다.
- 실제 가중치가 도착하면 4-bit 패턴을 인덱스로 LUT 에서 단순 선택 →
  MAC 한 번에 해당하는 값이 Stage 1 누적 DSP 로 바로 흘러간다.
- 스케일 계수는 Constant Cache 에서 인덱싱.

6. Softmax / Normalize 와의 연동
================================

GEMV 출력은 주로 아래 두 패턴으로 소비됩니다.

1. **Attention**: ``Q·Kᵀ`` → ``CVO_EXP`` / ``REDUCE_SUM`` (SFU)
   → ``V·softmax`` (다시 GEMV)
2. **FFN Projection**: GEMV → ``CVO_GELU`` / ``CVO_SCALE`` (SFU)
   → 다음 GEMV

GEMV ↔ SFU 경로는 L2 Cache 를 경유하지 않고 **직결 FIFO** 로 연결되어
왕복 레이턴시를 제거합니다. 자세한 내용은 :doc:`sfu_core` 를 참조하세요.
