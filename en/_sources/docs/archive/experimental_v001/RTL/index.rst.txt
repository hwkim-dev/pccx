RTL Source Reference (v001)
============================

This section is the authoritative browser for every SystemVerilog module
that makes up the archived v001 NPU (64 files across 8 categories, plus
the host-side C API). Every file under ``codes/v001/`` is reachable from
here via a language-aware ``literalinclude`` — click through to read
the real source with syntax highlighting; no separate repository visit
required.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      High-level block diagram and core roles.
   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      64-bit VLIW instruction set backing this RTL.

v001 is frozen. Active RTL is in
`hkimw/pccx-FPGA-NPU-LLM-kv260 <https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260>`_
and documented under :doc:`/docs/v002/RTL/index`.

.. grid:: 2 2 3 3
   :gutter: 3

   .. grid-item-card:: :octicon:`cpu` Top level
      :link: top
      :link-type: doc

      ``NPU_top`` wrapper, BF16 barrel shifter.

   .. grid-item-card:: :octicon:`package` Packages & Constants
      :link: packages
      :link-type: doc

      ISA package, device / type / arch packages, interface defs.

   .. grid-item-card:: :octicon:`command-palette` Controller
      :link: controller
      :link-type: doc

      AXI-Lite frontend, decoder, dispatcher, global scheduler.

   .. grid-item-card:: :octicon:`grabber` Matrix Core (GEMM)
      :link: mat_core
      :link-type: doc

      32×32 systolic array with DSP48E2 MACs.

   .. grid-item-card:: :octicon:`rows` Vector Core (GEMV)
      :link: vec_core
      :link-type: doc

      Parallel μV-cores with reduction tree.

   .. grid-item-card:: :octicon:`hubot` CVO Core (SFU)
      :link: cvo_core
      :link-type: doc

      Softmax / GELU / CORDIC non-linear engine.

   .. grid-item-card:: :octicon:`database` Memory Control
      :link: mem_control
      :link-type: doc

      L2 URAM cache, dispatcher, HP buffers, CVO bridge.

   .. grid-item-card:: :octicon:`filter` Preprocess
      :link: preprocess
      :link-type: doc

      Feature-map cache + BF16→fixed-point pipeline.

   .. grid-item-card:: :octicon:`tools` Library
      :link: library
      :link-type: doc

      BF16 math, general algorithms, FIFO queue primitives.

   .. grid-item-card:: :octicon:`code` Host API (C)
      :link: host_api
      :link-type: doc

      ``pccx_v1`` HAL + high-level C interface under ``sw/driver/``.

.. toctree::
   :hidden:
   :maxdepth: 1

   top
   packages
   controller
   mat_core
   vec_core
   cvo_core
   mem_control
   preprocess
   library
   host_api
