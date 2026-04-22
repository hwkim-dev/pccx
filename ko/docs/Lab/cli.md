# CLI 레퍼런스

모든 Rust 바이너리는 `src/core/src/bin/` 하위에 위치하며
`cargo build -p pccx-core` 로 빌드된다. 릴리스 바이너리는
`target/release/` 에 떨어진다.

## `pccx_analyze`

원샷 분석 엔진 — CI 파이프라인과 스크립티드 회귀 실행의 canonical 진입점.

### 개요

```text
pccx_analyze <trace.pccx> [--json | --markdown] [--synth UTIL TIMING]
pccx_analyze --run-synth <RTL_REPO> [--target synth|impl] [--dry-run] [--parse-only]
pccx_analyze --compare BASE.pccx CAND.pccx [--threshold-pct N] [--json]
pccx_analyze --research-list [--json]
pccx_analyze --explain <analyzer_id> [trace.pccx]
```

### 모드

| 플래그 | 동작 |
|---|---|
| *(기본)* | Pretty 콘솔 요약 — 분석기당 1 라인 + bottleneck / roofline 밴드 짧은 부연. |
| `--json` | `AnalysisReport` 의 adjacently-tagged JSON 배열. 안정 shape — CI 에서 `jq` 파이프 안전. |
| `--markdown` | canonical `report::render_markdown` 문서 emit. `--synth` 와 결합 가능. |
| `--synth UTIL TIMING` | Vivado 텍스트 리포트 쌍을 로드해 Markdown 출력에 인라인. |
| `--run-synth DIR` | `DIR/hw` 하위 RTL 레포에 대해 Vivado 를 spawn. 오류 시 non-zero exit. |
| `--target synth\|impl` | 호출할 `vivado/build.sh` 타겟 (기본: `synth`). |
| `--dry-run` | 실행될 커맨드만 프린트하고 종료. Vivado 불필요. |
| `--parse-only` | Vivado 스킵; 직전 실행의 `hw/build/reports/` 파싱. |
| `--compare B C` | 두 `.pccx` 캡처 diff; 회귀 시 exit 1. |
| `--threshold-pct N` | `--compare` 회귀 임계치 (기본: 15). |
| `--research-list` | 연구 계보 테이블 (기본 Markdown, `--json` 으로 JSON) 프린트. |
| `--explain ID` | 단일 analyzer id 에 대해 long-form 문서 (description + 최신 발견 + arxiv 인용) 렌더. |

### 예시 — Pretty 트레이스 분석

```console
$ pccx_analyze ./dummy_trace.pccx
═══════════════════════════════════════════════════════════════════════
  pccx_analyze · 16008 events over 5423940 cycles
═══════════════════════════════════════════════════════════════════════
✓  [roofline] AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound
✓  [roofline_hier] dwell 4 tier: Register=851200cy, URAM L1=52M cy, …
✓  [bottleneck] 19179 windows · DmaRead×12787, DmaWrite×6392
    · DmaRead @ [474624..474880] share=100%
✓  [dma_util] DMA SATURATED: read 46% + write 46% pinned — compute only 4%
✓  [stall_histogram] 4 stalls · mean 1472 cy · max 5000 cy · 50% long-tail
✓  [per_core_throughput] 4 cores active · mean 6.2% · σ=3.5pp
✓  [kv_cache_pressure] HBM-SPILL: decode 512 tokens → 60000 KB KV …
✓  [phase_classifier] mixed · prefill 22% · decode 61% (512 tok) · idle 17%
```

### 예시 — CI 용 JSON

```bash
pccx_analyze trace.pccx --json \
  | jq -r '.[] | select(.analyzer_id == "bottleneck") | .summary'
```

### 예시 — Vivado 합성 파이프라인

```bash
# Vivado 를 실제로 띄우지 않고 플로우 smoke-test.
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --dry-run

# 직전 실행의 리포트만 파싱 (수동으로 Vivado 를 띄운 경우 유용).
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --parse-only
# ───────────────────────────────────────────────────────────
# pccx_analyze · synth (parse-only mode)
# ───────────────────────────────────────────────────────────
# utilisation: LUT=  5611 DSP=   4 URAM= 56 BRAM36= 80
# timing     : WNS=-9.792 ns · worst clk core_clk · (NOT met)

# 실제 실행 — vivado spawn, stdout 스트림, 리포트 파싱.
pccx_analyze --run-synth ~/rtl/pccx-FPGA-NPU-LLM-kv260 --target impl
```

### 예시 — 회귀 게이트

```bash
# 후보 캡처가 임의 메트릭에서 15 % 초과 회귀 시 CI 실패.
pccx_analyze --compare baseline.pccx candidate.pccx --threshold-pct 15
```

### 예시 — 연구 계보

```bash
# canonical 레지스트리로부터 research.md 페이지 재생성.
pccx_analyze --research-list > docs/Lab/research.md

# kv_cache_pressure 분석기를 구동하는 근거 설명.
pccx_analyze --explain kv_cache_pressure
```

### Exit 코드

| 코드 | 의미 |
|---|---|
| 0 | 성공. 트레이스 non-empty, 분석기 실행 완료, Vivado (호출 시) 정상 종료. |
| 1 | 런타임 실패 — 트레이스 파싱 오류, Vivado ERROR 라인, JSON 인코딩 실패, 회귀 탐지. |
| 2 | 잘못된 호출 — 누락 인자, 미지원 플래그. |

### 환경 변수

없음. `--run-synth` 는 `VIVADO_HOME` 이 설정되어 있으면 사용하지만,
`hw/vivado/build.sh` 래퍼가 실제 PATH 를 처리한다.

## `pccx_cli`

기존의 대화형 / Vivado-shaped CLI. 일부 Vivado 배치 파이프라인이 쓰는
headless TCL 스크립트 모드를 위해 유지. **신규 워크플로우는
`pccx_analyze` 사용을 권장** — 구조화 JSON 출력과 기계 판독 exit 코드가
있다.

## `from_xsim_log`

`xsim` 테스트벤치 stdout 스트림을 `.pccx` 트레이스로 변환.
`hw/sim/run_verification.sh` 가 자동 호출; 일반적으로 수동 실행 대상은 아니다.

## 보드 bringup 스크립트

`pccx-FPGA-NPU-LLM-kv260/scripts/board/` 하위:

| 스크립트 | 목적 |
|---|---|
| `health_check.sh` | SSH 도달성 + 커널 + fpga_manager + 메모리 free |
| `load_bitstream.sh` | scp .bit → `/lib/firmware/` → PL 프로그램 |
| `run_inference.sh` | 보드에서 `pccx_host` 실행, 옵션으로 트레이스 emit |
| `capture_trace.sh` | 보드의 .pccx 를 호스트로 pull |
| `bringup.sh` | 위 네 개를 순차 오케스트레이션 |
