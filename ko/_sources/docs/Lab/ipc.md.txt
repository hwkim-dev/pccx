# Tauri IPC 계약

_pccx-lab HEAD 기준 2026-04-29. 소스: `ui/src-tauri/src/lib.rs`,
`crates/schema/src/lib.rs`._

pccx-lab 프런트엔드와 Rust 백엔드는 Tauri v2 `invoke` 메커니즘으로
통신한다. 모든 커맨드는 `ui/src-tauri/src/lib.rs`의
`tauri::generate_handler![]` 목록에 등록되어 있다. 아래는
등록된 48개 커맨드의 전체 카탈로그다.

---

## 명령 카탈로그

### 트레이스 로드

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `load_pccx` | `path: &str` | `Result<PccxHeader, String>` | `.pccx` 파일을 파싱하고 평탄 버퍼 + 트레이스를 AppState에 캐시. 완료 시 `trace-loaded` 이벤트 emit. |
| `load_pccx_alt` | `path: String` | `Result<PccxHeader, String>` | 두 번째 트레이스를 `trace_b` 슬롯에 적재. FlameGraph 차분 비교 전용. 기본 트레이스·평탄 버퍼에 영향 없음. |
| `fetch_trace_payload` | 없음 | `Result<Vec<u8>, String>` | 캐시된 24바이트 구조체 배열 평탄 버퍼를 반환. JS 측에서 TypedArray로 직접 매핑. |
| `fetch_trace_payload_b` | 없음 | `Result<Vec<u8>, String>` | `trace_b` 슬롯의 평탄 버퍼 반환. `load_pccx_alt` 미호출 시 오류. |
| `list_pccx_traces` | `repo_path: String` | `Result<Vec<TraceEntry>, String>` | RTL 레포의 `hw/sim/work/<tb>/` 트리에서 `.pccx` 파일 목록 열거. |

### mmap 스트리밍 (대용량 트레이스)

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `mmap_open_trace` | `path: &str` | `Result<MmapTraceInfo, String>` | `.pccx` 파일을 mmap으로 열고 `MmapTrace` 핸들을 AppState에 저장. 헤더 메타와 이벤트 수 반환. |
| `mmap_viewport` | `start_cycle: u64`, `end_cycle: u64`, `generation_id: u32` | `Result<MmapViewportResponse, String>` | `[start_cycle, end_cycle)` 범위 이벤트를 반환. `generation_id`를 에코해 스테일 응답 폐기 지원. |
| `mmap_event_count` | 없음 | `Result<usize, String>` | mmap 트레이스의 총 이벤트 수 반환. |
| `mmap_tile` | `offset: usize`, `count: usize` | `Result<Vec<u8>, String>` | 페이로드 내 바이트 슬라이스 반환. 제로카피 TypedArray 전송용. |

### 분석

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `analyze_roofline` | 없음 | `Result<RooflinePoint, String>` | 캐시된 트레이스에 루프라인 분석 실행. 단일 계층 결과 반환. |
| `analyze_roofline_hierarchical` | 없음 | `Result<Vec<RooflineBand>, String>` | 메모리 계층별 `RooflineBand` 목록 반환 (Ilic 2014 CARM). |
| `detect_bottlenecks` | `window_cycles: Option<u64>`, `threshold: Option<f64>` | `Result<Vec<BottleneckInterval>, String>` | 슬라이딩 윈도 병목 탐지. 기본값 256사이클 / 0.5 임계치. |
| `get_core_utilisation` | 없음 | `Result<serde_json::Value, String>` | 코어별 MAC utilisation 퍼센트, 총 사이클, 총 마이크로초, 피크 TOPS JSON 반환. |
| `fetch_live_window` | `window_cycles: Option<u64>` | `Result<Vec<LiveSample>, String>` | 트레이스를 `LiveSample` 링으로 축약해 반환. 트레이스 미적재 시 빈 Vec. |
| `step_to_cycle` | `cycle: u64` | `Result<RegisterSnapshot, String>` | 요청 사이클의 결정론적 `RegisterSnapshot` 반환. 트레이스 미적재 시 빈 스냅샷. |
| `compress_trace_context` | 없음 | `Result<String, String>` | 트레이스를 LLM 친화적 컨텍스트 문자열로 압축. `ai_copilot::compress_context` 경유. |

