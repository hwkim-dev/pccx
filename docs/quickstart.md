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
Everything on this page is the **reproducer** the NVIDIA consultation
report (§6.5) asked for — `docker compose up` lands you at a running
profiler with a real capture loaded.

```{contents}
:local:
:depth: 2
```

## 0. What you get

| Artefact | Produced by | Opens with |
|---|---|---|
| `.pccx` trace (16-token Gemma-3N decode) | `pccx-FPGA-NPU-LLM-kv260/hw/sim/run_verification.sh` | `pccx-lab` (Tauri app) |
| Sail ISA model (type-checked)            | `pccx-FPGA-NPU-LLM-kv260/formal/sail/`                | `sail`, `sail --doc` |
| Vivado synth + timing reports            | `pccx-FPGA-NPU-LLM-kv260/vivado/build.sh synth`       | `pccx_analyze --synth` |
| AnalyzerDashboard findings               | `pccx-lab` workspace                                  | 16 built-in analyzers |

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
git clone https://github.com/hwkim-dev/pccx.git                    # docs (this site)
git clone https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260.git  # RTL + Sail model
git clone https://github.com/hwkim-dev/pccx-lab.git                 # profiler + UVM Copilot
```

## 3. One-command reproducer (Docker)

```bash
cd ~/pccx-ws/pccx-lab
docker compose -f scripts/docker/quickstart.yml up
```

The container:

1. Builds `pccx-core` and the `pccx_analyze` CLI.
2. Runs the bundled xsim smoke TB (takes ~30 s on a recent laptop).
3. Writes the resulting `.pccx` to `./out/smoke.pccx`.
4. Prints the 16 analyzer summaries to stdout.
5. Exits 0 on success — ready for CI pipe.

Pipe it to a report:

```bash
docker compose ... > report.txt 2>&1
```

## 4. Native path (no Docker)

```bash
# ── Sail model ─────────────────────────────────────────────────
eval $(opam env)
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260/formal/sail
make check                           # type-check; < 5 s

# ── pccx-core + CLI ────────────────────────────────────────────
cd ~/pccx-ws/pccx-lab
cargo build -p pccx-core --bin pccx_cli --release
./target/release/pccx_cli \
    samples/gemma3n_16tok_smoke.pccx    # header + roofline + bottleneck

# ── pccx-lab (Tauri desktop app) ───────────────────────────────
cd src/ui
npm ci && npm run tauri dev
```

The `samples/` directory ships two pre-captured traces — see
[`samples/README.md`](https://github.com/hwkim-dev/pccx-lab/blob/main/samples/README.md):

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
  author       = {Kim, Hwangwoo},
  year         = {2026},
  howpublished = {\url{https://hwkim-dev.github.io/pccx/en/docs/quickstart.html}},
  note         = {Part of pccx: \url{https://hwkim-dev.github.io/pccx/}}
}
```
