# 로드맵 (Two-Track)

:::{dropdown} 빠른 탐색
:open:

```{contents}
:local:
:depth: 2
:backlinks: none
```
:::

pccx는 2026-04-20 기준으로 **두 트랙 병렬**로 진행된다. v002는 현재 active
아키텍처이고 v003은 다음 세대 타겟 모델(Gemma 4 E4B)을 위해 설계된다.
두 트랙은 RTL 자산 (sparse weight fetcher, SSD dispatcher, tree mask generator,
EAGLE 학습 파이프라인)을 상호 재사용한다.

장기 목표는 임의의 transformer config → pccx ISA 스트림 자동 생성기
(**Auto-Porting Pipeline α**)이며, 두 트랙이 안정화된 이후 Year 2 목표로 시작된다.

## 1. 공통 전제

- **플랫폼**: Xilinx Kria KV260 (Zynq UltraScale+ ZU5EV), bare-metal
- **양자화**: W4A8 (INT4 weights × INT8 activations), KV cache INT4
- **클럭**: AXI 250 MHz, core 400 MHz
- **VLIW ISA**: 5 base opcodes (GEMV, GEMM, MEMCPY, MEMSET, CVO) + SPEC 확장
- **L2 URAM 2.25 MB 배치**: activation pin 1.0 MB, KV prefetch 0.5 MB,
  tree mask + scheduler 0.25 MB, hot attention 0.5 MB

## 2. Track 1 — v002 Extended (Gemma 3N E4B, 20 tok/s)

현재 v002 active 구성 위에 sparsity 확장과 speculative decoding 스택을 얹어
**약속된 20 tok/s 실측**을 달성하는 목표를 갖는다.

### Tiered targets

| 수준 | tok/s | 달성 조건 |
|---|---|---|
| Baseline | 5–6 | Phase A–F 완료 |
| Viable | 10–12 | Phase G + H 완료 |
| **Promise** | **20** | Phase G–K 완료 |
| Stretch | 25+ | Tree EAGLE (Phase J) 추가 |

### Phase 구성

| Phase | 기간 | 주요 작업 | 기대 tok/s |
|---|---|---|---|
| A–F | Week 1–26 | 재파라미터화 → 드라이버 → Gemma 3N 앱 → 검증 → 합성 → 보드 bringup | 5–6 |
| G | Week 27–30 | 전 레이어 Gaussian Top-K sparsity (BW 1.95 → 1.36 GB/token) | 8–9 |
| H | Week 31–32 | Gemma 3 1B vanilla drafter (fast path) — tokenizer 호환 | 11–14 |
| H+ | Week 33–38 | EAGLE-3 head 학습 & 교체 ($20–30, Vast.ai RTX 4090) | 14–16 |
| I | Week 39–42 | SSD async overlap (draft/verify pipelining) | 17–19 |
| J | Week 43–46 | Tree EAGLE (선택, stretch) | 20–23 |
| K | Week 47–49 | 최종 튜닝 & 공식 실측 | **20** |

**궤도 수정의 이유**: 원래 Phase H 는 EAGLE-3 학습 먼저였으나, Gemma 3 1B 을
vanilla drafter 로 먼저 붙여 빠르게 검증한 뒤 acceptance 가 부족할 때만 EAGLE-3
학습으로 교체하는 **fast path** 로 변경.

### Exit 조건 & Fallback

```{mermaid}
flowchart TD
    W26{Week 26:<br>baseline < 5 tok/s?}
    W26 -- Yes --> RCA[원인 분석, G–K 보류]
    W26 -- No --> W36{Week 36:<br>EAGLE acc. < 2.0x?}
    
    W36 -- Yes --> PI[Phase I만 진행, J 생략]
    W36 -- No --> W40{Week 40:<br>< 15 tok/s?}
    
    W40 -- Yes --> PJ[Phase J 필수]
    W40 -- No --> W47{Week 47:<br>< 20 tok/s?}
    
    W47 -- Yes --> Settle[15–18 tok/s 타협,<br>v003으로 이관]
    W47 -- No --> Success([목표 20 tok/s 달성!])
```

| 결정 포인트 | 조건 | 대응 |
|---|---|---|
| Week 26 | baseline < 5 tok/s | 원인 분석, G–K 보류 |
| Week 36 | EAGLE acceptance < 2.0× | Phase I 만 진행, J 생략 |
| Week 40 | < 15 tok/s | Phase J 필수 |
| Week 47 | < 20 tok/s | 15–18 tok/s 로 타협, v003 에서 재달성 |

