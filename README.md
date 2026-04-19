<div align="center">

# pccx — Parallel Compute Core eXecutor

**A scalable NPU architecture for Transformer LLM inference on edge FPGAs**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Target](https://img.shields.io/badge/Target-Xilinx_Kria_KV260-red)](https://www.xilinx.com/products/som/kria/kv260-vision-starter-kit.html)
[![Architecture](https://img.shields.io/badge/Architecture-v002_Active-purple)](#architecture)
[![Precision](https://img.shields.io/badge/Precision-W4A8_→_BF16%2FFP32-green)](#precision)
[![Docs](https://img.shields.io/badge/Docs-Online-brightgreen)](https://hwkim-dev.github.io/pccx/)

**[📖 Full Documentation →](https://hwkim-dev.github.io/pccx/)**

</div>

---

## What is pccx?

pccx is a hardware-software co-design framework that accelerates **autoregressive decoding** of Transformer-based LLMs on resource-constrained edge devices. The primary target is the **Xilinx Kria KV260** SOM.

Rather than reusing a generic matrix accelerator, pccx is designed around the actual bottleneck of LLM decoding: **memory bandwidth-bound GEMV**, not compute-bound GEMM. The architecture separates matrix (GEMM) and vector (GEMV) datapaths, supplies weights through dedicated HP AXI ports, and uses a custom 64-bit VLIW ISA to eliminate dispatch stalls.

---

## Architecture (v002)

<table>
<tr>
<th>Core</th>
<th>Configuration</th>
<th>Peak Throughput</th>
<th>Primary Use</th>
</tr>
<tr>
<td><b>GEMM (Matrix)</b></td>
<td>32 × 32 systolic array (cascade split @ row 16)</td>
<td><b>819 GMAC/s @ 400 MHz</b></td>
<td>Prefill, Q·Kᵀ, score·V</td>
</tr>
<tr>
<td><b>GEMV (Vector)</b></td>
<td>4 cores × 32-MAC LUT pipeline + 5-stage reduction tree</td>
<td>Weight-streaming limited (~51.2 GMAC/s @ 400 MHz)</td>
<td>Autoregressive decoding</td>
</tr>
<tr>
<td><b>SFU / CVO</b></td>
<td>CORDIC + LUT hybrid</td>
<td>BF16 / FP32 promoted</td>
<td>Softmax, GELU, RMSNorm, RoPE</td>
</tr>
</table>

**Key design decisions:**

- **W4A8 precision** — INT4 weights × INT8 activations via DSP48E2 dual-channel bit packing (1 DSP = 2 MACs)
- **Precision promotion** — non-linear ops (Softmax, GELU, RMSNorm, RoPE) automatically upcast to BF16/FP32 for numerical stability
- **Custom 64-bit VLIW ISA** — 5 opcodes: `GEMV`, `GEMM`, `MEMCPY`, `MEMSET`, `CVO`; decoupled decode/dispatch eliminates front-end stalls
- **Shared L2 (URAM 1.75 MB)** — all three cores share a central SRAM cache; GEMV↔SFU are connected via a direct-connect FIFO, bypassing L2 round-trips
- **Dual clock domains** — 250 MHz AXI/control plane, 400 MHz core compute (×1.6 frequency gain over v001)
- **3.125× total throughput gain** vs. v001 (frequency × dual-MAC DSP packing)

```
External AXI (250 MHz)          Core Domain (400 MHz)
─────────────────────           ──────────────────────────────────────────────────────
S_AXIL_CTRL (HPM)    ────────►  npu_controller_top
                                  ├─ ctrl_npu_decoder   (64-bit VLIW → opcode + body)
S_AXI_HP0/HP1        ────────►  GEMM_systolic_top      (32×16×2, W-Stationary)
S_AXI_HP2/HP3        ────────►  GEMV_top               (4 cores × 32-MAC LUT, 5-stage tree)
S_AXIS_ACP_FMAP      ────────►  ┌─────────────────────────────────┐
M_AXIS_ACP_RESULT    ◄────────  │  Shared L2 Cache (URAM 1.75 MB)│
                                │  GEMV ──FIFO──► CVO_top (SFU)  │
                                └─────────────────────────────────┘
```

---

## Memory Hierarchy

| Level | Technology | Size | Access |
|-------|-----------|------|--------|
| L1 (Activation row buffer) | Block RAM | per-core | Systolic / GEMV lanes |
| L2 (Shared cache) | URAM | 1.75 MB (114,688 × 128-bit) | All cores + mem_dispatcher |
| Weight stream | HP AXI port × 4 | DDR4 bandwidth | HP0/1 → GEMM, HP2/3 → GEMV |
| KV Cache | DDR4 (off-chip) | Up to 10–12 GB | ACP coherent port |

> **KV cache bandwidth wall:** At 32K context (Gemma 3N E4B), the accumulated KV cache reaches ~1.31 GB. Mitigation: KV quantization (FP16→INT8/INT4), attention sink eviction, and a driver-enforced `KV_MAX_TOKENS` hard cap.

---

## Repository Layout

```
pccx/
├── conf.py / index.rst          # English Sphinx config & root toctree
├── ko/                          # Korean Sphinx subsite (ko-first authoring)
│   ├── conf.py
│   └── docs/                    # Korean documentation source
├── docs/                        # English documentation source
│   ├── v002/                    # Active architecture docs
│   │   ├── Architecture/        # Core design, DSP48E2, KV cache, rationale
│   │   ├── ISA/                 # 64-bit VLIW instruction set reference
│   │   ├── Drivers/             # Host API & driver documentation
│   │   └── RTL/                 # Embedded RTL source reference
│   └── archive/experimental_v001/
├── assets/images/               # Architecture diagrams (PNG)
├── _static/                     # JS/CSS (language switcher, Mermaid theme)
└── codes/
    ├── v001/hw/rtl/             # v001 RTL (archived, reference only)
    └── v002/                    # v002 RTL (CI-cloned from pccx-FPGA-NPU-LLM-kv260)
```

Two sibling repositories round out the pccx project:

- **[hwkim-dev/pccx-FPGA-NPU-LLM-kv260](https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260)** — active v002 SystemVerilog sources (CI-cloned into `codes/v002/`).
- **[hwkim-dev/pccx-lab](https://github.com/hwkim-dev/pccx-lab)** — performance simulator and AI-integrated profiler (mounted under `/en/lab/` and `/ko/lab/` on the docs site).

---

## Roadmap — Two-Track + Auto-Porting α

pccx is developed along **two parallel tracks** as of 2026-04-20. The
tracks share RTL assets (sparse weight fetcher, SSD dispatcher, tree mask
generator, EAGLE training pipeline); a long-term auto-porting compiler
begins once both tracks are stable.

| Track | Target model | Goal | Horizon | Key phases |
|-------|-------------|------|---------|------------|
| **v002 Extended** | Gemma 3N E4B | **20 tok/s** measured | Week 1–49 | A–F baseline → G sparsity → H/H+ EAGLE-3 → I SSD → J Tree → K benchmark |
| **v003** | Gemma 4 E4B | **12–15 tok/s** | Week 16–52 (parallel) | 1 foundation → 2 EAGLE linear → 3 Tree → 4 SSD → 5 P-EAGLE + LTD |
| **Auto-Porting α** | Arbitrary Transformer | `config.json` → pccx ISA codegen | Week 53+ (Year 2) | Parser → Resolver → Feature plugin → C-stub emitter |

**Compute budget**: $70–100 total for EAGLE head training ($40 if a TRC
TPU grant lands). Both tracks run on the same KV260 bitstream harness —
v003 branches off after v002 freeze.

→ **[Full roadmap (EN)](https://hwkim-dev.github.io/pccx/en/docs/roadmap.html)**
&nbsp;·&nbsp; [**한국어**](https://hwkim-dev.github.io/pccx/ko/docs/roadmap.html)

---

## Ecosystem

### pccx-lab — Simulator & AI Profiler

Performance simulator and AI-integrated profiler, purpose-built for the pccx NPU. Pre-RTL bottleneck detection, UVM co-simulation, and LLM-driven testbench generation in one workflow.

- Repository: https://github.com/hwkim-dev/pccx-lab
- Documentation: https://hwkim-dev.github.io/pccx/en/lab/ (Korean: https://hwkim-dev.github.io/pccx/ko/lab/)
- Status: Work in Progress

---

## Documentation

The full technical documentation — architecture deep-dives, ISA encoding tables, DSP48E2 bit-packing derivation, driver API, and embedded RTL source — is published at:

### **[hwkim-dev.github.io/pccx/](https://hwkim-dev.github.io/pccx/)**

Available in **English** and **한국어 (Korean)**.

Highlights:
- [Architecture Overview](https://hwkim-dev.github.io/pccx/en/docs/v002/Architecture/top_level.html) — block diagram, design rationale, 3.125× gain breakdown
- [DSP48E2 W4A8 Derivation](https://hwkim-dev.github.io/pccx/en/docs/v002/Architecture/dsp48e2_w4a8.html) — dual-channel bit packing math
- [Custom ISA Reference](https://hwkim-dev.github.io/pccx/en/docs/v002/ISA/index.html) — 64-bit VLIW encoding, opcode table, dataflow
- [RTL Source Reference](https://hwkim-dev.github.io/pccx/en/docs/v002/RTL/index.html) — embedded SystemVerilog with live syntax highlighting

---

## Building the Docs Locally

```bash
pip install -r requirements.txt
sudo apt-get install graphviz   # for Graphviz diagrams

# Clone v002 RTL (required for literalinclude directives)
git clone --depth 1 \
  https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260 \
  codes/v002

# Build English site
sphinx-build -b html . _build/html/en

# Build Korean site
sphinx-build -b html ko _build/html/ko

# Serve locally
python -m http.server --directory _build/html
# → open http://localhost:8000/en/ or /ko/
```

---

## v001 → v002 Migration

| Pain point (v001) | v002 solution |
|---|---|
| Core role ambiguity (Matrix/Vector/CVO blurred) | Strict separation: GEMM / GEMV / SFU |
| Excessive intermediate bus paths | Shared L2 + direct-connect FIFO for GEMV↔SFU |
| L2 ↔ Global Cache responsibility overlap | Single unified L2 (URAM) |
| Single HP port → one systolic array bottleneck | HP0/HP1 for GEMM, HP2/HP3 for GEMV (distributed) |
| 1 DSP = 1 MAC (bit headroom wasted) | Dual-channel packing → 1 DSP = 2 MACs |
| 250 MHz ceiling (AXI clock) | Decoupled 400 MHz core domain |

---

## License

Licensed under the **[Apache License 2.0](LICENSE)**.

---

See [`CLAUDE.md`](CLAUDE.md) for the full build & contribution guide.

---

<div align="center">

Built by [@hwkim-dev](https://hwkim-dev.github.io/hwkim-dev/) · [Documentation](https://hwkim-dev.github.io/pccx/) · [Issues](https://github.com/hwkim-dev/pccx/issues)

</div>
