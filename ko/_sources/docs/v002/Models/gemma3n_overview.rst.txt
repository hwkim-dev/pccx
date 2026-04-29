========================
Gemma 3N E4B — 개요
========================

pccx v002 는 베어메탈 Kria KV260 에서 **Gemma 3N E4B** 를 20 tok/s 로
돌리는 것을 기준으로 설계되었습니다. 연산자 수준 파이프라인으로
들어가기 전에, 이 페이지는 핵심 차원과 "표준" 디코더 전용 Transformer
에서 벗어난 부분을 정리합니다. 이 차이점들이 하드웨어가 반드시
수용해야 하는 제약입니다.

1. 모델 차원
=============

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - 항목
     - 값
     - 비고
   * - 히든 차원 ``D``
     - **2048**
     - 메인 residual stream 폭.
   * - FFN 중간 ``D_ffn``
     - **16384**
     - 8× 확장.
   * - 레이어 수
     - **35**
     - 35 개의 디코더 블록.
   * - 어텐션 헤드
     - **Q 8 / KV 2**
     - Grouped-Query Attention, 4:1 비율.
   * - 헤드 차원 ``d_head``
     - **256**
     - ``D / 8``.
   * - 어휘 크기
     - **262,400**
     - ``logits = x · W_lm_head``.
   * - Patch / Router 차원
     - ``D_patch = 256``, ``D_router = 4``
     - PLE 패치 임베딩 / AltUp 라우터.
   * - Stream (AltUp)
     - **4**
     - ``xs[0]`` 메인 + 3 개의 shadow stream.

2. Gemma 3N 만의 비표준 요소
=============================

Gemma 3N 은 다섯 군데에서 교과서적 디코더와 다릅니다. 각 항목이
pccx v002 명령어 스케줄링에 직접 영향을 미칩니다.

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - 항목
     - 동작
     - 하드웨어 영향
   * - **AltUp 4-stream**
     - 4 개의 병렬 residual stream. Shadow stream 은 깊이 의존적
       보정을 받고, 메인 stream 은 깨끗하게 유지.
     - L2 에 ``xs`` 4 개 copy 가 상주. 모든 GEMV/GEMM 피연산자는 해당
       stream slice 에서 읽음.
   * - **교차 RoPE θ**
     - 5 레이어 주기 ``[Local, Local, Local, Local, Global]``, θ = 10 000 /
       1 000 000.
     - θ 는 레이어별 상수. 각 RoPE ``CVO_SIN`` / ``CVO_COS`` 쌍 앞에
       ``MEMSET`` 로 선적재.
   * - **Attention scaling / softcap 제거**
     - ``/sqrt(d_head)`` 없음, softmax 앞 softcap 없음.
     - 어텐션 블록당 ``CVO_SCALE`` 하나 줄어듦. softmax 가 ``GEMV``
       직후 바로 시작.
   * - **LAuReL 병렬 분기**
     - 저랭크 사이드 패스를 attention 출력과 합친 뒤 ``sqrt(2)`` 로 나눔.
     - 작은 GEMV 두 개 (``D × 64``, ``64 × D``) + ``CVO_SCALE`` 하나 +
       residual 융합.
   * - **PLE shadow injection**
     - Per-Layer Embedding 은 레이어 *끝* 에 **오직** ``xs[1..3]`` 에만 주입.
     - 메인 stream 경로는 PLE 로 오염되지 않음. 스케줄러가 PLE 작업을
       critical path 바깥에 유지.

각 항목에 대한 상세 수식:

- :doc:`gemma3n_attention_rope` — scaling 제거와 동적 θ.
- :doc:`gemma3n_ple_laurel` — LAuReL scaling 과 PLE 주입 규칙.
- :doc:`gemma3n_ffn_sparsity` — 초기 레이어의 Gaussian Top-K 게이트.

3. 레이어 간 KV 공유
====================

Gemma 3N 은 **모든 레이어에** KV 엔트리를 저장하지 않습니다. 35 개
레이어 중:

- **레이어 0–19** 는 자기 고유의 ``K`` / ``V`` 를 캐시에 저장.
- **레이어 20–34** 는 5 레이어 주기에 따라 레이어 18 (local RoPE) 또는
  레이어 19 (global RoPE) 의 캐시를 재사용.

구체적으로 ``K_cache`` 와 ``V_cache`` 의 shape 는 ``[35, max_seq, 512]``
가 아니라 ``[20, max_seq, 512]``. 이것이
:doc:`../Architecture/kv_cache` 의 KV footprint 예산이 토큰당 70 KB 가
아닌 **~40 KB** 인 주된 이유입니다.

4. 데이터 타입 맵
=================

각 텐서 종류가 pccx v002 의 어느 경로에 해당하는가:

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 30

   * - 텐서
     - 저장
     - 연산 경로
     - 비고
   * - 가중치 (Q / K / V / O / FFN)
     - **INT4 패킹**
     - Systolic Array 또는 GEMV Core
     - W4 + per-channel scale.
   * - 활성화 (hidden, Q / K / V)
     - L2 에서 **INT8**
     - 전처리 후 동일
     - SFU 경유 시에만 BF16 으로 승격.
   * - KV 캐시
     - **FP16** (기본), **INT8/INT4** 권장
     - MEMCPY host ↔ L2
     - :doc:`../Architecture/kv_cache` 참고.
   * - AltUp / LAuReL / PLE 스케일
     - **FP32** (host) → **BF16** (device)
     - SFU
     - 작은 벡터, amortized.
   * - Logits
     - host 에서 **FP32**
     - CPU 후처리
     - Top-P / temperature 는 NPU 외부.

5. 다음 단계
=============

- 전체 연산자 사양 (embedding → sampling): :doc:`gemma3n_pipeline`.
- 명령어 수준 매핑 / 스케줄링: :doc:`gemma3n_execution`.
- x64 CPU 레퍼런스: `llm-lite <https://github.com/hkimw/llm-lite>`_.
