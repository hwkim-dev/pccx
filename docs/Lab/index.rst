pccx-lab Handbook
=================

**pccx-lab** is the desktop profiler + verification IDE for the pccx v002
NPU. It ingests ``.pccx`` binary traces emitted by the xsim testbench
suite on the companion ``pccx-FPGA-NPU-LLM-kv260`` RTL repo and surfaces
the timeline, roofline, bottleneck windows, waveform, Vivado synth
reports, and AI-driven UVM strategies in a single Tauri v2 window.

This section documents the tool's internal surface — the Phase 1
plugin-registry primitive every crate hangs trait objects off, the
current ``pccx-ai-copilot`` + ``pccx-lsp`` IntelliSense façade, the
command-line binaries distributed across crates after the workspace
split, and the research-lineage placeholder that will refresh once the
citation registry lands in its new home.

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

      ``pccx_cli``, ``generator``, ``from_xsim_log``,
      ``pccx_golden_diff`` — the four binaries pccx-lab ships today
      and the surfaces still awaiting re-landing.

   .. grid-item-card:: :octicon:`graph;1em;sd-mr-1` Analyzer API
      :link: analyzer_api
      :link-type: doc

      The ``PluginRegistry<P>`` primitive, its ``Plugin`` /
      ``PluginMetadata`` supertraits, and how each crate hangs its own
      plugin trait off it.

   .. grid-item-card:: :octicon:`beaker;1em;sd-mr-1` Copilot API
      :link: copilot
      :link-type: doc

      The ``pccx-ai-copilot`` static helpers (``compress_context``,
      ``generate_uvm_sequence``, ``list_uvm_strategies``) and the
      Phase 2 ``pccx-lsp`` provider traits + ``LspMultiplexer``.

   .. grid-item-card:: :octicon:`milestone;1em;sd-mr-1` Research lineage
      :link: research
      :link-type: doc
      :columns: 12

      Placeholder while the citation registry is rebuilt — the
      pre-Phase-1 ``pccx_core::research::CITATIONS`` module was
      removed in the module exodus and has not yet re-landed.

.. toctree::
   :hidden:
   :maxdepth: 1

   architecture
   cli
   analyzer_api
   copilot
   research