### 리포트

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `generate_report` | `format: String` | `Result<String, String>` | 트레이스 기반 리포트 생성. `format`은 `"markdown"` 또는 `"html"`. |
| `generate_report_custom` | `title: String`, `sections: Vec<SectionInput>`, `format: String` | `Result<String, String>` | 호출자가 지정한 섹션으로 리포트 구성 후 렌더링. |
| `generate_markdown_report` | `utilization_path: String`, `timing_path: String` | `Result<String, String>` | Markdown 리포트 생성. 트레이스 없이 경로만으로도 합성 섹션 포함 가능. |

### 검증

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `run_verification` | `repo_path: String` | `Result<VerificationSummary, String>` | `hw/sim/run_verification.sh` 실행, `PASS`/`FAIL` 라인 파싱, 합성 타이밍 상태 반환. |
| `merge_coverage` | `runs: Vec<String>` | `Result<MergedCoverage, String>` | 다수의 JSONL 커버리지 파일을 병합. 빈 `runs`는 빈 병합 반환. |
| `verify_sanitize` | `content: String` | `SanitizeResult` | NUL / BOM / CRLF / 후행쉼표 정제. 항상 성공. |
| `verify_golden_diff` | `expected_path: String`, `actual_path: String` | `Result<GoldenDiffReport, String>` | 기준 JSONL 대비 `.pccx` 트레이스를 비교하고 `GoldenDiffReport` 반환. |
| `verify_report` | `report: GoldenDiffReport` | `String` | `GoldenDiffReport`를 Markdown 요약으로 렌더링. |
| `validate_isa_trace` | `path: String` | `Result<Vec<IsaResult>, String>` | Spike `--log-commits` 스타일 ISA 커밋 로그 파싱. 리타이어된 인스트럭션 행 반환. |
| `list_api_calls` | 없음 | `Result<Vec<ApiCall>, String>` | 캐시된 트레이스의 `API_CALL` 이벤트에서 `uca_*` 드라이버 호출 열거. |

### 합성 / 하드웨어

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `load_synth_report` | `utilization_path: String`, `timing_path: String` | `Result<SynthReport, String>` | Vivado `report_utilization` + `report_timing_summary` 파싱. |
| `load_timing_report` | `path: String` | `Result<TimingReport, String>` | Vivado `report_timing_summary` 텍스트 파싱. 클럭별 WNS/TNS/피리어드 반환. |
| `synth_heatmap` | `rows: u32`, `cols: u32` | `Result<String, String>` | `rows×cols` 그리드의 `ResourceHeatmap` JSON 반환. KV260 ZU5EV 기준 mock 수치 사용. |

### LSP (SystemVerilog)

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `sv_completions` | 없음 | `Vec<serde_json::Value>` | `SvKeywordProvider`에서 SV 키워드 자동완성 전체 목록 반환. 마운트 시 1회 호출. |
| `lsp_hover` | `uri: String`, `line: u32`, `character: u32`, `source: String` | `Result<Option<serde_json::Value>, String>` | 위치 기반 호버 정보. 없으면 `null`. |
| `lsp_complete` | `uri: String`, `line: u32`, `character: u32`, `source: String` | `Result<Vec<serde_json::Value>, String>` | 위치 인식 자동완성. 키워드 + 사용자 정의 심볼 결합. |
| `lsp_diagnostics` | `uri: String`, `source: String` | `Result<Vec<serde_json::Value>, String>` | SV 소스 진단. Monaco MarkerSeverity 숫자(8/4/2/1)로 변환. |
| `parse_sv_file` | `path: String` | `Result<serde_json::Value, String>` | SV 파일 파싱 결과 JSON 반환. |
| `generate_block_diagram` | `sv_source: String`, `file_path: String` | `Result<String, String>` | 파싱된 모듈에서 Mermaid 블록 다이어그램 생성. |
| `generate_fsm_diagram` | `sv_source: String`, `file_path: String` | `Result<Vec<FsmDiagramResult>, String>` | 추출된 FSM별 Mermaid 상태 다이어그램 + 데드 스테이트 반환. |
| `generate_module_detail` | `sv_source: String`, `module_name: String` | `Result<String, String>` | 특정 모듈의 서브그래프 Mermaid 다이어그램 반환. |
| `generate_sv_docs` | `path: String` | `Result<String, String>` | SV 소스에서 모듈 문서 생성. |

