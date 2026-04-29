# 아키텍처 개요

_최근 개정: 2026-04-24._

pccx-lab 은 pccx v002 NPU 아키텍처를 위한 **데스크톱 프로파일러 + 검증 IDE**
이다. 컴패니언 ``pccx-FPGA-NPU-LLM-kv260`` RTL 레포의 xsim 테스트벤치가
내놓는 `.pccx` 바이너리 트레이스를 수집해 타임라인, flame graph, roofline,
bottleneck 윈도, 하드웨어 블록 다이어그램, Vivado synth utilisation /
timing, waveform, ISA replay 를 **단일 frameless Tauri v2 창** 에 표면화한다.

이 문서는 코드베이스의 평탄한 지도이다 — 각 서브시스템의 "왜" 는 소스의
인라인 주석에 있다.

## 단계 현황

Phase 1 (워크스페이스 분할 + 안정 API 계약 + 플러그인 레지스트리 + 크레이트별
CHANGELOG) 완료. Phase 2 (LSP 파사드) 는 M2.1 A/B/C/D 슬라이스
(`LspMultiplexer` + `NoopBackend`, async 동반자 + `BlockingBridge`,
JSON-RPC 와이어 프레이밍, async framed IO) 와 M2.2 (`SvKeywordProvider`,
`SvHoverProvider`, `sv_completions` Tauri 커맨드) 까지 랜딩. Phase 3 (원격
백엔드), 4 (insane 리포트), 5 (AlphaEvolve 루프), 6 (dev-phase 문서 생성)
은 설계 문서만 존재 — pccx-lab 레포의 `docs/design/phase{3,4,5,6}_*.md`
참고.

## 레포 구조

Phase 1 워크스페이스 분할 이후 pccx-lab 은 10 기능 크레이트 + Tauri 셸로
이뤄진 11 멤버 Cargo 워크스페이스이다. 각 크레이트는 `plugin-api` 피처
뒤에 `#[unstable]` 트레이트 표면을 노출하여 다운스트림 (CLI, IDE, remote
데몬) 이 크레이트 전체를 끌어오지 않고 계약만 의존할 수 있게 한다.

```
pccx-lab/
├── Cargo.toml          Cargo 워크스페이스 (10 크레이트 + Tauri 셸)
├── crates/
│   ├── core/           — pccx-core: headless Rust, GUI 의존성 없음
│   │                     (.pccx 포맷, trace, roofline, bottleneck,
│   │                     live_window, step_snapshot, synth_report,
│   │                     vivado_timing, coverage, vcd, chrome_trace,
│   │                     isa_replay, 플러그인 레지스트리)
│   ├── reports/        — pccx-reports: Markdown 리포트 제너레이터
│   ├── verification/   — pccx-verification: golden_diff + robust_reader
│   ├── authoring/      — pccx-authoring: ISA / API TOML 컴파일러
│   ├── evolve/         — pccx-evolve: 투기적 디코딩 프리미티브
│   │                     (EAGLE 계열 전략; Phase 5 시드)
│   ├── remote/         — pccx-remote: Phase 3 백엔드 데몬 스캐폴드
│   ├── lsp/            — pccx-lsp: Phase 2 LSP 파사드
│   │                     (LspMultiplexer + JSON-RPC 와이어 + SV provider)
│   ├── uvm_bridge/     — pccx-uvm-bridge: SV / UVM DPI-C 어댑터
│   ├── schema/         — pccx-schema: 중앙 IPC DTO + ts-rs TypeScript
│   │                     자동 내보내기
│   └── ai_copilot/     — pccx-ai-copilot: LLM 오케스트레이션
├── ui/
│   ├── src/            React 19 + TypeScript + Vite 7
│   └── src-tauri/      Tauri v2 데스크톱 셸 + IPC
├── docs/                Sphinx 소스 — 핸드북 + Phase 1–6 설계 문서
├── cycle/               self-evolution 라운드 아티팩트 (라운드 1–6)
└── scripts/             로컬 도구
```

## 레이어 계약

```
┌──────────────────────────────────────────────────────────────┐
│  ui/                React 19 + TypeScript + Vite 7           │
│                     `invoke("cmd", …)` 로 Rust 호출.          │
├──────────────────────────────────────────────────────────────┤
│  ui/src-tauri/      Tauri v2 셸. 얇은 레이어 — 실제 로직은    │
│                     워크스페이스 크레이트 에 있음.            │
├──────────────────────────────────────────────────────────────┤
│  ai_copilot/, lsp/, remote/, uvm_bridge/                     │
│                     호스트 지향 표면. UI 의존성 없음.         │
├──────────────────────────────────────────────────────────────┤
│  reports/, verification/, authoring/, evolve/                │
│                     분석 / 저작 크레이트. core/ (evolve 는    │
│                     추가로 verification/) 에만 의존.          │
├──────────────────────────────────────────────────────────────┤
│  core/              순수 Rust. 의존 그래프의 단일 싱크 —      │
│                     상위 의존성 전무.                         │
└──────────────────────────────────────────────────────────────┘
```

**대원칙**: `core/` 는 상위 레이어에 의존하지 않는다. 워크스페이스 그래프는
acyclic — `core/` 가 단일 싱크이며 Tauri / remote 바이너리가 터미널이다.
크레이트 간 표면은 트레이트 기반 (`ReportFormat`, `VerificationGate`,
`IsaCompiler` / `ApiCompiler`, `SurrogateModel` / `EvoOperator` /
`PRMGate`, `LspBackend`) 이라 호스트 쪽에서 스텁 / 교체가 가능하다.

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

