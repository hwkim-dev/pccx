==================================================
Gemma 3N — FFN Gaussian Top-K Sparsity
==================================================

Gemma 3N 의 초기 FFN 레이어는 **Gaussian Top-K Sparsity** 로 게이트
활성화의 95 % 를 0 으로 만듭니다. 정렬 대신 두 번의 reduction 으로
치환되므로 pccx v002 SFU 에 깔끔하게 매핑됩니다.

1. 규칙
========

레이어 0 ~ 9 (10 개) 에 대해, gate projection 출력을 threshold 처리해
상위 **5 %** 만 남깁니다:

.. math::

   cutoff = Mean(gate\_raw) + 1.6448536 \times Std(gate\_raw)

.. math::

   sparse\_gate = \max(gate\_raw - cutoff,\ 0)

.. math::

   hidden = GELU(sparse\_gate) \times up\_out

상수 ``1.6448536`` 는 표준 정규분포의 95 번째 percentile Z-score.
gate 출력이 근사적으로 Gaussian 을 따른다고 가정합니다 (FFN 전활성화에
서 실제로 잘 맞는 가정).

레이어 10 ~ 34 는 이 단계를 건너뛰고 표준 GELU 게이트를 씁니다:

.. math::

   hidden = GELU(gate\_raw) \times up\_out

2. 이 방식을 채택한 이유
==========================

- **병렬 하드웨어에서 정렬은 비싸다.** 실제 "top 5 %" 는 16 384 개
  요소에 대한 정렬이 필요 — NPU 에 좋은 모양이 아님.
- **Reduction 은 싸다.** ``Mean`` / ``Std`` 는 같은 버퍼에 대한
  ``CVO_REDUCE_SUM`` 2 회 + ``CVO_SCALE`` 몇 회. 총 비용이 수 사이클
  수준. ``16 384 × 2048`` ``GEMV`` 비용에 비해 무시 가능.
- **Gaussian 근사는 충분히 정확하다.** 5 % 경계는 날카롭지 않고, 경계
  근처의 소수 오분류가 downstream 정확도에 영향을 거의 주지 않음.

3. 파이프라인 관점
===================

.. mermaid::

   flowchart TD
       X["입력 x_n2"] --> GateOp(("x · W_gate^T"))
       GateOp --> GateOut["gate_raw (16384)"]
       GateOut --> CalcStats["Reduce-sum × 2<br/>→ Mean / Std"]
       CalcStats --> Threshold["cutoff = Mean + 1.6448·Std"]
       GateOut --> FilterOp
       Threshold --> FilterOp["max(gate_raw - cutoff, 0)"]
       FilterOp --> SparseGate["sparse_gate<br/>(~95% zeros)"]
       SparseGate --> GELU["GELU"]
       GELU --> MultOp(("element-wise ×"))
       X --> UpOp(("x · W_up^T"))
       UpOp --> UpOut["up_out (16384)"]
       UpOut --> MultOp
       MultOp --> FFN_Mid["hidden → W_down"]
       style FilterOp fill:#ffcc80,stroke:#e65100,stroke-width:2px
       style SparseGate fill:#c8e6c9,stroke:#388e3c

4. pccx v002 매핑
==================

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - 연산
     - 명령어
     - 비고
   * - :math:`\mathrm{Mean}(gate\_raw)`
     - ``CVO_REDUCE_SUM`` + ``CVO_SCALE`` (:math:`1/16384`)
     - 스케일은 ``MEMSET`` 로 선적재.
   * - :math:`\mathrm{Var}(gate\_raw)`
     - ``CVO_SCALE`` (제곱) → ``CVO_REDUCE_SUM`` →
       ``CVO_SCALE`` (:math:`1/16384`) → ``CVO_SQRT``
     - 총 4 CVO. ``W_up`` GEMV 와 overlap 가능.
   * - ``cutoff = μ + 1.645·σ``
     - SFU ALU 내부 스칼라 연산
     - 1 사이클.
   * - ``max(gate_raw - cutoff, 0)``
     - GELU 커널 내부에 bias + clip 단을 이용해 구현
     - SFU 의 GELU 경로는 정확히 이 용도로 설정 가능한 bias-and-clip
       front end 를 포함.
   * - ``up_out`` 과 element-wise 곱
     - GEMV / SFU 쌍 내부의 direct FIFO
     - L2 round-trip 없음.

5. 처리량 영향
================

``sparse_gate`` 의 95 % 가 0 이므로, downstream ``W_down`` GEMV 는
masked row 를 완전히 스킵 가능. pccx v002 드라이버는 레이어 0 ~ 9 에서
sparse ``GEMV`` 변형을 발행: weight streamer 가 각 row mask 를 비교하여
mask = 0 이면 DSP 사이클을 스킵.

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - 레이어 범위
     - 게이트 밀도
     - FFN GMAC/s (유효)
     - 비고
   * - 레이어 0 – 9
     - ~5 %
     - 토큰당 ~40 GMAC/s
     - ``W_gate`` + ``W_up`` 가 대부분 차지; ``W_down`` 은 거의 무료.
   * - 레이어 10 – 34
     - 100 %
     - 토큰당 ~130 GMAC/s
     - 전체 dense FFN.

.. note::

   희소성 mask 는 현재 토큰의 gate 출력에서 **실시간 계산** 됨 — 학습되는
   값이 아님. 따라서 드라이버는 cutoff 확정 후 L2 → weight streamer 로
   skip mask 를 ``MEMCPY`` 해야 함. pccx v002 는 ``MEMCPY async=1`` 로
   ``W_up`` GEMV 와 overlap.

.. seealso::

   - 전체 FFN 사양: :doc:`gemma3n_pipeline` §4.D.
   - SFU 함수 코드: :doc:`../ISA/instructions` §4.
