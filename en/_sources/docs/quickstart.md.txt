---
myst:
  html_meta:
    description lang=en: |
      One-command reproducer for the pccx NPU — clone, build, load the
      sample .pccx trace, run the Sail formal model, open the pccx-lab
      profiler.  Docker recipe + native bare-metal paths, both tested
      on Ubuntu 24.04.
---

# Quickstart

The shortest path from "git clone" to "I'm looking at a pccx trace".
Everything on this page is the **reproducer**: `docker compose up`
lands you at a running profiler with a real capture loaded.

```{contents} On this page
:depth: 2
:backlinks: none
```

## 0. What you get

```{mermaid}
flowchart LR
    A[RTL Repository<br>Vivado Synth] -->|generates| B(16-token .pccx trace)
    A -->|produces| C(Sail ISA Model)
    
    B -.->|loads into| D{pccx-lab Profiler}
    C -.->|type-checks in| E[OCaml / opam]
    
    D --> F[CLI Analytics<br>roofline / report]
    D --> G[Tauri Desktop App<br>Visual IDE]
    
    style D fill:#ff7a00,stroke:#fff,color:#fff
```

| Artefact | Produced by | Opens with |
|---|---|---|
| `.pccx` trace (16-token Gemma-3N decode) | `pccx-FPGA-NPU-LLM-kv260/hw/sim/run_verification.sh` | `pccx-lab` (Tauri app), `pccx_cli` |
| Sail ISA model (type-checked)            | `pccx-FPGA-NPU-LLM-kv260/formal/sail/`                | `sail`, `sail --doc` |
| Vivado synth + timing reports            | `pccx-FPGA-NPU-LLM-kv260/vivado/build.sh synth`       | `pccx-lab` IDE → Verification → Synth Status |
| Trace analytics                          | `pccx-lab` workspace                                  | `pccx_cli --roofline --report-md`, IDE analyzer tabs |

## 1. Prerequisites

A single 64-bit Linux box (Ubuntu 24.04 tested) with:

- `git` ≥ 2.40
- `opam` + `ocaml` ≥ 4.14 — for Sail
- `docker` ≥ 24 — for the reproducer container
- `rustup` (stable toolchain) — for `pccx-core` + Tauri
- *(optional)* Xilinx Vivado 2024.1 — for the RTL synth path
- *(optional)* Xilinx Kria KV260 board — for live token-generation

Only the first four are required to reproduce the **software** half of
the project.  Board access is optional.

## 2. Clone all three repos

pccx is a **three-repo federation** (see the ecosystem section on
{doc}`index`).  Clone them into sibling directories:

```bash
mkdir -p ~/pccx-ws && cd ~/pccx-ws
git clone https://github.com/hkimw/pccx.git                    # docs (this site)
git clone https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260.git  # RTL + Sail model
git clone https://github.com/hkimw/pccx-lab.git                 # profiler + UVM Copilot
```

## 3. One-command reproducer (Docker)

```{admonition} Planned — not yet shipped
:class: warning

The Docker reproducer (`scripts/docker/quickstart.yml`) is tracked on
the pccx-lab roadmap but has not landed on `main` yet.  Until it does,
follow the [native path below](#4-native-path-no-docker) — it is
identical to what the container will run internally.
```

## 4. Native path (no Docker)

```bash
# ── Sail model ─────────────────────────────────────────────────
eval $(opam env)
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260/formal/sail
make check                           # type-check; < 5 s

# ── pccx-core + CLI ────────────────────────────────────────────
cd ~/pccx-ws/pccx-lab
cargo build -p pccx-reports --bin pccx_cli --release
./target/release/pccx_cli \
    samples/gemma3n_16tok_smoke.pccx \
    --roofline --report-md          # header + roofline + bottleneck

# ── pccx-lab (Tauri desktop app) ───────────────────────────────
cd ui
npm ci && npm run tauri dev
```

The `samples/` directory ships two pre-captured traces — see
[`samples/README.md`](https://github.com/hkimw/pccx-lab/blob/main/samples/README.md):

- `gemma3n_16tok_smoke.pccx`   (101 KB, 2,568 events)  — CI smoke size.
- `gemma3n_128tok_decode.pccx` (797 KB, 20,488 events) — steady-state decode.

## 5. Board path (optional)

```bash
# Flash the bitstream and run a 16-token decode on the KV260.
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260/scripts/board
./bringup.sh kv260.local
# Pulls the .pccx back to the host automatically; open in pccx-lab.
```

## 6. Where to go next

- Read the [pccx-lab handbook](Lab/index) for the profiler API surface.
- Read the [Formal model page](v002/Formal/index) for the Sail scaffold.
- Read the [Evidence page](Evidence/index) for measured tok/s + latency
  numbers (board runs in progress).

## Cite this page

```bibtex
@misc{pccx_quickstart_2026,
  title        = {pccx Quickstart: one-command reproducer for the open NPU},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/quickstart.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
