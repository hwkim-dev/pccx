# Vivado 빌드

pccx v002 NPU 코어의 Vivado 빌드 흐름을 설명한다. 빌드 스크립트는
`hw/vivado/` 아래에 위치하며, `build.sh` 가 단일 진입점이다.
구현 파일은 `hkimw/pccx-FPGA-NPU-LLM-kv260` 저장소에서 관리한다.

## 빌드 흐름

`build.sh` 는 Vivado 배치(batch) 모드 실행의 얇은 래퍼다. 인자에 따라
네 가지 단계를 선택적으로 실행한다.

```{code-block} bash
./hw/vivado/build.sh project   # 프로젝트 생성만
./hw/vivado/build.sh synth     # 프로젝트 생성 + OOC 합성
./hw/vivado/build.sh impl      # 전체 구현 + 비트스트림 생성
./hw/vivado/build.sh clean     # build/ 디렉터리 삭제
```

스크립트는 `PATH` 에서 `vivado` 를 먼저 탐색하고, 없으면
`/tools/Xilinx/2025.2`, `2024.1`, `2023.2` 순으로 폴백한다.
Vivado 2023.2 이상이 필요하다.

**단계별 흐름:**

1. **`create_project.tcl`** — 파트 `xck26-sfvc784-2LV-c` (KV260 ZU5EV)
   를 타겟으로 Vivado 프로젝트를 `build/pccx_v002_kv260/` 에 생성한다.
   `filelist.f` 를 파싱하여 소스를 `sources_1` 필셋에 추가하고,
   `hw/constraints/*.xdc` 를 `constrs_1` 에 등록한다.
2. **`synth.tcl`** — `synth_design -mode out_of_context
   -flatten_hierarchy rebuilt` 로 OOC 합성을 수행한다. 합성 후
   `build/reports/` 에 `utilization_post_synth.rpt`,
   `clocks_post_synth.rpt`, `timing_summary_post_synth.rpt`,
   `drc_post_synth.rpt` 를 생성한다. `impl.tcl` 을 실행하기 전
   이 리포트에서 WNS 를 확인할 것을 권장한다.
3. **`impl.tcl`** — `synth_1` 진행률이 `100%` 임을 확인한 후
   `impl_1 -to_step write_bitstream -jobs 4` 를 실행한다. 완료 시
   비트스트림을 `build/pccx_v002_kv260.bit` 로 복사한다.
   구현은 시간 단위 작업이므로 OOC 합성이 클린한 상태에서만 실행한다.

OOC 모드를 사용하는 이유는 `NPU_top` 이 SystemVerilog 인터페이스 포트
(`axil_if` / `axis_if`) 를 사용하기 때문이다. OOC 합성에서는 포트를
미결합 상태로 두므로 블록 디자인 래퍼 없이 코어를 단독으로 합성·검증할
수 있다.

## SV 인터페이스 래퍼

`hw/vivado/npu_core_wrapper.sv` 는 `NPU_top` 의 SystemVerilog 인터페이스
포트를 평문 AXI4-Lite / AXI4-Stream 신호 묶음으로 변환하는 얇은 래퍼다.
레지스터와 CDC 는 포함하지 않으며 신호 배선만 수행한다.

```{literalinclude} ../../../../codes/v002/hw/vivado/npu_core_wrapper.sv
:language: systemverilog
:start-at: module npu_core_wrapper
:end-before: // ---------------------------------------------------------------------------
:caption: npu_core_wrapper — 포트 선언부
:name: lst-npu-core-wrapper-ports
```

래퍼가 노출하는 외부 인터페이스는 다음과 같다.

```{list-table} npu_core_wrapper 외부 인터페이스
:header-rows: 1
:name: tbl-wrapper-interfaces

* - 포트 그룹
  - 방향
  - 폭
  - 설명
* - `clk_core` / `rst_n_core`
  - 입력
  - 1-bit
  - 코어 도메인 클럭 및 액티브-로우 리셋
* - `clk_axi` / `rst_axi_n`
  - 입력
  - 1-bit
  - AXI 도메인 클럭 및 액티브-로우 리셋
* - `s_axil_*`
  - 슬레이브
  - 32-bit
  - AXI4-Lite 제어 채널 (CMD_IN / STAT_OUT)
* - `s_axis_hp0` .. `hp3`
  - 슬레이브
  - 128-bit
  - AXI4-Stream HP 포트 × 4 (가중치 스트리밍)
* - `s_axis_acp_fmap`
  - 슬레이브
  - 128-bit
  - AXI4-Stream ACP FMap 입력
* - `m_axis_acp_result`
  - 마스터
  - 128-bit
  - AXI4-Stream ACP 결과 출력
```

