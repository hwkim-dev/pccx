============================
pccx v002 Architecture
============================

.. rubric:: Parallel Compute Core eXecutor — Second Generation

**pccx v002** is the second generation of a heterogeneous NPU architecture
designed to accelerate **autoregressive decoding** of Transformer-based
large language models (LLMs) on edge devices. It takes a hard look at the
GEMM-centric v001 design and restructures the data path around a single
shared activation bus: GEMV, CVO, and GEMM now pull activations from the
same L2 cache, which sits at the geometric center of the floorplan. The
result is **shorter, more regular data movement** across every compute
path.

----

.. toctree::
   :maxdepth: 2
   :caption: Overview

   overview

.. toctree::
   :maxdepth: 2
   :caption: Hardware Architecture

   Architecture/index

.. toctree::
   :maxdepth: 2
   :caption: Instruction Set Architecture (ISA)

   ISA/index

.. toctree::
   :maxdepth: 2
   :caption: Software Stack

   Drivers/index

.. toctree::
   :maxdepth: 2
   :caption: Target Models

   Models/index
