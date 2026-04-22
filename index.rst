================================
pccx Documentation
================================

Welcome to the **pccx** (Parallel Compute Core eXecutor) documentation.
pccx is a scalable NPU architecture for accelerating Transformer-based LLMs
on edge devices. Select a section from the sidebar to begin.

Ecosystem
---------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4
   :class-container: pccx-ecosystem-grid

   .. grid-item-card:: :octicon:`cpu;1.5em;sd-mr-2` RTL Implementation
      :columns: 12 12 8 8
      :class-card: pccx-hero-card
      :link: https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260
      :link-type: url
      :link-alt: Open the pccx-FPGA-NPU-LLM-kv260 repository on GitHub

      **github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260**

      The active **v002** SystemVerilog sources — ISA package, controller,
      compute cores (GEMM / GEMV / CVO), memory hierarchy. Target device
      is the Xilinx Kria **KV260** (Zynq UltraScale+ ZU5EV).

      Every v002 RTL reference page on this site links back to the exact
      ``.sv`` file in that repository.

   .. grid-item::
      :columns: 12 12 4 4

      .. grid:: 1
         :gutter: 3

         .. grid-item-card:: :octicon:`book;1em;sd-mr-1` Documentation source
            :link: https://github.com/hwkim-dev/pccx
            :link-type: url
            :link-alt: Open the pccx documentation repository on GitHub

            **github.com/hwkim-dev/pccx** — the Sphinx project powering this site.

         .. grid-item-card:: :octicon:`person;1em;sd-mr-1` Author portfolio
            :link: https://hwkim-dev.github.io/hwkim-dev/
            :link-type: url
            :link-alt: Open the hwkim-dev portfolio site

            **hwkim-dev.github.io/hwkim-dev** — blog, other projects, about.

Tooling & Lab
-------------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4
   :class-container: pccx-toolchain-grid

   .. grid-item-card:: :octicon:`beaker;1.2em;sd-mr-1` pccx-lab
      :link: https://hwkim-dev.github.io/pccx/en/lab/
      :link-type: url
      :link-alt: Open the pccx-lab simulator and profiler
      :class-card: pccx-lab-card

      Performance simulator and AI-integrated profiler, built for the pccx NPU.
      Pre-RTL bottleneck detection, UVM co-simulation, and LLM-driven testbench
      generation in one workflow.

      :bdg-warning:`Work in Progress`

      Source: github.com/hwkim-dev/pccx-lab

   .. grid-item-card:: :octicon:`project-roadmap;1.2em;sd-mr-1` Design rationale
      :link: https://hwkim-dev.github.io/pccx/en/lab/design/rationale.html
      :link-type: url
      :link-alt: Read the pccx-lab design rationale

      Why pccx-lab is one repo, not five. Module boundary rules
      (``core/``, ``ui/``, ``uvm_bridge/``, ``ai_copilot/``).

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   docs/index
   docs/roadmap

.. toctree::
   :maxdepth: 1
   :caption: v002 Architecture

   docs/v002/index

.. toctree::
   :maxdepth: 1
   :caption: Target Hardware

   docs/Devices/index

.. toctree::
   :maxdepth: 1
   :caption: pccx-lab Handbook

   docs/Lab/index

.. toctree::
   :maxdepth: 1
   :caption: Archive

   docs/archive/index

.. toctree::
   :maxdepth: 1
   :caption: Toolchain Demos

   docs/samples/index

.. toctree::
   :maxdepth: 1
   :caption: Tools

   pccx-lab — Simulator & AI Profiler <https://hwkim-dev.github.io/pccx/en/lab/>
