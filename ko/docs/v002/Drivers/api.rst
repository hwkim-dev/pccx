==================
C API 개요
==================

본 페이지는 v002 드라이버의 C API 설계 개요를 기술합니다. API 는 세 개의
계층으로 구성됩니다.

1. **Low-level HAL** — AXI-Lite / AXI-HP 레지스터에 직접 접근.
2. **ISA Encoder** — 64-bit 명령어 조립 도우미.
3. **High-level Ops** — GEMM/GEMV/CVO/MEMCPY 를 호출하는 편의 API.

1. 초기화 & 라이프사이클
=========================

.. code-block:: c

   typedef struct pccx_ctx pccx_ctx_t;

   // 디바이스 초기화
   int  pccx_open(pccx_ctx_t **ctx, const char *device_path);

   // 디바이스 종료
   void pccx_close(pccx_ctx_t *ctx);

   // 하드웨어 레지스터 리셋
   int  pccx_reset(pccx_ctx_t *ctx);

2. 명령어 인코딩
=================

ISA 의 각 오피코드에 대응하는 인코더 헬퍼가 제공됩니다.

.. code-block:: c

   // GEMM / GEMV
   uint64_t pccx_encode_gemm(
       uint32_t dest_reg,
       uint32_t src_addr,
       uint8_t  flags,
       uint8_t  size_ptr,
       uint8_t  shape_ptr,
       uint8_t  parallel_lane);

   uint64_t pccx_encode_gemv( /* 동일 시그니처 */ );

   // MEMCPY
   uint64_t pccx_encode_memcpy(
       bool     from_host,
       bool     to_host,
       uint32_t dest_addr,
       uint32_t src_addr,
       uint32_t aux_addr,
       uint8_t  shape_ptr,
       bool     async);

   // MEMSET
   uint64_t pccx_encode_memset(
       uint8_t  dest_cache,
       uint8_t  dest_addr,
       uint16_t a,
       uint16_t b,
       uint16_t c);

   // CVO
   uint64_t pccx_encode_cvo(
       uint8_t  func,       // CVO_EXP, CVO_GELU, ...
       uint32_t src_addr,
       uint32_t dst_addr,
       uint16_t length,
       uint8_t  flags,
       bool     async);

3. 디스패치 & 동기화
=====================

.. code-block:: c

   // 단일 명령어 발행 (CMD_IN FIFO 에 push)
   int pccx_dispatch(pccx_ctx_t *ctx, uint64_t instr);

   // 배치 발행
   int pccx_dispatch_batch(pccx_ctx_t *ctx,
                           const uint64_t *instrs,
                           size_t n);

   // 비동기 명령어 완료 대기 (폴링)
   int pccx_wait_idle(pccx_ctx_t *ctx, uint32_t timeout_ms);

   // STAT_OUT 레지스터 조회
   uint32_t pccx_read_status(pccx_ctx_t *ctx);

4. 고수준 도우미
=================

빈번한 시퀀스(예: 레이어 시작 시 shape/size 프리셋) 는 헬퍼로 제공됩니다.

.. code-block:: c

   // Constant Cache 의 shape 엔트리 프리셋
   int pccx_set_shape(pccx_ctx_t *ctx,
                      uint8_t idx,
                      uint16_t M, uint16_t N, uint16_t K);

   // Host → L2 가중치 로딩
   int pccx_load_weights(pccx_ctx_t *ctx,
                         uint32_t l2_dest_addr,
                         const void *host_src,
                         size_t nbytes);

   // L2 → Host 결과 회수
   int pccx_fetch_result(pccx_ctx_t *ctx,
                         void *host_dest,
                         uint32_t l2_src_addr,
                         size_t nbytes);

5. 예제: Transformer FFN 블록
==============================

FFN 블록 (`y = W_down · GELU(W_up · x)`) 의 간단한 실행 예시:

.. code-block:: c

   // 1) shape 프리셋
   pccx_set_shape(ctx, /*idx*/ 0, M=1, N=4096, K=4096);   // W_up
   pccx_set_shape(ctx, /*idx*/ 1, M=1, N=4096, K=4096);   // W_down

   // 2) W_up · x  (GEMV)
   uint64_t i0 = pccx_encode_gemv(
       /*dest*/  0x0100, /*src*/ 0x0000,
       /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 0,
       /*lane*/  0);
   pccx_dispatch(ctx, i0);

   // 3) GELU
   uint64_t i1 = pccx_encode_cvo(
       CVO_GELU,
       /*src*/  0x0100, /*dst*/ 0x0200,
       /*len*/  4096, /*flags*/ 0, /*async*/ false);
   pccx_dispatch(ctx, i1);

   // 4) W_down · activation (GEMV)
   uint64_t i2 = pccx_encode_gemv(
       /*dest*/  0x0300, /*src*/ 0x0200,
       /*flags*/ 0, /*size_ptr*/ 0, /*shape_ptr*/ 1,
       /*lane*/  0);
   pccx_dispatch(ctx, i2);

   pccx_wait_idle(ctx, /*timeout_ms*/ 100);

6. 에러 처리
=============

모든 드라이버 함수는 ``0`` 성공, 음수 errno 호환 에러 코드를 반환합니다.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 에러
     - 의미
   * - ``-EBUSY``
     - CMD_IN FIFO full.
   * - ``-ETIMEDOUT``
     - ``pccx_wait_idle`` 타임아웃.
   * - ``-EINVAL``
     - 인코딩 실패 (예: 필드 오버플로우).
   * - ``-EIO``
     - AXI 전송 실패.

.. note::

   드라이버 구현은 추후 ``codes/v002/sw/`` 경로에 포함될 예정이며,
   현재 문서는 API 계약을 사전 정의하는 단계입니다.
