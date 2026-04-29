# Architecture Adoption Record — 2026-04-25

## 1. 배경

외부 다중-AI 협의 문서(2026-04-25)가 5개 모델의 교차 검토를 통해 12개의 아키텍처 권고안을 제시하였다.
본 문서는 각 권고안을 프로젝트 현황과 대조하여 ACCEPT / ADAPT / REJECT / 이미 완료 중 하나로
판정하고, 우선순위와 근거를 기록한다. 이 기록은 이후 모든 에이전트 및 기여자의 의사결정 기준으로 사용된다.

---

## 2. 판정 테이블

| # | 항목 | 판정 | 우선순위 | 현재 상태 | 근거 |
|---|------|------|---------|-----------|------|
| 1 | Svelte 5 마이그레이션 | **REJECT** | — | React 19, 20+ 컴포넌트 | 주석 1 |
| 2 | CLI/GUI 분리 | **이미 완료** | — | 10-crate 워크스페이스 완료 | 주석 2 |
| 3 | pccx-cli 바이너리 | **ACCEPT** | P2 | 해당 crate 없음 | 주석 3 |
| 4 | Typed newtypes | **ACCEPT** | P1 | CycleCount, CoreId, EventTypeId, MemAddr, TraceId 도입 완료 (typed.rs). trace.rs/step_snapshot.rs 이식 진행 중 | 주석 4 |
| 5 | IPC 경계 안전성 (u64) | **ADAPT** | P1 | generation_id: u32 RegisterSnapshot에 추가 완료. useCycleCursor.ts에서 generation 기반 stale 응답 폐기 구현 | 주석 5 |
| 6 | ts-rs 타입 생성 | **ACCEPT** | P2 | 수동 유지 중 | 주석 6 |
| 7 | MMAP + viewport 스트리밍 | **ACCEPT** | P2 | 개념 참조만 존재 | 주석 7 |
| 8 | pccx-schema DTO crate | **ACCEPT** | P2 | 없음 | 주석 8 |
| 9 | Dioxus 장기 옵션 | **NOTED** | P3 | 해당 없음 | 주석 9 |
| 10 | macOS 배포 안전성 | **ADAPT** | P3 | 미검증 플랫폼 | 주석 10 |
| 11 | Object pooling / $state.raw | **REJECT** | — | Svelte 전용 패턴 | 주석 11 |
| 12 | ArrayBuffer 바이너리 IPC | **이미 완료** | — | fetch_trace_payload 패턴 | 주석 12 |

### 근거 주석

**주석 1 — Svelte 5 마이그레이션 REJECT**
React 19 코드베이스는 20개 이상의 프로덕션 컴포넌트, 12개의 lazy-loaded 경로로 구성된다.
`@monaco-editor/react`, Three.js, React Flow, ECharts 연동이 모두 React 생태계에 기반하며,
동등한 Svelte 바인딩이 존재하지 않는다. 마이그레이션 비용이 기술적 이득을 초과한다.

**주석 2 — CLI/GUI 분리 이미 완료**
Phase 1에서 10-crate 워크스페이스 분리가 완료되었다. 외부 문서의 용어는 이 구조에
직접 매핑된다: 외부 문서의 `pccx-core` = `crates/core/`, `pccx-tauri` = `ui/src-tauri/`.
`pccx-core`는 UI 의존성을 일절 가지지 않으며, 어떤 crate도 `pccx-ide`에 의존하지 않는다.

**주석 3 — pccx-cli ACCEPT (P2)**
CI 환경 및 헤드리스 트레이스 분석에 유용하다. GUI가 1차 인터페이스이므로 긴급하지 않다.
필요 시 `crates/cli/`로 추가한다.

**주석 4 — Typed newtypes ACCEPT (P1)**
`CycleCount(u64)`, `MemAddr(u64)`, `TraceId(u64)` 를 `crates/core/`에 도입하고
checked arithmetic을 적용한다. 기존 코드에 단계적으로 이식한다.

**주석 5 — IPC 경계 안전성 ADAPT**
2^53을 초과할 가능성이 있는 u64 필드(절대 메모리 주소 등)는 String으로 직렬화한다.
NPU 트레이스의 일반적 사이클 카운트처럼 안전 정수 범위 내에 머무는 값은 number를 유지하여
단순성을 보존한다. 모든 비동기 viewport 응답에 `generation_id: u32`를 추가한다.

**주석 6 — ts-rs ACCEPT (P2)**
`pccx-schema` crate 도입 시 함께 채택한다. 현재 규모에서는 수동 타입 유지가 가능하다.

**주석 7 — MMAP + viewport 스트리밍 ACCEPT (P2)**
100 MB 이상의 프로덕션 규모 트레이스에 필수적이다. 현재 데모 트레이스는 소규모이나,
트레이스 크기가 증가하는 시점에 맞춰 구현한다. `live_window.rs`의 개념적 참조를 출발점으로 삼는다.

**주석 8 — pccx-schema DTO crate ACCEPT (P2)**
ts-rs 채택과 묶어 진행한다. Rust DTO 정의를 한 곳에서 관리하고 TypeScript 타입을 자동 생성한다.

**주석 9 — Dioxus 장기 옵션 NOTED**
`pccx-core`가 UI 의존성을 전혀 가지지 않으므로 프론트엔드 교체는 구조적으로 지원된다.
Blitz 렌더러가 성숙하는 시점에 재평가한다. 현재 조치 없음.

**주석 10 — macOS 배포 ADAPT**
1차 타깃은 Linux(Ubuntu 24.04)이다. macOS 지원이 활성화될 때 overlay titlebar 설정을 적용한다.

**주석 11 — Object pooling / $state.raw REJECT**
Svelte 5 전용 패턴이다. React 동등물(`useMemo`, `useCallback`, `React.lazy`)은 이미 적용되어 있다.

