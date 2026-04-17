====================
Overview
====================

|Status| |Architecture| |Target| |Precision|

.. |Status| image:: https://img.shields.io/badge/Status-Active_Development-yellow
.. |Architecture| image:: https://img.shields.io/badge/Architecture-Heterogeneous_NPU-purple
.. |Target| image:: https://img.shields.io/badge/Target-Kria_KV260-orange
.. |Precision| image:: https://img.shields.io/badge/Precision-W4A8-green

1. Project Goal
================

**pccx (Parallel Compute Core eXecutor) v002** is a general-purpose NPU
architecture that accelerates quantized Transformer-based LLMs in a
bare-metal environment, with the Xilinx Kria KV260 SoM as its primary
target.

Core Design Principles
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Principle
     - Description
   * - **Generality**
     - The architecture is not tied to a single model (e.g., Gemma 3N E4B).
       A **device-agnostic instruction set (ISA)** and a **decoupled
       dataflow** let the same silicon host a wide range of Transformer
       variants.
   * - **Scalability**
     - Systolic-array dimensions, GEMV/SFU core counts, and local cache
       sizes are all exposed as **generate parameters** so the design can
       be resynthesized to fit the resource budget of a different target.
   * - **Memory-centric Layout**
     - The L2 cache is physically centered in the floorplan and serves as
       the **shared activation source** for GEMM, GEMV, and CVO. This
       removes the inter-layer shuffle cost that dogged v001.

2. Target Workload
==================

The decoding stage of the target models is a **GEMV-dominated** workload —
batch size 1, sequence length 1. Prefill, in contrast, is GEMM-dominated.
pccx v002 runs both efficiently on a single architecture by physically
separating the **matrix core (GEMM)** from the **vector core (GEMV)**, and
by placing a dedicated **Special Function Unit (SFU)** for **Complex
Vector Operations (CVO)** so non-linear activations never stall the main
pipeline.

Performance Targets
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Metric
     - Target
     - Rationale
   * - Decoding throughput
     - **20 tok/s (Gemma 3N E4B)**
     - Bandwidth-matched between L2 cache and the GEMV cores
   * - Core clock frequency
     - **400 MHz**
     - DSP48E2 timing ceiling
   * - Quantization
     - **W4A8 (INT4 × INT8)**
     - Best fit for integer math on KV260's DSP48E2
   * - SFU precision
     - **BF16 / FP32 promotion**
     - Numerical stability for Softmax, RMSNorm, and GELU

3. Key Differences from v001
============================

The transition rationale and the full breakdown of the 3.125× throughput
improvement are covered in :doc:`Architecture/rationale`. In short:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Aspect
     - v001 (Archived)
     - v002
   * - Design bias
     - GEMM-centric (prefill-optimized)
     - Three-core layout: GEMM · GEMV · SFU
   * - L2 cache placement
     - Peripheral; overlaps with Global Cache
     - **Central placement**, Global Cache absorbed, symmetric interconnect
   * - Quantization
     - W4A16 (BF16 activations)
     - **W4A8 (INT8 activations)**
   * - Core composition
     - Matrix + Vector + CVO (blurred boundaries)
     - Matrix + **GEMV 32×1 × 4** + **SFU 32×1 × 4**
   * - HP port layout
     - One SA mapped to one port (250 MHz ceiling)
     - HP2 / HP3 distributed, consumed internally at 400 MHz
   * - DSP utilization
     - 1 DSP = 1 MAC
     - **1 DSP = 2 MAC (dual-channel bit packing)**
   * - Theoretical speedup
     - —
     - **× 3.125** (1.6 × 2)

.. seealso::

   - Speedup analysis and design trade-offs: :doc:`Architecture/rationale`
   - KV cache bandwidth strategy: :doc:`Architecture/kv_cache`
   - v001 archive: :doc:`../archive/experimental_v001/index`

4. Ecosystem Layers
===================

pccx is split into three strictly separated layers so that it stays
portable across devices.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Layer
     - Location
     - Responsibility
   * - **Architecture**
     - ``codes/v002/hw/rtl/``
     - Core RTL logic and generate parameters. Defines ISA, pipeline, and
       scheduling. Vendor-independent.
   * - **Device**
     - ``codes/v002/hw/device/``
     - Maps the architecture onto a specific target (e.g., KV260). Fixes
       systolic-array size, AXI interfaces, URAM layout.
   * - **Driver**
     - ``codes/v002/sw/``
     - C/C++ hardware abstraction layer (HAL) and high-level API. Handles
       instruction dispatch, memory mapping, and host-device sync.

5. Documentation Map
=====================

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Section
     - Contents
   * - :doc:`Architecture/index`
     - Top-level block diagram, physical floorplan, GEMM/GEMV/SFU
       microarchitecture, memory hierarchy, and the DSP48E2 W4A8 bit-packing
       technique.
   * - :doc:`ISA/index`
     - 64-bit instruction format, encodings for the five opcodes
       (GEMV / GEMM / MEMCPY / MEMSET / CVO), and per-instruction dataflow.
   * - :doc:`Drivers/index`
     - C API overview and the instruction dispatch flow.
