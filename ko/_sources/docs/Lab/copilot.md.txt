# Copilot API

_페이지 과도기 상태. pccx-lab HEAD 기준 2026-04-24 재정비._

Phase 1 이전의 `Copilot` 구조체 (`investigate()`,
`investigate_summary()`, `explain()`, `rank_by_severity()`,
`suggest_fix()`, `generate_report()`) 는 폐기되었다. 오늘
`pccx-ai-copilot` 은 Tauri UI 용 얇은 정적 헬퍼 세트와 Phase 2 / Phase 5
오케스트레이션이 착륙할 unstable 트레이트 스캐폴드 두 개를 출하한다.
자연어 → UVM 워크플로우는 Phase 2 **pccx-lsp 파사드** 위에 재구축
중이다 — M2.1 의 A 부터 D 슬라이스 (`LspMultiplexer` + `NoopBackend`,
async 컴패니언 + `BlockingBridge`, `encode_frame` / `decode_frame`
JSON-RPC 와이어 프레이밍, async framed IO) 와 M2.2 (`SvKeywordProvider`,
`SvHoverProvider`, `sv_completions` Tauri 커맨드) 까지 착륙했다.

이 페이지는 오늘 출하 가능한 표면을 문서화한다. 구체 verible /
rust-analyzer / cloud LLM 백엔드가 lsp provider 트레이트에 꽂히면 더 풍부한
파사드로 갱신된다.

## 정적 헬퍼 (`pccx-ai-copilot`)

네 개 함수 + 레지스트리 상수 하나. 모두 구조체 생성 없이 호출 가능.
과거 Copilot 표면 중 Tauri UI 가 여전히 필요한 서브셋을 커버한다.

### `compress_context(cycles: u64, bottlenecks: usize) -> String`

트레이스 통계를 간결한 LLM 프롬프트 프리픽스로 압축. 출력은 약
300 자 — 임의 사용자 질의 앞에 prepend 해도 안전.

```rust
use pccx_ai_copilot::compress_context;

let ctx = compress_context(5_423_940, 19_179);
// "NPU trace: 5423940 total simulation cycles across a 32×32 systolic
//  MAC array with 32 cores at 1 GHz (est. 5423.9 µs wall-time). 19179
//  high-occupancy DMA bottleneck intervals detected. AXI bus contention
//  visible during simultaneous multi-core DMA. Peak theoretical: 2.05
//  TOPS."
```

### `generate_uvm_sequence(strategy: &str) -> String`

명명된 완화 전략에 대해 SystemVerilog UVM 시퀀스 스텁 반환. 미지원
slug 은 `generic_opt_seq` TODO 스텁으로 fallback.

```rust
use pccx_ai_copilot::generate_uvm_sequence;

let sv = generate_uvm_sequence("l2_prefetch");
// class l2_prefetch_seq extends uvm_sequence;
//   `uvm_object_utils(l2_prefetch_seq)
//
//   task body();
//     // Stagger DMA requests by AXI transaction overhead (15 cycles)
//     foreach (cores[i]) begin ...
//   endtask
// endclass : l2_prefetch_seq
```

### `list_uvm_strategies() -> Vec<&'static str>`

`generate_uvm_sequence` 가 인식하는 모든 전략 slug 을 열거. UI 피커와
향후 LSP / 에이전트 오케스트레이터가 match arm 을 하드코딩하지
않기 위해 사용.

현재 목록 (Phase 1 HEAD):

| slug                         | 바디 동작                                             |
|------------------------------|------------------------------------------------------|
| `l2_prefetch`                | DMA 읽기를 AXI 트랜잭션 오버헤드로 staggering.       |
| `barrier_reduction`          | 글로벌 sync 대신 wavefront barrier.                  |
| `dma_double_buffer`          | 인접 타일에 대해 compute / DMA ping-pong.            |
| `systolic_pipeline_warmup`   | 첫 실제 타일 전에 MAC 어레이 pre-roll.               |
| `weight_fifo_preload`        | 셋업 윈도 동안 HP weight FIFO front-load.            |

다섯 개로, Phase 1 이전 문서의 13 행 의도 라우팅 테이블보다 축소되었다.
더 풍부한 전략 세트 (`back_pressure_gate`, `kv_cache_thrash_probe`,
`speculative_draft_probe`, …) 는 재착륙되지 않았다 — pccx-lab
`docs/design/phase5_alphaevolve.md` 에서 진행 상황을 추적.

### `get_available_extensions() -> Vec<Extension>`

Tauri UI 의 Extensions 탭이 렌더하는 확장 카탈로그 반환. 로컬 LLM,
하드웨어 가속 플러그인, 클라우드 브리지, 분석 플러그인, 내보내기
플러그인을 커버. enum 표면은 크레이트 소스의 `ExtensionCategory` 참고.

## Unstable 트레이트 (Phase 1 M1.2)

Phase 2 IntelliSense 와 Phase 5 에이전트 오케스트레이션이 구현할 두
개 스캐폴드. 둘 다 public 이지만 크레이트의 "v0.3 까지 unstable"
마커를 달고 `plugin-api` 피처 뒤에 게이트되어 있다.

