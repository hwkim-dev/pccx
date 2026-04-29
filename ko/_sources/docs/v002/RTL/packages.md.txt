# 컴파일 우선순위 패키지

v002 RTL은 패키지와 헤더를 컴파일 우선순위 계층(`Constants/compilePriority_Order/`)으로
분리 관리한다. 각 계층은 이전 계층에만 의존하므로 `xvlog` 또는 Vivado 컴파일러가
전방 참조 없이 순서대로 처리할 수 있다. `hw/vivado/filelist.f`가 이 순서를 정식으로
기록한다.

## 컴파일 우선순위

컴파일 단계는 A → B → C → D 순으로 진행된다.

**A — 순수 `` `define `` 헤더 (`A_const_svh/`)**: `xvlog -i` 플래그로 인클루드 경로에
추가될 뿐 직접 컴파일되지 않는다.

- `NUMBERS.svh` — 기본 비트 폭 정의. `` `N_SIZEOF_INT4 = 4 ``, `` `N_BF16_SIZE = 16 ``,
  `` `N_FP32_SIZE = 32 ``.
- `npu_arch.svh` — NPU 아키텍처 매크로. 포트 선언과 `generate` 범위에서 `localparam`
  대신 `` `define ``이 필요한 값들을 보유한다. 주요 상수: `` `ARRAY_SIZE_H = 32 ``,
  `` `ARRAY_SIZE_V = 32 ``, `` `ISA_WIDTH = 64 ``, `` `ISA_BODY_WIDTH = 60 ``,
  `` `SYSTOLIC_TOTAL_LATENCY = 64 ``, `` `FMAP_CACHE_DEPTH = 2048 ``,
  `` `FIXED_MANT_WIDTH = 27 ``.
- `kv260_device.svh` — Kria KV260 물리 하드웨어 상수. HP 포트 수 4, HP 단일 폭
  128비트, DSP48E2 A/B/P 포트 폭 30/18/48비트, XPM FIFO 깊이 512/16.
- `GLOBAL_CONST.svh` — **폐기 예정 shim.** `NUMBERS.svh` + `kv260_device.svh` +
  `npu_arch.svh`를 순서대로 re-include하고 레거시 별칭(`HP_PORT_MAX_WIDTH`,
  `DSP48E2_POUT_SIZE` 등)을 추가한다. 신규 코드는 이 파일 대신 각 출처 헤더를 직접
  include해야 한다.
- `DEVICE_INFO.svh` — **폐기 예정 shim.** `kv260_device.svh`를 re-include하고 레거시
  별칭(`DEVICE_HP_SINGLE_LANE_MAX_IN_BIT`, `DEVICE_HP_CNT`)을 제공한다. 신규 코드에서
  사용 금지.

**B — `device_pkg.sv` (`B_device_pkg/`)**: A 헤더에 의존. 알고리즘 수준의 타입 선택을
담는 첫 번째 SystemVerilog 패키지.

**C — `dtype_pkg.sv`, `mem_pkg.sv` (`C_type_pkg/`)**: B에 의존. 수치 타입 상수와
메모리 아키텍처 파라미터를 각각 분리한다.

**D — `vec_core_pkg.sv` (`D_pipeline_pkg/`)**: A + B + C에 의존. Vector Core 설정
구조체와 기본값을 정의한다.

## 핵심 패키지

**`device_pkg`** (`B_device_pkg/device_pkg.sv`)
피처맵(activation) 포트 정밀도를 BF16(16비트), 내부 누산 정밀도를 FP32(32비트)로
고정하고, 파이프라인 인스턴스 수를 `VecPipelineCnt = 4`, `MatPipelineCnt = 1`로
선언한다. 모든 하위 패키지는 이 값을 참조하므로, 아키텍처 변경 시 이 파일이 첫 번째
수정 지점이 된다.

```{literalinclude} ../../../../codes/v002/hw/rtl/Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
:language: systemverilog
:caption: Constants/compilePriority_Order/B_device_pkg/device_pkg.sv
:start-at: package device_pkg;
:end-before: endpackage
```

**`dtype_pkg`** (`C_type_pkg/dtype_pkg.sv`)
BF16(`Bf16Width = 16`, `Bf16ExpWidth = 8`, `Bf16MantWidth = 7`), 고정소수점 가수 폭
`FixedMantWidth = 27`, INT4(`Int4Width = 4`), INT8(`Int8Width = 8`), FP32(`Fp32Width =
32`), DSP48E2 P-레지스터 폭 `DspPWidth = 48`을 `localparam`으로 노출한다. 의미론적
단위 없이 순수 수치만 보유하므로 합성 타겟이 바뀌어도 이 파일만 수정하면 된다.

