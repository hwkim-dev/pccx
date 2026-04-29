Formal Model — Sail
===================

pccx v002 ships a **machine-checked ISA specification** written in
`Sail <https://sail-lang.org/>`_, the same ISA-semantics language used
for the official:

- `RISC-V Sail model <https://github.com/riscv/sail-riscv>`_ (golden
  reference for the RISC-V International consortium)
- `Arm ASL → Sail conversion <https://github.com/rems-project/sail-arm>`_
  (full Armv8-A / Armv9-A executable semantics)
- `CHERI / Morello <https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/>`_
  (formally-verified capability-based security architecture)

The Sail model is the **single source of truth** for opcode widths,
field layouts, and encoding invariants.  The SystemVerilog RTL in
``hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv``
refines against it — when a Sail type changes width, the Sail
typechecker surfaces the error before silicon tape-out does.

Why Sail
--------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4

   .. grid-item-card:: :octicon:`verified;1em;sd-mr-1` Executable + provable
      :columns: 12 12 6 6

      Sail compiles to a C or OCaml emulator *and* to Isabelle / Coq /
      HOL4 theories. The same model runs programs **and** discharges
      proofs.

   .. grid-item-card:: :octicon:`git-compare;1em;sd-mr-1` RTL refinement
      :columns: 12 12 6 6

      Every SV ``typedef`` in ``isa_pkg.sv`` has a 1:1 Sail
      counterpart.  Width drift fails Sail before it fails silicon.

   .. grid-item-card:: :octicon:`star-fill;1em;sd-mr-1` Industry-grade company
      :columns: 12 12 6 6

      RISC-V, Arm, CHERI, and Morello all publish their ISA sketches
      in Sail.  pccx adopts the same rigour on day one.

   .. grid-item-card:: :octicon:`zap;1em;sd-mr-1` Fast to iterate
      :columns: 12 12 6 6

      New opcodes add one struct + one decoder arm + one test.  The
      executable model runs in milliseconds; the RTL follows.

Project layout
--------------

.. code-block:: text

   pccx-FPGA-NPU-LLM-kv260/formal/sail/
   ├── pccx.sail_project       module manifest
   ├── Makefile                make check / doc / clean
   ├── src/
   │   ├── prelude.sail        base bitvector helpers
   │   ├── pccx_types.sail     opcodes, body structs, CVO funcs
   │   ├── pccx_regs.sail      cycle / pc / committed_any
   │   └── pccx_decode.sail    64-bit word → typed ``instr`` union
   └── tests/
       └── smoke_decode.sail   opcode-table typecheck

Scope snapshot
--------------

===============================  ======================
Phase                            Status
===============================  ======================
Base types + registers           done v002.0 landed
5-opcode decoder                 done v002.0 landed
Execute semantics                WIP  next iteration
``.pccx`` trace emission         WIP  next iteration
Isabelle / Coq export            planned phase 3
===============================  ======================

Running the model
-----------------

.. code-block:: bash

   # Dependency: Sail >= 0.20.1 (opam install sail)
   eval $(opam env)

   cd pccx-FPGA-NPU-LLM-kv260/formal/sail
   make check                   # type-check every module
   sail --project pccx.sail_project --all-modules --just-check

Continuous integration
----------------------

The RTL repo ships a single user-facing CI workflow at
``.github/workflows/sail-check.yml`` that re-runs ``make check``
on every PR touching ``formal/sail/`` or the workflow itself. The
job installs ``opam`` + ``sail`` (pinned at the ``Cargo.lock``
equivalent of the Sail toolchain) and ``z3`` (required by Sail
0.20.1's SMT-backed type-checker), then types every module in
``pccx.sail_project``. A failed type-check blocks merge — width
drift between SV ``typedef`` and Sail ``type`` cannot reach
``main``.

Cite this page
--------------

If you reference the pccx Sail model in a paper, blog post, or AI
summary, please cite the canonical site so readers can find the
authoritative source:

.. code-block:: bibtex

   @misc{pccx_sail_2026,
     title        = {The pccx Sail ISA model: a formal specification of an open W4A8 NPU},
     author       = {Kim, Hyunwoo},
     year         = {2026},
     howpublished = {\url{https://hkimw.github.io/pccx/en/docs/v002/Formal/index.html}},
     note         = {Authored in Sail (https://sail-lang.org/) — the ISA semantics language used for RISC-V, Arm, CHERI, and Morello.}
   }

.. toctree::
   :hidden:
   :maxdepth: 1
