---
myst:
  html_meta:
    description lang=ko: |
      pccx-lab 설치부터 첫 트레이스 로드까지 — cargo build, npm ci,
      Linux WebKitGTK 우회, 샘플 .pccx 로딩, 주요 패널 진입.
---

# pccx-lab 퀵스타트

`.pccx` 트레이스를 처음 여는 것을 목표로 한다. 빌드, Linux 우회, 패널
진입까지 최단 경로를 제공한다.

```{contents} 이 페이지 목차
:depth: 2
:backlinks: none
```

## 설치

pccx-lab 은 Rust 워크스페이스(`crates/`) + React/Vite 프론트엔드(`ui/`) 로
구성된 Tauri v2 데스크톱 앱이다. Rust 워크스페이스는 9개 크레이트로 구성된다:
`core`, `reports`, `verification`, `authoring`, `evolve`, `lsp`, `remote`,
`uvm_bridge`, `ai_copilot`. 모든 크레이트는 `pccx-core` 를 의존 그래프의
싱크로 사용하며 `pccx-ide`(`ui/src-tauri/`) 와 `pccx-remote` 는 터미널
바이너리다.

**사전 조건**

| 항목 | 요구사항 |
|---|---|
| OS | Ubuntu 24.04 LTS (1차 지원); macOS · Windows 미검증 |
| Rust | `rustup` stable (`rust-toolchain.toml` 참고) |
| Node.js | Vite 7 호환 LTS |
| 디스플레이 | X11 세션 (Wayland 는 현재 릴리스에서 지원하지 않음) |
| 선택 | Xilinx KV260 보드 — 실측 트레이스 생성 시 |

```bash
# 1. 저장소 클론
git clone https://github.com/hkimw/pccx-lab.git
cd pccx-lab

# 2. Rust 워크스페이스 전체 빌드 (헤드리스 CLI 포함)
cargo build --release

# 3. 프론트엔드 의존성 설치 및 개발 모드 실행
cd ui
npm ci
npm run tauri dev
```

`npm run tauri dev` 는 Rust 백엔드 재빌드 + Vite 핫리로드를 함께 실행한다.
릴리스 바이너리만 필요하면 `cargo tauri build` 를 대신 사용한다.

## Linux WebKitGTK 우회

Linux 에서는 반드시 다음 환경변수를 설정한 뒤 앱을 실행해야 한다:

```bash
export WEBKIT_DISABLE_DMABUF_RENDERER=1
export GDK_BACKEND=x11
npm run tauri dev
```

**이유**: Three.js + Monaco + WebKitGTK 2.50 가 DMA-BUF 컴포지팅을 동시에
사용할 때 렌더러가 멈춘다. `ui/src-tauri/src/main.rs` 가 앱 시작 시
이 변수를 자동으로 설정하지만, 셸에서 직접 실행하는 경우에는 위와 같이
명시적으로 선언해야 한다. XWayland 없는 순수 Wayland 세션은 현재 릴리스에서
지원하지 않는다.

위 우회 후에도 멈춤이 재현되면 `pccx-lab` 이슈 트래커와
`CLAUDE_TASKS_lab.md` §3 의 5단계 에스컬레이션 절차를 참고한다.

## 첫 트레이스 로드

앱이 시작되면 상태 바에 `No trace loaded` 가 표시된다. 트레이스를 여는
방법은 두 가지다.

**방법 1 — 메뉴**

`File ▸ Open .pccx…` (`Ctrl+O`) 를 선택하고 `.pccx` 파일을 지정한다.
로드에 성공하면 탭 스트립 오른쪽에 녹색 `trace loaded` 배지가 표시되고
상태 바에 `cycles` 와 `cores` 카운트가 나타난다.

**방법 2 — CLI**

```bash
# 사전 빌드된 바이너리 사용
./target/release/pccx_cli samples/gemma3n_16tok_smoke.pccx \
    --roofline --report-md

# 또는 cargo run 으로 직접 실행
cargo run -p pccx-reports --bin pccx_cli -- \
    samples/gemma3n_16tok_smoke.pccx --roofline --report-md
```

**샘플 트레이스 위치**

저장소에 포함된 사전 캡처 트레이스 두 가지:

| 파일 | 크기 | 이벤트 수 | 용도 |
|---|---|---|---|
| `samples/gemma3n_16tok_smoke.pccx` | 101 KB | 2,568 | CI smoke |
| `samples/gemma3n_128tok_decode.pccx` | 797 KB | 20,488 | steady-state decode |

RTL 시뮬레이션에서 생성하려면 sibling 저장소의 검증 스크립트를 실행한다:

```bash
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260
./hw/sim/run_verification.sh
# 결과물: hw/sim/work/<tb>/<tb>.pccx
```

## 주요 패널

트레이스 로드 직후 탭 바에서 아래 다섯 패널에 진입할 수 있다:

| 패널 | 탭 이름 | 역할 |
|---|---|---|
| Timeline | Timeline | 코어별 사이클 정확 이벤트 타임라인 |
| FlameGraph | Flame Graph | 계층적 성능 분해 및 병목 식별 |
| System Simulator | System Simulator | pccx v002 모듈 계층 인터랙티브 시뮬레이터 |
| Verification Suite | Verify | ISA 검증 / API 정합성 / UVM 커버리지 / 합성 결과 |
| Reports | Report | PDF/Markdown 분석 리포트 자동 생성 |

**Timeline 이벤트 색상 코딩**

| 이벤트 타입 | 색상 | 의미 |
|---|---|---|
| MAC_COMPUTE | 청록 | systolic array 행렬 곱 실행 중 |
| DMA_READ | 초록 | 외부 메모리 → 온칩 버퍼 DMA 전송 |
| DMA_WRITE | 노랑 | 온칩 버퍼 → 외부 메모리 DMA 전송 |
| SYSTOLIC_STALL | 보라 | systolic array 파이프라인 stall |
| BARRIER_SYNC | 빨강 | 크로스-코어 동기화 배리어 대기 |

Timeline 주요 단축키: `Ctrl+Scroll` 로 사이클 축 줌, 드래그로 팬,
`Ctrl+G` 로 특정 사이클로 이동.

각 패널의 상세 기능은 {doc}`panels` 를 참고한다.

`?` 또는 `F1` 을 누르면 전체 단축키 모달이 열린다.

## 다음 단계

- {doc}`verification-workflow` — xsim → `.pccx` → UI 검증 파이프라인 전 과정.
- {doc}`pccx-format` — `.pccx` 바이너리 포맷 명세.
- {doc}`panels` — 각 분석 패널 상세 레퍼런스.
- {doc}`ipc` — Tauri IPC 커맨드 목록 및 바이너리 페이로드 패턴.
- {doc}`core-modules` — `pccx-core` 크레이트 공개 모듈 레퍼런스.

## 이 페이지 인용

```bibtex
@misc{pccx_lab_quickstart_2026,
  title        = {pccx-lab Quickstart: installing the profiler and loading the first trace},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/quickstart.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
