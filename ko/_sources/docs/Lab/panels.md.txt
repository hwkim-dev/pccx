# UI 패널 카탈로그

_pccx-lab HEAD 기준 2026-04-29. `ui/src/` 아래 주요 패널 파일 목록._

pccx-lab UI(`ui/src/`)는 flexlayout-react 탭 셸 위에 목적별로 나뉜
패널 컴포넌트들을 올린다. 각 패널은 `App.tsx`에서 lazy-import되고
`invoke(...)` 또는 Tauri 이벤트로 백엔드와 통신한다.

---

## 트레이스 시각화

### `Timeline.tsx` — `Timeline`

`trace-loaded` 이벤트를 수신한 뒤 `.pccx` 평탄 버퍼를 캔버스에
그린다. 이벤트 수가 `MMAP_EVENT_THRESHOLD`(50,000) 를 초과하면
mmap 스트리밍 경로(`mmap_open_trace` → `mmap_viewport`)로 자동
전환되어 대용량 트레이스도 메모리 초과 없이 렌더링된다.
뷰포트 이동 중 IPC 호출은 100 ms 디바운스 + RAF 스케줄러
(`useRafScheduler`)로 코얼레스트(coalesced)된다. 수직 행은 코어 ID,
수평 축은 클럭 사이클이며, `useCycleCursor`가 여러 패널 간
커서 위치를 공유한다.

- 피드 커맨드: `fetch_trace_payload`, `mmap_open_trace`, `mmap_viewport`
- 이벤트: `trace-loaded` (Tauri emit)

### `FlameGraph.tsx` — `FlameGraph`

평탄 버퍼를 계층별(Fetch / Decode / MAC / DMA / Retire) 스팬으로
버킷팅해 플레임 그래프로 그린다. 비교 모드에서는 `load_pccx_alt`로
적재된 두 번째 트레이스(`trace_b` 슬롯)의 평탄 버퍼를
`fetch_trace_payload_b`로 받아 Gregg 2018 차분 플레임 그래프
계약(IEEE SW §III-D)으로 렌더링한다. RAF 스케줄러가 120 Hz 마우스
이벤트를 vsync당 한 번의 페인트로 감쇄한다.

- 피드 커맨드: `fetch_trace_payload`, `fetch_trace_payload_b`
- 비교 경로: `load_pccx_alt`

### `WaveformViewer.tsx` — `WaveformViewer`

IEEE 1364-2005 VCD 파일을 신호 라인별로 시각화하는 다중 채널
파형 뷰어. `parse_vcd_file`이 반환하는 `WaveformDump`를
소비하며, 신호별 이진 탐색(`O(log n)`)으로 주어진 틱의 값을
조회한다. 라디스(radix)를 `bin` / `oct` / `hex` / `dec` / `ascii`로
전환할 수 있고, `useLiveWindow` 훅으로 라이브 창 샘플을 오버레이한다.
커서는 `useCycleCursor`로 Timeline과 동기화된다.
Tauri `export_vcd` 커맨드로 현재 캐시된 `.pccx` 트레이스를 VCD로 내보낼 수 있다.

- 피드 커맨드: `parse_vcd_file`, `export_vcd`

### `MemoryDump.tsx` — `MemoryDump`

pccx v002 KV260 메모리 맵(BRM, 가중치 SRAM, AXI HP 포트)에 대한
접근 패턴을 16진수 그리드 + 접근 히트맵으로 시각화한다.
미리 계산된 256엔트리 HEX LUT(`HEX_LUT`)로 렌더링 속도를 최적화한다.
`useCycleCursor`로 현재 사이클의 리드/라이트 접근을 강조 표시한다.
직접 Tauri 커맨드에 의존하지 않고 평탄 버퍼에서 접근 레코드를 파싱한다.

- 피드 커맨드: `fetch_trace_payload` (간접)

---

## 분석

### `Roofline.tsx` — `Roofline`

ECharts 기반 루프라인 차트. `analyze_roofline`이 반환하는
`RooflinePoint`(단일 계층)와 `analyze_roofline_hierarchical`이 반환하는
`RooflineBand` 목록(캐시 인식 다계층 — Ilic 2014
DOI 10.1109/L-CA.2013.6, Yang 2020 arXiv:2009.02449)을 동시에 그린다.
각 메모리 계층 밴드는 대시 천장선 + 궤적 선분으로 표시되어
워크로드가 pccx 메모리 계층 어디에 머무는지를 나타낸다.
`useVisibilityGate` + `useRafScheduler`로 탭이 숨겨진 동안 ECharts
인스턴스를 일시 정지시킨다.

- 피드 커맨드: `analyze_roofline`, `analyze_roofline_hierarchical`

### `RooflineCard.tsx` — `RooflineCard`

