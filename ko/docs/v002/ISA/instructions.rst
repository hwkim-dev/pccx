==========================
명령어 상세 인코딩
==========================

각 명령어는 ``opcode[3:0]`` 이후 60-bit 본체(body) 로 구성됩니다.
본 페이지는 오피코드별로 body 레이아웃과 각 필드의 의미를 기술합니다.

1. GEMV / GEMM (opcode = 0x0 / 0x1)
====================================

GEMV 와 GEMM 은 동일한 본체 레이아웃을 공유합니다.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - 비트
     - 폭
     - 필드
     - 설명
   * - [59:43]
     - 17
     - ``dest_reg``
     - 결과를 저장할 L2 주소.
   * - [42:26]
     - 17
     - ``src_addr``
     - 액티베이션 소스 L2 주소.
   * - [25:20]
     - 6
     - ``flags``
     - :ref:`gemm-flags` 참조.
   * - [19:14]
     - 6
     - ``size_ptr_addr``
     - Constant Cache 의 size 엔트리 인덱스.
   * - [13:8]
     - 6
     - ``shape_ptr_addr``
     - Constant Cache 의 shape 엔트리 인덱스.
   * - [7:3]
     - 5
     - ``parallel_lane``
     - 사용할 코어 레인 수 (0 = 전체).
   * - [2:0]
     - 3
     - reserved
     - 0 으로 채움.

.. _gemm-flags:

1.1 Flags 필드 (6-bit)
----------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - 비트
     - 이름
     - 설명
   * - [5]
     - ``findemax``
     - 출력 정규화를 위해 e_max 레지스터 갱신 (Softmax 용).
   * - [4]
     - ``accm``
     - dest 위치에 누적 (기본: overwrite).
   * - [3]
     - ``w_scale``
     - MAC 중 weight scale factor 적용.
   * - [2:0]
     - reserved
     - 0.

2. MEMCPY (opcode = 0x2)
========================

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - 비트
     - 폭
     - 필드
     - 설명
   * - [59]
     - 1
     - ``from_device``
     - 0 = NPU, 1 = Host.
   * - [58]
     - 1
     - ``to_device``
     - 0 = NPU, 1 = Host.
   * - [57:41]
     - 17
     - ``dest_addr``
     - 목적지 주소.
   * - [40:24]
     - 17
     - ``src_addr``
     - 소스 주소.
   * - [23:7]
     - 17
     - ``aux_addr``
     - 보조 주소 (호스트 DDR 오프셋 등).
   * - [6:1]
     - 6
     - ``shape_ptr_addr``
     - 전송 shape 포인터.
   * - [0]
     - 1
     - ``async``
     - 0 = 동기 완료 대기, 1 = 비동기 실행.

3. MEMSET (opcode = 0x3)
========================

Constant Cache 의 shape / size / scale 레지스터 등을 초기화합니다.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - 비트
     - 폭
     - 필드
     - 설명
   * - [59:58]
     - 2
     - ``dest_cache``
     - 0 = fmap_shape, 1 = weight_shape.
   * - [57:52]
     - 6
     - ``dest_addr``
     - Constant Cache 인덱스.
   * - [51:36]
     - 16
     - ``a_value``
     - 첫 번째 16-bit 값.
   * - [35:20]
     - 16
     - ``b_value``
     - 두 번째 16-bit 값.
   * - [19:4]
     - 16
     - ``c_value``
     - 세 번째 16-bit 값.
   * - [3:0]
     - 4
     - reserved
     - 0.

.. tip::

   MEMSET 명령어 하나로 (M, N, K) 튜플을 한 번에 기록할 수 있도록
   a/b/c 세 슬롯을 제공합니다.

4. CVO (opcode = 0x4)
=====================

Complex Vector Operation — SFU 에 전달되는 명령어입니다.

.. list-table::
   :header-rows: 1
   :widths: 12 10 20 58

   * - 비트
     - 폭
     - 필드
     - 설명
   * - [59:56]
     - 4
     - ``cvo_func``
     - 함수 코드 (아래 표 참조).
   * - [55:39]
     - 17
     - ``src_addr``
     - 입력 벡터 L2 주소.
   * - [38:22]
     - 17
     - ``dst_addr``
     - 결과 L2 주소.
   * - [21:6]
     - 16
     - ``length``
     - 처리할 원소 수.
   * - [5:1]
     - 5
     - ``flags``
     - :ref:`cvo-flags` 참조.
   * - [0]
     - 1
     - ``async``
     - 0 = 동기, 1 = 비동기.

4.1 CVO 함수 코드
------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - 함수
     - 코드
     - 설명
   * - ``CVO_EXP``
     - ``4'h0``
     - `exp(x)` — softmax 에서 사용.
   * - ``CVO_SQRT``
     - ``4'h1``
     - `sqrt(x)` — RMSNorm.
   * - ``CVO_GELU``
     - ``4'h2``
     - `gelu(x)` — FFN 비선형.
   * - ``CVO_SIN``
     - ``4'h3``
     - `sin(x)` — RoPE.
   * - ``CVO_COS``
     - ``4'h4``
     - `cos(x)` — RoPE.
   * - ``CVO_REDUCE_SUM``
     - ``4'h5``
     - 벡터 원소의 합.
   * - ``CVO_SCALE``
     - ``4'h6``
     - 스칼라 × 벡터.
   * - ``CVO_RECIP``
     - ``4'h7``
     - `1/x`.
   * - ``4'h8`` – ``4'hF``
     - —
     - reserved (향후 확장).

.. _cvo-flags:

4.2 CVO Flags (5-bit)
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - 비트
     - 이름
     - 설명
   * - [4]
     - ``sub_emax``
     - 연산 전 e_max 뺄셈 (softmax 안정화).
   * - [3]
     - ``recip_scale``
     - 스칼라의 역수 사용 (곱셈 대신 나눗셈 효과).
   * - [2]
     - ``accm``
     - dst 에 누적.
   * - [1:0]
     - reserved
     - 0.

5. 요약
=======

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - 오피코드
     - 핵심 활용 시나리오
   * - **GEMM**
     - Prefill. Q/K/V projection, FFN up/down projection.
   * - **GEMV**
     - Decoding. Autoregressive step 의 모든 projection.
   * - **CVO**
     - Softmax, RMSNorm, RoPE, GELU.
   * - **MEMCPY**
     - Host ↔ Device 가중치 로딩, KV 캐시 업데이트, 토큰 출력.
   * - **MEMSET**
     - 레이어 시작 시 shape/size 포인터 프리셋, scale factor 주입.
