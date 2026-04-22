# 아키텍처 개요

_최근 개정: 2026-04-22._

pccx-lab 은 pccx v002 NPU 아키텍처를 위한 **데스크톱 프로파일러 + 검증 IDE**
이다. 컴패니언 ``pccx-FPGA-NPU-LLM-kv260`` RTL 레포의 xsim 테스트벤치가
내놓는 `.pccx` 바이너리 트레이스를 수집해 타임라인, flame graph, roofline,
bottleneck 윈도, 하드웨어 블록 다이어그램, Vivado synth utilisation /
timing, waveform, ISA replay 를 **단일 frameless Tauri v2 창** 에 표면화한다.

이 문서는 코드베이스의 평탄한 지도이다 — 각 서브시스템의 "왜" 는 소스의
인라인 주석에 있다.

## 레포 구조

```
pccx-lab/
├── src/
│   ├── core/            — pccx-core: headless Rust, GUI 의존성 없음
│   │   ├── src/
│   │   │   ├── lib.rs            단일 public surface
│   │   │   ├── pccx_format.rs    on-disk 바이너리 포맷
│   │   │   ├── trace.rs          NpuTrace + NpuEvent
│   │   │   ├── hw_model.rs       KV260 레퍼런스 상수
│   │   │   ├── analyzer.rs       TraceAnalyzer 트레이트 + 16 빌트인 ★
│   │   │   ├── research.rs       Citation 레지스트리 ★
│   │   │   ├── synth_runner.rs   Vivado spawn + 로그 파싱
│   │   │   ├── compare.rs        두 트레이스 회귀 게이트
│   │   │   ├── roofline.rs       Williams/Waterman + hierarchical
│   │   │   ├── bottleneck.rs     sliding-window contention detector
│   │   │   ├── report.rs         Markdown 렌더러
│   │   │   ├── live_window.rs    PerfChart 용 rolling stats
│   │   │   ├── step_snapshot.rs  결정론적 cycle → registers
│   │   │   ├── vivado_timing.rs  report_timing_summary 파서
│   │   │   ├── synth_report.rs   utilisation + timing 요약
│   │   │   ├── coverage.rs       UVM coverage JSONL merger
│   │   │   ├── vcd{,_writer}.rs  VCD 수집 + emit
│   │   │   ├── chrome_trace.rs   Perfetto JSON writer
│   │   │   ├── isa_replay.rs     Spike 스타일 커밋 로그 파서
│   │   │   ├── api_ring.rs       uca_* 호출 링 버퍼
│   │   │   └── bin/
│   │   │       ├── pccx_cli.rs       Vivado-shaped TCL runner
│   │   │       ├── pccx_analyze.rs   one-shot 분석 CLI ★
│   │   │       ├── from_xsim_log.rs  xsim 로그 → .pccx 컨버터
│   │   │       └── generator.rs      합성 트레이스 제너레이터
│   │   └── tests/       크로스 모듈 통합 테스트
│   ├── ai_copilot/      — LLM 오케스트레이션, core 에 의존
│   │   └── src/
│   │       ├── lib.rs            카탈로그, 확장, uca_sync helper
│   │       ├── copilot.rs        Copilot 구조체 + investigate/explain/rank ★
│   │       └── uvm.rs            UvmStrategy 트레이트 + 16 전략 ★
│   ├── uvm_bridge/      — SV / UVM DPI-C 어댑터, core 에 의존
│   └── ui/              — Tauri v2 + React 19 데스크톱 셸
│       ├── src/                  TypeScript React 컴포넌트
│       └── src-tauri/            Rust Tauri 셸 + IPC 명령
├── docs/                — Sphinx 소스 + 핸드북 (본 문서 트리로 이관됨)
└── scripts/             — 로컬 도구
```

★ = 연구 주도 추가 (2026-Q2 literature sweep).

## 레이어 계약

```
┌──────────────────────────────────────────────────────────────┐
│  ui/              React 19 + TypeScript + Vite 7             │
│                   `invoke("cmd", args)` 로 Rust 호출.         │
├──────────────────────────────────────────────────────────────┤
│  src-tauri/       Tauri v2 셸 (Rust). 얇은 레이어 — 실제      │
│                   비즈니스 로직은 core/ 에 있음.              │
├──────────────────────────────────────────────────────────────┤
│  ai_copilot/      Copilot 구조체; core 의 analyzer 레지스트리 │
│  uvm_bridge/      사용. UI 의존성 없음.                       │
├──────────────────────────────────────────────────────────────┤
│  core/            순수 Rust. ui/, ai_copilot/ 에 zero 의존성. │
│                   analyser surface 는 임의의 host 바이너리가  │
│                   사용 가능.                                  │
└──────────────────────────────────────────────────────────────┘
```

