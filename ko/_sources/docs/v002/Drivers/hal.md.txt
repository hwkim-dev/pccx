# HAL — AXI-Lite MMIO 계층

`uca_hal_*` 함수 집합은 공개 C API (`uca_*`, :doc:`api`)와 NPU 하드웨어
사이의 AXI-Lite MMIO 계층이다. 이 계층 위의 코드는 물리 주소나
레지스터 오프셋에 직접 접근하지 않는다.

구현은 `codes/v002/sw/driver/uCA_v1_hal.c` /  `uCA_v1_hal.h` 에
위치한다.

## HAL 위치

드라이버 스택은 두 계층으로 나뉜다.

```{list-table} 드라이버 계층 구조
:header-rows: 1
:name: tbl-driver-layers

* - 계층
  - 심볼 접두사
  - 역할
* - Public API
  - `uca_*`
  - 연산·메모리 프리미티브. 64-bit VLIW 명령어를 조립해 HAL 로 전달.
    자세한 내용은 :doc:`api` 참조.
* - HAL
  - `uca_hal_*`
  - AXI-Lite 레지스터 읽기·쓰기, 64-bit 명령어 래칭, 상태 폴링.
    KV260 베어메탈 포인터 MMIO 에 직접 의존.
```

HAL 은 `volatile uint32_t *` 파일 스코프 싱글턴 `g_mmio_base` 하나로
전체 상태를 보관한다. 컨텍스트 포인터를 사용하지 않으므로 단일 프로세스
내에서 NPU 인스턴스가 하나임을 전제한다.

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.c
:language: c
:start-at: static volatile uint32_t
:end-before: // ===| HAL Init
:caption: uCA_v1_hal.c — MMIO 기반 포인터 선언
:name: lst-hal-mmio-ptr
```

## 레지스터 맵

MMIO 기반 주소는 `UCA_MMIO_BASE_ADDR = 0xA0000000` 이다. 이 값은
Vivado 블록 디자인의 AXI-Lite 슬레이브 주소 할당과 일치해야 한다.

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.h
:language: c
:start-at: // ===| MMIO Base Address
:end-before: // ===| Status Register
:caption: uCA_v1_hal.h — 기반 주소 및 레지스터 오프셋 정의
:name: lst-hal-regmap
```

```{list-table} 레지스터 맵
:header-rows: 1
:name: tbl-hal-regmap

* - 이름
  - 오프셋
  - 접근
  - 설명
* - `UCA_REG_INSTR_LO`
  - `0x00`
  - 쓰기
  - 64-bit VLIW 명령어 하위 32비트. 먼저 기록한다.
* - `UCA_REG_INSTR_HI`
  - `0x04`
  - 쓰기
  - 64-bit VLIW 명령어 상위 32비트. 기록 시 NPU 명령어 래치가 트리거된다.
* - `UCA_REG_STATUS`
  - `0x08`
  - 읽기
  - NPU 상태 레지스터 (읽기 전용). `UCA_STAT_BUSY` / `UCA_STAT_DONE` 비트 포함.
```

64-bit 명령어는 쌍으로 기록되며, **LO 먼저, HI 나중** 순서를 지켜야
한다. HI 쓰기가 컨트롤러의 명령어 래칭을 트리거한다.

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.c
:language: c
:start-at: void uca_hal_issue_instr
:end-before: // ===| Status Polling
:caption: uCA_v1_hal.c — uca_hal_issue_instr 구현
:name: lst-hal-issue-instr
```

## CMD_IN / STAT_OUT 메커니즘

`uca_hal_issue_instr` 는 레지스터 쌍에 64-bit 명령어를 기록하여
NPU 의 CMD_IN 경로에 명령어를 제출한다. 발행 후 즉시 반환하며,
NPU 컨트롤러는 내부 파이프라인에서 독립적으로 명령어를 실행한다.

상태 레지스터 `UCA_REG_STATUS` 의 비트 필드:

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.h
:language: c
:start-at: // ===| Status Register Bit Fields
:end-before: // ===| HAL Init
:caption: uCA_v1_hal.h — 상태 비트 정의
:name: lst-hal-status-bits
```

- **`UCA_STAT_BUSY` (bit 0)** — NPU 가 명령어를 실행 중임을 나타낸다.
  이 비트가 세트된 상태에서 새 명령어를 발행하지 않는다.
- **`UCA_STAT_DONE` (bit 1)** — 마지막 연산이 정상 완료되었음을 나타낸다.

폴링은 `uca_hal_wait_idle` 이 수행한다. 베어메탈 환경이므로 하드웨어
타이머가 없으며, 현재 구현은 400 MHz 코어 기준 반복 횟수 추정치를
사용한 busy-wait 루프다.

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.c
:language: c
:start-at: int uca_hal_wait_idle
:caption: uCA_v1_hal.c — uca_hal_wait_idle 구현
:name: lst-hal-wait-idle
```

`timeout_us` 가 0 이 되면 -1 을 반환한다. 타임아웃이 발생해도 NPU 상태를
강제로 초기화하지 않으며, 상위 계층이 오류 처리를 담당한다.

## uca_init 흐름

`uca_hal_init` 은 세 가지 작업을 순서대로 수행한다.

1. `g_mmio_base` 를 `(volatile uint32_t *)UCA_MMIO_BASE_ADDR` 로 설정한다.
   KV260 베어메탈 환경에서는 물리 주소가 직접 접근 가능하다.
2. `uca_hal_read32(UCA_REG_STATUS)` 를 호출하여 상태 레지스터를 읽는다.
3. 반환값이 `0xFFFFFFFF` 이면 AXI 버스가 응답하지 않는 것으로 판단하고
   `-1` 을 반환한다. 그 외에는 `0` 을 반환한다.

```{literalinclude} ../../../../codes/v002/sw/driver/uCA_v1_hal.c
:language: c
:start-at: int uca_hal_init
:end-before: void uca_hal_deinit
:caption: uCA_v1_hal.c — uca_hal_init 구현
:name: lst-hal-init
```

`uca_hal_deinit` 은 `g_mmio_base` 를 `NULL` 로 설정한다. 이후 발생하는
`uca_hal_write32` / `uca_hal_read32` 호출은 널 포인터 역참조가 되므로,
`deinit` 이후 HAL 호출이 없도록 상위 계층이 보장해야 한다.

:::{seealso}

- 공개 API 프리미티브: :doc:`api`
- AXI-Lite 명령어 경로 아키텍처: :doc:`../Architecture/top_level`
- ISA 명령어 인코딩: :doc:`../ISA/encoding`
:::

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
:::
