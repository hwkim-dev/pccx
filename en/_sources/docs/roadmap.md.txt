# Roadmap (Two-Track)

:::{dropdown} Quick Navigation
:open:

```{contents}
:local:
:depth: 2
:backlinks: none
```
:::

As of 2026-04-20, pccx is developed along **two parallel tracks**. v002 is
the currently active architecture; v003 targets the next-generation model
(Gemma 4 E4B) on the same KV260 platform. The two tracks share RTL
assets — sparse weight fetcher, SSD dispatcher, tree mask generator,
EAGLE training pipeline.

The long-term stretch goal is an **Auto-Porting Pipeline α** — a compiler
that emits a pccx ISA stream from an arbitrary transformer config. It
begins in Year 2 once both tracks are stable.

## 1. Common assumptions

- **Platform**: Xilinx Kria KV260 (Zynq UltraScale+ ZU5EV), bare-metal
- **Quantization**: W4A8 (INT4 weights × INT8 activations), KV cache INT4
- **Clock**: AXI 250 MHz, core 400 MHz
- **VLIW ISA**: 5 base opcodes (GEMV, GEMM, MEMCPY, MEMSET, CVO) + SPEC extensions
- **L2 URAM 2.25 MB budget**: 1.0 MB activation pinning, 0.5 MB KV prefetch,
  0.25 MB tree mask + scheduler state, 0.5 MB hot-attention tile

## 2. Track 1 — v002 Extended (Gemma 3N E4B, 20 tok/s)

Layers FFN sparsity and a speculative-decoding stack on top of the active
v002 to reach the **promised 20 tok/s measured throughput**.

### Tiered targets

| Tier | tok/s | Gate |
|---|---|---|
| Baseline | 5–6 | Phase A–F done |
| Viable | 10–12 | Phase G + H done |
| **Promise** | **20** | Phase G–K done |
| Stretch | 25+ | Add Tree EAGLE (Phase J) |

### Phase plan

| Phase | Weeks | Main work | Target tok/s |
|---|---|---|---|
| A–F | 1–26 | Re-parameterization → driver → Gemma 3N app → verification → synthesis → board bring-up | 5–6 |
| G | 27–30 | All-layer Gaussian Top-K sparsity (BW 1.95 → 1.36 GB/token) | 8–9 |
| H | 31–32 | Gemma 3 1B vanilla drafter (fast path, tokenizer-compatible) | 11–14 |
| H+ | 33–38 | EAGLE-3 head training & swap-in ($20–30 on Vast.ai RTX 4090) | 14–16 |
| I | 39–42 | SSD async overlap (draft/verify pipelining) | 17–19 |
| J | 43–46 | Tree EAGLE (optional, stretch) | 20–23 |
| K | 47–49 | Final tuning & official benchmark | **20** |

**Why the schedule changed**: the original Phase H trained EAGLE-3 first.
Current plan attaches **Gemma 3 1B as a vanilla drafter first** (fast path)
and swaps in a trained EAGLE-3 head only if the measured acceptance rate
is insufficient.

### Decision points & fallbacks

```{mermaid}
flowchart TD
    W26{Week 26:<br>baseline < 5 tok/s?}
    W26 -- Yes --> RCA[Root-cause analysis, hold G–K]
    W26 -- No --> W36{Week 36:<br>EAGLE acc. < 2.0x?}
    
    W36 -- Yes --> PI[Run Phase I only, drop J]
    W36 -- No --> W40{Week 40:<br>< 15 tok/s?}
    
    W40 -- Yes --> PJ[Phase J becomes mandatory]
    W40 -- No --> W47{Week 47:<br>< 20 tok/s?}
    
    W47 -- Yes --> Settle[Settle for 15–18 tok/s, push 20 to v003]
    W47 -- No --> Success([Goal 20 tok/s Met!])
```

| Week | Condition | Action |
|---|---|---|
| 26 | baseline < 5 tok/s | Root-cause analysis, hold G–K |
| 36 | EAGLE acceptance < 2.0× | Run Phase I only, drop J |
| 40 | < 15 tok/s | Phase J becomes mandatory |
| 47 | < 20 tok/s | Settle for 15–18 tok/s, push 20 tok/s to v003 |

