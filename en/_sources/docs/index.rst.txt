pccx: Parallel Compute Core eXecutor
=====================================

|License| |Architecture| |Target| |Precision|

   **Notice: Active Development in Progress.** pccx is a scalable,
   modular Neural Processing Unit (NPU) architecture designed to
   accelerate Transformer-based large language models (LLMs) on
   resource-constrained edge devices.

--------------

1. Architecture Overview
------------------------

pccx is a device-agnostic hardware-software co-design framework. It
attacks the memory-bandwidth and compute bottlenecks of edge hardware
by scaling the core architecture to match the physical resource budget
of each target device.

1.1 Ecosystem Structure
~~~~~~~~~~~~~~~~~~~~~~~

The project is strictly separated into three layers for maximum
portability and scalability.

-  ``/architecture`` **(Logic Layer)** — core RTL and generate
   parameters.

   -  Defines the logical pipeline, instruction scheduling, and the
      **custom 64-bit ISA**.
   -  Independent of any specific hardware vendor or interface protocol.

-  ``/device`` **(Implementation Layer)** — maps the pccx architecture
   onto a specific hardware target.

   -  Adjusts core count, systolic-array dimensions, and memory port
      widths to the available resource budget (DSP count, local memory
      size, etc.).

-  ``/driver`` **(Software Layer)** — a C/C++ hardware abstraction layer
   (HAL) and high-level API.

   -  Handles instruction dispatch and memory mapping, bridging
      high-level AI models with the pccx hardware.

--------------

2. Key Technical Features
-------------------------

2.1 Decoupled Dataflow & Custom ISA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pccx uses a **custom 64-bit ISA** tuned for matrix and vector
operations. A **decoupled-dataflow** pipeline separates instruction
decode from execution, eliminating dispatch-side stalls and maximizing
throughput.

2.2 W4A8 Dynamic Precision Promotion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pccx balances efficiency with accuracy:

-  **Compute**: a parallel 2D systolic array executes dense
   **INT4 (weight) × INT8 (activation)** operations.
-  **Promotion**: during non-linear operations (Softmax, RMSNorm, GELU),
   the CVO core automatically promotes precision to **BF16 / FP32** so
   numerical integrity is preserved.

2.3 Tiered Memory Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **Matrix core**: dedicated GEMM, with a scalable array size.
-  **Vector core**: GEMV and element-wise operations.
-  **Shared interconnect**: a flexible bus that lets cores and local
   caches access each other concurrently without arbitration overhead.

--------------

3. Documentation
----------------

Detailed technical specifications live under :doc:`v002/index`:

1. :doc:`v002/ISA/index` — 64-bit custom instruction set.
2. :doc:`v002/Architecture/index` — hardware architecture and
   floorplan.
3. :doc:`v002/Drivers/index` — driver and SDK documentation.

The v001 architecture is archived at
:doc:`archive/experimental_v001/index`.

--------------

4. License
----------

Licensed under the **Apache License 2.0**. This provides freedom of use
and modification while protecting the architecture from patent-related
risks, keeping the ecosystem safe for open-source hardware development.

--------------

5. Ecosystem
------------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4
   :class-container: pccx-ecosystem-grid

   .. grid-item-card:: :octicon:`cpu;1.5em;sd-mr-2` RTL Implementation
      :columns: 12 12 8 8
      :class-card: pccx-hero-card
      :link: https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260
      :link-type: url
      :link-alt: Open the pccx-FPGA-NPU-LLM-kv260 repository on GitHub

      **github.com/hkimw/pccx-FPGA-NPU-LLM-kv260**

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
            :link: https://github.com/hkimw/pccx
            :link-type: url
            :link-alt: Open the pccx documentation repository on GitHub

            **github.com/hkimw/pccx** — the Sphinx project powering this site.

         .. grid-item-card:: :octicon:`telescope;1em;sd-mr-1` pccx-lab (verify / profile)
            :link: https://hkimw.github.io/pccx/en/lab/
            :link-type: url
            :link-alt: Open the pccx-lab verification + profiling hub

            **pccx-lab** — Tauri 2 IDE. ``.pccx`` trace loader,
            ``run_verification`` runner, Roofline / Bottleneck cards,
            Vivado synth report view. See the
            `verification workflow guide <https://hkimw.github.io/pccx/en/lab/verification-workflow.html>`_.

         .. grid-item-card:: :octicon:`person;1em;sd-mr-1` Author portfolio
            :link: https://hkimw.github.io/hkimw/
            :link-type: url
            :link-alt: Open the hkimw portfolio site

            **hkimw.github.io/hkimw** — blog, other projects, about.

.. |License| image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
.. |Architecture| image:: https://img.shields.io/badge/Architecture-Scalable_NPU-purple
.. |Target| image:: https://img.shields.io/badge/Target-Edge_AI-orange
.. |Precision| image:: https://img.shields.io/badge/Precision-W4A8_Promotion-green
