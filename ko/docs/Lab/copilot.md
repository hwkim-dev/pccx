# Copilot API

`Copilot` 구조체는 pccx-lab 의 모든 AI 구동 워크플로우의 canonical
진입점이다. 다음을 래핑한다:

- 현재 로딩된 `NpuTrace` 에 대한 선택적 참조
- pccx KV260 레퍼런스 `HardwareModel`
- `pccx-core` 의 전체 `TraceAnalyzer` 레지스트리
- `pccx-ai-copilot::uvm` 의 `UvmStrategy` 레지스트리

소비자는 트레이스 로드당 한 인스턴스를 생성해 아래 메서드로 구동한다.

## 생성

```rust
use pccx_ai_copilot::Copilot;

let c = Copilot::new(Some(&trace));
// 또는
let c = Copilot::new(None);   // 트레이스 미로드; investigate() 는 [] 반환
```

분석기 레지스트리를 확장하려면 첫 `investigate()` 호출 전에
`c.analyzers.push(...)` 한다.

## 메서드

### `investigate() -> Vec<AnalysisReport>`

등록된 모든 분석기를 트레이스에 대해 실행. 레지스트리 순서대로 리포트
반환. 트레이스 미로드 시 빈 Vec.

### `investigate_summary() -> String`

모든 리포트를 단일 LLM 용 시스템 프롬프트로 압축. 각 라인은
`"- [<analyzer_id>] <summary>"`; 총 길이는 분석기 수 × summary 당
500 chars 로 바운드.

```rust
let prompt = c.investigate_summary();
// Trace analysis summary (automated):
// - [roofline] AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound
// - [dma_util] DMA SATURATED: read 46% + write 46% pinned — compute only 4%
// - [bottleneck] 19179 windows · DmaRead×12787, DmaWrite×6392
// ...
```

LLM 의 `system` 채널에 그대로 투입.

### `rank_by_severity() -> Vec<AnalysisReport>`

대시보드 severity 정렬의 서버사이드 등가물. error 급 발견이 먼저, 그
다음 warning, 마지막에 정보성 엔트리 순으로 정렬된 리포트 반환.
동점은 레지스트리 선언 순서로 깨 안정적 출력 보장.

```rust
let top = c.rank_by_severity();
println!("가장 시급: {}", top[0].summary);
```

### `explain(analyzer_id: &str) -> Option<String>`

단일 분석기에 대한 long-form Markdown 설명. 매칭되는 모든
`research::Citation` 을 당겨와 description + 최신 발견과 함께 포맷.

```rust
let md = c.explain("kv_cache_pressure").unwrap();
// # KV-Cache Pressure (kv_cache_pressure)
// Projects per-decode KV-cache footprint against L2 URAM; cites …
//
// ## Latest finding
// HBM-SPILL: decode 512 tokens → 60000 KB KV …
//
// ## Research lineage
// - **QServe …** (2024) — [2405.04532](…). _Why_: …
```

id 가 레지스트리에 없으면 `None` 반환 → UI 가 "미지원 id" 와 "트레이스
미로드" 를 구분.

### `suggest_fix(intent: &str) -> (String, String)`

자연어 의도 → (strategy_slug, SystemVerilog 스텁). slug 가 의도에
포함되지 않으면 키워드 규칙 사용.

```rust
let (slug, sv) = c.suggest_fix("please reduce DMA barrier contention");
// slug == "barrier_reduction"
// sv   == "class barrier_reduction_seq extends uvm_sequence; …"
```

**키워드 라우팅** — Copilot 이 (우선순위 순) 확인하는 서브스트링과 해당
canonical 전략:

| 의도 키워드 | 전략 | 연구 계보 |
|---|---|---|
| `barrier`, `sync` | `barrier_reduction` | — |
| `prefetch`, `dma` | `l2_prefetch` | Packing-Prefetch (arxiv 2508.08457) |
| `thermal`, `tdp`, `power`, `heat` | `back_pressure_gate` | KV260 7 W PL TDP; Hybrid-Systolic ISLPED 2025 |
| `latency`, `tail`, `p95`, `p99`, `jitter` | `kv_cache_thrash_probe` | HERMES 2025 tail-latency model |
| `early exit`, `edge-cloud` | `early_exit_decoder` | arxiv 2505.21594 |
| `speculative`, `draft`, `spec decode` | `speculative_draft_probe` | OpenPangu NPU (arxiv 2603.03383 — 1.35×) |
| `evict`, `sparsif`, `kv drop` | `sparsified_kv_eviction` | LoopServe + EVICPRESS |
| `w4a8`, `kv4`, `quantize`, `qserve`, `qoq` | `qoq_kv4_quantize` | QServe (arxiv 2405.04532) + QQQ |
| `matryoshka`, `subnet`, `e2b`, `e4b` | `matryoshka_subnet_switch` | arxiv 2205.13147 |
| `wavelet`, `low-rank`, `long context` | `wavelet_attention_probe` | arxiv 2312.07590 |
| `flash`, `tile`, `softmax` | `flash_attention_tile_probe` | FlashAttention-2/3 |
| `moe`, `expert`, `mixture` | `kv_cache_thrash_probe` | Switch Transformer (arxiv 2101.03961) |
| `throughput`, `core` | `back_pressure_gate` | — |

### `generate_report(synth: Option<&SynthReport>) -> String`

`pccx-core::report::render_markdown` 에 위임.
`synth_report::load_from_files` 또는 `synth_runner::run` 이 파싱한
`SynthReport` 를 넘기면 utilisation + timing 테이블 포함.

## 레지스트리 확장

```rust
// investigate() 전에 임의의 분석기 런타임 등록.
let mut c = Copilot::new(Some(&trace));
c.analyzers.push(Box::new(MyCustomAnalyzer));
let reports = c.investigate();
```

전략 레지스트리는 `uvm::strategies_for_analyzer(id)` 로 질의 가능 —
Copilot 이 임의 분석기의 발견을 하드코딩 키워드 매칭 없이 후보 완화
집합으로 매핑할 때 사용.

## 자동화에서 사용

```rust
use pccx_ai_copilot::Copilot;
use pccx_core::{PccxFile, NpuTrace};
use std::fs::File;

fn summarise(path: &str) -> anyhow::Result<String> {
    let mut f = File::open(path)?;
    let pccx = PccxFile::read(&mut f)?;
    let trace = NpuTrace::from_payload(&pccx.payload)?;
    let c = Copilot::new(Some(&trace));
    Ok(c.investigate_summary())
}
```

CI 파이프라인에서 `pccx_analyze <trace.pccx>` 와 자연스럽게 짝을 이룬다
— CLI 는 기본적으로 `investigate_summary()` 와 동등한 출력을 프린트.

## 오류 처리

`Copilot` 은 설계상 infallible 이다. 트레이스가 없어도 모든 메서드는
값을 반환 (빈 `Vec` / `"No trace loaded"` 문자열 / 빈 SV 스텁 /
`explain` 의 `None`). 웰컴 스크린, 토스트, CI 스킵 렌더 결정은 호출자의
empty-state 브랜치 몫이다 — copilot 내부가 아니다.