## 3. Track 2 — v003 (Gemma 4 E4B, 12–15 tok/s)

Gemma 4 E4B (42 layers, MQA, sliding + full attention, 128 K context)
on the same KV260 platform. Reuses v002 RTL assets to cut Phase 2+
implementation cost by ~30 %.

### Tiered targets

| Tier | tok/s | Gate |
|---|---|---|
| Minimum viable | 10 | Phase 2 done |
| Acceptable | 12 | Phase 3 done |
| **Target** | **12–15** | Phase 5 done |
| Stretch | 15+ | Add experimental techniques (e.g. DEER) |

### Phase plan

| Phase | Weeks | Main work | Target tok/s |
|---|---|---|---|
| 1 | 16–26 | Foundation — extend `quantize_and_save`, vocab trim 262K → 50K, re-parameterize RTL | 7 |
| 2 | 27–34 | EAGLE-3 linear chain baseline ($30–50 or TRC TPU if granted) | 10 |
| 3 | 35–39 | Tree EAGLE verify (acceptance 3.5–4×) | 12 |
| 4 | 40–43 | SSD async overlap (reuse v002 Phase I RTL) | 13–14 |
| 5 | 44–52 | P-EAGLE + LTD (dynamic K, RL policy) | **15** |

### Cross-track asset reuse

```{mermaid}
flowchart LR
  subgraph v002["v002 Extended — Gemma 3N E4B"]
    A[A–F baseline] --> G[G: sparsity] --> H[H/H+: EAGLE-3] --> I[I: SSD] --> J[J: Tree] --> K[K: 20 tok/s benchmark]
  end
  subgraph v003["v003 — Gemma 4 E4B"]
    P1[1: foundation] --> P2[2: EAGLE linear] --> P3[3: Tree] --> P4[4: SSD] --> P5[5: P-EAGLE + LTD]
  end
  G -. sparse weight fetcher .-> P1
  H -. EAGLE training pipeline .-> P2
  J -. tree mask generator .-> P3
  I -. SSD dispatcher .-> P4
```

## 4. Integrated timeline (52 weeks)

```{mermaid}
gantt
    title Integrated Timeline (52 Weeks)
    dateFormat  YYYY-MM-DD
    
    section v002 (Track 1)
    Phase A–C               :v2_1, 2026-01-01, 105d
    Phase D                 :v2_2, after v2_1, 21d
    Phase E–F (5-6 tok/s)   :v2_3, after v2_2, 56d
    Phase G (Sparsity)      :v2_4, after v2_3, 28d
    Phase H / H+ (EAGLE)    :v2_5, after v2_4, 56d
    Phase I (SSD)           :v2_6, after v2_5, 28d
    Phase J (Tree)          :v2_7, after v2_6, 28d
    Phase K (Tuning)        :v2_8, after v2_7, 21d
    20 tok/s benchmark      :milestone, m1, after v2_8, 0d
    
    section v003 (Track 2)
    Phase 1 (Foundation)    :v3_1, after v2_1, 77d
    Phase 2 (EAGLE linear)  :v3_2, after v3_1, 56d
    Phase 3 (Tree EAGLE)    :v3_3, after v3_2, 35d
    Phase 4 (SSD overlap)   :v3_4, after v3_3, 28d
    Phase 5 (P-EAGLE)       :v3_5, after v3_4, 63d
    12-15 tok/s benchmark   :milestone, m2, after v3_5, 0d
```

| Week | v002 | v003 |
|---|---|---|
| 1–15 | Phase A–C | — |
| 16–18 | Phase D | Phase 1 starts |
| 19–26 | Phase E–F (**baseline 5–6 tok/s**) | Phase 1 continues |
| 27–30 | Phase G | Phase 2 starts |
| 31–38 | Phase H / H+ | Phase 2 completes |
| 39–42 | Phase I | Phase 3 |
| 43–46 | Phase J (optional) | Phase 4 |
| 47–49 | **Phase K (20 tok/s benchmark)** | Phase 4 continues |
| 50–52 | — | Phase 5 (**15 tok/s**) |