`VerificationSuite.tsx` 내에 임베드되는 콤팩트 루프라인 요약 카드.
`analyze_roofline`의 `RooflinePoint`를 소비해 산술 강도,
달성 GOPS, compute/memory-bound 판정을 한 줄 뱃지로 표시한다.
Tauri IPC가 없는 브라우저 전용 빌드에서는 경고 배너를 표시하고 실패하지 않는다.

- 피드 커맨드: `analyze_roofline`

### `BottleneckCard.tsx` — `BottleneckCard`

`VerificationSuite.tsx` 안에 임베드되는 병목 요약 카드.
`detect_bottlenecks`가 반환하는 `BottleneckInterval` 배열을
소비해 DMA 읽기 / 쓰기 / systolic stall / 배리어 동기화 구간을
비율 바로 표시한다.

- 피드 커맨드: `detect_bottlenecks`

### `OccupancyCalculator.tsx` — `OccupancyCalculator`

MAC 배열 크기(N×N, 범위 4–16), 활성화 SRAM, 가중치 SRAM,
파이프라인 깊이, DMA 채널 수를 파라미터로 받아 KV260 PL 패브릭
300 MHz 기준 점유율(%), INT4 TOPS 처리량, 필요 메모리 대역폭을
실시간 계산한다. Tauri 커맨드에 의존하지 않으며 전적으로 프런트엔드
순수 계산이다.

- 피드 커맨드: 없음 (독립 계산기)

### `PipelineDiagram.tsx` — `PipelineDiagram`

Fetch → Decode → Dispatch → MAC → Accumulate → Activation →
DMA_Write / DMA_Read 9단 파이프라인을 SVG 흐름도로 그린다.
각 단계는 `utilization`(0.0–1.0)을 색으로, `stalled` 여부를
빨간 테두리로 시각화하며, 클릭 시 사이드 패널에서 상세 메트릭을 표시한다.
라이브 창(`useLiveWindow`) 폴링으로 실시간 스톨 상태를 업데이트한다.

- 피드 커맨드: `fetch_live_window` (훅 경유)

### `MetricTree.tsx` — `MetricTree`

계층적 메트릭 트리 인스펙터. 루트 그룹(처리량, 메모리, 파이프라인,
검증)을 접고 펼 수 있으며, 리프 노드는 단위·범위·경고/오류 임계값을
갖는다. 값이 임계값 이하/이상이면 배지 색상이 전환된다. 트레이스
데이터를 직접 소비하지 않고 부모(VerificationSuite 또는 App)로부터
메트릭 값을 props로 받는다.

- 피드 커맨드: 없음 (props 주입)

---

## 하드웨어 뷰

### `HardwareVisualizer.tsx` — `HardwareVisualizer`

ELK.js 자동 레이아웃 위에 pccx v002 KV260 모듈 계층
(`hw/rtl/` 구조 반영)을 블록 다이어그램으로 그린다.
각 모듈은 종류(`ctrl` / `mat` / `vec` / `sfu` / `mem` / `bus` / `io`)별로
색 구분되며, 클릭 시 포트 목록과 RTL 경로를 표시한다.
`step_to_cycle` 커맨드로 커서 사이클에서의 레지스터 + MAC 배열 상태를
받아 활성 모듈을 강조 표시한다. ECharts 미니 차트가 모듈 내
활용도를 오버레이한다. `useRafScheduler` + `useVisibilityGate`로
숨겨진 탭에서는 렌더링을 중단한다.

- 피드 커맨드: `step_to_cycle`, `analyze_roofline`, `fetch_trace_payload`

### `CanvasView.tsx` — `CanvasView`

Three.js 기반 32×32 MAC 배열 3D 히트맵. 각 셀의 utilisation을
[0,1] 범위의 HSL 색상(파랑=유휴, 초록=활성, 빨강=핫)으로 표현한다.
`synth_heatmap` 커맨드가 반환하는 `ResourceHeatmap` JSON을
인스턴스화드 메시(instanced mesh) 인스턴스 색상 버퍼로 업로드해
GPU 드로우 콜을 최소화한다. `useVisibilityGate`로 탭이 숨겨지면
Three.js 애니메이션 루프를 정지시킨다.

- 피드 커맨드: `synth_heatmap`

### `SynthStatusCard.tsx` — `SynthStatusCard`

Vivado `report_utilization` + `report_timing_summary` 출력을 파싱해
LUT / FF / DSP / BRAM 사용률과 WNS/TNS 슬랙을 카드 형식으로 표시한다.
`load_synth_report`(합성 리포트) 또는 `load_timing_report`(타이밍 리포트)
중 하나 이상이 있어야 렌더링된다. 타이밍 충족 시 초록색, 미충족 시
빨간색 뱃지를 표시한다.

