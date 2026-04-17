=======================================================
Gemma 3N — LAuReL 과 PLE Calibration 모듈
=======================================================

Gemma 3N 에는 메인 Attention / FFN 스택 바깥에 있는 두 가지 보정
경로가 있습니다. **LAuReL** (Attention 과 병렬로 돌아가 결합되는 저랭크
분기) 과 **PLE** (shadow stream 에만 주입되는 레이어 깊이 임베딩).
두 모듈 모두 scaling / routing 규칙이 매우 구체적이며, 잘못 적용해도
모델은 여전히 *돌지만* 출력 분포가 조용히 틀어집니다.

1. LAuReL: Attention 병렬 보정
===============================

LAuReL 은 Attention 과 병렬로 입력을 처리하고, 그 출력은 Attention
출력과 **첫 residual 연결 전에** 합쳐집니다.

1.1 수식
---------

.. math::

   x_{out} = \frac{\text{Attention}(x) + \text{LAuReL}(x_{norm})}{\sqrt{2.0}}

중요: LAuReL 에 들어가는 입력은 원본 :math:`x` 가 **아니라**
RMSNorm 된 :math:`x_{norm}`. post-attention RMSNorm 및 residual add
를 포함한 전체 수식은 :doc:`gemma3n_pipeline` §4.C 참고.

1.2 다이어그램
---------------

.. mermaid::

   graph TD
       X["Input x"] --> N["RMSNorm (input_ln)"]
       N --> Attn["Attention block"]
       N --> LAuReL["LAuReL block<br/>(저랭크 GEMV 2 개: D×64, 64×D)"]
       Attn --> AddOp((+))
       LAuReL --> AddOp
       AddOp --> ScaleOp["× 1/sqrt(2)"]
       ScaleOp --> FinalOut["Attention + LAuReL 출력"]
       style Attn fill:#c8e6c9,stroke:#388e3c
       style LAuReL fill:#ffccbc,stroke:#d84315
       style ScaleOp fill:#bbdefb,stroke:#1976d2

1.3 pccx v002 매핑
-------------------

LAuReL 은 저랭크 GEMV 2 개와 간단한 스케일로 구현됩니다:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - 연산
     - pccx 명령어
     - 비고
   * - :math:`x_{norm} \cdot W_{laurel\_left}^{T}` (2048 → 64)
     - ``GEMV``
     - 아주 작은 행렬. Attention GEMV 보다 지연 짧음 → 병렬 실행 가능.
   * - :math:`\ldots \cdot W_{laurel\_right}^{T}` (64 → 2048)
     - ``GEMV``
     -
   * - :math:`1/\sqrt{2}` 스케일
     - ``CVO_SCALE``, flags.recip_scale=0
     - 상수 스칼라를 MEMSET 으로 사전 적재.
   * - ``attn_output`` 과 최종 합
     - ``GEMV`` with ``flags.accm=1``
     - 출력 projection write-back 에 융합.

LAuReL 의 두 GEMV 크기가 매우 작기 때문에 (``[2048 × 64]``,
``[64 × 2048]``), 메인 projection 과 GEMV 레인을 공유해도 지연 증가가
거의 없습니다.

2. PLE (Per-Layer Embedding): Shadow-Stream 주입
=================================================

PLE 는 레이어 깊이 기반 위치 정보를 주입하되, **오직 shadow stream 에만**
적용됩니다. Gemma 3N 에서 가장 틀리기 쉬운 디테일.

2.1 주입 지점 제약
-------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - 동작
     - 잘못된 구현
     - 올바른 구현
   * - Stream
     - 메인 ``xs[0]``
     - shadow ``xs[1..3]`` 에만
   * - 타이밍
     - 레이어 시작
     - 레이어 끝, AltUp correction 이후
   * - 대상 텐서
     - ``xs`` 의 4 행 모두
     - 1, 2, 3 행만

코드 표현 (:doc:`gemma3n_pipeline` §4.E step 4 참조):

.. math::

   xs_{new}[1:] \mathrel{+}= RMSNorm(gate\_ple \cdot W_{ple\_proj},
                                   W_{ple\_post\_ln})

``xs[0]`` 은 의도적으로 더해지는 대상에서 제외됩니다. 메인 stream 은
깨끗한 residual 경로로 보존.

2.2 다이어그램
---------------

.. mermaid::

   graph TD
       subgraph "Layer Processing"
         X0["메인 stream xs[0]"] --> MainComputation["Attn · LAuReL · FFN"]
         X1["Shadow stream xs[1..3]"] --> Wait["(bypass)"]
       end
       MainComputation --> X0_Out["업데이트된 메인 stream xs[0]"]
       Wait --> AddPLE((+))
       PLE["Per-Layer Embedding<br/>(depth context)"] --> AddPLE
       AddPLE --> X1_Out["업데이트된 shadow stream xs[1..3]"]
       X0_Out --> NextLayer["다음 레이어"]
       X1_Out --> NextLayer
       style X0 fill:#a5d6a7,stroke:#2e7d32
       style MainComputation fill:#a5d6a7,stroke:#2e7d32
       style X1 fill:#ce93d8,stroke:#6a1b9a
       style AddPLE fill:#ce93d8,stroke:#6a1b9a
       style PLE fill:#ffe082,stroke:#ff8f00

2.3 하드웨어 매핑
------------------

PLE 는 두 단계:

- **사전 계산 (토큰당 1 회, 레이어 0 앞에서).**
  :doc:`gemma3n_pipeline` §3 에서 ``W_ple_proj`` 와 ``W_ple`` 로부터
  ``pli_all[35][256]`` 을 계산. GEMV 1 + 임베딩 lookup 1 + CVO 2 회.
  두 테이블 모두 토큰 진입 시 ``MEMCPY`` 로 L2 에 적재.

- **레이어별 주입 (각 레이어 끝).** ``gate_ple`` (GEMV + GELU) 계산,
  ``pli`` 와 element-wise 곱, ``W_ple_proj`` 로 ``D`` 차원으로 확장
  (GEMV), RMSNorm, ``xs_new[1..3]`` 에 가산. 마지막 가산은
  ``GEMV flags.accm=1`` 로 해당 shadow-stream L2 행에 in-place 업데이트.

메인 stream 은 이 모든 과정에서 건드려지지 않으므로, 메인 stream 을
맡은 GEMV 레인이 shadow-stream 레인이 PLE 로 바쁠 때 다음 레이어
AltUp 사전 계산을 돌릴 수 있습니다.

3. 왜 중요한가
================

두 모듈 모두 깊은 residual 동역학을 안정화하기 위해 존재합니다. 잘못
배선해도 명확한 런타임 에러 없이 모델이 그럴듯한 토큰을 내지만 보정이
틀어집니다. pccx v002 스케줄러에는 **강제 규칙** 이 들어가 있습니다:

- LAuReL 출력 경로는 항상 residual 가산 전에 :math:`1/\sqrt{2}` 스케일.
  이 스케일은 전용 MEMSET 슬롯 사용.
- PLE 의 shadow-stream 쓰기 GEMV 는 명시적 mask 로 ``xs`` 의 0 행을
  절대 타겟으로 하지 않음. 해당 mask 는 Global Scheduler 가 발행하는
  per-layer uop 의 일부.

.. seealso::

   - 연산자 사양: :doc:`gemma3n_pipeline` §4.C, §4.E.
   - 전체 명령어 셋: :doc:`../ISA/instructions`.