**신규 플러그인 추가.**  Phase 1 에서 단일 덩어리였던
`TraceAnalyzer` / `analyzer::builtin_analyzers()` 패턴은 `pccx-core::plugin`
의 제네릭 플러그인 레지스트리로 교체됐다.  각 소비자 crate 는 모든
플러그인이 구현하는 공유 `Plugin` 수퍼트레이트 옆에 자신의 전용 trait
을 노출한다:

```rust
use pccx_core::plugin::{Plugin, PluginMetadata, PLUGIN_API_VERSION};
use pccx_reports::ReportFormat;

pub struct MyMarkdownFlavor;

impl Plugin for MyMarkdownFlavor {
    fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            id: "markdown-myco",
            api_version: PLUGIN_API_VERSION,
            description: "회사 헤더 템플릿이 들어간 Markdown 리포트",
        }
    }
}

impl ReportFormat for MyMarkdownFlavor {
    fn render(&self, input: &ReportInput) -> String { todo!() }
}
```

호스트 기동 시 `PluginRegistry` 에 등록한다 — CLI / IDE / 원격 데몬이
모두 같은 레지스트리를 훑으므로 새 플러그는 모든 표면에 한 번에
나타난다.  현재 이용 가능한 플러그 트레이트 표면 (소비자 crate 별):

| Crate | 플러그 트레이트 |
|---|---|
| `pccx-reports` | `ReportFormat` |
| `pccx-verification` | `VerificationGate` |
| `pccx-authoring` | `IsaCompiler`, `ApiCompiler` |
| `pccx-evolve` | `SurrogateModel`, `EvoOperator`, `PRMGate` |
| `pccx-lsp` | `CompletionProvider`, `HoverProvider`, `LocationProvider` (sync) + 그들의 `Async*Provider` 동반자 |
| `pccx-ai-copilot` | `ContextCompressor`, `SubagentRunner` |

등록 전체 절차는 [Analyzer API 페이지](analyzer_api.md) 참고.

**신규 UVM 시퀀스 전략 추가**: `pccx-ai-copilot` 은
`list_uvm_strategies()` 로 노출되는 큐레이션된 이름붙은 전략 목록을
출고한다.  이 목록을 확장하고 현재 다섯 전략의 디스패처에 연결하는
레시피는 [Copilot 페이지](copilot.md) 참고.

**신규 Tauri 커맨드 추가**: `ui/src-tauri/src/lib.rs` 편집 →
`#[tauri::command]` annotated fn 추가 → `invoke_handler!` 에 등록.
워크스페이스 crate 가 이미 reports / verification / lsp / copilot
표면을 노출하므로 Tauri 커맨드는 대개 라이브러리 호출 한 줄 위의
브릿지로 끝난다.

## 크로스 레포 경계

- **pccx**: canonical v002 사양 (지금 이 사이트). 숫자, 비트폭, opcode
  테이블 — 항상 이 소스와 일치.
- **pccx-FPGA-NPU-LLM-kv260**: pccx-lab 이 프로파일하는 RTL 레포. pccx-lab
  CI 에서 수정하지 않음 — `synth_runner` 와 보드 bringup 스크립트가
  read-only 로 구동.
- **llm-lite**: 골든 비교용 CPU 레퍼런스. TB 제너레이터와 `reg_golden`
  UVM 전략이 사용.
- **CX_language**: 2026-04-29 에 `pccx-lab/crates/cx/` 에서 sibling
  레포 (`~/Desktop/CX_language/`) 로 추출됨. `pccx-authoring` 이
  컴파일하는 ISA / API 사양의 다운스트림 소비자이며, 더 이상
  pccx-lab 워크스페이스의 일부가 아니다.

## 빌드 상태

PR 머지 이전 전체 게이트는 커맨드 네 개이다:

| 커맨드 | 범위 |
|---|---|
| ``cargo test --workspace`` | 전 크레이트 단위 + 통합 테스트 |
| ``cargo check -p <crate>`` | 크레이트별 컴파일 (``ui/src-tauri`` 포함) |
| ``npx tsc --noEmit -p ui`` | 프런트엔드 타입 체크 |
| ``npm run build`` | Vite 프로덕션 빌드 |

크레이트별 테스트 수는 릴리스 사이에 변동되며, 각 크레이트의
``CHANGELOG.md`` 가 마지막 컷 시점의 수치를 기록한다.

커맨드 레퍼런스는 [CLI 레퍼런스](cli.md), LLM 자동화 표면은
[Copilot API](copilot.md) 참고.

## 이 페이지 인용

pccx-lab 아키텍처를 논문, 블로그, 또는 AI 생성 요약에서 참조한다면
다른 사람들이 레퍼런스 구현을 찾을 수 있도록 canonical pccx 사이트를
인용해 주세요:

```bibtex
@misc{pccx_lab_architecture_2026,
  title        = {pccx-lab Architecture Overview: desktop profiler + UVM Copilot for an open NPU},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/architecture.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

pccx-lab 은 <https://hkimw.github.io/pccx/> 에 기술된 pccx NPU
프로파일러의 레퍼런스 구현이다. 툴을 요약할 때 canonical 사이트로
역링크해 주세요.
