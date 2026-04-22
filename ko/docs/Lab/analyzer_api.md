# 분석기 API

`TraceAnalyzer` 트레이트는 pccx-lab 의 모든 분석이 구현하는 단일
추상화이다. 소비자 (UI / CLI / Copilot / 확장) 는 더 이상 개별
`roofline::analyze()` / `bottleneck::detect()` free 함수를 호출하지
않는다 — 레지스트리를 iterate 하며 `AnalysisPayload` 변형에
pattern-match 한다.

## 트레이트

```rust
pub trait TraceAnalyzer: Send + Sync {
    fn id(&self)           -> &'static str;        // 안정 id
    fn display_name(&self) -> &'static str;        // 메뉴 라벨
    fn description(&self)  -> &'static str;        // 한 줄 설명
    fn analyze(&self, trace: &NpuTrace, hw: &HardwareModel) -> AnalysisReport;
}
```

**Purity 요구사항**: `analyze()` 는 외부 상태를 변경하거나 IPC 를 수행
해선 안 된다. 레지스트리는 미래에 호출을 병렬화할 권리를 보존한다.

## 반환 shape

```rust
pub struct AnalysisReport {
    pub analyzer_id: String,       // == analyzer 의 id()
    pub summary:     String,       // ≤ 500 chars — LLM 용
    pub payload:     AnalysisPayload,
}

pub enum AnalysisPayload {
    Roofline(RooflinePointPayload),
    RooflineHierarchical(Vec<RooflineBand>),
    Bottleneck(Vec<BottleneckInterval>),
    Custom(serde_json::Value),   // 타입드 변형이 없는 신규 분석기용
    Text,                        // summary 가 전체 결과
}
```

`Custom` 은 탈출구다 — 실험적 분석기는 core enum 수정 없이 임의의
JSON-serialisable 페이로드를 실어 나를 수 있다.

## 빌트인 레지스트리

| id | 표시명 | 페이로드 | 보고 내용 |
|---|---|---|---|
| `roofline` | Roofline | `Roofline` | Williams/Waterman AI vs. achieved GOPS |
| `roofline_hier` | Hierarchical Roofline | `RooflineHierarchical` | 메모리 티어별 dwell (Ilic 2014, Yang 2020) |
| `bottleneck` | Bottleneck Windows | `Bottleneck` | Sliding-window contention detector |
| `dma_util` | DMA Utilisation | `Custom` (`DmaUtilisationPayload`) | Read/write/MAC 사이클 share, starved vs. saturated |
| `stall_histogram` | Stall Histogram | `Custom` (`StallHistogramPayload`) | `SYSTOLIC_STALL` 지속의 log-bucket 분포 |
| `per_core_throughput` | Per-Core Throughput | `Custom` (`PerCoreThroughputPayload`) | `core_id` 별 MAC share + balance σ |
| `latency_distribution` | Latency Distribution | `Custom` (`LatencyDistributionPayload`) | `API_CALL` 지속의 P50/P95/P99 + 최악 callers |
| `power_estimate` | Power Estimate | `Custom` (`PowerEstimatePayload`) | 동적 W + KV260 7 W TDP 비율; thermal-bound 플래그 |
| `kv_cache_pressure` | KV-Cache Pressure | `Custom` (`KvCachePressurePayload`) | 디코드당 KV footprint vs L2 URAM; HBM spill 플래그 |
| `phase_classifier` | Prefill/Decode Phase | `Custom` (`PhaseClassifierPayload`) | prefill/decode/idle span 태깅; wall-clock split |
| `ai_trend` | Arithmetic Intensity Trend | `Custom` (`AiTrendPayload`) | 롤링 윈도우 AI (ops/byte); prefill→decode collapse 플래그 |
| `dma_burst_efficiency` | DMA Burst Efficiency | `Custom` (`DmaBurstEfficiencyPayload`) | AXI overhead 상쇄 후 effective BW |
| `matryoshka_footprint` | Matryoshka Subnet | `Custom` (`MatryoshkaFootprintPayload`) | Gemma-3N E2B/E4B 스왑 절감 projection |
| `moe_sparsity` | MoE Expert Sparsity | `Custom` (`MoESparsityPayload`) | 전문가당 활성화율; over-sparse 라우팅 플래그 |
| `flash_attention_tile` | FlashAttention Tile Efficiency | `Custom` (`FlashAttentionTilePayload`) | 타일 임계치 충족 MAC burst 비율 |
| `dual_hp_port_balance` | Dual-HP-Port Balance | `Custom` (`DualHpPortBalancePayload`) | HP0/1 vs HP2/3 traffic share; 단일 포트 starvation |

