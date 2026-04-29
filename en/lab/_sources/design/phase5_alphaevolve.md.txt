# Phase 5 — AlphaEvolve → OpenEvolve

**Status:** scaffold landed (`pccx-evolve` trait scaffolds + speculative); implementation kicks off in Phase 5 proper.
**Scope:** roadmap Weeks 19-30 (±4 weeks uncertainty band); milestones 5A, 5B, 5C + user-requested 5D, 5E.
**Thesis:** Fix the weaknesses of existing AlphaEvolve-style systems by combining **LLM + Reinforcement Learning + Formal Methods + Surrogate Models**.

## 1. Architecture overview

```
            ┌─────────────────────────────────────────────────┐
            │              pccx-evolve                         │
            │                                                  │
User spec ──▶│  ┌──────────┐   ┌──────────┐   ┌──────────┐  │── accepted
            │  │ LLM prop. │──▶│ PRM gate │──▶│ Surrogate│  │   candidate
            │  │ (Sonnet)  │   │ (fast)   │   │ (GNN)    │  │──▶
            │  └──────────┘   └──────────┘   └──────────┘  │
            │        ▲                                       │
            │        │   evolutionary loop (mutate+cross)   │
            │        └───────────────────────────────────────┤
            │                                                │
            │  Sail refinement check (pccx-verification)    │
            │  Formal property check (Lean 4)               │
            └────────────────────────────────────────────────┘
```

Five lanes:

| Lane | Input | Output | Audience |
|---|---|---|---|
| **5A** Chip DSE | RTL + target | RTL variants (Pareto front) | HW engineer |
| **5B** Compiler DSE | High-level code | LLVM pass order + RL'd alloc | SW engineer |
| **5C** OS/Kernel formal | Kernel C | Proven kernel module | Systems engineer |
| **5D** Model → API | HF model + spec | Target-specific driver code | AI researcher |
| **5E** Model → RTL | HF model + spec | Custom NPU RTL + proof | Chip architect |

5D + 5E are user-requested on 2026-04-24 and build on top of 5A + 5C.

## 2. Milestones

### 5A — Chip Design Space Exploration (Weeks 19-22)

**Problem:** RTL design space is enormous (instruction width, opcode encoding, DSP cluster size, pipeline depth).

**Solution:**

1. **Surrogate** — GNN on RTL AST predicts area / power / delay / fmax without synthesis.  Trained on ~10 K historical Vivado runs from `pccx-FPGA-NPU-LLM-kv260`.  Target latency: < 10 ms / query.
2. **Evolutionary loop** — population = RTL variants, fitness = surrogate prediction + Verilator pass + verible-lint pass + timing-sanity check.
3. **PRM gate** — deep cloud LLM proposes RTL → Verilator elaborates → verible lints → timing-check sanity-tests → survivors go to the surrogate.
4. **Formal diff** — promoted variants must pass `pccx-verification::GoldenDiffGate` + Sail refinement check.

Deliverable: "design an NPU for Gemma-3N E4B decoding at 20 tok/s on KV260" in < 1 day wall-clock.

### 5B — Compiler Superoptimization (Weeks 22-24)

**Problem:** `-O3` leaves performance on the table.  Register allocation + instruction scheduling are NP-hard, so compilers use heuristics.

**Solution:**

1. **MCTS** over LLVM pass orderings.  Reward = measured runtime on the target (or cycle-accurate sim on TinyNPU).
2. **GNN + RL** for register allocation and instruction scheduling.  Policy network ingests the data-flow graph; actions are "assign register R to virtual V".  Reward = -pipeline-stalls - register-pressure.
3. **Compiler explainer** — post-run, Sonnet narrates *why* the found pass order beats `-O3` in terms the developer understands.

Deliverable: AI-compiled kernel beats hand-tuned expert kernel on ≥ 3 benchmarks (matmul, attention, layer-norm).

### 5C — OS / Kernel Formal Co-Design (Weeks 24-27)

**Non-negotiable: stability > everything.**

Hybrid architecture:

1. LLM drafts kernel module / driver / scheduler.
2. Feed to Lean 4 theorem prover (extract proof obligations automatically).
3. Prove: no memory leaks, no deadlocks, mutex correctness, scheduler starvation-free.
4. On failure: return counter-example trace to LLM → propose fix → re-prove.  Iterate until mathematically correct.

Start narrow: reuse seL4-style libraries; don't reinvent formal primitives.

Deliverable: pccx-NPU driver with signed Lean 4 correctness proof bundled.

