# CLI 레퍼런스

_페이지 과도기 상태. pccx-lab HEAD 기준 2026-04-24 재정비._

이 페이지의 Phase 1 이전 리비전이 기술한 단일 `pccx_analyze` 우산
바이너리는 워크스페이스 분할이 코드를 `crates/` 로 이동시킬 때
**재착륙되지 않았다**. 오늘 pccx-lab 은 더 작은 Rust 바이너리 네
개를 출하하며, 각 표면을 소유한 크레이트 별로 분산되어 있다.
각각이 과거 `pccx_analyze` 가 다중화하던 조각 하나를 커버한다. 나머지
(research-list 내보내기, analyzer id explain, `--compare` 회귀 게이트,
synth runner) 는 적절한 크레이트 안에서 재착륙을 대기 중이다.

## 크레이트에 분산된 바이너리

| 바이너리            | 소스 크레이트       | 빌드 커맨드                           |
|--------------------|---------------------|---------------------------------------|
| `pccx_cli`         | `pccx-reports`      | `cargo build -p pccx-reports`         |
| `generator`        | `pccx-core`         | `cargo build -p pccx-core`            |
| `from_xsim_log`    | `pccx-core`         | `cargo build -p pccx-core`            |
| `pccx_golden_diff` | `pccx-verification` | `cargo build -p pccx-verification`    |

릴리스 아티팩트는 여전히 워크스페이스 공통 `target/release/` 디렉토리에
떨어진다.

## `pccx_cli`

헤드리스 트레이스 인스펙션 CLI — 코어별 utilisation, bottleneck
윈도, roofline 판단, Markdown 요약만 필요한 CI 파이프라인이 오늘
타겟팅해야 할 표면.

### 개요

```text
pccx_cli <path/to/trace.pccx>
         [--util]
         [--roofline]
         [--bottleneck <ratio>]
         [--windows <cycles>]
         [--threshold <ratio>]
         [--report-md]
         [--source <script>]
```

### 플래그 레퍼런스

| 플래그                  | 동작                                                            |
|-------------------------|-----------------------------------------------------------------|
| `--util`                | 코어별 MAC utilisation 바 차트 프린트.                           |
| `--roofline`            | Arithmetic intensity + compute/memory-bound 판정 프린트.         |
| `--bottleneck <ratio>`  | 레거시 per-event DMA 핫스팟 필터 (기본 `0.5`).                   |
| `--windows <cycles>`    | 신규 bottleneck 탐지기의 슬라이딩 윈도 크기 (기본 256).           |
| `--threshold <ratio>`   | Share-of-window 임계치 (기본 `0.5`).                             |
| `--report-md`           | `pccx-reports::render_markdown` 요약을 stdout 으로 emit.         |
| `--source <script>`     | `pccx_tcl` 스타일 배치 스크립트 실행 (헤드리스 모드).             |

오늘은 `--json`, `--compare`, `--research-list`, `--explain`,
`--run-synth` 모드가 존재하지 않는다. 이전 문서가 이 플래그들을 통합
`pccx_analyze` 바이너리의 일부로 기술했는데 그 바이너리는 연기되었다 —
재착륙 대상으로 추적 중이지만 현재 트리에서 호출 불가.

### 예시 — Pretty 트레이스 인스펙션

```bash
pccx_cli ./dummy_trace.pccx --util --roofline --report-md
```

`--report-md` 출력은 `pccx-reports::render_markdown` 이 생성하는 것과
동일한 Markdown 문서다. Rust API 만 원하는 소비자는 바이너리를
건너뛰고 함수를 직접 호출하면 된다.

## `generator`

개발과 테스트용 데모 `.pccx` 트레이스 생성. UI 의 첫 실행 플로우와
CI smoke 테스트에 사용.

### 개요

```text
generator [output_path] [tiles] [cores]
```

기본값: `dummy_trace.pccx`, `tiles=100`, `cores=32`.
`pccx_core::simulator::generate_realistic_trace` 를 거쳐 `NpuTrace` 를
구성하고, 현재 `HardwareModel::pccx_reference()` 메타데이터를 가진
`PccxFile` 로 래핑해 디스크에 기록.

## `from_xsim_log`

