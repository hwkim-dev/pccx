# 메모리 디스패치

`mem_dispatcher`는 스케줄러로부터 수신한 uop를 L2 캐시 커맨드로 변환하고,
ACP DMA 경로, NPU 버스트 경로, CVO 스트림 경로의 세 채널로 분기시킨다.
이 페이지는 디스패치 경로, uop ABI, CDC 가중치 버퍼, CVO 스트림 브리지를
다룬다.

## 디스패치 경로

스케줄러는 세 종류의 uop를 `mem_dispatcher`에 전달한다.

- `memory_control_uop_t` (`IN_LOAD_uop`) — MEMCPY 명령 디코드 결과.
  `data_dest` 필드의 `data_route_e` 값에 따라 ACP 채널 또는 NPU 채널 커맨드로
  변환된 뒤 `mem_u_operation_queue`에 적재된다.
- `memory_set_uop_t` (`IN_mem_set_uop`) — MEMSET 명령 디코드 결과.
  fmap 또는 weight shape 상수 RAM(`fmap_array_shape` / `weight_array_shape`)에
  직접 기록한다.
- `cvo_control_uop_t` (`IN_CVO_uop`) — CVO 명령 디코드 결과.
  `mem_CVO_stream_bridge`가 직접 감시하며, 디스패처의 FIFO를 거치지 않는다.

`mem_u_operation_queue`에서 커맨드가 팝되면 `mem_GLOBAL_cache`의
`IN_acp_rx_start` 또는 `IN_npu_rx_start`가 어서트되고, L2 상태 기계가
128비트 워드 단위 순차 전송을 시작한다. Port B는 CVO 브리지가 활성(`OUT_busy`)인
경우 브리지가 선점하고, 그 외에는 NPU DMA 상태 기계가 구동한다.

## uop ABI

`acp_uop_t`와 `npu_uop_t`는 스케줄러와 메모리 서브시스템 사이의 전송 ABI를
정의하는 35비트 패킹 구조체이다. 두 타입은 필드 레이아웃이 동일하다.

```{table} acp_uop_t / npu_uop_t 필드 (35비트)
:name: tbl-uop-fields-ko

| 비트 | 폭 | 신호 | 의미 |
|---|---|---|---|
| [34] | 1 | `write_en` | 1 = L2에 쓰기, 0 = L2에서 읽기 |
| [33:17] | 17 | `base_addr` | 전송 시작 워드 주소 |
| [16:0] | 17 | `end_addr` | 전송 종료 워드 주소 (exclusive) |
```

RTL 정의:

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv
:language: systemverilog
:start-at: // ===| ACP / NPU Transfer uops (used by mem_dispatcher) |
:end-before: endpackage
```

두 FIFO 채널(`xpm_fifo_sync`, 깊이 128, 폭 35비트)이 ACP 커맨드와 NPU 커맨드를
독립적으로 버퍼링한다. `PROG_FULL_THRESH = 100`에 도달하면 `OUT_fifo_full`이
어서트되어 상위 스케줄러에 역압(backpressure)을 전달한다.

## CDC 가중치 버퍼

`mem_HP_buffer`는 PS HP0–HP3 포트에서 유입되는 가중치 스트림을
AXI 250 MHz 도메인에서 NPU 코어 400 MHz 도메인으로 교차하는 CDC FIFO 집합이다.

- HP 포트별로 `xpm_fifo_axis`(깊이 4096, 폭 128비트, BRAM) 1개씩, 총 4개.
- 슬레이브 측은 `clk_axi`(250 MHz), 마스터 측은 `clk_core`(400 MHz).
- `S_AXI_HP{0..3}_WEIGHT` → `M_CORE_HP{0..3}_WEIGHT`로 명명된
  `axis_if` 인터페이스를 사용한다.

GEMM 가중치는 HP0/HP1을, GEMV 가중치는 HP2/HP3을 통해 공급된다(CLAUDE.md §4 참고).
각 FIFO의 깊이 4096 × 128비트 = 64 KiB는 가중치 타일 한 배치를 버퍼링하기에
충분한 크기다.

## CVO 스트림 브리지

`mem_CVO_stream_bridge`는 L2 Port B의 128비트 인터페이스와 CVO 엔진의
16비트 BF16 스트림 인터페이스를 이어준다. 4상태 FSM(IDLE / READ / WRITE / DONE)으로
동작한다.

**Phase 1 — READ**: L2의 `src_addr`부터 `src_addr + ceil(length/8) - 1`까지
128비트 워드를 순차 읽고, 워드당 8개의 16비트 슬라이스로 역직렬화하여
CVO 엔진에 공급한다. URAM 읽기 레이턴시 3클럭은 3비트 시프트 레지스터
`rd_lat_pipe`로 처리한다. CVO 출력은 내부 `xpm_fifo_sync`(깊이 2048, 폭 16비트,
최대 32 KiB)에 버퍼링된다.

**Phase 2 — WRITE**: FIFO에서 16비트 원소를 8개씩 직렬화하여 128비트 워드를
구성한 뒤 L2의 `dst_addr`부터 순차 기록한다.

주소 변환: `src_addr`와 `dst_addr`는 16비트 원소 단위 주소이며, 128비트 워드
주소로 변환할 때 3비트 우시프트(`>> 3`)를 적용한다. 최대 벡터 길이는 2048
원소(16비트 기준 32 KiB)이다.

```{admonition} 마지막 검증 대상
:class: note
커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
```
