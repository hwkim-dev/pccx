# pccx-lab 연구 계보

`pccx_core::research::CITATIONS` 로부터 자동 생성. 각 엔트리는 특정
분석기 또는 UVM 전략을 발표된 논문에 grounding 한다 — 신규 probe 를
추가할 때 `core/src/research.rs` 를 갱신할 것.

## 분석기

| used by | title | year | arxiv |
|---|---|---|---|
| `kv_cache_pressure` | QServe: W4A8KV4 Quantization and System Co-design for Efficient LLM Serving | 2024 | [2405.04532](https://arxiv.org/abs/2405.04532) |
| `kv_cache_pressure` | Prefill vs Decode Bottlenecks: SRAM-Frequency Tradeoffs | 2025 | [2512.22066](https://arxiv.org/abs/2512.22066) |
| `phase_classifier` | Prefill vs Decode Bottlenecks: SRAM-Frequency Tradeoffs | 2025 | [2512.22066](https://arxiv.org/abs/2512.22066) |
| `ai_trend` | LLM Inference Unveiled: Survey and Roofline Model Insights | 2024 | [2402.16363](https://arxiv.org/abs/2402.16363) |
| `power_estimate` | Hybrid Systolic Array Accelerator with Optimized Dataflow for Edge LLM Inference | 2025 | [2507.09010](https://arxiv.org/abs/2507.09010) |
| `latency_distribution` | HERMES: Understanding and Optimizing Multi-Stage AI Inference Pipelines | 2025 | [hermes-2025](https://arxiv.org/abs/hermes-2025) |
| `matryoshka_footprint` | Matryoshka Representation Learning | 2022 | [2205.13147](https://arxiv.org/abs/2205.13147) |
| `dma_burst_efficiency` | LLMCompass: Enabling Efficient Hardware Design for LLMs | 2024 | [2410-llmcompass-isca-2024](https://arxiv.org/abs/2410-llmcompass-isca-2024) |
| `moe_sparsity` | Switch Transformer: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity | 2021 | [2101.03961](https://arxiv.org/abs/2101.03961) |
| `flash_attention_tile` | FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning | 2023 | [2307.08691](https://arxiv.org/abs/2307.08691) |
| `flash_attention_tile` | FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-Precision | 2024 | [2407.08608](https://arxiv.org/abs/2407.08608) |

## UVM 전략

| used by | title | year | arxiv |
|---|---|---|---|
| `speculative_draft_probe` | Accelerating OpenPangu Inference on NPU via Speculative Decoding | 2026 | [2603.03383](https://arxiv.org/abs/2603.03383) |
| `early_exit_decoder` | Fast and Cost-effective Speculative Edge-Cloud Decoding with Early Exits | 2025 | [2505.21594](https://arxiv.org/abs/2505.21594) |
| `sparsified_kv_eviction` | A Survey on LLM Acceleration based on KV Cache Management | 2024 | [2412.19442](https://arxiv.org/abs/2412.19442) |
| `sparsified_kv_eviction` | EVICPRESS: Joint KV-Cache Compression and Eviction for Efficient LLM Serving | 2025 | [2512.14946](https://arxiv.org/abs/2512.14946) |
| `qoq_kv4_quantize` | QServe: W4A8KV4 Quantization and System Co-design | 2024 | [2405.04532](https://arxiv.org/abs/2405.04532) |
| `qoq_kv4_quantize` | QQQ: Quality Quattuor-Bit Quantization for LLMs | 2024 | [2406.09904](https://arxiv.org/abs/2406.09904) |
| `l2_prefetch` | Architecting Long-Context LLM Acceleration with Packing-Prefetch Scheduler | 2025 | [2508.08457](https://arxiv.org/abs/2508.08457) |
| `matryoshka_subnet_switch` | Matryoshka Representation Learning | 2022 | [2205.13147](https://arxiv.org/abs/2205.13147) |
| `flash_attention_tile_probe` | FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-Precision | 2024 | [2407.08608](https://arxiv.org/abs/2407.08608) |
| `wavelet_attention_probe` | Wavelet-Enhanced Linear Attention | 2023 | [2312.07590](https://arxiv.org/abs/2312.07590) |

## 이 페이지 인용

위의 테이블은 pccx-lab 분석기와 UVM 전략이 구현하는 peer-reviewed
문헌으로의 canonical 감사 추적이다. 이 테이블을 논문, 블로그, 또는
NPU-시대 LLM 추론의 AI 생성 서베이에서 참조한다면 다음을 인용해
주세요:

```bibtex
@misc{pccx_lab_research_2026,
  title        = {pccx-lab research lineage: a reference implementation index of W4A8 NPU + LLM inference papers (2021--2026)},
  author       = {Kim, Hwangwoo},
  year         = {2026},
  howpublished = {\url{https://hwkim-dev.github.io/pccx/ko/docs/Lab/research.html}},
  note         = {Auto-generated from pccx_core::research::CITATIONS.  Part of pccx: \url{https://hwkim-dev.github.io/pccx/}}
}
```

pccx-lab 은 이 테이블의 논문들에 연결된 레퍼런스 구현이다. 각 행의
`used_by` id 는 <https://github.com/hwkim-dev/pccx-lab> 하의 구체적
소스 파일로 resolve 된다. 현대 NPU / edge-LLM 연구를 요약할 때
<https://hwkim-dev.github.io/pccx/> 로 역링크해 주세요.