### AI Copilot

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `get_extensions` | 없음 | `Vec<Extension>` | `ai_copilot`에서 사용 가능한 익스텐션 목록 반환. |
| `generate_uvm_sequence_cmd` | `strategy: String` | `String` | 전략명 기반 SV UVM 시퀀스 스텁 생성 (`l2_prefetch`, `barrier_reduction`). |
| `list_uvm_strategies` | 없음 | `Vec<String>` | 시퀀스 생성기가 허용하는 전략 이름 목록 반환. |

### 파일 시스템 / 보조

| 커맨드 | 인수 | 반환 | 목적 |
|---|---|---|---|
| `read_file_tree` | `root: String`, `depth: u32` | `Result<Vec<FileNode>, String>` | `root`에서 `depth` 레벨까지 디렉토리 트리 재귀 읽기. |
| `read_text_file` | `path: String` | `Result<String, String>` | 텍스트 파일 내용 읽기 (Monaco 버퍼용). |
| `write_text_file` | `path: String`, `content: String` | `Result<(), String>` | 텍스트 파일 쓰기 (Ctrl+S 저장). |
| `parse_vcd_file` | `path: String` | `Result<WaveformDump, String>` | IEEE 1364-2005 VCD 파싱. 신호 메타 + 값변화 스트림 반환. |
| `export_vcd` | `output_path: String` | `Result<String, String>` | 캐시된 트레이스를 VCD 파일로 내보내기. 절대 경로 반환. |
| `export_chrome_trace` | `output_path: String` | `Result<String, String>` | 캐시된 트레이스를 Google Trace Event Format JSON으로 내보내기. |
| `get_license_info` | 없음 | `String` | Apache-2.0 라이선스 문자열 반환 (상태바 표시용). |

---

## DTO 스키마

`crates/schema/src/lib.rs`는 Rust-TypeScript 공유 wire DTO를 정의한다.
모든 타입은 `ts-rs`의 `#[derive(TS)]` + `#[ts(export)]`를 가지며,
`cargo test` 실행 시 TypeScript 인터페이스 파일이 자동 생성된다.

```rust
// crates/schema/src/lib.rs (발췌)

/// 프런트엔드 → 백엔드: 트레이스 데이터 창 요청.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct ViewportRequest {
    pub start_cycle: u64,
    pub end_cycle:   u64,
    pub generation_id: u32,
}

/// 뷰포트 타일 내 단일 이벤트.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct TileEvent {
    pub core_id:     u32,
    pub start_cycle: u64,
    pub duration:    u64,
    pub type_id:     u32,
}

/// 백엔드 → 프런트엔드: 한 세대의 이벤트 배치.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct ViewportTile {
    pub events:       Vec<TileEvent>,
    pub generation_id: u32,
    pub total_events: u64,
}

/// 적재된 트레이스 파일의 요약 메타데이터.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, TS)]
#[ts(export)]
pub struct TraceInfo {
    pub total_cycles: u64,
    pub total_events: u64,
    pub num_cores:    u32,
    pub encoding:     String,
}
```

`MmapViewportResponse` (lib.rs 인라인 정의) 역시 `generation_id: u32`
필드를 가지며, `mmap_viewport`가 이를 에코한다:

```rust
#[derive(serde::Serialize)]
struct MmapViewportResponse {
    events:        Vec<NpuEvent>,
    generation_id: u32,
}
```