## 3. Track 2 — v003 (Gemma 4 E4B, 12–15 tok/s)

Gemma 4 E4B (42 layers, MQA, sliding + full attention, 128K 컨텍스트) 를
동일 KV260 플랫폼에서 구동하는 트랙이다. v002의 RTL 자산을 재사용하여 Phase 2+
구현 비용을 약 30% 단축한다.

### Tiered targets

| 수준 | tok/s | 달성 조건 |
|---|---|---|
| Minimum viable | 10 | Phase 2 종료 |
| Acceptable | 12 | Phase 3 종료 |
| **Target** | **12–15** | Phase 5 완료 |
| Stretch | 15+ | DEER 등 실험적 기법 추가 |

### Phase 구성

| Phase | 기간 | 주요 작업 | 기대 tok/s |
|---|---|---|---|
| 1 | Week 16–26 | Foundation — quantize_and_save 확장, vocab trim 262K → 50K, RTL 재파라미터화 | 7 |
| 2 | Week 27–34 | EAGLE-3 linear chain baseline ($30–50 또는 TRC TPU) | 10 |
| 3 | Week 35–39 | Tree EAGLE verify (acceptance 3.5–4×) | 12 |
| 4 | Week 40–43 | SSD async overlap (v002 Phase I RTL 재활용) | 13–14 |
| 5 | Week 44–52 | P-EAGLE + LTD (dynamic K, RL 정책) | **15** |

### Two-track 재사용 관계

```{mermaid}
flowchart LR
  subgraph v002["v002 Extended — Gemma 3N E4B"]
    A[A–F baseline] --> G[G: sparsity] --> H[H/H+: EAGLE-3] --> I[I: SSD] --> J[J: Tree] --> K[K: 실측 20 tok/s]
  end
  subgraph v003["v003 — Gemma 4 E4B"]
    P1[1: foundation] --> P2[2: EAGLE linear] --> P3[3: Tree] --> P4[4: SSD] --> P5[5: P-EAGLE + LTD]
  end
  G -. sparse weight fetcher .-> P1
  H -. EAGLE 학습 파이프라인 .-> P2
  J -. tree mask generator .-> P3
  I -. SSD dispatcher .-> P4
```

## 4. 통합 타임라인 (52주)

```{mermaid}
gantt
    title 통합 타임라인 (52주)
    dateFormat  YYYY-MM-DD
    
    section v002 (Track 1)
    Phase A–C               :v2_1, 2026-01-01, 105d
    Phase D                 :v2_2, after v2_1, 21d
    Phase E–F (5-6 tok/s)   :v2_3, after v2_2, 56d
    Phase G (Sparsity)      :v2_4, after v2_3, 28d
    Phase H / H+ (EAGLE)    :v2_5, after v2_4, 56d
    Phase I (SSD)           :v2_6, after v2_5, 28d
    Phase J (Tree)          :v2_7, after v2_6, 28d
    Phase K (튜닝)          :v2_8, after v2_7, 21d
    20 tok/s 실측           :milestone, m1, after v2_8, 0d
    
    section v003 (Track 2)
    Phase 1 (기반 작업)     :v3_1, after v2_1, 77d
    Phase 2 (EAGLE linear)  :v3_2, after v3_1, 56d
    Phase 3 (Tree EAGLE)    :v3_3, after v3_2, 35d
    Phase 4 (SSD overlap)   :v3_4, after v3_3, 28d
    Phase 5 (P-EAGLE)       :v3_5, after v3_4, 63d
    12-15 tok/s 실측        :milestone, m2, after v3_5, 0d
```

| Week | v002 | v003 |
|---|---|---|
| 1–15 | Phase A–C | — |
| 16–18 | Phase D | Phase 1 시작 |
| 19–26 | Phase E–F (**baseline 5–6 tok/s**) | Phase 1 계속 |
| 27–30 | Phase G | Phase 2 시작 |
| 31–38 | Phase H / H+ | Phase 2 완료 |
| 39–42 | Phase I | Phase 3 |
| 43–46 | Phase J (선택) | Phase 4 |
| 47–49 | **Phase K (20 tok/s 실측)** | Phase 4 계속 |
| 50–52 | — | Phase 5 (**15 tok/s**) |

총 52주 (~12개월). 혼자 파트타임 작업이면 2배 시간 가정.

## 5. Compute 예산

```{mermaid}
pie title 예상 클라우드 컴퓨팅 예산 분배 (총합 ~$100)
    "EAGLE-3 Gemma 3N (v002)" : 30
    "EAGLE Tree variant (v002)" : 15
    "EAGLE-3 Gemma 4 (v003)" : 45
    "초기 보증금" : 10
```

