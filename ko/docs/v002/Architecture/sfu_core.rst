======================================
SFU 코어 (Complex Vector Operations)
======================================

SFU(Special Function Unit) 는 Transformer 의 비선형 연산 — **Softmax**,
**GELU**, **RMSNorm**, **RoPE** — 을 담당하는 전용 유닛입니다.
ISA 상에서는 **CVO (Complex Vector Operation)** 명령어 계열로 노출됩니다.

1. 구성
========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 파라미터
     - 값
   * - 유닛 차원
     - **32 × 1 (per instance)**
   * - 인스턴스 수
     - **4** per 슬라이스 (상하 2 슬라이스)
   * - 내부 정밀도
     - **BF16 / FP32** (동적 승격)
   * - 지원 함수
     - **EXP, SQRT, GELU, SIN, COS, REDUCE_SUM, SCALE, RECIP**

2. 정밀도 승격 전략
===================

**입력 / 출력** 은 L2 Cache 와의 대역폭 효율을 위해 INT8 또는 BF16 이지만,
**내부 연산** 은 다음과 같이 승격됩니다.

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - 함수
     - 입력
     - 내부
     - 근거
   * - ``CVO_EXP``
     - BF16
     - FP32
     - overflow 방지 (softmax 에서 `sub_emax` 플래그로 완화)
   * - ``CVO_SQRT``
     - BF16
     - FP32
     - RMSNorm 의 `1/sqrt(var + ε)` 수치 안정성
   * - ``CVO_GELU``
     - BF16
     - BF16
     - 근사식 (tanh 또는 rational) 사용
   * - ``CVO_SIN/COS``
     - BF16
     - FP32
     - RoPE 의 phase 누적 오차 방지
   * - ``CVO_REDUCE_SUM``
     - BF16/INT8
     - FP32
     - 장기 누적 오차 최소화
   * - ``CVO_SCALE``
     - INT8/BF16
     - BF16
     - dequantize × 스칼라
   * - ``CVO_RECIP``
     - BF16
     - FP32
     - softmax denominator, layer-norm divisor

3. 구현 기법
=============

3.1 CORDIC + LUT 하이브리드
----------------------------

v001 의 ``CVO_cordic_unit.sv`` / ``CVO_sfu_unit.sv`` 설계를 계승:

- **CORDIC**: ``SIN``, ``COS``, ``SQRT``, ``RECIP`` 등 반복 수렴 연산.
  15~20 단 파이프라인.
- **LUT + 다항식 보정**: ``EXP``, ``GELU``. LUT 에서 조악한 추정을
  얻고, 2~3 차 다항식으로 보정.

3.2 Reduction
-------------

``CVO_REDUCE_SUM`` 은 32 레인 입력을 5 단계 adder tree 로 축약하며,
Softmax 의 denominator 계산에 사용됩니다.

3.3 Softmax Fast Path
---------------------

Softmax 는 3 명령어 시퀀스로 분해됩니다.

.. mermaid::

   sequenceDiagram
     autonumber
     participant D as Dispatcher
     participant S as SFU
     participant E as e_max reg
     D->>S: CVO_REDUCE_SUM (flags.findemax)
     S->>E: e_max 갱신
     D->>S: CVO_EXP (flags.sub_emax)
     S->>S: exp(x − e_max)
     D->>S: CVO_RECIP × CVO_SCALE
     S-->>D: softmax(x)

`findemax` / `sub_emax` 플래그가 연산 중 **online max-normalization** 을
하드웨어 레벨에서 수행하여, 소프트웨어 측의 별도 스캔을 제거합니다.

4. 파이프라인 통합
==================

SFU 는 GEMV 코어와 **직결 FIFO** 로 연결되어 다음 경로를 지원합니다.

- GEMV → SFU: Attention 의 `Q·K^T → softmax`, FFN 의 GEMV → GELU 경로에서
  L2 왕복을 생략.
- SFU → GEMV: Softmax 결과를 V 에 재곱할 때 L2 경유 없이 즉시 소비.

SFU 는 **비동기 실행(Async mode)** 을 지원하여 (`async_e` ISA 필드),
컨트롤러는 완료를 기다리지 않고 다음 명령어를 디스패치합니다.
완료 통지는 ``fsmout_npu_stat_collector`` (v001 계승) 가 처리합니다.

5. 물리 배치
=============

플로어플랜(:doc:`floorplan`) 상 SFU 는 상·하 슬라이스 각각에 4 개씩,
총 8 개가 배치됩니다. GEMV 코어 옆에 나란히 두어 직결 FIFO 의
배선 길이를 최소화합니다.

6. 확장성
=========

CVO 함수 테이블(:doc:`../ISA/instructions` 의 ``cvo_func_e``) 에 새 함수를
추가하려면:

1. ``cvo_func_e`` enum 확장 (4-bit 여분 존재: 현재 8/16 사용).
2. SFU 유닛 내부에 해당 CORDIC/LUT 블록 추가.
3. Dispatcher 의 decode 테이블 업데이트.

하드웨어 측의 함수 슬롯은 generate 파라미터 ``SFU_ENABLE_MASK`` 로
토글되어, 사용하지 않는 함수를 합성에서 제외해 LUT 를 절약할 수 있습니다.