- 피드 커맨드: `load_synth_report`, `load_timing_report`, `synth_heatmap`

### `NodeEditor.tsx` — `NodeEditor`

React Flow(`@xyflow/react`) 기반 비주얼 노드 편집기. pccx 파이프라인
단계를 드래그 앤 드롭으로 연결할 수 있는 인터랙티브 캔버스이며,
커스텀 노드 타입(컴퓨트, 메모리, I/O, 시퀀서)을 지원한다. 현재
트레이스 커맨드에 직접 연결되지 않으며, 상위 ScenarioFlow 또는
App에서 노드 그래프 상태를 props로 받는다.

- 피드 커맨드: 없음 (그래프 편집기)

---

## 검증 / 보고

### `VerificationSuite.tsx` — `VerificationSuite`

검증 워크플로우 전체를 탭(ISA / API / UVM / Synth / Golden) 형태로
통합하는 컨테이너 패널. `run_verification`을 호출해
`hw/sim/run_verification.sh`를 실행하고 `PASS`/`FAIL` 라인을
파싱해 테스트벤치별 결과를 표시한다. `merge_coverage`로 xsim 커버리지
JSONL을 병합하고 빈 히트 테이블을 가상 스크롤(`@tanstack/react-virtual`)로
렌더링한다. `SynthStatusCard`, `VerificationRunner`, `RooflineCard`,
`BottleneckCard`를 서브 컴포넌트로 내장한다.

- 피드 커맨드: `run_verification`, `merge_coverage`, `list_api_calls`,
  `validate_isa_trace`

### `VerificationRunner.tsx` — `VerificationRunner`, `GoldenDiffCard`, `SanitizeCard`

`VerificationSuite` 하위에 임베드되는 세 컴포넌트.

- `VerificationRunner`: `run_verification` 결과를 테스트벤치 행 테이블로
  표시하고, 개별 `.pccx` 경로를 클릭하면 Timeline에 로드한다.
- `GoldenDiffCard`: `verify_golden_diff`를 호출해 기준 JSONL 대비
  후보 트레이스를 비교하고, `verify_report`로 렌더링된 Markdown
  리포트를 DiffView에 전달한다.
- `SanitizeCard`: `verify_sanitize`로 입력 콘텐츠를 정제(NUL 제거,
  BOM/CRLF 정규화, 후행 쉼표 허용)하고 적용된 fixup 목록을 표시한다.

- 피드 커맨드: `run_verification`, `verify_golden_diff`, `verify_report`,
  `verify_sanitize`

### `DiffView.tsx` — `DiffView`

좌우 분할 side-by-side 텍스트 diff 뷰어. 줄 단위 myers diff를 직접
계산하며(외부 라이브러리 없음), `@tanstack/react-virtual`로 대형
파일도 가상 스크롤로 처리한다. `equal` / `added` / `removed` /
`modified` 네 가지 행 종류를 색으로 구분한다.
`GoldenDiffCard`가 `verify_golden_diff` 결과를 이 컴포넌트에 전달한다.

- 피드 커맨드: 없음 (상위로부터 문자열 주입)

### `ReportBuilder.tsx` — `ReportBuilder`

섹션 선택 UI를 통해 실행 요약, 방법론, 하드웨어 구성, 타임라인 분석,
코어 utilisation, 병목 분석, 루프라인, 커널 분해 등을 on/off하고
`generate_markdown_report`(Markdown) 또는 `generate_report`(HTML)를
호출해 완성된 리포트를 생성한다. `useLiveWindow`로 라이브 창 샘플을
섹션 미리보기에 사용한다.

- 피드 커맨드: `generate_markdown_report`, `generate_report`

### `ReportGenerator.tsx` — `ReportGenerator`

Radix UI Dialog를 사용하는 단순 트리거 컴포넌트. `generate_report`를
호출해 현재 캐시된 트레이스의 리포트를 요청하고, 생성 중 로딩
스피너를 표시한다.

- 피드 커맨드: `generate_report`

### `TestbenchAuthor.tsx` — `TestbenchAuthor`

ISA 인스트럭션 시퀀스를 세 가지 동기화된 뷰(ISA 어셈블리, API TOML,
SystemVerilog UVM 시퀀스)로 동시에 표시하는 크로스-레벨 저작 도구.
ISA 또는 API 레벨에서 편집하면 SV 패널이 자동 갱신된다(역방향은
현재 미구현). `generate_uvm_sequence_cmd`로 전략별(`l2_prefetch`,
`barrier_reduction`) SV UVM 시퀀스 스텁을 생성한다.

- 피드 커맨드: `generate_uvm_sequence_cmd`, `list_uvm_strategies`

---

## 편집 / 보조

### `CodeEditor.tsx` — `CodeEditor`

