======================
메모리 계층
======================

pccx v002의 메모리 서브시스템은 **호스트 DDR4 → Weight Buffer / L2 Cache →
L1 / Constant Cache → PE 레지스터**\ 의 4단 계층으로 구성된다.
각 레벨은 **대역폭 매칭**\ 과 **데이터 기아(starvation) 방지**\ 를 목표로
설계되었다.

.. mermaid::

   flowchart TB
     DDR[("Host DDR4<br/>19.2 GB/s")]
     subgraph ext["외부 250 MHz"]
       HP["AXI HP2 / HP3<br/>256 bit/clk × 2"]
     end
     subgraph core["내부 400 MHz"]
       WB["Weight Buffer<br/>URAM FIFO"]
       L2[("L2 Cache<br/>URAM ~1.75 MB")]
       L1["L1 Cache<br/>코어 로컬 BRAM"]
       CC["Constant Cache<br/>BRAM"]
       L0["L0 Accumulator<br/>DSP48E2 P-reg"]
     end
     DDR --> HP
     HP -->|weights| WB
     HP -->|activations| L2
     WB --> L1
     L2 --> L1
     L2 --> CC
     L1 --> L0

1. 계층 구조
=============

.. list-table::
   :header-rows: 1
   :widths: 18 14 18 20 30

   * - 레벨
     - 매체
     - 용량 (KV260)
     - 대역폭 (peak)
     - 용도
   * - **L0 레지스터**
     - FF
     - DSP48E2 내부
     - 48 bit / clk / DSP
     - 누적기 (accumulator)
   * - **L1 Cache**
     - BRAM
     - 코어당 수 KB
     - 32 element / clk
     - GEMV 액티베이션/결과 스테이징
   * - **Constant Cache**
     - BRAM
     - 코어당 수 KB
     - 16 bit × N / clk
     - ISA 의 shape/size 포인터, scale factor
   * - **L2 Cache**
     - URAM
     - **1.75 MB** (114,688 × 128-bit; 64 URAM 중 ~50 개 사용)
     - 256 bit × 2 / clk (양측 슬라이스)
     - 액티베이션, KV 캐시, 중간 결과
   * - **Weight Buffer**
     - URAM (FIFO)
     - 4 × 64 KB (HP 포트 당 4096 깊이)
     - HP 포트 당 128 bit/clk @ 250 MHz
     - INT4 가중치 스트림
   * - **Host DDR4**
     - 외부 DRAM
     - 4 × 512 Mb × 16-bit
     - **19.2 GB/s**
     - 모델 가중치, 추론 입력, 토큰 출력

2. 대역폭 매칭 분석
===================

2.1 Weight 경로
---------------

**목표**: GEMM 시스톨릭 어레이의 매 클럭 MAC 요구량을 HP 포트의 대역폭이
충족해야 한다.

- Systolic Array: **32 × 32 = 1,024 DSP** @ 400 MHz (단일 격자, cascade
  가 16 행에서 끊겨 32 × 16 서브체인 2 개로 나뉨).
- W4A8 듀얼 채널 패킹으로 **1 DSP = 2 MAC**, 따라서 2,048 MAC/clk.
- 가중치 요구량: 2,048 × 4 bit = **8,192 bit/clk @ 400 MHz**.
- 공급량: HP0 + HP1 이 **2 × 128 bit/clk @ 250 MHz** (= raw 64 Gbit/s)
  를 전달, CDC FIFO 를 거쳐 400 MHz 도메인 기준 **~160 bit/clk** 상당.

위 차이는 **Weight 재사용(Weight Stationary)** 전략으로 해소된다.
GEMM 시스톨릭 어레이는 가중치를 프리로드 후 수백~수천 사이클 동안 재사용하며,
Weight Buffer 는 프리페치만 수행합니다. 자세한 재사용 패턴은
:doc:`gemm_core` 참조.

2.2 Activation 경로
-------------------

**목표**: L2 Cache가 GEMM·GEMV·SFU의 동시 액티베이션 접근 요구를 충족해야
한다.

- L2 Cache 포트: **듀얼 포트 URAM** — Port A 는 ACP DMA, Port B 는
  NPU 컴퓨트 전용. 두 포트 모두 매 클럭 128-bit 폭.
- 최대 소비량: 4 개 GEMV 코어 × 32 INT8 원소 / clk = 총 128 INT8
  원소 / clk. 한 번의 128-bit URAM 읽기로 16 INT8 원소를 공급하지만,
  GEMV 는 동일 액티베이션을 4 개 코어로 브로드캐스트하므로 단일
  포트로 충분.

2.3 Host ↔ Device 경로
----------------------

**목표**: 프리필 단계에서 모델 가중치를 로드하고, 디코딩 단계에서 KV 캐시
업데이트와 토큰 출력을 지원해야 한다.

- AXI ACP 포트 경유 DMA. 호스트 DDR4 의 19.2 GB/s 대역폭이 상한.
- 디코딩 단계 토큰 출력 주기가 초당 20 회 수준이므로, 호스트 ↔ 디바이스
  트래픽은 주로 KV 캐시와 새 토큰 업데이트에 사용된다.

3. 캐시 운용 정책
==================

3.1 L2 Cache: 중앙 공유 버퍼
-----------------------------

L2 Cache는 **소프트웨어 관리형 스크래치패드**\ 로 동작한다. 하드웨어
자동 대체(replacement) 정책을 두지 않고, 명령어 레벨에서 주소를 명시
(``MEMCPY dest_addr``, ``GEMM src_addr``)한다. 이는 다음의 이점을 제공한다:

- 예측 가능한 레이턴시 (태그 매칭·미스 처리 없음).
- 컴파일러가 데이터 배치를 정적으로 결정하여 인터커넥트 충돌 회피.

3.2 Constant Cache: ISA 포인터 백업
------------------------------------

ISA 는 6-bit ``shape_ptr_addr``, ``size_ptr_addr`` 를 통해 shape/size 메타데이터를
참조한다. 이 포인터들은 Constant Cache의 64 엔트리에서 인덱싱되며,
MEMSET 명령어로 사전 설정된다. 자세한 인코딩은
:doc:`../ISA/instructions` 참조.

3.3 Weight Buffer: 스트리밍 FIFO
---------------------------------

Weight Buffer 는 순환 FIFO 로 구현되며, HP 포트 프리페치와 코어 소비 간의
타이밍 차이를 완충합니다. GEMM 시의 Weight Stationary 재사용과 GEMV 시의
Weight Streaming 재사용을 모두 지원하기 위해 뱅크 레벨 인터리빙 구조를
가진다.

4. 데이터 기아 방지
===================

파이프라인 스톨을 방지하기 위해 다음과 같은 **더블 버퍼링(double buffering)**
기법이 적용된다.

- **GEMM 액티베이션**: L2 → PE 간 ping-pong 버퍼.
- **GEMV 액티베이션**: L1 Cache 의 bank split 을 통한 read/write 동시 수행.
- **Weight**: Weight Buffer 의 ping-pong FIFO.

이상적인 조건에서 모든 컴퓨트 코어는 **100% busy rate**\ 를 유지하도록
설계되었으며, 실제 달성률은 Implementation 섹션에서 합성 후 측정 결과로
갱신된다.