**`mem_pkg`** (`C_type_pkg/mem_pkg.sv`)
`device_pkg`와 `kv260_device.svh`에서 유도되는 메모리 파라미터를 집약한다.
`HpPortCnt = 4`, `HpSingleWidthBit = 128`, `HpTotalWidthBit = 512`,
`HpSingleWeightCnt = 32`, `FmapL2CacheOutCnt = 32`(= `ARRAY_SIZE_H`),
`FmapCacheDepth = 2048`, `XpmFifoDepth = 512`. 매직 넘버 없이 모든 값이 상위
헤더에서 파생된다.

**`vec_core_pkg`** (`D_pipeline_pkg/vec_core_pkg.sv`)
Vector Core 토폴로지를 서술하는 `vec_cfg_t` 구조체(packed struct)와 KV260 타겟 기본값
`VecCoreDefaultCfg`를 정의한다. `GemvBatch = 512`, `GemvCycle = 512`,
`GemvLineCnt = 32`. 레거시 타입 별칭 `gemv_cfg_t`는 마이그레이션 기간 동안 유지된다.

## 인터페이스 헤더

**`npu_interfaces.svh`** (`NPU_Controller/npu_interfaces.svh`)
`GLOBAL_CONST.svh`를 include한 뒤 두 개의 SystemVerilog 인터페이스를 정의한다.

`axis_if #(DATA_WIDTH = 128)` — AXI4-Stream 버스. `slave` modport는 `tdata`,
`tvalid`, `tlast`, `tkeep`를 입력으로, `tready`를 출력으로 받는다. `master` modport는
방향이 반전된다.

`axil_if #(ADDR_W = 12, DATA_W = 64)` — AXI4-Lite 제어 버스. 클록/리셋(`clk`,
`rst_n`)을 인터페이스 포트로 받는다. `slave` modport는 AW/W/AR 채널을 입력으로,
B/R 채널을 출력으로 구분한다.

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: NPU_Controller/npu_interfaces.svh
:start-at: interface axis_if
:end-before: `endif  // NPU_INTERFACES_SVH
```

**`GEMM_Array.svh`** (`MAT_CORE/GEMM_Array.svh`)
`npu_arch.svh`를 re-include하는 호환성 shim이다. `ARRAY_SIZE_H`, `ARRAY_SIZE_V`를
`npu_arch.svh`에서 단일 원천화하여 재정의 경고를 막는다. `MINIMUM_DELAY_LINE_LENGTH =
1`, `gemm_instruction_dispatcher_CLOCK_CONSUMPTION = 1`은 MAT_CORE에만 적용되는
추가 상수다. 신규 MAT_CORE 모듈은 `npu_arch.svh`를 직접 include해야 한다.

## 사용 위치

아래 표는 소스에서 직접 확인된 `import` 구문과 `` `include `` 를 기준으로
각 RTL 모듈이 의존하는 패키지/헤더를 정리한다.

```{list-table} 컴퓨트 코어별 패키지 의존성
:name: tbl-pkg-usage
:header-rows: 1
:widths: 28 13 13 13 16 13 14

* - 모듈 (코어)
  - `device_pkg`
  - `dtype_pkg`
  - `mem_pkg`
  - `vec_core_pkg`
  - `isa_pkg`
  - 헤더 (include)
* - `GEMM_systolic_top` (MAT_CORE)
  - —
  - —
  - —
  - —
  - —
  - `GEMM_Array.svh`, `GLOBAL_CONST.svh`
* - `GEMV_top` (VEC_CORE)
  - —
  - o
  - —
  - o
  - —
  - `GLOBAL_CONST.svh`
* - `CVO_top` (CVO_CORE)
  - —
  - —
  - —
  - —
  - o
  - `GLOBAL_CONST.svh`
* - `ctrl_npu_frontend` (Controller)
  - —
  - —
  - —
  - —
  - —
  - `npu_interfaces.svh`, `GEMM_Array.svh`
* - `AXIL_CMD_IN` (ctrl_npu_frontend 하위)
  - —
  - —
  - —
  - —
  - —
  - `GLOBAL_CONST.svh`
```

`o` = 소스에서 직접 확인된 import. `—` = 해당 파일에 import 없음.

`GEMM_systolic_top`은 패키지를 직접 import하지 않고 `` `define `` 헤더 매크로만 사용한다.
`GEMV_top`은 `import vec_core_pkg::*;`를 선언하며, 포트 폭에 `dtype_pkg::Bf16ExpWidth`를
참조한다. `CVO_top`은 `import isa_pkg::*;`와 `import bf16_math_pkg::*;`를 선언한다
(`bf16_math_pkg`는 라이브러리 패키지로 {doc}`library` 페이지에서 다룬다).
`ctrl_npu_dispatcher`는 현재 전체가 주석 처리된 상태이므로 표에서 제외한다.

---

```{admonition} 마지막 검증 대상
:class: note

커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
```
