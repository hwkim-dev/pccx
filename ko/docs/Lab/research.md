# pccx-lab 연구 계보

_페이지 과도기 상태. pccx-lab HEAD 기준 2026-04-24 재정비._

## 상태: 아키텍처 사이

이 페이지는 연구 계보 레인이 재구축되는 동안의 **플레이스홀더** 이다.
이전 리비전은 두 인용 테이블 (분석기 + UVM 전략) 을
`pccx_core::research::CITATIONS` — `core/src/research.rs` 에 있던
컴파일 타임 레지스트리 — 에서 자동 생성했다. Phase 1 의 모듈 이주가
그 파일을 제거했다. 인용 정보는 아직 다른 크레이트에 재착륙하지
않았으므로, 오늘 이 페이지가 재생성할 수 있는 권위 있는 온디스크
소스는 존재하지 않는다.

과거 테이블을 키잉하던 `used_by` id (`kv_cache_pressure`,
`phase_classifier`, `speculative_draft_probe`, `qoq_kv4_quantize`, …)
는 Phase 1 분할에서 마찬가지로 폐기된 분석기 / UVM 전략 slug 을
가리켰다. 코드에 더 이상 존재하지 않는 id 에 대해 낡은 테이블을
게시하는 것은 적극적으로 오해를 부르는 행위이므로, 새 홈이 도착할
때까지 테이블은 삭제했다.

## 작업이 이동한 곳

연구 기반 분석 코드는 하나도 삭제되지 않았다 — 그것이 구동하던
free 함수 (`pccx_core::roofline::analyze`,
`pccx_core::bottleneck::detect`, `pccx_core::synth_report::*`, …) 는
여전히 `pccx-core` 에서 출하된다. 다만 더 이상 인라인 인용을
실어 나르지 않을 뿐이다. `pccx-ai-copilot` 크레이트는
`list_uvm_strategies()` 로 노출되는 문헌 근거 UVM 전략 스텁 다섯
개를 유지한다 ([Copilot API](copilot.md) 참고).

재구축된 계보에 유입될 활성 설계 표면:

- `pccx-evolve` (Phase 5 시드) — `SurrogateModel`, `EvoOperator`,
  `PRMGate` 트레이트 스캐폴드 + 투기적 디코딩 프리미티브. EAGLE 계열
  레퍼런스는 여기에 속한다.
- `pccx-authoring` (`IsaCompiler`, `ApiCompiler`) — 과거 테이블의
  `authoring` 인접 행이 추적하던 ISA / API 스펙 계보의 상류.
- `pccx-lsp` — `CompletionSource` enum 이 모든 completion 을
  `Lsp` / `AiFast` / `AiDeep` / `Cache` 로 태그한다. AI-fast / AI-deep
  백엔드가 착륙하면 각자의 provenance 계보가 필요해진다.

pccx-lab 레포의 설계 문서 네 개
(`docs/design/phase2_intellisense.md`, `phase3_remote_backend.md`,
`phase4_insane_reports.md`, `phase5_alphaevolve.md`) 는 자신들의
작업이 계승하는 논문을 명시한다. 온디스크 레지스트리가 돌아올
때까지는 이 문서들이 가장 살아 있는 계보에 가장 가깝다.

## 이 페이지 재생성 시점

다음이 충족될 때 페이지는 처음부터 재생성된다:

1. 한 크레이트 (아마 `pccx-reports` 또는 신설 `pccx-analytics`) 가
   안정 `CITATIONS` 레지스트리를 재공개하고,
2. 큐레이션 분석기 / UVM 전략 세트가 테이블을 키잉할 안정
   `used_by` id 와 함께 재착륙.

그 시점에 두 테이블이 여기 다시 나타나며, 과거
`pccx_analyze --research-list` 표면을 대체하는 바이너리 (현재
바이너리 카탈로그는 [CLI 레퍼런스](cli.md) 참고) 에 의해 생성된다.

## 로드맵 포인터

- pccx-lab 레포: <https://github.com/hwkim-dev/pccx-lab>
- Phase 1 변경 이력: `crates/*/CHANGELOG.md`
- 페이즈별 설계 문서: `docs/design/phase{1,2,3,4,5}_*.md`

## 이 페이지 인용

```bibtex
@misc{pccx_lab_research_2026,
  title        = {pccx-lab research lineage (placeholder): registry rebuild underway after Phase 1 module exodus},
  author       = {Kim, Hwangwoo},
  year         = {2026},
  howpublished = {\url{https://hwkim-dev.github.io/pccx/ko/docs/Lab/research.html}},
  note         = {Part of pccx: \url{https://hwkim-dev.github.io/pccx/}}
}
```

이 페이지가 실제 테이블을 다시 싣게 되면 인용 키는 유지되므로,
이전에 인용된 참조는 계속 해석된다.
