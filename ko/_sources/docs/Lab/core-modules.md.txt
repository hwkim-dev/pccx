---
myst:
  html_meta:
    description lang=ko: |
      pccx-core 크레이트 공개 모듈 레퍼런스 — live_window, mmap_reader,
      step_snapshot, api_ring, chrome_trace, isa_replay, cycle_estimator,
      vivado_timing, coverage, vcd/vcd_writer, pccx_format.
---

# pccx-core 모듈 레퍼런스

`crates/core/` (`pccx-core`) 는 워크스페이스 의존 그래프의 단일 싱크다.
UI, reports, verification, lsp 등 모든 크레이트가 여기서 공개 타입을
가져온다. 이 페이지는 `lib.rs` 가 `pub mod` 로 선언한 각 모듈의 역할과
최상위 공개 항목을 기술한다.

모듈 구현 파일: `pccx-lab/crates/core/src/<module>.rs`.

```{contents} 이 페이지 목차
:depth: 2
:backlinks: none
```

## live_window

라이브 텔레메트리 링 버퍼 구현. `perf_event_open(2)` 의 mmap head/tail
링과 Perfetto SHM producer/consumer API 를 모델로 삼아 실 `NpuTrace`
이벤트를 사이클 윈도우 단위로 집계한다. Math.random / Math.sin 합성값을
쓰지 않는다 — 트레이스가 비어 있으면 빈 스냅샷을 반환한다(Yuan OSDI 2014
loud-fallback 계약). 각 `LiveSample` 은 `mac_util`, `dma_bw`,
`stall_pct` 세 비율값과 pccx v002 기준 클럭(200 MHz = 5 ns/사이클)에서
유도한 단조 증가 타임스탬프 `ts_ns` 를 담는다. Tauri `fetch_live_window`
IPC 가 이 모듈을 소비해 프론트엔드 BottomPanel / PerfChart / Roofline 에
데이터를 공급한다.

**공개 항목**: `LiveSample`, `LiveWindow`

## mmap_reader

프로덕션 규모(100 MB 이상) `.pccx` 파일을 위한 제로-카피 리더. `memmap2`
로 파일을 열고 고정 크기 헤더만 파싱한 뒤 플랫 버퍼 페이로드는 뷰포트
또는 타일 쿼리가 도달할 때까지 매핑 상태로 유지한다. `PccxFile::read` 가
대형 트레이스에서 초 단위 힙 할당을 유발하는 문제를 우회하기 위해
도입됐다. `flatbuf` 인코딩(24바이트 고정 stride 이벤트)만 지원하며,
bincode 페이로드는 가변 길이라 바이너리 탐색이 불가능해 에러를 반환한다.
뷰포트 바이너리 탐색의 정확성을 위해 플랫 버퍼 내 이벤트는
`start_cycle` 오름차순으로 정렬돼 있어야 한다 — 파일 생성 시
`NpuTrace::to_flat_buffer_sorted` 를 사용해야 하는 이유다.

**공개 항목**: `MmapTrace`

## step_snapshot

커서 위치(단일 사이클)에서의 레지스터 및 MAC 어레이 상태 스냅샷. 캐시된
`NpuTrace` 와 대상 사이클을 받아 코어별 활성 이벤트 클래스·잔여 사이클,
그리고 NPU 전체의 MAC/DMA/stall/barrier 카운트를 `RegisterSnapshot` 으로
집계한다. `[0, trace.total_cycles]` 범위 밖의 사이클은 에러 대신 결정적
빈 스냅샷을 반환해 UI 가 "idle" 로 렌더링한다. 동일 코어에 이벤트가 겹칠
경우 `start_cycle` 이 더 늦은 쪽이 우선한다(latest-dispatch 규칙). 제로
duration 이벤트는 정확히 `start_cycle` 에만 발화하며 다음 사이클로 투영
되지 않는다(IEEE 1364-2005 §Annex 18 VCD 관례 준수).

**공개 항목**: `step_to_cycle`, `CoreState`, `RegisterSnapshot`

## api_ring

`uca_*` 드라이버 진입/종료 경계를 기록하는 API 정합성 링 버퍼. CUPTI
드라이버 트레이스 패턴을 따르며, 주기적으로 p99 레이턴시와 drop 카운트를
집계해 UI 의 API-Integrity 패널에 고정 스키마 행 벡터로 전달한다. 링은
`.pccx` 이벤트 스트림의 `API_CALL` 이벤트에서만 채워진다 — 합성 폴백이
없으며, `API_CALL` 이벤트가 없는 트레이스에서는 빈 `Vec` 을 반환하고
경고를 기록한다. `list_api_calls` 함수가 이 표면을 소비한다.

**공개 항목**: `ApiCall`, `NS_PER_CYCLE`(상수, 5 ns/cycle @ 200 MHz)

## chrome_trace

Chromium Trace Event Format(Google/Chromium "Trace Event Format" 명세,
`ph: "X"` Complete Event) 익스포터. `NpuTrace` 를 `ui.perfetto.dev`,
`chrome://tracing`, Perfetto proto 임포터에서 바로 열 수 있는 JSON 배열로
직렬화한다. 카테고리는 이벤트 종류별로 `"mac"`, `"dma"`, `"stall"`,
`"sync"` 로 구분되며 타임스탬프는 pccx v002 기준 클럭(200 사이클 = 1 µs)
을 적용해 마이크로초 정수로 변환된다. `pid` 는 가속기 인스턴스,
`tid` 는 `core_id` 에 매핑된다.

