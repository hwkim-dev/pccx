===============================================
Gemma 3N — Attention 및 RoPE 제약
===============================================

Gemma 3N 은 어텐션 블록에서 두 가지 선택을 표준 Transformer 와 다르게
합니다. 두 결정 모두 pccx v002 명령어 스트림을 단순화시키므로 명시해
둘 가치가 있습니다.

1. Attention Scaling 과 Softcap 완전 제거
==========================================

표준 어텐션에서는 ``Q · Kᵀ`` 결과를 :math:`\sqrt{d_{head}}` 로 나눕니다.
이전 Gemma 세대는 softmax 이전 로짓과 최종 로짓에 **softcap**
(보통 ``50.0``) 을 추가로 적용했습니다.

**Gemma 3N 은 이 둘을 모두 제거합니다.**

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * -
     - 표준 Transformer
     - Gemma 3N
   * - 어텐션 score
     - :math:`Q \cdot K^{T} / \sqrt{d_{head}}`
     - :math:`Q \cdot K^{T}`
   * - Softcap
     - softmax 전 :math:`50 \cdot \tanh(x / 50)`
     - 없음
   * - 최종 logit cap
     - 선택적
     - 최종 단계에서 :math:`30 \cdot \tanh(x / 30)` 1 회

.. code-block:: python

   # 잘못된 방식:
   # attn_weights = np.dot(Q, K.T) / np.sqrt(256)
   # attn_weights = softcap(attn_weights, 50.0)

   # Gemma 3N 방식:
   attn_weights = np.dot(Q, K.T)

.. note::

   **pccx v002 하드웨어 영향.** Softmax 시퀀스가 4 개 → 3 개로 축소:

   .. code-block:: text

      GEMV   flags.findemax=1            ; Q · Kᵀ, e_max 추적
      CVO    CVO_EXP  flags.sub_emax=1   ; exp(score - e_max)
      CVO    CVO_REDUCE_SUM              ; Σ exp → scalar
      CVO    CVO_SCALE flags.recip_scale=1  ; 각 exp 를 sum 으로 나눔

   ``CVO_EXP`` 앞에 별도 ``CVO_SCALE`` 없음, 중간에 softcap ``tanh`` 없음.

2. 레이어 교차 동적 θ RoPE
===========================

보통 RoPE 는 모든 레이어에서 고정된 ``theta_base`` (10 000 또는
1 000 000) 을 사용합니다. Gemma 3N 은 5 레이어 주기로 레이어마다
번갈아 씁니다.

2.1 5 레이어 패턴
------------------

``[Local, Local, Local, Local, Global]`` 의 반복.

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - 레이어 슬롯
     - 역할
     - ``theta_base``
     - 수용 범위
   * - 0, 1, 2, 3, 5, 6, 7, 8, …
     - Local
     - **10 000**
     - 단거리 구문
   * - 4, 9, 14, 19, 24, 29, 34
     - Global
     - **1 000 000**
     - 장거리 의미

2.2 시각화
-----------

.. mermaid::

   block-beta
       columns 5
       L0["Layer 0\nLocal\n(10,000)"]
       L1["Layer 1\nLocal\n(10,000)"]
       L2["Layer 2\nLocal\n(10,000)"]
       L3["Layer 3\nLocal\n(10,000)"]
       L4["Layer 4\nGlobal\n(1,000,000)"]
       L5["Layer 5\nLocal\n(10,000)"]
       L6["Layer 6\nLocal\n(10,000)"]
       L7["Layer 7\nLocal\n(10,000)"]
       L8["Layer 8\nLocal\n(10,000)"]
       L9["Layer 9\nGlobal\n(1,000,000)"]
       E1["..."]
       E2["..."]
       E3["..."]
       E4["..."]
       E5["..."]
       style L0 fill:#e3f2fd,stroke:#1e88e5
       style L1 fill:#e3f2fd,stroke:#1e88e5
       style L2 fill:#e3f2fd,stroke:#1e88e5
       style L3 fill:#e3f2fd,stroke:#1e88e5
       style L4 fill:#ffe0b2,stroke:#f57c00
       style L5 fill:#e3f2fd,stroke:#1e88e5
       style L6 fill:#e3f2fd,stroke:#1e88e5
       style L7 fill:#e3f2fd,stroke:#1e88e5
       style L8 fill:#e3f2fd,stroke:#1e88e5
       style L9 fill:#ffe0b2,stroke:#f57c00

2.3 pccx v002 하드웨어 영향
----------------------------

- ``theta_base`` 는 **토큰 단위가 아닌 레이어 단위 상수**. 레이어 시작
  때마다 ``MEMSET`` 한 번으로 Constant Cache 에 선적재.
- ``CVO_SIN`` / ``CVO_COS`` 커널은 위상
  :math:`pos \cdot \omega_j` (:math:`\omega_j = \theta^{-2j/d_{head}}`)
  만 필요. 두 θ 값에 대한 주파수 테이블을 host 에서 미리 계산해 부팅
  시 ``MEMCPY`` 로 1 회 적재.
- Cross-layer sharing 에서 ``target_K`` / ``target_V`` 는 맞는 캐시
  슬롯 (global θ 이면 레이어 19, local θ 이면 레이어 18) 에서 읽음 —
  :doc:`gemma3n_pipeline` §4.B-4 참고.

3. 전체 TPS 기여
=================

두 단순화로 레이어당 어텐션 블록마다 **CVO_SCALE 1 개** + **CVO_TANH
1 개** 가 줄어듭니다. Gemma 3N E4B 35 레이어 기준으로 토큰당 70 회의
CVO 호출 절감. 20 tok/s 목표에서 SFU 예산 기준 약 2–3 % 의 시간
이득입니다.

.. seealso::

   - 연산자 사양: :doc:`gemma3n_pipeline` §4.B.
   - CVO 함수 코드: :doc:`../ISA/instructions` §4.
