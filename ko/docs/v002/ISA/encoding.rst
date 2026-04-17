=====================
명령어 인코딩
=====================

1. 포맷 개요
=============

pccx v002 의 모든 명령어는 **64 bit 고정 길이** 이며, 다음과 같은 최상위
구조를 갖습니다.

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - 비트
     - 필드
     - 설명
   * - ``[63:60]``
     - opcode
     - 4-bit. 최대 16 종, 현재 5 종 사용.
   * - ``[59:0]``
     - instruction body
     - 60-bit. 오피코드별 세부 레이아웃 (§ 3).

2. 오피코드 테이블
==================

.. list-table::
   :header-rows: 1
   :widths: 15 15 30 40

   * - Opcode
     - Mnemonic
     - 기능
     - 주요 필드
   * - ``4'h0``
     - **GEMV**
     - 행렬 × 벡터 연산
     - dest_reg, src_addr, flags, shape_ptr, size_ptr, parallel_lane
   * - ``4'h1``
     - **GEMM**
     - 행렬 × 행렬 연산
     - GEMV 와 동일 레이아웃
   * - ``4'h2``
     - **MEMCPY**
     - 디바이스 간 데이터 이동
     - from_device, to_device, dest_addr, src_addr, aux_addr, shape_ptr, async
   * - ``4'h3``
     - **MEMSET**
     - Constant Cache 값 설정
     - dest_cache, dest_addr, a/b/c_value
   * - ``4'h4``
     - **CVO**
     - Complex Vector Op (SFU)
     - cvo_func, src_addr, dst_addr, length, flags, async
   * - ``4'h5`` – ``4'hF``
     - *reserved*
     - —
     - 향후 확장

3. 디코딩 플로우
================

명령어는 AXI-Lite 의 CMD_IN FIFO 로 호스트가 write 하며, 다음 경로로
디코딩됩니다.

.. mermaid::

   flowchart TB
     CMD[[AXI-Lite<br/>CMD_IN FIFO]] --> DEC["Decoder<br/>(ctrl_npu_decode)<br/>opcode[63:60] 분기"]
     DEC -->|제어 μop<br/>메모리 μop<br/>CVO μop| DISP["Dispatcher<br/>(ctrl_dispatcher)"]
     GS[[Global Scheduler<br/>의존성 / 해저드 체크]] -.-> DISP
     DISP --> GEMM[GEMM ctrl]
     DISP --> GEMV[GEMV ctrl]
     DISP --> MC[MEMCTRL<br/>ACP / NPU]
     DISP --> MS[MEMSET<br/>Constant]
     DISP --> CVO[CVO ctrl]

4. μop 분해
============

각 오피코드는 디스패처 내부에서 다음 μop 들로 분해됩니다.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - μop 타입
     - 구성 요소
   * - ``gemm_control_uop_t``
     - flags (6-bit) + size_ptr_addr (6-bit) + parallel_lane (5-bit)
   * - ``GEMV_control_uop_t``
     - 동일 레이아웃
   * - ``memory_control_uop_t`` (49-bit)
     - data_route (8-bit) + dest_addr + src_addr + shape_ptr + async
   * - ``memory_set_uop_t``
     - dest_cache (2-bit) + dest_addr + a/b/c_value (16-bit × 3)
   * - ``cvo_control_uop_t``
     - cvo_func (4-bit) + src_addr + dst_addr + length + flags + async

5. 메모리 라우팅 인코딩
========================

MEMCPY 의 `from_device` + `to_device` 조합은 Control Unit 내부에서 8-bit
route enum (``data_route_e``) 으로 확장됩니다.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Route
     - Encoding
     - 경로
   * - ``from_host_to_L2``
     - ``8'h01``
     - 호스트 DDR4 → L2 Cache
   * - ``from_L2_to_host``
     - ``8'h10``
     - L2 Cache → 호스트 DDR4
   * - ``from_L2_to_L1_GEMM``
     - ``8'h12``
     - L2 → GEMM L1
   * - ``from_L2_to_L1_GEMV``
     - ``8'h13``
     - L2 → GEMV L1
   * - ``from_L2_to_CVO``
     - ``8'h14``
     - L2 → SFU
   * - ``from_GEMM_res_to_L2``
     - ``8'h21``
     - GEMM 결과 → L2
   * - ``from_GEMV_res_to_L2``
     - ``8'h31``
     - GEMV 결과 → L2
   * - ``from_CVO_res_to_L2``
     - ``8'h41``
     - SFU 결과 → L2

6. 포인터 / 파라미터 레지스터
=============================

ISA 는 6-bit pointer 를 통해 소형 Constant Cache 항목을 참조합니다.

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - 포인터
     - 비트폭
     - 저장 내용
   * - ``shape_ptr_addr``
     - 6-bit
     - 텐서의 (M, N, K) shape 메타데이터
   * - ``size_ptr_addr``
     - 6-bit
     - 타일 크기, 루프 상한 등
   * - ``ptr_addr_t`` (공통)
     - 6-bit
     - 64 엔트리 Constant Cache 인덱스

포인터 항목은 **MEMSET** 명령어로 사전 초기화됩니다.
(:doc:`dataflow` 의 MEMSET 섹션 참조)

7. 어드레스 공간
=================

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - 필드
     - 비트폭
     - 어드레스 공간
   * - ``dest_addr`` / ``src_addr``
     - 17-bit
     - 128 K 엔트리 (L2 Cache 블록 인덱스 기준)
   * - ``aux_addr``
     - 17-bit
     - MEMCPY 의 보조 주소 (예: host DDR 오프셋)

엔트리 크기는 디바이스 레이어에서 정의되며 (KV260 기준 128-bit word),
17-bit × 16 byte = **2 MB** 의 선형 L2 주소 공간을 표현합니다.