| 항목 | 비용 | 시기 |
|---|---|---|
| Vast.ai / RunPod 가입 | $10 minimum deposit | Week 0 |
| v002 Phase H+ EAGLE-3 Gemma 3N | $20–30 | Week 33–38 |
| v002 Phase J EAGLE Tree variant | $10–15 | Week 43–46 |
| v003 EAGLE-3 Gemma 4 | $30–50 (TRC 승인 시 $0) | Week 27–34 |
| **총합** | **$70–100** ($40 with TRC) | — |

- Phase 0 에 TRC TPU 신청 제출 (승인 1–2주)
- 처음 3–4주는 로컬 개발만으로 충분
- GPU 가 필요한 시점은 Phase H+ 부터

## 6. Year 2 목표 — Auto-Porting Pipeline α (Stretch)

v002 + v003 안정화 후 시작하는 장기 목표. 임의 transformer 의 ``config.json`` +
weight safetensors 를 받아 **pccx 드라이버 API를 호출하는 C 코드 + 양자화된
weight binary**를 자동 생성하는 파이프라인이다.

### 기술 구성

```{mermaid}
flowchart TD
  CFG[Transformer config.json] --> P[Config Parser]
  P --> R[Architecture Resolver]
  R --> F[Special Feature Detector]
  F --> I[ISA Code Generator]
  I --> W[Weight Layout Planner]
  W --> C[C Stub Generator]
  C --> V[Validator: Python golden vs RTL]
```

### 지원 타겟 (우선순위)

- **Tier 1**: 수동 포팅 완료한 모델 재생성 검증 — Gemma 3N E4B, Gemma 4 E4B
- **Tier 2**: 표준 구조 — Llama 3.x, Qwen3, Mistral 7B
- **Tier 3**: 복잡 구조 — DeepSeek-V3 (MoE), Gemma 4 26B A4B (MoE), Phi-3/4

### 일정 (Week 53+)

Week 53–76 (24주 / 6개월) 풀타임 가정:

```{mermaid}
gantt
    title Year 2 — Auto-Porting Pipeline α (Weeks 53–76)
    dateFormat  YYYY-MM-DD
    
    section 코어 파이프라인
    Parser & Resolver       :y2_1, 2027-01-01, 42d
    Tier 2 (Llama, Mistral) :y2_2, after y2_1, 42d
    MoE & Plugins           :y2_3, after y2_2, 42d
    E2E UI / CLI / Docs     :y2_4, after y2_3, 42d
```

- Week 53–58: Parser + Resolver + Gemma 3N/4 재생성 검증
- Week 59–64: Tier 2 지원 (Llama, Qwen, Mistral)
- Week 65–70: Feature plugin 시스템 + MoE 지원
- Week 71–76: E2E 자동화, 웹 UI / CLI, 문서화

### 논문 가능성

*"Auto-Compilation of Transformer Inference Workloads to Custom NPU ISAs"* —
ISCA / MICRO / HPCA / FCCM / FPGA 타겟.

## 7. 마일스톤

### Year 1 KPI

- [ ] Week 26 — Gemma 3N E4B 보드 코히런트 출력, 5+ tok/s
- [ ] Week 38 — EAGLE-3 Gemma 3N checkpoint HF 공개 (세계 최초)
- [ ] Week 47 — **Gemma 3N E4B 20 tok/s 공식 실측** ← 약속 이행
- [ ] Week 52 — Gemma 4 E4B 12+ tok/s 달성
- [ ] Blog post / 논문 초안 (v002 결과 정리)

### Year 2 KPI (Auto-Porting α)

- [ ] Week 76 — Llama 3.1 8B 자동 생성 + KV260 동작
- [ ] Year 2 end — 5+ 모델 family 자동 지원
- [ ] 학술 publication

## 8. RTL 저장소

Track 1 과 Track 2 모두 [`hkimw/pccx-FPGA-NPU-LLM-kv260`](https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260)
에서 구현된다. v002 freeze 시점에 `codes/v002/` 스냅샷을 이 문서 repo 에
고정하고 (§8.4 cutover ceremony), v003 브랜치를 분기한다.

---

**문서 버전**: 2026-04-20 초판. 작성 출처 — 로컬 plan drafts
(`pccx_master_roadmap_final.md`, `pccx_v002_extended_20toks_plan.md`,
`tinynpu_v003_gemma4_e4b_plan.md`). 다음 업데이트: v002 Phase F 완료 시점
(약 Week 26).