### 연구 계보

2025 이후 분석기는 최신 논문에 grounding 되어 있어, UVM Copilot 이
발견을 설명할 때 근거를 인용할 수 있다. 전체 자동 생성 인용 테이블은
[연구 계보 페이지](research.md) 참고.

## 전부 실행

```rust
use pccx_core::{analyze_all, HardwareModel, NpuTrace};

let hw = HardwareModel::pccx_reference();
for report in analyze_all(&trace, &hw) {
    println!("[{}] {}", report.analyzer_id, report.summary);
}
```

## 신규 분석기 작성

```rust
use pccx_core::analyzer::{TraceAnalyzer, AnalysisReport, AnalysisPayload};
use pccx_core::{NpuTrace, HardwareModel};

pub struct DmaLatencyAnalyzer;

impl TraceAnalyzer for DmaLatencyAnalyzer {
    fn id(&self) -> &'static str           { "dma_latency" }
    fn display_name(&self) -> &'static str { "DMA Latency Distribution" }
    fn description(&self) -> &'static str  {
        "Distribution of DMA_READ durations; flags long-tail outliers."
    }
    fn analyze(&self, trace: &NpuTrace, _hw: &HardwareModel) -> AnalysisReport {
        let durs: Vec<u64> = trace.events.iter()
            .filter(|e| e.event_type == "DMA_READ")
            .map(|e| e.duration)
            .collect();
        let max  = durs.iter().copied().max().unwrap_or(0);
        let mean = if durs.is_empty() { 0.0 }
                   else { durs.iter().sum::<u64>() as f64 / durs.len() as f64 };
        AnalysisReport {
            analyzer_id: self.id().to_string(),
            summary: format!("{} DMA reads · mean {:.0} cy · max {} cy",
                             durs.len(), mean, max),
            payload: AnalysisPayload::Text,
        }
    }
}
```

**출하하려면**:

1. `builtin_analyzers()` 에 `Box::new(DmaLatencyAnalyzer)` 추가.
2. 소비자가 직접 타입을 생성하려면 `lib.rs` 에서 re-export.
3. `analyzer::tests` 에 단위 테스트 추가.
4. (선택) `core/src/research.rs` 에 `Citation` 엔트리 추가.
5. `cargo test -p pccx-core` 통과 확인.

Copilot 은 레지스트리를 통해 신규 분석기를 집어들고; UI 는 동일한
`invoke("run_all_analyzers", ...)` Tauri 커맨드로 본다.

## Summary 포맷 관행

- `summary` 는 ≤ 500 chars.
- 메트릭으로 시작: `"AI 0.69 ops/byte · 321.4 GOPS (0% of peak) · memory-bound"`.
- 예약된 대문자 접두사는 UI 심각도 색상을 결정한다:
  - `error:` / `HBM-SPILL` / `OVER-SPARSE` / `PORT-STARVED` / `TILE-BOUND` / `AI-COLLAPSE` / `OVERHEAD-BOUND` → 빨강
  - `THERMAL-BOUND` / `PREFILL-BOUND` / `DECODE-BOUND` / `SWAP-E2B` → 주황
- Copilot 은 모든 summary 를 하나의 LLM 시스템 프롬프트로 합치므로,
  각 summary 는 독자 문맥 없이도 스스로 성립해야 한다.
