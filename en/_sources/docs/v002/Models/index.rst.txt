=======================
Target Models
=======================

This section documents how concrete Transformer models are **mapped
onto pccx v002**: the model-level structural choices that matter for
the accelerator, the non-standard numerical tricks we have to honor,
and how the resulting operator graph breaks down into the five pccx
instructions (``GEMV``, ``GEMM``, ``MEMCPY``, ``MEMSET``, ``CVO``).

The primary reference model is **Google Gemma 3N E4B** — the model that
drove the sizing of GEMV cores, the KV cache budget, and the SFU
function list.

.. toctree::
   :maxdepth: 2
   :caption: Gemma 3N E4B

   gemma3n_overview
   gemma3n_pipeline
   gemma3n_attention_rope
   gemma3n_ple_laurel
   gemma3n_ffn_sparsity
   gemma3n_execution

.. note::

   The host-side application that drives this pipeline lives in the
   FPGA repo as a submodule, ``sw/gemma3NE4B/`` →
   `hkimw/llm-lite <https://github.com/hkimw/llm-lite>`_. It serves
   both as the golden CPU reference for verification and as the
   stimulus generator for the xsim testbench suite.
