Evidence
========

.. rubric:: "설계" → "검증된 시스템"

This page answers the single question a skeptical reviewer asks:
**"does this actually run?"**  Each row links to a reproducible
artefact (captured ``.pccx`` trace, Vivado utilisation report, or
board-log excerpt) so the numbers can be independently verified.

When a measurement is not yet in hand the row is **pending** with
the gating task explicitly called out — never a speculative figure.

Measured (reproducible)
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 30

   * - Metric
     - Value
     - Source
     - Reproducer
   * - Sail model type-check
     - clean
     - ``formal/sail/`` (64-bit / 4-bit opcode)
     - ``make check`` (< 5 s)
   * - pccx-core test suite
     - 7/7 ISA + 16 analyzer tests
     - ``cargo test -p pccx-core``
     - ``cargo test`` from pccx-lab root
   * - ``.pccx`` binary format decode round-trip
     - bit-exact
     - ``pccx_format.rs``
     - ``pccx_analyze sample.pccx``
   * - Sphinx zero-warning build
     - EN + KO
     - ``_ext/*.py`` + ``docs/**``
     - ``make strict``
   * - Golden-diff regression gate (self-calibrated)
     - 8 / 8 steps + 128 / 128 steps within ±15 %
     - ``samples/*.ref.jsonl`` in pccx-lab
     - ``pccx_golden_diff --check samples/gemma3n_16tok_smoke.ref.jsonl samples/gemma3n_16tok_smoke.pccx``

Pending (board / synth)
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Metric
     - Status
     - Gate
   * - End-to-end Gemma-3N E4B decode tok/s
     - pending board run
     - §4.1 RTL dispatcher + Global_Scheduler wiring
       (:doc:`../v002/Architecture/index`)
   * - KV260 resource usage (LUT / DSP / URAM / BRAM)
     - pending Vivado impl
     - ``pccx_analyze --run-synth <rtl_repo>`` landing
       (:doc:`../Lab/cli`)
   * - Timing closure @ 400 MHz core / 250 MHz AXI
     - pending Vivado impl
     - Gate as above
   * - Layer-by-layer golden-model diff (vs PyTorch reference)
     - pending ``tools/pytorch_reference.py`` landing
     - Scaffold (``pccx_golden_diff`` CLI + ``.ref.jsonl`` schema)
       already landed — see the measured row above.  PyTorch side
       will replace self-calibrated references with
       semantically-grounded expectations.
   * - P99 decode latency under sustained load
     - pending board capture
     - Requires 512-token run on real DDR traffic.
   * - 7 W TDP headroom under W4A8KV4 decode
     - pending Vivado impl + board pmbus
     - Gates same as resource usage.

Baselines (for future comparison)
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Baseline
     - Target
     - Method
   * - CPU (Ryzen 4500U, llama.cpp Q4_K_M)
     - tok/s on Gemma-3N E4B
     - ``llama.cpp`` with pinned thread count (4 × 2 GHz Zen 2).
   * - GPU (RTX 4060, HF Transformers bf16)
     - tok/s on Gemma-3N E4B
     - PyTorch 2.4, generate() with KV cache on, batch = 1.
   * - On-device (pccx v002 @ KV260)
     - tok/s on Gemma-3N E4B
     - ``pccx_analyze --board kv260.local`` (queued).

How this page gets updated
--------------------------

1. ``pccx-FPGA-NPU-LLM-kv260`` captures a new ``.pccx`` or Vivado
   report.
2. ``pccx-lab`` exports the relevant fields via ``pccx_analyze --json``.
3. A commit to this repo lands the numbers in the tables above, with
   the source link and a permanent ``samples/`` artefact.
4. ``make strict`` passes, CI re-deploys the page.

No speculative numbers.  Every row either links to a reproducible
artefact or is marked **pending** with a named gate.

.. toctree::
   :hidden:
   :maxdepth: 1

Cite this page
--------------

.. code-block:: bibtex

   @misc{pccx_evidence_2026,
     title        = {pccx Evidence: reproducible measurement log for an open W4A8 NPU},
     author       = {Kim, Hyunwoo},
     year         = {2026},
     howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Evidence/index.html}},
     note         = {Tracks the "설계 → 검증된 시스템" closure plan.  Part of pccx: \url{https://hkimw.github.io/pccx/}}
   }