Total 52 weeks (~12 months) assuming full-time solo work. Double the
duration for a part-time schedule.

## 5. Compute budget

```{mermaid}
pie title Estimated Compute Budget Allocation (Total ~$100)
    "EAGLE-3 Gemma 3N (v002)" : 30
    "EAGLE Tree variant (v002)" : 15
    "EAGLE-3 Gemma 4 (v003)" : 45
    "Initial deposits" : 10
```

| Item | Cost | Window |
|---|---|---|
| Vast.ai / RunPod sign-up | $10 minimum deposit | Week 0 |
| v002 Phase H+ EAGLE-3 (Gemma 3N) | $20–30 | Week 33–38 |
| v002 Phase J EAGLE tree variant | $10–15 | Week 43–46 |
| v003 EAGLE-3 (Gemma 4) | $30–50 (or $0 with TRC) | Week 27–34 |
| **Total** | **$70–100** ($40 with TRC) | — |

- Submit TRC TPU application at Phase 0 (1–2 week approval).
- First 3–4 weeks need no cloud compute — local development only.
- GPU becomes necessary starting at Phase H+.

## 6. Year 2 — Auto-Porting Pipeline α (stretch)

Kicks off once v002 + v003 are stable. Takes an arbitrary transformer
`config.json` + weight safetensors and emits **C code that calls the pccx
driver API, plus a quantized weight binary**.

### Technical shape

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

### Target priority

- **Tier 1**: regenerate hand-ported models — Gemma 3N E4B, Gemma 4 E4B
- **Tier 2**: standard architectures — Llama 3.x, Qwen3, Mistral 7B
- **Tier 3**: complex architectures — DeepSeek-V3 (MoE), Gemma 4 26B A4B (MoE), Phi-3/4

### Schedule (Week 53+)

Week 53–76 (24 weeks / 6 months), full-time:

```{mermaid}
gantt
    title Year 2 — Auto-Porting Pipeline α (Weeks 53–76)
    dateFormat  YYYY-MM-DD
    
    section Core Pipeline
    Parser & Resolver       :y2_1, 2027-01-01, 42d
    Tier 2 (Llama, Mistral) :y2_2, after y2_1, 42d
    MoE & Plugins           :y2_3, after y2_2, 42d
    E2E UI / CLI / Docs     :y2_4, after y2_3, 42d
```

- Week 53–58 — Parser + Resolver + Gemma 3N/4 regeneration check
- Week 59–64 — Tier 2 support (Llama, Qwen, Mistral)
- Week 65–70 — Feature plugin system + MoE support
- Week 71–76 — E2E automation, web UI / CLI, docs

### Publication angle

*"Auto-Compilation of Transformer Inference Workloads to Custom NPU ISAs"* —
target venues ISCA / MICRO / HPCA / FCCM / FPGA.

## 7. Milestones

### Year 1 KPIs

- [ ] Week 26 — Coherent Gemma 3N E4B decode on board, 5+ tok/s
- [ ] Week 38 — EAGLE-3 Gemma 3N checkpoint released on HF (first public)
- [ ] Week 47 — **Gemma 3N E4B 20 tok/s officially measured** ← promise met
- [ ] Week 52 — Gemma 4 E4B at 12+ tok/s
- [ ] Blog post / paper draft (v002 results)

### Year 2 KPIs (Auto-Porting α)

- [ ] Week 76 — Llama 3.1 8B auto-generated + running on KV260
- [ ] Year 2 end — 5+ model families supported
- [ ] Academic publication

## 8. RTL repository

Both tracks are implemented in [`hkimw/pccx-FPGA-NPU-LLM-kv260`](https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260).
At v002 freeze the `codes/v002/` snapshot is pinned into this docs repo
(see the version-cutover ceremony), then v003 branches off.

---

**Document version**: 2026-04-20, first edition. Compiled from local plan
drafts (`pccx_master_roadmap_final.md`, `pccx_v002_extended_20toks_plan.md`,
`tinynpu_v003_gemma4_e4b_plan.md`). Next update: at v002 Phase F
completion (~ Week 26).
