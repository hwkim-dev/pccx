# 분석기 API

_페이지 과도기 상태. pccx-lab HEAD 기준 2026-04-24 재정비._

Phase 1 은 분할 이전의 `TraceAnalyzer` 트레이트와 모놀리식
`analyzer::builtin_analyzers()` 목록을 폐기했다. 대신 pccx-core 는
모든 워크스페이스 크레이트 (reports, verification, authoring, evolve,
lsp, ai_copilot, …) 가 자기 자신의 trait-object 플러그인을 걸기 위해
재사용하는 작은 제네릭 **플러그인 레지스트리 프리미티브** 를 출하한다.
호출자는 더 이상 고정 빌트인 목록을 호출하지 않고 크레이트별
`PluginRegistry<P>` 에 플러그인을 등록한다.

이 페이지는 프리미티브 자체와 소비 크레이트가 자신의 플러그인 트레이트를
거기 어떻게 거는지를 문서화한다. Phase 1 이전의 16 개 큐레이션 분석기
카탈로그는 아직 재착륙되지 않았다 — 돌아올 때는 분석 크레이트 중 하나
(reports 또는 신설 `pccx-analytics`) 안에 자리 잡고 이 프리미티브로
등록될 것이다. 그때까지 pccx-core 는 날(raw) free 함수
(`roofline::analyze`, `bottleneck::detect`, …) 와 얇은
`pccx-reports::render_markdown` 래퍼를 그대로 노출한다.

## 프리미티브

```rust
// pccx_core::plugin
pub const PLUGIN_API_VERSION: u32 = 1;

#[derive(Debug, Clone, Copy)]
pub struct PluginMetadata {
    pub id:           &'static str,  // 안정 식별자
    pub api_version:  u32,           // PLUGIN_API_VERSION 과 일치 필수
    pub description:  &'static str,  // 한 줄 설명
}

pub trait Plugin {
    fn metadata(&self) -> PluginMetadata;
}

pub struct PluginRegistry<P: Plugin> {
    /* private Vec<P> */
}

impl<P: Plugin> PluginRegistry<P> {
    pub fn new() -> Self;
    pub fn register(&mut self, plugin: P) -> Result<(), PluginError>;
    pub fn all(&self)  -> &[P];
    pub fn find(&self, id: &str) -> Option<&P>;
    pub fn len(&self)  -> usize;
    pub fn is_empty(&self) -> bool;
}
```

`register` 만 실패 가능하며 — `api_version` 이 `PLUGIN_API_VERSION` 과
다른 플러그인은 거부된다. 오래된 헤더로 빌드된 외부 dylib 가 로드 전에
걸러진다. 중복 id 는 허용되며 `find` 는 먼저 등록된 쪽이 이긴다. 스레드
안전성은 호출자 책임이다 — 스레드 간 공유 시 `Mutex` / `RwLock` 으로
감쌀 것.

## 왜 `P` 에 제네릭인가?

단일 레지스트리 타입이 각 크레이트가 정의하는 모든 플러그인 종류를
수용한다 — `ReportFormat` (reports), `VerificationGate`
(verification), `IsaCompiler` / `ApiCompiler` (authoring),
`SurrogateModel` / `EvoOperator` / `PRMGate` (evolve),
`CompletionProvider` / `HoverProvider` / `LocationProvider` (lsp),
`ContextCompressor` / `SubagentRunner` (ai_copilot). 각 크레이트의
unstable 트레이트는 `Plugin` 의 서브트레이트이며, 자체 인스턴스의
`PluginRegistry<CrateTrait>` 를 가지고, 호출 지점에서 독립적으로
iterate 된다.

## 플러그인 등록

소비 크레이트는 자체 트레이트를 정의해 `Plugin` 의 서브트레이트로 삼고,
호스트에 레지스트리 인스턴스를 제공한다:

```rust
use pccx_core::plugin::{Plugin, PluginMetadata, PluginRegistry,
                        PLUGIN_API_VERSION};

// 1.  크레이트 트레이트 — `Plugin` 을 확장.
pub trait ReportFormat: Plugin {
    fn render(&self, trace: &NpuTrace) -> String;
}

// 2.  구체 구현.
pub struct MarkdownReport;

impl Plugin for MarkdownReport {
    fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            id:          "markdown",
            api_version: PLUGIN_API_VERSION,
            description: "GitHub-flavoured Markdown 리포트 렌더러",
        }
    }
}

impl ReportFormat for MarkdownReport {
    fn render(&self, trace: &NpuTrace) -> String { /* … */ }
}

// 3.  호스트가 구체 플러그인 타입으로 키잉된 레지스트리를 만들고
//     인스턴스를 등록한다.
let mut reports: PluginRegistry<MarkdownReport> = PluginRegistry::new();
reports.register(MarkdownReport)?;
```