```rust
/// 채팅 기록, 트레이스 요약, 문서 발췌용 토큰 버짓 컴프레서.
/// 결정론적 head/tail 트리머와 학습된 LLMLingua 계열 컴프레서
/// 모두 이 트레이트를 구현.
pub trait ContextCompressor {
    fn compress(&self, input: &str, target_tokens: usize) -> String;
    fn name(&self) -> &'static str;
}

/// 단일 서브에이전트 태스크 (log analysis, research,
/// doc drafting) 를 실행해 응답 반환. pccx-ide 와 pccx-remote 가
/// 공유하는 parallel-subagent 패턴을 구동.
pub trait SubagentRunner {
    fn run(&self, task: &str, context: &str) -> anyhow::Result<String>;
    fn name(&self) -> &'static str;
}
```

pccx-lab v0.2.x 에는 구체 구현이 동봉되지 않는다 — Phase 2 / Phase 5
진행에 따라 착륙한다. 다운스트림 소비자는 pccx-lab v0.3 까지 이
시그니처가 변경 대상임을 전제해야 한다.

## pccx-lsp (Phase 2 M2.1 + M2.2)

LSP 파사드는 앞으로 LSP / 캐시 라우팅이 사는 곳이다. sync provider
트레이트 세 개 + async 컴패니언:

```rust
pub trait CompletionProvider {
    fn complete(&self, language: Language, file: &str,
                pos: SourcePos, source: &str)
        -> Result<Vec<Completion>, LspError>;
    fn name(&self) -> &'static str;
}

pub trait HoverProvider {
    fn hover(&self, language: Language, file: &str,
             pos: SourcePos, source: &str)
        -> Result<Option<Hover>, LspError>;
    fn name(&self) -> &'static str;
}

pub trait LocationProvider {
    fn definitions(&self, language: Language, file: &str,
                   pos: SourcePos, source: &str)
        -> Result<Vec<SourceRange>, LspError>;
    fn references(&self, language: Language, file: &str,
                  pos: SourcePos, source: &str)
        -> Result<Vec<SourceRange>, LspError>;
    fn name(&self) -> &'static str;
}
```

라우팅은 `LspMultiplexer` 를 거친다:

```rust
use pccx_lsp::{Language, LspMultiplexer, NoopBackend};

let mut m = LspMultiplexer::new();
m.register(
    Language::SystemVerilog,
    Box::new(NoopBackend),   // 이후: verible 래퍼
    Box::new(NoopBackend),
    Box::new(NoopBackend),
);
let completions = m.complete(
    Language::SystemVerilog, "foo.sv",
    SourcePos { line: 0, character: 0 },
    "module foo;",
)?;
```

`NoopBackend` 는 빈 결과를 반환 — 실제 백엔드가 wire-up 되는 동안
쓰는 의도적인 "여기 아무것도 없다" 응답이다. async 워크플로우에서는
`BlockingBridge<P>` 가 `tokio::task::spawn_blocking` 을 거쳐 임의 sync
provider 를 `AsyncCompletionProvider` / `AsyncHoverProvider` /
`AsyncLocationProvider` 로 끌어올린다. 외부 LSP 서버 (verible,
rust-analyzer, clangd) 는 `SpawnConfig` + `LspSubprocess` 로 spawn;
그 파이프 위의 JSON-RPC 코덱은 후속 슬라이스에 착륙한다.

`CompletionSource` enum 은 결과의 출처 — 상류 LSP, 빠른 cloud 예측기,
깊은 cloud 예측기, AST-해시 캐시 — 를 구분한다. 향후
예측 파이프라인이 이 enum 으로 feedback 되므로 UI 는 모든 제안 옆에
provenance 배지를 렌더할 수 있다.

엔드 스테이트 디자인 (LSP 라우팅, tower-lsp 어댑터, Monaco 와이어링) 은
pccx-lab `docs/design/phase2_intellisense.md` 참고.

## UI 지향 정적 커맨드

전면 파사드 도입 전까지 Tauri UI 는 `invoke("compress_context", …)`,
`invoke("generate_uvm_sequence", …)`, `invoke("list_uvm_strategies")`
로 정적 헬퍼를 직접 호출한다. 브리지는 `ui/src-tauri/src/lib.rs` 에서
함수당 한 줄짜리다. 단일 `invoke("copilot_investigate", …)` 우산 호출은
더 이상 존재하지 않는다.

전체 Tauri 커맨드 카탈로그 (load / mmap / analytics / verification /
lsp / synth / copilot 카테고리에 걸친 48 개 커맨드) 와 IPC 경계
규칙 (u64 → String, generation_id, 원시 트레이스의 IPC 통과 금지) 은
[IPC 레퍼런스](ipc.md) 참고.

## 관련 문서

- [분석기 API](analyzer_api.md) — 모든 크레이트별 플러그인 트레이트
  (`ContextCompressor` / `SubagentRunner` 포함) 가 걸리는 플러그인
  레지스트리 프리미티브.
- [CLI 레퍼런스](cli.md) — 현재 출하 중인 바이너리. 과거
  `pccx_analyze` 우산은 오늘 존재하지 않는다.

## 이 페이지 인용

```bibtex
@misc{pccx_lab_copilot_2026,
  title        = {pccx-ai-copilot and pccx-lsp: current AI / IntelliSense surface of pccx-lab after Phase 1},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/copilot.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

이 페이지가 문서화하는 헬퍼는
<https://github.com/hkimw/pccx-lab/blob/main/crates/ai_copilot/src/lib.rs>
에 위치하고, LSP 파사드는
<https://github.com/hkimw/pccx-lab/blob/main/crates/lsp/src/lib.rs>
에 있다.
