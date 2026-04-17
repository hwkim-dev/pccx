=================================================================
Gemma 3N E4B 를 pccx v002 에서 실행 — Execution / Scheduling
=================================================================

이 페이지는 Gemma 3N E4B 의 디코드 토큰 1 개가 pccx v002 에서 end-to-end
로 어떻게 돌아가는지를 설명합니다. 어떤 텐서가 어디에 있고, 어느 명령어가
어느 코어를 때리며, 스케줄러가 세 컴퓨트 엔진을 어떻게 바쁘게 유지하는지.

수식은 :doc:`gemma3n_pipeline`, 명령어 인코딩 자체는
:doc:`../ISA/instructions` 참고.

1. 정상 동작 시 메모리 레이아웃
================================

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 40

   * - 영역
     - 저장소
     - 단위
     - 내용
   * - **Host DDR4**
     - PS 와 공유되는 4 GB
     - byte
     - 모든 가중치 (INT4 + per-channel scale), KV 캐시 ring buffer,
       embedding / LM head 테이블.
   * - **L2 cache** (URAM)
     - 1.75 MB, 128-bit word
     - 128-bit word
     - 현재 ``xs[0..3]``, ``x_norm``, ``Q/K/V``, ``attn_output``,
       ``gate_raw``, ``up_out``, ``hidden``, ``mlp_out``, ``pli_all``,
       e_max, reduction 누산.
   * - **Weight Buffer** (BRAM/URAM FIFO)
     - ~512 KB
     - 128-bit word
     - HP2/HP3 (250 MHz) 과 400 MHz 코어 사이의 burst buffer. 한 번에
       GEMV/GEMM 하나만큼의 가중치 저장.
   * - **Constant Cache** (BRAM)
     - 64 엔트리 × 48-bit
     - shape / scale tuple
     - RMSNorm scale, attention shape, RoPE θ, sparsity cutoff
       ``μ + 1.645·σ``, LAuReL :math:`1/\sqrt{2}` 스칼라.

2. 호스트 설정 (모델 로드 시 1 회)
==================================

드라이버는 토큰 생성 전에 다음을 수행:

1. ``pccx_open(&handle)`` — AXI-Lite 제어 창을 map, HP/ACP DMA 채널
   오픈.
2. **불변 가중치 적재** (L2 가 작으므로 가중치는 DDR 에 두고 HP 포트로
   on-demand 스트리밍).

   - 임베딩 테이블 (``W_embed``), PLE 테이블, AltUp projection, LM
     head 는 첫/마지막 레이어에서 ``MEMCPY from_device=1 to_device=0
     async=1`` 로 L2 에 상주.
3. **상수 선적재** (``MEMSET`` 연속 발행):

   - Attention / FFN shape tuple.
   - 5 레이어 주기에 따른 레이어별 RoPE ``theta_base`` (10 000 또는
     1 000 000).
   - FFN sparsity z-score ``1.6448536``.
   - LAuReL :math:`1/\sqrt{2}` 스칼라, attention+LAuReL merge scale.
4. **KV ring buffer 초기화**:
   ``pccx_kv_init(handle, max_tokens=8192)``. KV 캐시는 하드 캡을 가진
   ring 으로 동작 — :doc:`../Architecture/kv_cache` 참고.
5. ``pccx_start(handle)`` — ``core_enable`` 을 올리고 dispatcher FIFO 해제.

3. 토큰당 디코드 흐름
=======================

한 토큰은 :doc:`gemma3n_pipeline` §1 ~ §6 를 실행. 명령어 주석 추가한
고수준 데이터 플로우:

.. mermaid::

   flowchart TB
       A["Host: 토큰 id 읽기"] --> B["MEMCPY host → L2<br/>W_embed row + pli_all"]
       B --> C["GEMV: xs[k+1] = x0 · altup_projs[k]"]
       C --> L["레이어 루프 (i = 0 ... 34)"]
       L --> L1["GEMV/CVO: AltUp router + pred"]
       L1 --> L2["GEMV: Q/K/V projection"]
       L2 --> L3["CVO: QK-Norm + RoPE"]
       L3 --> L4["GEMV: Q · Kᵀ<br/>flags.findemax = 1"]
       L4 --> L5["CVO: softmax 시퀀스"]
       L5 --> L6["GEMV: scores · V"]
       L6 --> L7["GEMV: W_o projection<br/>(+ LAuReL GEMV 병렬)"]
       L7 --> L8["GEMV: FFN gate + up"]
       L8 --> L9["CVO: sparsity / GELU / merge"]
       L9 --> L10["GEMV: W_down + residual add"]
       L10 --> L11["GEMV/CVO: AltUp correction + PLE shadow inject"]
       L11 --> L
       L --> D["GEMV: Mean magnitude + unprojection"]
       D --> E["GEMV: LM head projection"]
       E --> F["CVO: softcap tanh"]
       F --> G["MEMCPY L2 → host: logits"]
       G --> H["Host: 샘플링"]

