# 로드맵

상세 실행 보드는 [GitHub Projects][project]에서 관리한다. 이 페이지는
pccx 생태계 전체의 현재 릴리스 방향만 짧게 요약한다.

## Now — v0.2.0: FPGA bring-up and closure

- `pccx-FPGA-NPU-LLM-kv260` 의 남은 RTL 통합 마무리
- `pccx-lab` 기반 trace-driven verification
- Sail execute 증분 작업
- xsim / KV260 bring-up 로그 정리
- 검증 근거가 공개되기 전까지 production-ready / timing-closed 주장 금지

추적 이슈: [pccxai/pccx#28 — v0.2.0 umbrella][v020].

## Next — v0.3.0: Lab 확장성 + 사용자 워크플로 분리

- pccx-lab plugin system (CLI 우선, GUI 후속)
- AI worker 를 위한 controlled MCP 인터페이스
- pccx-lab 에서 `pccx-systemverilog-ide` 를 spin-out
- `pccx-llm-launcher` MVP 기획
- pccx-lab ↔ IDE handoff 포맷
- pccx-lab ↔ launcher workflow boundary

## Later — v0.4+: AI 보조 하드웨어/소프트웨어 워크플로

- AI-assisted SystemVerilog development workflow
- evolutionary generate / simulate / evaluate / refine loop
- testbench / log / waveform feedback loop
- VS Code extension 경로
- 추가 모델 / 디바이스 지원
- 논문 수준의 재현 가능한 아티팩트

## 링크

- GitHub Project (source of truth): <https://github.com/orgs/pccxai/projects/1>
- v0.2.0 umbrella: <https://github.com/pccxai/pccx/issues/28>

[project]: https://github.com/orgs/pccxai/projects/1
[v020]: https://github.com/pccxai/pccx/issues/28