한 trait object 뒤에 이질적 플러그인을 두고 싶은 크레이트는 (a) 각
구체 타입을 감싸는 얇은 enum 에 `Plugin` 을 구현하거나, (b) Phase 2/4
를 기다리면 된다 — 다가오는 dylib 로더가 C-ABI 계약 안정화 시점에
`Box<dyn CrateTrait>` 형태의 등록을 지원한다.

호출자는 `registry.all()` 로 순회하거나 `registry.find("markdown")`
으로 id 조회한다.

## 오류 표면

```rust
#[derive(Debug, Clone, thiserror::Error)]
pub enum PluginError {
    #[error("plugin '{id}' declares API version {got}; \
             host expects {expected}")]
    ApiMismatch { expected: u32, got: u32, id: &'static str },
}
```

오늘 런타임 오류는 `ApiMismatch` 하나뿐이다. dylib 로드 실패 (심벌
누락, C-ABI 불일치, unload 패닉) 는 Phase 2/4 동적 로더가 도착하면
같은 enum 에 들어온다 — 그때 레지스트리에 in-process `register` 위에
`load_dylib(path)` 가 추가된다.

## 안정성

`pccx_core::plugin` 의 모든 것은 **pccx-lab v0.3 까지 unstable** 이다.
enum 은 정신상 `#[non_exhaustive]` 이며 — Phase 1/2 창 동안 SemVer
major 범프 없이 신규 variant 가 추가된다.

Dylib 로딩 기계 (libloading + C-ABI `register()` 심볼 + unload 시
안전한 drop) 는 **아직 미구현** 이다. 아웃오브트리 플러그인이 실제로
출하될 때 Phase 2/4 중에 착륙한다. 그때까지 모든 레지스트리는
in-process `Vec<Box<dyn T>>` 이다.

## Phase 1 시점 크로스 크레이트 플러그인 트레이트

| 크레이트              | `Plugin` 으로 게이트된 트레이트                              |
|----------------------|--------------------------------------------------------------|
| `pccx-reports`       | `ReportFormat`                                               |
| `pccx-verification`  | `VerificationGate`                                           |
| `pccx-authoring`     | `IsaCompiler`, `ApiCompiler`                                 |
| `pccx-evolve`        | `SurrogateModel`, `EvoOperator`, `PRMGate`                   |
| `pccx-lsp`           | `CompletionProvider`, `HoverProvider`, `LocationProvider`    |
| `pccx-ai-copilot`    | `ContextCompressor`, `SubagentRunner`                        |

이 테이블의 모든 트레이트는 크레이트 자체 `plugin-api` 피처 뒤에
스캐폴딩 되어 있다. 구체 구현은 Phase 2–5 워크스트림 진행에 따라
점진적으로 착륙한다. 트레이트별 착륙 타임라인은 각 크레이트의
`CHANGELOG.md` 참고.

## 관련 문서

- [CLI 레퍼런스](cli.md) — 워크스페이스 분할 이후 오늘 존재하는
  바이너리와 각각이 실제로 담당하는 표면.
- [Copilot API](copilot.md) — 현재 `pccx-ai-copilot` 의 정적 헬퍼와
  Phase 2 pccx-lsp provider 트레이트.
- [연구 계보](research.md) — 현재 플레이스홀더. 인용 레지스트리는
  `core/src/research.rs` 에 있었으며 Phase 1 에서 제거되었다.

## 이 페이지 인용

pccx-core 플러그인 레지스트리 프리미티브를 논문, 블로그, AI 요약에서
참조한다면 다음을 인용해 주세요:

```bibtex
@misc{pccx_lab_analyzer_api_2026,
  title        = {pccx-core plugin registry: the generic primitive every pccx-lab crate hangs its trait-object plugins off},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/analyzer_api.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

프리미티브 소스는
<https://github.com/hkimw/pccx-lab/blob/main/crates/core/src/plugin.rs>
에 있다.