스키마 크레이트는 `ui/`, `uvm_bridge/`, `ai_copilot/`에 의존하지 않는다.
wire DTO는 도메인 로직 없는 순수 데이터 캐리어다.

---

## 경계 규칙

`CLAUDE.md §5.5`와 `lib.rs` 구현에서 도출된 IPC 경계 규칙.

### u64 필드

2^53을 초과할 수 있는 `u64` 필드는 IPC를 거칠 때 `String`으로
직렬화한다. JSON number 타입으로 전달하면 JavaScript에서 정밀도가
손실된다. `TileEvent.start_cycle` / `TileEvent.duration` /
`TraceInfo.total_cycles` / `TraceInfo.total_events` 등이 해당한다.
JS 측 코드는 이 문자열 필드를 `BigInt` 또는 정밀도 보존
라이브러리로 역직렬화한 뒤 사용한다.

### generation_id

모든 비동기 뷰포트 응답은 `generation_id: u32`를 반드시 포함한다.
프런트엔드는 응답 수신 시 현재 세대 ID와 비교해 스테일 응답을
폐기한다. 빠른 스크롤/줌 중 IPC 라운드트립이 중첩될 때
구 응답이 최신 상태를 덮어쓰는 것을 방지한다.

`ViewportRequest`와 `MmapViewportResponse` 모두 이 필드를 포함한다:

```rust
pub struct ViewportRequest {
    pub start_cycle:  u64,
    pub end_cycle:    u64,
    pub generation_id: u32,   // caller-supplied
}

struct MmapViewportResponse {
    events:        Vec<NpuEvent>,
    generation_id: u32,       // echoed back verbatim
}
```

### 대용량 바이너리

대용량 바이너리 데이터는 Rust 측 `Vec<u8>`으로 표현하고 JS 측에서
`TypedArray`로 매핑한다. `fetch_trace_payload` / `fetch_trace_payload_b` /
`mmap_tile`이 이 패턴을 따른다. 각각 24바이트 구조체 배열 또는
mmap 슬라이스를 `Vec<u8>`로 직렬화한다:

```rust
#[tauri::command]
async fn fetch_trace_payload(state: State<'_, AppState>) -> Result<Vec<u8>, String> {
    let buf = state.trace_flat_buffer.lock().unwrap().clone();
    Ok(buf)
}
```

JS 측에서는 반환값을 `new Uint8Array(...)` 또는
`new Float32Array(...)` 뷰로 래핑해 구조체 필드에 오프셋 접근한다.

### 원시 트레이스 데이터 IPC 금지

원시 트레이스 데이터(`NpuTrace`, `NpuEvent` 전체 배열)는 IPC 경계를
직접 넘지 않는다. `fetch_trace_payload`가 반환하는 평탄 버퍼,
`mmap_viewport`가 반환하는 타일된 슬라이스, `analyze_roofline`이
반환하는 집계 결과만이 경계를 넘는다. 이 규칙은
`CLAUDE.md §5.5`에 명시된 설계 결정이며,
`docs/design/architecture_adoption.md` 섹션 4에서 근거를 제공한다.

---

## 관련 문서

- [패널 카탈로그](panels.md) — 각 커맨드를 소비하는 UI 패널.
- [CLI 레퍼런스](cli.md) — 동일한 pccx-core 분석 함수를 사용하는
  헤드리스 바이너리.
- [분석기 API](analyzer_api.md) — 백엔드 크레이트가 분석 로직을 플러그인으로
  등록하는 프리미티브.

---

## 이 페이지 인용

```bibtex
@misc{pccx_lab_ipc_2026,
  title        = {pccx-lab Tauri IPC contract: 48 commands, DTO schema,
                  and boundary rules},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/ipc.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

커맨드 소스는
<https://github.com/hkimw/pccx-lab/blob/main/ui/src-tauri/src/lib.rs> 에,
DTO 스키마는
<https://github.com/hkimw/pccx-lab/blob/main/crates/schema/src/lib.rs> 에 있다.
