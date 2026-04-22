pccx-lab Handbook
=================

**pccx-lab** is the desktop profiler + verification IDE for the pccx v002
NPU. It ingests ``.pccx`` binary traces emitted by the xsim testbench
suite on the companion ``pccx-FPGA-NPU-LLM-kv260`` RTL repo and surfaces
the timeline, roofline, bottleneck windows, waveform, Vivado synth
reports, and AI-driven UVM strategies in a single Tauri v2 window.

This section documents the tool's internal surface — the ``TraceAnalyzer``
registry, the ``Copilot`` automation facade, the command-line binaries,
and the research lineage that grounds each analyzer in a published paper.

For the user-facing desktop app itself, see the separate
`pccx-lab site <https://hwkim-dev.github.io/pccx/en/lab/>`_.

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4

   .. grid-item-card:: :octicon:`book;1em;sd-mr-1` Architecture
      :link: architecture
      :link-type: doc

      Repo layout, layer contract, data flow, extension hooks.

   .. grid-item-card:: :octicon:`terminal;1em;sd-mr-1` CLI reference
      :link: cli
      :link-type: doc

      ``pccx_analyze`` modes (pretty / JSON / Markdown / synth /
      ``--compare`` / ``--research-list`` / ``--explain``), plus
      ``pccx_cli`` and ``from_xsim_log``.

   .. grid-item-card:: :octicon:`graph;1em;sd-mr-1` Analyzer API
      :link: analyzer_api
      :link-type: doc

      The ``TraceAnalyzer`` trait, the 16-entry built-in registry, and
      how to land a new analysis in one file.

   .. grid-item-card:: :octicon:`beaker;1em;sd-mr-1` Copilot API
      :link: copilot
      :link-type: doc

      The ``Copilot`` struct — ``investigate()``, ``explain(id)``,
      ``rank_by_severity()``, ``suggest_fix(intent)`` — and the intent
      keyword routing table.

   .. grid-item-card:: :octicon:`milestone;1em;sd-mr-1` Research lineage
      :link: research
      :link-type: doc
      :columns: 12

      Auto-generated table of every arxiv paper each analyzer / UVM
      strategy implements. Updated via ``pccx_analyze --research-list``.

.. toctree::
   :hidden:
   :maxdepth: 1

   architecture
   cli
   analyzer_api
   copilot
   research