Vivado IP 패키저는 평문 신호 포트를 AXI 인터페이스로 자동 추론하므로,
이 래퍼를 거치면 `NPU_top` 을 Zynq PS 와 함께 블록 디자인에 직접 배치할
수 있다.

## 제약

`hw/constraints/pccx_timing.xdc` 는 타이밍 전용 제약 파일이다.
핀·IO 제약은 포함하지 않으며, 이는 해당 코어를 감싸는 블록 디자인에
위임된다.

두 개의 클럭 도메인이 정의된다.

```{list-table} 클럭 도메인 정의
:header-rows: 1
:name: tbl-clock-domains

* - 클럭 이름
  - 주기
  - 주파수
  - 대상
* - `axi_clk`
  - 4.000 ns
  - 250 MHz
  - AXI-Lite MMIO, CDC FIFO drain 측, DMA 경로
* - `core_clk`
  - 2.500 ns
  - 400 MHz
  - DSP48E2 어레이, GEMV 레인, CVO SFU
```

두 도메인은 완전히 비동기적이다. `set_clock_groups -asynchronous` 로
처리되며, 모든 경계 교차는 CDC FIFO 또는 리셋 동기화기를 통해 이루어진다.

추가로 다음 경로 예외가 설정되어 있다.

- **False path** — 리셋 브릿지 첫 플롭으로의 경로 및 `XPM_FIFO_ASYNC`
  그레이 코드 포인터 크로싱.
- **Multicycle path (setup 2, hold 1)** — GEMM systolic array 의 DSP48E2
  P-레지스터에서 `mat_result_normalizer` 까지. 컨트롤러가 누산 flush 중
  새 MAC 를 스톨시키므로 drain 경로에 2 사이클을 허용한다.

## 파일 매니페스트

`hw/vivado/filelist.f` 는 OOC 합성 및 `xvlog` 린트 모두의
소스 목록이다. `create_project.tcl` 이 이 파일을 파싱하여 소스를
Vivado 프로젝트에 추가한다.

컴파일 순서는 파일 내 선언 순서를 따른다. 패키지·인터페이스가 그것을
임포트하는 모듈보다 앞에 위치해야 한다.

```{literalinclude} ../../../../codes/v002/hw/vivado/filelist.f
:language: text
:start-at: B_device_pkg/device_pkg.sv
:end-before: Library/Algorithms/BF16_math.sv
:caption: filelist.f — 패키지 컴파일 순서 (앞부분)
:name: lst-filelist-packages
```

전체 파일은 다음 섹션으로 구성된다.

```{list-table} filelist.f 섹션 구성
:header-rows: 1
:name: tbl-filelist-sections

* - 섹션
  - 내용
* - A (주석 전용)
  - `` `include `` 헤더 (`*.svh`); `-i` 플래그로 포함, 직접 컴파일하지 않음
* - B
  - `device_pkg.sv` — 디바이스 파라미터
* - C
  - `dtype_pkg.sv`, `mem_pkg.sv` — 데이터·메모리 타입
* - D
  - `vec_core_pkg.sv` — Vector Core 파이프라인 파라미터
* - Library
  - BF16 수학 라이브러리, 알고리즘, QUEUE 인터페이스
* - ISA
  - `isa_pkg.sv` — 64-bit VLIW 인코딩 패키지
* - MAT_CORE
  - GEMM systolic array 및 결과 패커
* - VEC_CORE
  - GEMV 코어 (누산, LUT 생성, reduction, 탑)
* - CVO_CORE
  - CORDIC 유닛, SFU, CVO 탑
* - PREPROCESS
  - BF16↔fixed-point 파이프라인, fmap cache
* - MEM_control
  - L2 캐시, HP 버퍼, CVO 브릿지, 디스패처
* - NPU_Controller
  - AXI-Lite 디코더, 디스패처, 프론트엔드, Global Scheduler, 탑
* - 최상위
  - `NPU_top.sv` — 항상 마지막
```

새 `.sv` 파일을 추가할 때는 의존성 순서를 지켜 `filelist.f` 에 등록한다.

## 관련 페이지

```{toctree}
:maxdepth: 1
```

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
:::