**공개 항목**: `write_chrome_trace`, `write_chrome_trace_to`

## isa_replay

ISA 수준 리플레이 diff 엔진. Spike `--log-commits` 스타일 커밋 로그를
소비해 명령어별 (예상, 실제) 사이클 쌍을 방출한다. 예상 사이클은
mnemonic prefix 로 키잉된 NPU 레이턴시 테이블에서 조회하고, 실제 사이클은
로그 라인의 `;cycles=<N>` 접미사에서 읽는다. 접미사가 없으면
`actual == expected` 를 PASS 로 처리한다. 허용 오차 ±10 % 이내는 WARN,
초과는 FAIL 로 분류한다. 알 수 없는 mnemonic 은 기본값 1사이클로 처리한다.

**공개 항목**: `IsaReplayEntry`, `IsaVerdict`(PASS/WARN/FAIL),
`replay_log`

## cycle_estimator

`TileOperation`(타일 GEMM M/N/K/bytes_per_element)과 `AttentionOperation`
(MQA/GQA 파라미터) 으로부터 예상 사이클을 추정하는 엔진. `HardwareModel`
에서 MAC 어레이 크기, AXI 버스 구성, BRAM 구성을 조회해 산술 연산 사이클,
DMA 전송 사이클, 스톨 패널티를 계산한다. pre-RTL 설계 공간 탐색(DSE) 과
Roofline 분석의 기대값 생성에 사용된다.

**공개 항목**: `CycleEstimator`, `TileOperation`

## vivado_timing

Vivado `report_timing_summary -quiet -no_header` 텍스트 출력 파서. UG906
"Design Timing Summary" / "Clock Summary" / "Intra Clock Table" /
"Timing Details" 섹션 헤더를 구조체로 집계한다. UI 의 SynthStatusCard 가
`synth_report.rs` 의 regex 스텁 대신 이 파서를 소비한다. KV260 ZU5EV
픽스처(WNS, TNS, failing endpoints, clock domain별 period)를 지원한다.

**공개 항목**: `parse_timing_report`, `parse_worst_endpoint`,
`TimingReport`, `ClockDomain`, `FailingPath`, `TimingParseError`

## coverage

UVM 커버리지 JSONL 런 덤프 병합기. 런별 `.jsonl` 파일을 소비해 그룹별
bin 히트 수와 cross tuple 을 Accellera UCIS 병합 의미론(count-based bins
합산)으로 집계한다. `goal` 필드는 선택적이며 없으면 이전 런 중 가장 큰
goal 값을 승계한다(없으면 0). 병합 결과는 UI 의 VerificationSuite 패널이
렌더링하며, 미도달 그룹은 강조 표시된다.

**공개 항목**: `merge_coverage_jsonl`, `CovBin`, `CovGroup`, `CrossTuple`,
`MergedCoverage`, `CoverageError`

## vcd / vcd_writer

VCD(Value Change Dump, IEEE 1364) 리더/라이터 쌍.

**vcd** — `vcd` crate(MIT) 에 렉싱을 위임하고 출력을 평탄하고
serde 직렬화 가능한 `WaveformDump` 로 재포장한다. `$scope/$var` 헤더에서
`Vec<SignalMeta>` 를, `$timestamp` + value 변화에서 `Vec<VcdChange>` 를
생성한다. UI 가 `parse_vcd_file` Tauri 커맨드로 소비하며 O(log n)
신호별 값 조회를 위해 바이너리 탐색을 적용한다.

**vcd_writer** — `NpuTrace` 에서 GTKWave / Surfer / Verdi / 내장
Waveform 패널 호환 VCD 를 생성한다. `clk`, `rst_n`, `mac_busy`,
`dma_rd`, `dma_wr`, `stall`, `barrier`, `core_id` 8가지 신호를 방출한다.
타임스케일 1 ns, IEEE 1364-2005 §18 준수.

**공개 항목(vcd)**: `parse_vcd_file`, `WaveformDump`, `SignalMeta`,
`VcdChange`, `VcdError`

**공개 항목(vcd_writer)**: `write_vcd`, `write_vcd_to`

## pccx_format

`.pccx` 바이너리 트레이스 포맷 코덱. 파일 레이아웃: 매직 `PCCX`(4바이트)
→ 메이저/마이너 버전(각 u8) → 예약 2바이트 → JSON 헤더 길이(u64) →
UTF-8 JSON 헤더 → 바이너리 페이로드. 현재 포맷 버전은 `MAJOR_VERSION
= 0x01`, `MINOR_VERSION = 0x01`. 메이저 버전 불일치는 `UnsupportedMajorVersion`
에러를 반환한다. 포맷 전체 명세는 {doc}`pccx-format` 를 참고한다.

**공개 항목**: `PccxFile`, `PccxHeader`, `PccxError`, `ArchConfig`,
`TraceConfig`, `PayloadConfig`, `fnv1a_64`

## 이 페이지 인용

```bibtex
@misc{pccx_lab_core_modules_2026,
  title        = {pccx-core module reference: public modules of the pccx-lab Rust core crate},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/core-modules.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
