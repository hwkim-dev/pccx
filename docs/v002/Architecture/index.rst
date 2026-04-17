==========================
Hardware Architecture
==========================

The pccx v002 hardware is organized along three axes: a **top-level
interconnect**, a set of **heterogeneous compute cores**, and a
**hierarchical memory subsystem**. This section walks through the design
rationale and the microarchitecture of each piece.

.. toctree::
   :maxdepth: 1
   :caption: Design Rationale

   rationale

.. toctree::
   :maxdepth: 1
   :caption: System View

   top_level
   floorplan
   memory_hierarchy
   kv_cache

.. toctree::
   :maxdepth: 1
   :caption: Compute Cores

   gemm_core
   gemv_core
   sfu_core

.. toctree::
   :maxdepth: 1
   :caption: Numerical Techniques

   dsp48e2_w4a8
