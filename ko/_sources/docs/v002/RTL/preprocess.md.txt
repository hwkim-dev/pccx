# PREPROCESS RTL 레퍼런스

PREPROCESS 서브디렉터리는 다섯 개의 SystemVerilog 모듈로 구성된다.
`barrel_shifter_BF16.sv`는 작업 트리에 현재 존재하지 않는다.

## `preprocess_fmap`

```{literalinclude} ../../../../codes/v002/hw/rtl/PREPROCESS/preprocess_fmap.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/preprocess_fmap.sv
:start-at: module preprocess_fmap
:end-before: // ===| Bridge & Alignment
```

ACP `S_AXIS_ACP_FMAP` 인터페이스에서 128-bit BF16 스트림을 수신하고,
XPM block FIFO를 통해 256-bit으로 묶은 뒤 지수 캐싱과 가수 정렬을
두 경로로 병렬 처리한다. 정렬된 432-bit 출력을 `fmap_cache`에 기록하고,
외부에 `o_fmap_broadcast`와 `o_cached_emax` 두 벡터를 공급한다.

`fmap_width` 파라미터는 `` `DEVICE_ACP_WIDTH_BIT ``으로 기본 설정된다.
`ARRAY_SIZE_H` 매크로가 레인 수(출력 배열 크기)를 결정한다.

## `preprocess_bf16_fixed_pipeline`

```{literalinclude} ../../../../codes/v002/hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
:start-at: module preprocess_bf16_fixed_pipeline
:end-before: // ===| Stage 1
```

256-bit AXI-Stream 슬레이브(16 × BF16)를 입력받아 432-bit 마스터
(16 × 27-bit fixed-point)를 출력하는 **3단 파이프라인** 컨버터다.

- **스테이지 1** (`phase / buffer_low / block_valid`): 짝수 클럭에 하위
  16개 BF16과 그 `e_max`를 버퍼에 저장하고, 홀수 클럭에 상위 16개를
  합쳐 32-원소 블록을 구성한 뒤 global `e_max`를 계산한다.
- **스테이지 2** (`shift_phase / shift_trigger / shift_target_data`):
  블록을 2클럭에 걸쳐 16레인씩 처리한다. 각 레인은 hidden bit를 삽입한
  27-bit 가수를 `(e_max - e_val)` 만큼 right-shift하고 2의 보수 부호를
  적용한다. `delta_e ≥ 27`이면 결과를 0으로 플러시한다.
- **스테이지 3** (`m_axis_tvalid / m_axis_tdata` 출력 레지스터):
  `shift_trigger` 신호가 유효한 클럭에만 432-bit 결과를 레지스터에 래치한다.

슬레이브 `s_axis_tready`는 항상 `1`로 고정되어 있으므로 상위 스트림에서
역압(backpressure)을 발행하지 않는다.

## `bf16_to_INT8_pipeline_power_of_two_scale`

`hw/rtl/PREPROCESS/bf16_to_INT8_pipeline_power_of_two_scale.sv` 는
Option A (power-of-two scale) INT8 양자화기에 대응하는 **자리표시자
모듈**이다. 포트 선언은 256-bit 입력 / 256-bit 출력(32 × INT8)이나,
현재 본문은 `preprocess_bf16_fixed_pipeline`의 사본 구조를 포함하며
미완성 `always_ff` 블록(`buffer_low[]` 빈 인덱스)이 존재해 합성되지 않는다.
TODO.md §A-1 의 scale 정책 결정 이후 구현될 예정이라 RTL 레포에는
아직 untracked 상태로만 존재한다.

## `bf16_to_INT8_pipeline_true_symmetric_INT8`

Option B(true symmetric INT8) 양자화기에 대응하는 **자리표시자 모듈**이다.
포트 구조는 `bf16_to_INT8_pipeline_power_of_two_scale`과 동일하며,
본문 역시 동일한 미완성 상태다. `max_abs` 기반 실수 스케일 경로는
driver-computed scale + Constant Cache 방식으로 설계될 예정이며,
구체적인 구현 요건은 TODO.md §A-1에 정리되어 있다.

## `fmap_cache`

```{literalinclude} ../../../../codes/v002/hw/rtl/PREPROCESS/fmap_cache.sv
:language: systemverilog
:caption: hw/rtl/PREPROCESS/fmap_cache.sv
:start-at: module fmap_cache
:end-before: // ===| SRAM Instantiation
```

`preprocess_bf16_fixed_pipeline` 출력을 수신해 2048-깊이 BRAM에
스테이징하고, MAT_CORE에 1워드씩 브로드캐스트한다.

주요 파라미터는 네 개다: `DATA_WIDTH`(기본 27), `WRITE_LANES`(기본 16),
`CACHE_DEPTH`(기본 2048), `LANES`(기본 32). 기록 포트는 `xpm_memory_sdpram`
Port A (7-bit 주소, 432-bit 데이터)이고, 읽기 포트는 Port B (11-bit 주소,
27-bit 데이터)다. `READ_LATENCY_B = 2`로 설정되어 있으며, 이를 보상하기
위해 읽기 유효 신호를 3단 shift-chain
(`rd_valid_pipe_1 → rd_valid_pipe_2 → rd_valid`)으로 지연시킨다.

읽기 제어 FSM은 `rd_start` 펄스에서 `rd_addr = 0`으로 초기화하고,
`CACHE_DEPTH - 1`에 도달하면 `is_reading`을 해제한다. 브로드캐스트는
`rd_valid_pipe_2`가 유효한 클럭에 `LANES`개 출력을 모두 동시에 업데이트한다.

:::{admonition} 마지막 검증 대상
:class: note

커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