**대원칙**: `core/` 는 상위 레이어에 의존하지 않는다. 신규 분석은
`core/src/analyzer.rs` 에 넣고 `TraceAnalyzer` 트레이트로 노출한다 —
UI / Copilot / CLI 모두 자동으로 집어든다.

## 데이터 흐름 (단일 트레이스)

```
 ┌────────────────────┐                ┌──────────────────────┐
 │ xsim 테스트벤치    │ .pccx bytes    │ pccx-core::pccx_format│
 │ (RTL 레포)         ├───────────────►│ ::PccxFile::read     │
 └────────────────────┘                └──────────┬───────────┘
                                                  │ NpuTrace
                      ┌───────────────────────────┼───────────────────────────┐
                      ▼                           ▼                           ▼
           ┌───────────────────┐     ┌───────────────────────┐    ┌────────────────────┐
           │  analyze_all()    │     │  step_to_cycle()      │    │  write_vcd()       │
           │  → Vec<Report>    │     │  → RegisterSnapshot   │    │  write_chrome_trace│
           └─────────┬─────────┘     └──────────┬────────────┘    └────────────────────┘
                     │                           │
                     ▼                           ▼
           ┌───────────────────┐     ┌───────────────────────┐
           │ Copilot::         │     │  useRegisterSnapshot   │
           │ investigate_      │     │  (React 훅, rAF       │
           │ summary() → str   │     │  debounced + LRU)     │
           └─────────┬─────────┘     └───────────────────────┘
                     │
                     ▼
           LLM 시스템 프롬프트 (≤ 2 kB)
```

## 확장 훅

**신규 분석기 추가** (`core/`):

```rust
pub struct MyAnalyzer;
impl TraceAnalyzer for MyAnalyzer {
    fn id(&self) -> &'static str            { "my_analyzer" }
    fn display_name(&self) -> &'static str  { "My Analysis" }
    fn description(&self) -> &'static str   { "..." }
    fn analyze(&self, trace: &NpuTrace, hw: &HardwareModel) -> AnalysisReport {
        // ...
    }
}
```

`analyzer::builtin_analyzers()` 에 등록 → CLI 와 UI 가 즉시 집어든다.
전체 레시피 + 레퍼런스 `DmaLatencyAnalyzer` 구현은
[분석기 API 페이지](analyzer_api.md) 참고.

**신규 UVM 전략 추가** (`ai_copilot/`):

```rust
pub struct MyFix;
impl UvmStrategy for MyFix {
    fn id(&self) -> &'static str   { "my_fix" }
    fn category(&self) -> UvmCategory { UvmCategory::Memory }
    fn applies_to_analyzers(&self) -> &'static [&'static str] {
        &["my_analyzer"]
    }
    fn generate(&self) -> GeneratedStub { /* ... */ }
}
```

`uvm::builtin_strategies()` 에 append. Copilot 이 "my_analyzer" 발견을
"my_fix" 로 자동 매핑한다.

**신규 Tauri 커맨드 추가**: `src-tauri/src/lib.rs` 편집 → `#[tauri::command]`
annotated fn 추가 → `invoke_handler!` 에 등록. `Copilot` 이 이미
analyzer surface 를 노출하므로 와이어링은 보통 한 줄 브릿지로 끝난다.

## 크로스 레포 경계

- **pccx**: canonical v002 사양 (지금 이 사이트). 숫자, 비트폭, opcode
  테이블 — 항상 이 소스와 일치.
- **pccx-FPGA-NPU-LLM-kv260**: pccx-lab 이 프로파일하는 RTL 레포. pccx-lab
  CI 에서 수정하지 않음 — `synth_runner` 와 보드 bringup 스크립트가
  read-only 로 구동.
- **llm-lite**: 골든 비교용 CPU 레퍼런스. TB 제너레이터와 `reg_golden`
  UVM 전략이 사용.

## 빌드 상태 (현재)

```text
cargo test --workspace                → 131 passed (90 core lib + 25 core bin + 10 uvm + 6 copilot)
cargo check (src-tauri)               → 0 error
npx tsc --noEmit -p src/ui            → 0 error
npm run build (vite)                  → 3.6 MB main chunk + 14 split, 38 s
```

커맨드 레퍼런스는 [CLI 레퍼런스](cli.md), AI 자동화 surface 는
[Copilot API](copilot.md) 참고.
