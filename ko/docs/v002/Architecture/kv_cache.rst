============================================
KV 캐시 최적화 전략
============================================

자기회귀 디코딩 단계의 실질적 성능 한계는 **연산량이 아니라 KV 캐시의
메모리 대역폭**\ 이다. 본 문서에서는 Gemma 3N E4B 타겟에서 pccx v002가
KV 캐시를 어떻게 관리하는지, 그리고 RTL / 드라이버 계층에서 적용되는
3대 지침을 다룬다.

1. GEMV 지배성과 메모리 장벽
=============================

디코딩(토큰 1개 생성) 단계에서 연산량의 **85 ~ 98% 이상이 GEMV**\ 이며,
GQA Attention 부분만이 시퀀스 길이 ``L``\ 에 비례하는 GEMM을 수행한다.
따라서 GEMV 유효 가동률이 TPS에 직결된다.

반면 KV 캐시는 레이어마다 누적·재사용되므로, 시퀀스가 길어질수록 **매 토큰
마다 읽어야 할 메모리 총량**\ 이 선형으로 증가한다.

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - 시퀀스 길이 L
     - 토큰 당 KV
     - 누적 KV 크기
     - KV260 DDR4 (10–12 GB/s) 기준 예상 여유
   * - 1 K
     - ~40 KB
     - ~40 MB
     - 넉넉함 — MAC 이 병목
   * - 8 K
     - ~40 KB
     - ~320 MB
     - 빠듯함 — 대역폭 경쟁 시작
   * - 32 K
     - ~40 KB
     - **~1.31 GB**
     - **대역폭 포화 — MAC 정지**

32K 컨텍스트 기준 1.31 GB를 매 토큰마다 DDR4에서 읽어야 하므로,
실효 대역폭 ~10 GB/s에서 토큰 당 ~131 ms의 메모리 전송 시간만으로도
TPS가 8 이하로 떨어진다.

.. note::

   Gemma 3N의 **Cross-Layer Sharing** 최적화(35층 중 20층만 KV 저장)를
   반영해도 토큰 당 40 KB 수준이다. 이 값이 KV260 등 엣지 장치에서
   ``L = 32 K``\ 를 직접 수용할 수 없는 본질적 원인이다.

2. 하드웨어 레벨 3 대 지침
===========================

pccx v002는 RTL / NPU 메모리 컨트롤러 / 드라이버 계층에 다음 세 가지
기법을 우선 반영한다.

.. mermaid::

   flowchart TB
     KV["토큰 당 40 KB<br/>KV 엔트리"]
     Q["① <b>KV Quantization</b><br/>FP16 → INT8 / INT4<br/>×2 ~ ×4 대역폭 절감"]
     E["② <b>Compression / Eviction</b><br/>Attention Sink + Local Window<br/>+ Google Turbo Quant"]
     C["③ <b>Size Hard Cap</b><br/>Ring Buffer + 펌웨어 상한"]
     OUT[("실효 Bandwidth<br/>관리 가능 수준")]
     KV --> Q --> E --> C --> OUT

2.1 KV 캐시 양자화 (Quantization)
---------------------------------

- **대상**: 기존 FP16 로 저장하던 KV 엔트리를 **INT8** 또는 **INT4** 로
  양자화하여 DRAM 에 적재.
- **효과**:

  - FP16 → INT8: 2 배, FP16 → INT4: 4 배의 대역폭·용량 절감.
  - W4A8 연산 파이프라인과 포맷이 일치하여 dequantize 경로 재사용 가능.

- **구현 경로**:

  - ``MEMCPY from_device=1, to_device=1`` 명령어로 KV 쓰기 경로에 in-line
    양자화 삽입 (activation-scale 공유).
  - Per-head / per-channel scale 은 Constant Cache 에 MEMSET 으로 프리셋.

2.2 압축 및 폐기 (Compression / Eviction)
-----------------------------------------

- **Attention Sink** (프롬프트 선두 몇 개 토큰) + **Local Window** (최근
  대화) 만 남기고 중간 토큰은 주기적으로 **폐기(eviction)** 하는 정책을
  드라이버 레벨에서 관리.
- Google **Turbo Quant** 류 실시간 재양자화와 결합 시, KV의 유효 크기를
  추가로 축소할 수 있다.
- Eviction 단위는 드라이버의 KV ring 인덱스 갱신으로 표현되며, 하드웨어는
  "어느 인덱스까지 유효한가"만 확인하고 실제 폐기 없이 논리적 삭제로 처리한다.

2.3 최대 크기 하드 캡 (Maximum Size Limit)
------------------------------------------

- 드라이버 초기화 시 **KV ring buffer 의 최대 용량** 을 하드코딩 — 예:
  ``KV_MAX_TOKENS = 8192``.
- 한계 초과 시 가장 오래된 엔트리를 eviction 정책에 따라 덮어씀.
- 목적:

  - 보드 가용 RAM(≲ 4 GB) 안에서 OOM 을 원천 차단.
  - 대역폭 사용량을 사전에 예측 가능하게 고정.

3. 명령어 매핑
==============

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - 기법
     - 주 명령어
     - 비고
   * - KV 양자화
     - ``MEMCPY``, ``CVO_SCALE``
     - dest/src 경로에 dequantize / requantize 조합.
   * - Eviction
     - 드라이버 전용
     - ``pccx_kv_evict(handle, upto_idx)`` — 하드웨어 상태 무관.
   * - 크기 제한
     - 드라이버 전용
     - ``pccx_kv_init(handle, max_tokens)`` — Ring buffer base/size 초기화.

4. 성능 영향 요약
=================

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - 시나리오
     - 대역폭 압박
     - MAC 활용도
     - 비고
   * - FP16 KV, 32 K
     - **극심**
     - ~10 %
     - 메모리 장벽 지배
   * - INT8 KV, 32 K
     - 중간
     - ~35 %
     - 기본 권장 설정
   * - INT4 KV + Eviction, 32 K
     - 완화
     - ~70 %
     - Attention Sink + Window 정책과 결합 시 달성
   * - INT4 KV + Turbo Quant, 32 K
     - 완화
     - **~85 %+**
     - 추가 압축으로 cold 경로까지 가속

5. 열린 과제
=============

- **정확도 영향 측정**: INT4 KV의 task-level 정확도 편차를 Gemma 3N
  eval suite를 통해 추적해야 한다.
- **Eviction 정책의 모델 의존성**: Attention Sink 수 / 윈도우 크기는
  모델 고유 튜닝 값이며, 드라이버 설정 API 로 노출 필요.
- **동적 재양자화 레이턴시**: Turbo Quant 류의 주기적 재양자화가 추가
  될 경우, ``CVO_SCALE`` 경로의 스케줄링 슬롯 확보가 과제.

관련 드라이버 API 는 :doc:`../Drivers/api` 의 KV 관리 섹션 참조.
