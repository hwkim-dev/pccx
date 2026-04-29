==============================
RTL Source Reference (v002)
==============================

This section embeds key SystemVerilog modules from the pccx v002 RTL
repository: `hkimw/pccx-FPGA-NPU-LLM-kv260
<https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260>`_.

The RTL is cloned into :file:`codes/v002/` at CI build time. Local
development requires a manual clone:

.. code-block:: bash

   git clone https://github.com/hkimw/pccx-FPGA-NPU-LLM-kv260 codes/v002

.. toctree::
   :maxdepth: 1

   isa_pkg
   npu_top
   compute_cores
   controller
   frontend
   memory_l2
   memory_dispatch
   preprocess
   packages
   library
