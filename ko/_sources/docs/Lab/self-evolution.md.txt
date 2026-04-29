# 사이클 루프

_최근 개정: 2026-04-29._

`cycle/` 디렉토리는 pccx-lab 을 사용자 개입 없이 반복적으로 개선하는
**4역할 루프** 의 아티팩트 저장소이다.
루프는 Judge → Research → Plan → Implement 순으로 한 라운드를 완성하고,
다음 라운드에서 Judge 가 이전 구현물을 재평가한다.
아티팩트 경로, 진행 표, 현재 상태는 이 페이지에 집약한다.

루프 드라이버 규격: `cycle/driver.md`.
라운드 요약 인덱스: `cycle/ROUNDS.md`.

## 루프 구조

루프는 네 역할로 구성된다. 각 역할은 독립된 에이전트 프롬프트 파일을
갖는다 (`cycle/agents/` 아래).

**Judge** (`agents/judge.md`) 는 pccx-lab 의 현재 상태를 여러 상용 RTL 시뮬레이터·
GPU 프로파일러·FPGA 벤더 합성 도구와 객관적으로 비교해 점수를 매긴다.
UI, ISA 검증, API 무결성, UVM 커버리지, FPGA/ASIC 검증, 문서 등 주요
차원을 독립적으로 채점하고, 결과를 `round_NNN/judge_report.md` 에 기록한다.
라운드 N+1 의 Judge 는 이전 `judge_report_N` 과 `implemented_N` 을 함께
받으므로 절대 품질과 라운드 대비 진척도를 동시에 평가한다.

**Research** (`agents/research.md`) 는 arxiv, IEEE, ACM, 공식 벤더 문서를 조사해
Judge 가 지적한 약점에 대한 선행 기술·표준 인용을 수집한다.
모든 주장에 canonical 인용을 첨부해 `round_NNN/research_findings.md` 로
출력한다.

**Planner** (`agents/planner.md`) 는 Judge 와 Research 결과를 읽고 구체적인
구현 티켓으로 변환한다. 각 티켓에는 대상 파일 경로, 패치 방향, 수용 기준이
명시된다. 출력: `round_NNN/roadmap.md`.

**Implementer** 는 세 전문화 프롬프트로 분기된다
(`implementer_ui.md`, `implementer_core.md`, `implementer_bridge.md`).
`roadmap.md` 의 상위 티켓을 격리된 worktree 에서 병렬로 실행하고,
diff 와 테스트 결과를 `round_NNN/implemented_T*.md` 에 기록한다.
빌드·테스트 통과 없이 커밋하지 않는다.

## 라운드 아티팩트

각 라운드 디렉토리(`cycle/round_NNN/`)는 아래 파일 세트를 포함한다.

```{list-table} 라운드 디렉토리 표준 파일 세트
:name: tbl-round-artefacts
:header-rows: 1
:widths: 30 20 50

* - 파일
  - 생성 역할
  - 내용
* - `judge_report.md`
  - Judge
  - 차원별 채점 + 전체 등급 + Top-5 이슈
* - `research_findings.md`
  - Research
  - 이슈별 canonical 인용 + SOTA 요약
* - `roadmap.md`
  - Planner
  - T-1/T-2/T-3 티켓 (파일 경로, 패치, 수용 기준)
* - `implemented_T1.md`
  - Implementer
  - T-1 diff + 테스트 결과
* - `implemented_T2.md`
  - Implementer
  - T-2 diff + 테스트 결과
* - `implemented_T3.md`
  - Implementer
  - T-3 diff + 테스트 결과
```

라운드 완료 후 `cycle/ROUNDS.md` 에 한 줄 요약이 추가된다.
`cycle/STATE.json` 이 `round` 와 `phase` 를 갱신하고 다음 wake-up 이 예약된다.

## 진행 표

아래 표는 `cycle/ROUNDS.md` 를 바탕으로 라운드 1–6 의 Judge 등급과
핵심 산출물을 정리한 것이다.

```{list-table} 라운드별 Judge 등급 및 핵심 산출물
:name: tbl-round-grades
:header-rows: 1
:widths: 10 15 75

* - 라운드
  - Judge 등급
  - 핵심 산출물
* - 001
  - C-
  - T-1 WaveformViewer 실제 VCD/.pccx 수집, T-2 커버리지 병합, T-3 flame-graph bottleneck; 하드코딩 데이터 5개 갭 → 실제 IPC 티켓 3개 모두 착륙
* - 002
  - C
  - T-1/T-2 core+UI 등록 및 이름 수정, T-3 docs 접근성; 구현 에이전트 API 한도 도달 → 메인 스레드 완결
* - 003
  - C+
  - T-1 synthetic_fallback 제거 + resolveResource 수정, T-2 ELK 자동 레이아웃, T-3 두 번째 트레이스 실제 파일 피커; 가짜 수정 6개 적발
* - 004
  - B-
  - T-1 가짜 텔레메트리 제거(Math.random 20→9), T-2 Vivado 파서, T-3 flat-buf v2; 테스트 39→51
* - 005
  - B
  - T-1 SynthStatusCard, T-2 Monaco+Monarch 구문 강조, T-3 useLiveWindow 훅; 4라운드 Monaco 기술 부채 상환
* - 006
  - B-
  - T-1 step_to_cycle + useCycleCursor, T-2 Roofline 2.0 + resizable-panels v4 수정, T-3 스케줄러/가시성 훅 + 패널 재배선; 사이클 단위 UI + 60 fps 목표
```

라운드 7 은 `cycle/STATE.json` 기준 Judge 단계 대기 중이다
(2026-04-29 현재).

## 현재 상태

`cycle/STATE.json` 의 현재 내용:

```json
{
  "round": 7,
  "phase": "judge",
  "r1_grade": "C-",
  "r2_grade": "C",
  "r3_grade": "C+",
  "r4_grade": "B-",
  "r5_grade": "B",
  "r6_grade": "B-",
  "max_rounds": 50,
  "heartbeat_every": 10
}
```

`round: 7`, `phase: "judge"` 는 라운드 6 구현이 완료되었고
다음 Judge 평가가 아직 실행되지 않은 상태임을 나타낸다.

**정지 조건** (`cycle/driver.md` 참고):

- `cycle/HALT` 파일이 존재하면 루프는 즉시 정지한다. 셸에서
  `touch cycle/HALT` 로 활성화한다.
- `max_rounds: 50` 에 도달하면 사용자 확인 후 재개한다.
- 연속 2라운드에서 구현 커밋이 없으면 루프는 자동 정지한다 — 무한 재시도하지 않는다.
- 동일 Top-1 이슈가 3라운드 연속 반복되면 루프를 정지하고 에스컬레이션한다.

매 10번째 라운드(10, 20, 30, 40)에 직전 10라운드 등급 추세와 착륙 티켓을
요약하는 하트비트가 전송된다.

## 인용

```bibtex
@misc{pccx_self_evolution_2026,
  title        = {pccx-lab cyclic self-evolution loop: 4-role iterative design refinement},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/self-evolution.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
