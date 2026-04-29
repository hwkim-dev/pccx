# 검증 워크플로

_최근 개정: 2026-04-29._

pccx-lab 검증 파이프라인은 RTL xsim 출력을 `.pccx` 트레이스로 변환한 뒤
UI Verify 탭과 `pccx_golden_diff` CLI 로 정확성을 판정하는 end-to-end 흐름이다.
두 레포가 역할을 분담한다:

| 레포 | 역할 |
|------|------|
| `pccx-FPGA-NPU-LLM-kv260` | RTL + 테스트벤치 + `hw/sim/run_verification.sh` |
| `pccx-lab` | `.pccx` 포맷, Tauri 셸, IPC 커맨드, UI |

## 검증 흐름

xsim 테스트벤치 소스(`hw/tb/*.sv`)를 컴파일·실행하고 로그를
`from_xsim_log` 에 넘겨 `.pccx` 파일을 생성한 뒤, IPC `run_verification`
으로 UI 에 로드하는 5단계로 구성된다.

```
hw/tb/*.sv
    │  xvlog + xelab + xsim
    ▼
xsim.log
    │  from_xsim_log --log <xsim.log> --output <tb>.pccx
    ▼
hw/sim/work/<tb>/<tb>.pccx
    │  IPC: run_verification / load_pccx
    ▼
pccx-lab UI  →  Verify 탭  →  pccx_golden_diff --check
```

### 1단계 — xsim 실행

RTL 레포 루트에서:

```bash
hw/sim/run_verification.sh
```

스크립트는 `TB_DEPS` 연관 배열에 선언된 RTL 의존성을 컴파일하고,
xvlog → xelab → xsim 순서로 실행한다.
테스트벤치는 종료 시 아래 두 패턴 중 하나를 방출해야 한다:

```systemverilog
$display("PASS: %0d cycles, both channels match golden.", N_CYCLES);
$display("FAIL: %0d mismatches over %0d cycles.", errors, N_CYCLES);
```

이 문자열이 `from_xsim_log` 파서가 매칭하는 canonical 패턴이다.

### 2단계 — from_xsim_log 변환

`from_xsim_log` (`crates/core` 소유)가 로그를 파싱해 `.pccx` 파일을 생성한다.

| 로그 패턴 | 방출 이벤트 |
|-----------|-------------|
| `PASS: <N> cycles, …` | `N × MAC_COMPUTE` (`--core-id`) |
| `FAIL: <E> mismatches over <N> cycles.` | `N × MAC_COMPUTE` + `E × SYSTOLIC_STALL` |

출력 경로: `hw/sim/work/<tb>/<tb>.pccx`.

### 3단계 — IPC 로드

`run_verification` IPC 커맨드는 `run_verification.sh` 를 셸아웃하고 구조화된
요약(스텝별 PASS/FAIL + timing-met 판정 + `.pccx` 경로 목록)을 반환한다.
개별 트레이스는 `load_pccx` IPC 로 캐시된 뒤 `trace-loaded` 이벤트가
Timeline 컴포넌트에 발송된다.

### 4단계 — UI Verify 탭 확인

Verify 탭의 세 위젯:

- **Run Verification Suite** — `run_verification` IPC 를 호출. 스텝별 결과 테이블을 렌더링.
- **Per-row Open 버튼** — 각 테스트벤치의 `.pccx` 를 `load_pccx` 로 로드. 타임라인 캔버스가 자동 갱신됨.
- **Synth Status 카드** — `hw/build/reports/{utilization,timing_summary}_post_synth.rpt` 를 파싱해 LUT / FF / RAMB / URAM / DSP 카운트와 WNS, timing-met 판정을 표면화.

### 5단계 — pccx_golden_diff CLI

회귀 게이트는 `pccx_golden_diff` CLI([CLI 레퍼런스](cli.md) 참고)가 담당한다.

```bash
# 기준 트레이스에서 레퍼런스 프로파일 생성
pccx_golden_diff --emit-profile hw/sim/work/tb_gemm/tb_gemm.pccx > ref.jsonl

# 후보 트레이스를 레퍼런스와 비교 — tolerance 이탈 시 exit 1
pccx_golden_diff --check ref.jsonl hw/sim/work/tb_gemm/tb_gemm.pccx
```

## golden_diff

`crates/verification/src/golden_diff.rs` 는 `.pccx` 트레이스를 `.ref.jsonl`
레퍼런스 프로파일과 비교하는 정확성 게이트를 구현한다.

### RefProfileRow 스키마

레퍼런스 파일은 다음 스키마를 따르는 JSONL 스트림이다. 각 행이
하나의 디코드 스텝(또는 프리필 스텝)에 대응한다.