Xilinx `xsim` 시뮬레이션 로그를 UI 가 로드 가능한 `.pccx` 트레이스로
변환. RTL 레포의 `hw/sim/run_verification.sh` 가 자동 호출하며,
보통 수동 실행 대상은 아니다.

### 개요

```text
from_xsim_log --log <xsim.log> --output <out.pccx>
              [--core-id <u32>] [--testbench <name>]
```

인식 패턴 (pccx-FPGA 테스트벤치가 방출):

| 로그 패턴                                      | 방출 이벤트                                      |
|------------------------------------------------|--------------------------------------------------|
| `PASS: <N> cycles, ...`                        | `--core-id` 에 `N × MAC_COMPUTE`.                |
| `FAIL: <E> mismatches over <N> cycles.`        | `N × MAC_COMPUTE` + `E × SYSTOLIC_STALL`.        |

## `pccx_golden_diff`

후보 `.pccx` 트레이스를 JSONL 레퍼런스 프로파일과 비교하는 end-to-end
정확성 게이트.

### 개요

```text
pccx_golden_diff --emit-profile <trace.pccx> [--tolerance-pct N] > ref.jsonl
pccx_golden_diff --check        ref.jsonl <trace.pccx> [--json]
```

두 모드:

- `--emit-profile` — 자가 교정. 알려진 good 트레이스를 로드해
  `API_CALL` 경계로 버킷팅하고, 관측 카운트 + 구성 가능 tolerance 를
  가진 JSONL 레퍼런스를 기록.
- `--check` — 회귀 게이트. 레퍼런스 JSONL + 후보 트레이스를 로드해
  `golden_diff::diff` 를 실행, 한 줄 판정 + 스텝별 메트릭 테이블 프린트,
  어느 스텝이든 tolerance 를 벗어나면 exit 1.

Tolerance 는 레퍼런스 행에 존재하므로 (미구현) PyTorch 측 레퍼런스
파이프라인이 pccx-lab 측 플래그 폭발 없이 엄격도를 제어한다.

## 보드 bringup 스크립트 (RTL 레포)

`pccx-FPGA-NPU-LLM-kv260/scripts/board/` 하위 — pccx-lab 과 독립이며,
편의상 여기 열거:

| 스크립트              | 목적                                                  |
|----------------------|-------------------------------------------------------|
| `health_check.sh`    | SSH 도달성 + 커널 + fpga_manager + free RAM.          |
| `load_bitstream.sh`  | `.bit` 를 `/lib/firmware/` 로 scp 후 PL 프로그램.     |
| `run_inference.sh`   | 보드에서 `pccx_host` 실행, 옵션으로 트레이스 emit.    |
| `capture_trace.sh`   | 보드의 `.pccx` 를 호스트로 pull.                      |
| `bringup.sh`         | 위 네 개를 순차 오케스트레이션.                       |

## 아직 재착륙되지 않은 표면

가장 적합한 크레이트 (아마 `pccx-reports` 와 신설 분석 크레이트의
조합) 에서의 재착륙 대상으로 추적 중:

- `--json` adjacently-tagged 구조화 출력.
- `--compare BASE CAND` `--threshold-pct` 회귀 게이트.
- `--run-synth`, `--dry-run`, `--parse-only` Vivado 래퍼
  (RTL 레포의 `hw/vivado/build.sh` 는 여전히 단독 동작).
- `--research-list` 인용 레지스트리 내보내기 (이것이 보류된 이유는
  [연구 계보](research.md) 참고).
- `--explain <id>` long-form 분석기 / 전략 문서.

## Exit 코드

네 바이너리는 관용적 Rust 관례를 따른다: 성공 시 `0`, 런타임 실패 시
non-zero. `pccx_golden_diff --check` 는 임의 행이 tolerance 를 벗어나면
`1` 종료 — 현재로서는 canonical CI 회귀 게이트.

## 이 페이지 인용

```bibtex
@misc{pccx_lab_cli_2026,
  title        = {pccx-lab command-line binaries after the Phase 1 workspace split: pccx\_cli, generator, from\_xsim\_log, pccx\_golden\_diff},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/cli.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

각 바이너리의 소스는 소유 크레이트 아래 — <https://github.com/hkimw/pccx-lab> —
에 위치한다.