3.1 코어별 역할
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - 파이프라인 단계
     - Systolic Array
     - GEMV ×4
     - SFU ×4
   * - 임베딩 row fetch + AltUp 초기화 (×4)
     - —
     - 4 GEMV (각 ``altup_projs[k]``)
     - —
   * - PLE 사전 계산
     - —
     - 1 GEMV
     - 2 (RMSNorm + scale)
   * - Attention Q/K/V
     - —
     - 3 GEMV
     - 2 (Q-norm, K-norm per head)
   * - RoPE
     - —
     - —
     - 2 (sin, cos) × Q, K
   * - Attention score + softmax + context
     - —
     - 2 GEMV
     - 3 (exp, reduce_sum, scale)
   * - Output + LAuReL 결합
     - —
     - 3 GEMV (W_o + LAuReL 2 개)
     - 1 (× 1/sqrt 2)
   * - FFN gate + up
     - —
     - 2 GEMV (16384 × 2048 각)
     - —
   * - FFN sparsity (레이어 0–9) 또는 GELU only
     - —
     - —
     - 4 (reduce × 2, gate compute, GELU)
   * - FFN down + residual
     - —
     - 1 GEMV (2048 × 16384)
     - 1 (RMSNorm)
   * - AltUp correction + PLE 주입
     - —
     - 3 GEMV (ple_gate, ple_proj, shadow-only add)
     - 2 (tanh, RMSNorm)

디코드 중에는 Systolic Array 가 **놀고 있음**. 프리필에서만 — 전체
컨텍스트에 대한 ``Q · Kᵀ`` 가 실제 GEMM 이 되어 — 깨어남.

3.2 Overlap 전략
-----------------

세 가지 규칙으로 모든 코어를 바쁘게 유지:

1. **HP2/HP3 의 weight prefetch 는 직전 GEMV 가 launch 되는 순간 시작.**
   Weight Buffer 가 GEMV 하나의 전체 가중치를 담을 수 있을 만큼 깊어
   weight DMA 와 compute 가 항상 overlap.
2. **SFU 는 소비자보다 앞서 달림.** GEMV 가 끝나는 즉시 결과가 L2 에
   쓰이고, 직결 FIFO 를 통해 SFU 가 바로 받음. SFU 결과는 다음 GEMV
   시작과 병렬로 L2 에 다시 쓰임.
3. **PLE 사전 계산은 critical path 바깥.** ``pli_all`` 은 레이어마다가
   아닌 토큰 진입 시 1 회 계산. 레이어별 PLE 주입도 메인 stream 에서
   벗어나 있으므로 (:doc:`gemma3n_ple_laurel`) 메인 stream 레인의 다음
   레이어 AltUp router 와 overlap.

4. KV 캐시 관리
================

KV 캐시가 가장 큰 대역폭 소비자. 드라이버 레벨에서 두 동작이 필수:

1. **Cross-layer sharing.** 레이어 0 ~ 19 만 자기 KV 엔트리를 쓰고,
   레이어 20 ~ 34 는 레이어 18 (local θ) 또는 19 (global θ) 의 캐시를
   재사용. 스케줄러는 ``i < 20`` 에서만 ``K`` / ``V`` 생성 GEMV 를
   발행하고, ``i >= 20`` 에서는 ``target_K`` / ``target_V`` 를 캐시에서
   재조회.
2. **Hard-cap ring buffer.** ``max_tokens`` 는 init 시점에 설정, 이후
   증가 불가. ring 이 wrap 되면 attention-sink + local-window 정책에
   따라 **가장 오래된** 엔트리부터 overwrite.
3. **선택적 INT4 / INT8 KV 양자화** (:doc:`../Architecture/kv_cache`
   §2.1 참고). 컨텍스트 > 4 K 인 경우 기본값으로 권장.

5. 에러 / 완료 처리
====================

- 모든 명령어에 1-bit ``async`` 필드가 있음. 드라이버는 레이어 내부
  명령어는 모두 async 로 간주하고, 레이어 단위로만 (AltUp correction
  앞에서) ``done`` 상태 레지스터를 폴링.
- ``flags.recip_scale=1`` 에서 스칼라가 ``0`` 이면 ``CVO_SCALE`` 은
  ``0`` 을 반환. 이런 명령어를 발행하지 않을 책임은 드라이버에 있음
  (프로그래머 오류, 하드웨어 fault 아님).
- Global Scheduler 는 decode 오류 (reserved bit 비영, 미지 opcode,
  범위를 벗어난 주소) 시 AXI-Lite 제어 뱅크에 **error interrupt** 를
  발생. 드라이버는 명령어를 로깅하고 중단.

6. 성능 예산 (목표)
=====================

기본 설정 (W4A8 compute, INT4 KV 캐시, ``L = 8192`` 하드 캡) 기준
end-to-end 디코드 목표:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - 메트릭
     - 목표
     - 병목 원인
   * - 디코드 처리량
     - **20 tok/s**
     - 400 MHz × 4 레인 × 1024 MAC/clk 에서 GEMV 대역폭.
   * - L2 활성화 대역폭
     - **~1.6 GB/s**
     - ``xs[0..3]``, ``gate_raw``, ``up_out``, ``hidden`` round-trip.
   * - 8 K 에서 KV 읽기 대역폭
     - **~6 GB/s**
     - 20 층 × 512 × INT4 × 2 (K, V) × 8 K / 50 ms.
   * - Weight 스트림 대역폭
     - **~3 GB/s**
     - HP 두 포트 × 128-bit × 250 MHz, amortized.

컨텍스트 > 4 K 이면 KV 대역폭이 병목 — 완화책은
:doc:`../Architecture/kv_cache` 참고.

.. seealso::

   - 연산자 사양: :doc:`gemma3n_pipeline`
   - pccx v002 ISA: :doc:`../ISA/index`
   - Driver API: :doc:`../Drivers/api`