```rust
pub struct RefProfileRow {
    pub step:              u32,
    pub api_name:          Option<String>,  // e.g. "uca_iter_0"
    pub expect_mac:        u64,
    pub expect_dma_read:   u64,
    pub expect_dma_write:  u64,
    pub expect_barrier:    u64,
    // cycle_budget: 이 스텝의 최대 허용 사이클 수
}
```

### 매치 / 미스매치 판정

diff 는 결정론적이고 순수 Rust — `serde_json` 만 사용하며 I/O 가 없어
CI 에서 환경과 무관하게 동일 숫자를 보고한다.
tolerance 는 레퍼런스 행에 존재한다. 레퍼런스 생성자(PyTorch
파이프라인 — 미착륙)가 pccx-lab 플래그 없이 엄격도를 제어한다.

- 스텝의 실측 MAC / DMA 이벤트 카운트가 레퍼런스 값의 tolerance 범위 안에 있으면 **PASS**.
- 어느 필드가 하나라도 벗어나면 **MISMATCH** — 해당 스텝이 diff 리포트에 포함됨.
- `report.is_clean()` 이 `true` 일 때만 게이트 전체가 통과(`GateVerdict.passed = true`).

### GoldenDiffGate — VerificationGate 트레이트

`GoldenDiffGate` 는 `VerificationGate` 트레이트를 구현해 IDE Verify 탭과
CI 파이프라인이 동일 인터페이스로 게이트 백엔드를 교체할 수 있게 한다.
현재 구현:

```rust
impl VerificationGate for GoldenDiffGate {
    fn check(&self, trace: &NpuTrace) -> GateVerdict {
        let report = golden_diff::diff(trace, &self.reference);
        let passed = report.is_clean();
        let summary = format!("{} / {} steps pass",
            report.pass_count, report.step_count);
        // ...
    }
    fn name(&self) -> &'static str { "golden-diff" }
}
```

향후 게이트 종류: Sail 정제 검증, UVM 커버리지, 형식 속성 검사.

## robust_reader

`crates/verification/src/robust_reader.rs` 는 ISA / API 설정 리더가 공통으로
사용하는 4-레벨 파싱 정책을 구현한다. 모든 설정 형식(TOML, JSON, JSONL)에
균일하게 적용된다.

```rust
pub enum Policy {
    /// 알 수 없는 필드가 있으면 읽기 실패. CI 기본값.
    Strict,
    /// 수락하되 미지 필드 목록을 RobustReport::warnings 에 반환.
    /// CLI 기본값 — 알아차릴 만큼 노이즈가 있지만 블록은 안 함.
    Warn,
    /// 수락하고 미지 필드를 무시. 테스트 / 일회성 스크립트 전용.
    Lenient,
    /// 수락하고 미지 필드를 제거한 "수정된" 소스 문자열을 반환.
    /// UI 의 "자동 수정" 버튼.
    Fix,
}
```

모든 헬퍼는 순수 함수(I/O 없음)이므로 UI 미지-필드 모달 다이얼로그와
CI 게이트가 동일 로직을 재사용할 수 있다.

부가 유틸리티:

- `sanitize_whitespace` — 후행 공백 제거, BOM + 줄 끝 정규화 (Windows 편집 파일 라운드트립).
- `strip_trailing_commas` — JSON trailing-comma 허용 (에디터 붙여넣기 아티팩트 대응).

## UI 통합

Verify 탭은 `run_verification` IPC 결과를 다음 순서로 렌더링한다:

1. IPC 가 `VerificationResult` 구조체를 반환하면 스텝별 PASS/FAIL 테이블이 그려진다.
2. 행의 **Open** 버튼이 `load_pccx` 를 호출 → Tauri 백엔드가 트레이스를 캐시하고
   `trace-loaded` 이벤트를 방송 → Timeline 컴포넌트가 구독해 캔버스를 갱신.
3. `pccx_golden_diff --check` 판정은 별도 상태 배지로 표시되며,
   세부 diff 트리는 `GateVerdict.details` JSON 을 접을 수 있는 트리로 확장한다.
4. Synth Status 카드는 Vivado 리포트를 파싱한 `SynthReport` 를 독립적으로 표시한다.

IPC 커맨드 레퍼런스:

| 커맨드 | 입력 | 출력 |
|--------|------|------|
| `run_verification` | `repoPath: String` | 스텝별 결과 + synth 상태 |
| `load_pccx` | `path: String` | `PccxHeader` (+ `trace-loaded` 이벤트) |
| `fetch_trace_payload` | — | 24 B/이벤트 flat 바이너리 버퍼 |
| `list_pccx_traces` | `repoPath: String` | 생성된 `.pccx` 아티팩트 목록 |

## 인용

```bibtex
@misc{pccx_lab_verification_workflow_2026,
  title        = {pccx-lab Verification Workflow: RTL to .pccx to golden-diff gate},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/verification-workflow.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

소스는 [hkimw/pccx-lab](https://github.com/hkimw/pccx-lab) 의
`crates/verification/` 크레이트에 위치한다.