### 5D — Model → ISA-API Compiler (Weeks 27-30)  **USER BIG BET**

**Input:** a HuggingFace model (`.safetensors` + `config.json` + tokenizer) + pccx ISA spec.

**Pipeline:**

1. Parse the model's computation graph → tensor op sequence.
2. Map each op to pccx ISA opcodes (Sail spec is the ground truth).
3. deep cloud LLM generates Rust/C driver code that issues those opcodes in order.
4. Run pccx-lab simulator against PyTorch reference trace → bit-exact check (or `pccx-verification::GoldenDiffGate`).
5. Emit the signed driver + a verification report.

**Deliverable:** drop a model file in → get a `uca_run_<model>` function out, validated by the Sail oracle.

Depends on: Phase 4 `M4.8-M4.10` Sail completion (for reliable refinement check).

### 5E — Generative Chip Design (Weeks 30+)  **USER ULTIMATE GOAL**

**Input:** same model file + target silicon family (KV260 / ASIC-22nm).

**Pipeline:**

1. Run 5D, inspect the resulting `.pccx` trace, identify bottleneck (compute-bound vs memory-bound).
2. Feed bottleneck + model structure to 5A's evolutionary loop.
3. Candidates must pass:
   - Verilator + verible-lint (PRM gate),
   - Surrogate Pareto threshold (area / power / fmax),
   - Sail refinement (every ISA op behaves equivalently to the spec),
   - Formal property check (every pccx invariant holds — e.g. "no MAC overflow").
4. Synthesize top-K survivors in parallel via 5C-authorised Vivado runners.
5. Pick Pareto front; user selects final.

**Deliverable:** feed `gemma-3n-e4b.safetensors` + "KV260" → receive a tailor-made NPU RTL + bitstream + correctness proof in < 48 hours.

## 3. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Surrogate accuracy poor on out-of-distribution designs | Medium | High | Keep the "truth" escape valve — any variant whose predicted metrics diverge > 20% from actual synth gets the surrogate retrained on it. |
| Lean 4 proof obligations auto-extraction brittle | Medium | High | Start with known-provable kernel modules; expand only as tooling matures. |
| Model input shapes outside pccx v002 ISA capacity | Low | High | Surface as a compile-time error in 5D; fall back to CPU reference path. |
| Sonnet RTL proposals generate linter-clean but timing-broken candidates | High | Medium | PRM gate does static timing sanity check (critical-path estimate) before the surrogate. |
| 5E wall-clock target (48 h) unachievable on KV260 workstations | High | Medium | Offload synth to a cloud Vivado cluster; document the trade-off. |

## 4. Decision — internal first, open later

**Phase 5.0 Gate:**  use the engine on pccx-lab's **own** RTL and kernel for the first 3 months before exposing publicly.  Rationale:

- Proves value on code we understand.
- Surfaces infra bugs before customer exposure.
- Generates training data for the surrogate.
- Establishes a credible launch story ("we used it to build ourselves").

Open to external users once:
- Surrogate accuracy ≥ 90% on PCCX-Lab's internal benchmarks.
- Formal gate signs off ≥ 3 non-trivial kernel modules.
- 5D succeeds on ≥ 3 third-party models (Gemma 3N, Llama-2, BERT).

Target public release: **pccx-lab v0.5** (roughly Q1-2027 at current cadence).

## 5. Token budget

- Surrogate queries: 0 LLM tokens (pure inference).
- PRM gate: 0 LLM tokens (static analysis only).
- LLM mutation proposals: Haiku (500-1 K tokens/mutation; thousands/day).
- LLM final-round refinement: Sonnet (2-5 K tokens/candidate; tens/day).
- LLM Lean 4 repair (5C): Sonnet/Opus (5-20 K tokens/iteration; hundreds/week).
- LLM concept-to-RTL narration (5D/5E): Opus (10-50 K tokens/session; dozens/week).

Cache all narrations by `(input hash, prompt template hash)` — 60%
hit rate target in steady state.

## 6. Dependencies on earlier phases

- Phase 1 scaffold — done (pccx-evolve traits landed).
- Phase 2 M2.6 (target-aware suggestions) — feeds FPGA presets into 5A.
- Phase 3 M3.4 (sandboxed sessions) — runs Vivado in isolation.
- Phase 4 M4.5 (what-if engine) — visualises 5A's Pareto front.
- Phase 4 M4.8-4.10 (Sail finale) — refinement oracle for 5D/5E.

Don't start 5E before all of the above land.