**주석 12 — ArrayBuffer 바이너리 IPC 이미 완료**
`fetch_trace_payload` 패턴이 `Vec<u8>` → TypedArray 변환을 구현하고 있다.
원시 트레이스 데이터는 IPC 경계를 직접 통과하지 않으며, 집계된 viewport 타일만 전달된다.

---

## 3. 우선순위 로드맵

| 단계 | 항목 |
|------|------|
| **P0** (즉시) | 없음 — 현재 아키텍처는 정상 상태이다 |
| **P1** (다음 스프린트) | ✓ 완료 (Sprint 1): Typed newtypes (`CycleCount`, `CoreId`, `EventTypeId`, `MemAddr`, `TraceId`), viewport IPC에 `generation_id` 추가 |
| **P1** (완료) | ✓ 완료 (Sprint 4): trace.rs/step_snapshot.rs/roofline.rs/bottleneck.rs/chrome_trace.rs/api_ring.rs/vcd_writer.rs/live_window.rs 타입 이식 |
| **P2** (중기) | ✓ 완료 (Sprint 6) — MmapTrace viewport + tile, `pccx-cli` crate, `pccx-schema` + ts-rs 채택 |
| **P3** (장기) | Dioxus 재평가 (Blitz 성숙 후), macOS 배포 강화 |

---

## 4. 채택된 IPC 경계 규칙

다음 규칙은 외부 협의 문서의 권고를 수용하여 프로젝트 표준으로 확정한다.

1. **u64/u128 직렬화**: 2^53을 초과할 수 있는 필드는 JSON String으로 직렬화한다.
2. **generation_id**: 모든 비동기 viewport 응답 DTO에 `generation_id: u32`를 포함한다.
   클라이언트는 자신이 발행한 세대보다 오래된 응답을 폐기한다.
3. **대용량 바이너리**: `Vec<u8>` / ArrayBuffer 채널을 사용하며 JSON 경로를 거치지 않는다.
4. **IPC 데이터 최소화**: 원시 트레이스 데이터는 IPC 경계를 넘지 않는다. viewport 타일만 전달된다.
5. **타입 대응 강제**: Rust DTO와 TypeScript 타입의 대응 관계를 문서화한다.
   현재는 수동 유지, P2 이후 ts-rs로 자동화한다.

---

## 5. 변경하지 않는 것

- 프론트엔드 프레임워크: React 19 + TypeScript + Vite 7 유지
- 워크스페이스 구조: 10개 crate + `ui/` 레이아웃 유지
- Svelte 컴포넌트 및 Svelte 스토어 도입 없음
- 현재 10개 crate 외 조기 분리 없음

---

## 6. 구현 이력

| 스프린트 | 날짜 | 완료 항목 |
|---------|------|----------|
| Sprint 1 | 2026-04-25 | typed.rs newtypes (CycleCount, CoreId, EventTypeId, MemAddr, TraceId), RegisterSnapshot.generation_id, CanvasView DataTexture 최적화, CX lexer UTF-8 테스트 (28 pass), SV parser M6.1 완성 + 버그 수정 (29 pass) |
| Sprint 2 | 2026-04-25 | WaveformViewer RAF 통합 + 양방향 커서 동기화, @tanstack/react-virtual 리스트 가상화, FlameGraph RAF 마이그레이션, MemoryDump 전면 최적화 (HEX_LUT + O(N) canvas + 가상 스크롤) |
| Sprint 3 | 2026-04-26 | LSP M2.2 SV hover + diagnostics (65 tests), Roofline ECharts 최적화 + useLiveWindow 공유 폴링, ReactFlow 13개 커스텀 노드 React.memo, BottomPanel useLiveWindow 통합 + 가상 스크롤 로그 |
| Sprint 4 | 2026-04-26 | Core typed newtype 이식 완료 (trace/step_snapshot/roofline/chrome_trace/api_ring), Verification golden_diff abs_tolerance + robust_reader 복구 휴리스틱 (49 tests), Evolve speculative TreeMask + SpeculativeVerifier (25 tests), CodeEditor/CxPlayground useMemo 최적화, FileTree 가상 트리 + CommandPalette fuzzy 검색 40+ 명령, Dashboard 카드 React.memo + theme 통일 |
| Sprint 5 | 2026-04-26 | Remote daemon (ConnectionConfig, TraceStreamProtocol, HealthCheck — 20 tests), i18n 30+ KO 번역 키 + StatusBar FPS 카운터 + TitleBar/MainToolbar theme 통일, Core roofline/bottleneck/coverage 테스트 34개 추가 |
| Sprint 6 | 2026-04-26 | Phase 2 M2.3 MonacoBridge JSON-RPC 프로토콜 (14 tests), M2.4 ISA TOML completion provider (10 tests), Monaco LSP 클라이언트 통합 (hover/completion/diagnostics), MMAP 트레이스 리더 memmap2 viewport (9 tests), CycleCount Add/Sub/Mul/Div arithmetic traits (19 tests) |
| Sprint 7 | 2026-04-26 | M6.3 FSM state extraction + Mermaid stateDiagram-v2 (13 tests), M4.1 report engine document tree + HTML renderer (13 tests), DiffView LCS diff + virtual scroll 재작성, Verification golden-diff/sanitize Tauri IPC + VerificationRunner/Suite 프론트엔드 통합 |
| Sprint 8 | 2026-04-26 | CX LSP cx_provider hover/completion/diagnostics (30 tests), FSM + block diagram Tauri IPC 명령, ScenarioFlow diagram 탭 (Block/FSM), ReportBuilder HTML/Markdown 백엔드 연결 + iframe 렌더 + export, CxPlayground Monaco LSP 통합 |