Monaco(VSCode 편집기 엔진) 기반 SystemVerilog 소스 편집기.
`monarch_sv.ts`에서 정의된 Monarch 문법으로 SV 하이라이팅을 적용하며,
`sv_completions` / `lsp_hover` / `lsp_complete` / `lsp_diagnostics`
네 개의 LSP 커맨드를 Monaco `registerCompletionItemProvider` /
`registerHoverProvider` / `setModelMarkers`에 연결한다.
`read_text_file` / `write_text_file`로 파일 I/O를 처리하며,
`parse_sv_file`, `generate_block_diagram`, `generate_fsm_diagram`,
`generate_module_detail`, `generate_sv_docs`로 정적 분석 뷰를 제공한다.

- 피드 커맨드: `sv_completions`, `lsp_hover`, `lsp_complete`,
  `lsp_diagnostics`, `read_text_file`, `write_text_file`,
  `parse_sv_file`, `generate_block_diagram`, `generate_fsm_diagram`,
  `generate_module_detail`, `generate_sv_docs`

### `ScenarioFlow.tsx` — `ScenarioFlow`

React Flow 기반 ISA 실행 시나리오 시각화. ISA 이벤트(cycle / op / body /
unit)와 데이터 이동 엣지를 플로우 그래프로 렌더링한다. i18n 지원.
직접 Tauri 커맨드에 의존하지 않으며, 부모 탭으로부터 시나리오 데이터를
받는다.

- 피드 커맨드: 없음 (데이터는 props 또는 로컬 상태)

### `ExtensionManager.tsx` — `ExtensionManager`

`get_extensions`로 `ai_copilot` 익스텐션 목록을 받아 카테고리별
(Local LLM, Hardware Acceleration, Cloud Bridge, Analysis Plugins,
Export Plugins) 카드 그리드로 표시한다. 설치 진행률 표시 UI가
있으나 실제 다운로드 로직은 현재 스텁이다.

- 피드 커맨드: `get_extensions`

### `BottomPanel.tsx` — `BottomPanel`

도킹 가능한 바텀/사이드 패널. 터미널 로그, 라이브 활동, 정보의 세 탭을
갖는다. `useLiveWindow`로 2 Hz 폴링해 MAC/DMA/stall 활동을 로그 스트림에
추가한다. `@tanstack/react-virtual`로 로그 행(22 px 고정 높이)을
가상 스크롤한다. `dock`(left / right / bottom) prop로 배치 방향을
전환한다.

- 피드 커맨드: `fetch_live_window` (훅 경유)

### `MainToolbar.tsx` — `MainToolbar`

재생/일시정지/정지/스텝/새로고침/레이어/디버그 액션을 14 px 아이콘
버튼 행으로 노출하는 상단 툴바 컴포넌트. i18n 지원. 직접 Tauri 커맨드를
호출하지 않고 `onAction` 콜백을 통해 `App.tsx`에 이벤트를 위임한다.

- 피드 커맨드: 없음 (App.tsx 위임)

### `MenuBar.tsx` — `MenuBar`

File / View / Analyze / Tools / Help 메뉴를 드롭다운으로 제공하는
네이티브 스타일 메뉴바. `.pccx` 열기(`Ctrl+O`), VCD 열기
(`Ctrl+Shift+O`), 세션 저장, 평탄 버퍼 내보내기, 트레이스 생성 등
파일 관련 액션과 테마 전환, 패널 표시/숨김, 익스텐션 관리자 진입
등의 뷰 액션을 `onAction` 콜백으로 위임한다.

- 피드 커맨드: 없음 (App.tsx 위임)

### `StatusBar.tsx` — `StatusBar`

하단 상태바. 트레이스 로드 여부, 총 사이클 수, 코어 수, 라이선스 문자열,
활성 탭 이름을 표시한다. 디버그 모드에서는 rAF 프레임 카운터로
FPS를 노출한다. `get_license_info`는 App 레벨에서 호출되고
`license` prop으로 전달된다.

- 피드 커맨드: 없음 (props)

### `FileTree.tsx` — `FileTree`

`read_file_tree`가 반환하는 `FileNode` 트리를 탐색기 사이드바로
렌더링한다. 디렉토리 접기/펼치기, 파일 유형별 아이콘(SV, TOML, JSON,
바이너리 등), `onFileOpen` 콜백을 지원한다. 읽기 실패한 엔트리는 조용히
건너뛴다.

- 피드 커맨드: `read_file_tree`

---

## 이 페이지 인용

```bibtex
@misc{pccx_lab_panels_2026,
  title        = {pccx-lab UI panel catalogue: trace visualisation, analysis,
                  hardware view, verification, and editing components},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/panels.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

패널 소스는 <https://github.com/hkimw/pccx-lab/tree/main/ui/src/> 에 있다.
