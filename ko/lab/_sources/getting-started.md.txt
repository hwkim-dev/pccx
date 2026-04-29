# 시작하기

> pccx-lab 에 처음 입장하는 사용자를 위한 5 분 튜토리얼.
> VS Code `walkthroughs` 계약을 따라 3 단계로 구성됩니다:
> 앱 실행 → 샘플 `.pccx` 로드 → Flame Graph + Waveform 열기.

## 사전 준비

- pccx-lab 빌드가 완료되어야 합니다 (`cargo tauri dev` 또는 릴리스
  바이너리).
- 샘플 트레이스 `hw/sim/fixtures/smoke.pccx` 는
  [pccx-FPGA](https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260)
  저장소의 `hw/sim/run_verification.sh` 를 한 번 실행하면 생성됩니다.
  아직 없다면 이 단계를 먼저 수행하십시오.

---

## 1 단계 — pccx-lab 실행

```bash
cd ui
npm install            # 최초 1 회
npx tauri dev
```

기동되면 다음 화면이 나타납니다:

- **타이틀 바 + 메뉴 바** — File / Edit / View / Trace / Analysis / Verify / Run / Tools / Window / Help
- **탭 스트립** — Timeline / Flame Graph / Waveform / System Simulator /
  Memory Dump / …
- **AI Copilot 패널** (오른쪽 도킹, `Ctrl+\`` 로 토글)
- **Bottom Panel** (Log / Console / Telemetry, `Ctrl+J` 로 토글)

우측 상단 활동 바에서 Copilot 및 Telemetry 토글이 있습니다.
모든 아이콘 버튼에는 `aria-label` 이 부여되어 있어 스크린 리더로
사용할 수 있습니다 (WCAG 2.2 SC 2.1.1 / 2.4.3).

---

## 2 단계 — 샘플 `.pccx` 로드

두 가지 방법이 있습니다:

1. **메뉴**: `File ▸ Open .pccx…` (`Ctrl+O`)
2. **자동 로드**: 앱이 기동하면 기본적으로 `dummy_trace.pccx` 를
   로드하려고 시도합니다.
   성공 시 상단 탭 스트립 오른쪽에 `trace loaded` 배지가 초록색으로
   표시됩니다.

실제 pccx-FPGA 시뮬레이션 결과를 보려면 다음 경로를 선택하십시오:

```
../pccx-FPGA-NPU-LLM-kv260/hw/sim/fixtures/smoke.pccx
```

로드가 완료되면 상태 바에 `cycles` 와 `cores` 수치가 채워집니다.

---

## 3 단계 — Flame Graph + Waveform 열기

### Flame Graph

상단 탭 스트립에서 **Flame Graph** 를 클릭하십시오.

```{image} ../_static/screenshots/flamegraph-gemma3n.png
:alt: Gemma 3N E4B 디코드 스텝을 표현한 플레임 그래프
:width: 100%
```

조작:

- `Ctrl + 스크롤` — 시간축 줌 인/아웃
- 드래그 — 팬
- **Find Bottleneck** 버튼 — `detect_bottlenecks` IPC 를 호출해 가장
  혼잡한 창을 자동으로 찾아 AI 권장사항을 표시
- `Ctrl + Shift + D` — 두 번째 런과 비교하는 diff 모드 토글

### Waveform

**Waveform** 탭을 클릭하십시오. `.vcd` 파일을 직접 열려면
`File ▸ Open VCD…` (`Ctrl + Shift + O`) 를 사용합니다.

```{image} ../_static/screenshots/waveform.png
:alt: 2 커서 · 북마크 · 다중 radix 를 지원하는 웨이브폼 뷰어
:width: 100%
```

조작:

- `Alt + 클릭` — A 커서, `Shift + 클릭` — B 커서
- 우클릭 — 북마크 추가 / 제거
- `Ctrl + B` — 다음 북마크로 점프
- `Ctrl + 스크롤` — 줌

---

## 키보드 단축키 전체 목록

앱 어디서든 **`?`** 또는 **`F1`** 을 누르면 모든 단축키를 나열한
모달이 열립니다.

WCAG 2.2 SC 2.1.1 (Keyboard) 및 WAI-ARIA 1.2 §5.2.8.4 (aria-label)
기반의 접근성 패스가 적용되어 있으므로 마우스 없이 전체 IDE 를
탐색할 수 있습니다.

---

## 다음 단계

- `docs/pccx-format.md` — `.pccx` 바이너리 레이아웃 명세
- `docs/verification-workflow.md` — xsim → `.pccx` → UI 로 이어지는
  전체 검증 파이프라인
- `docs/modules/node-editor.md` — Blender-grade 노드 에디터 소개
