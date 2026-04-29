Verification
=============

This section tracks the **unit-level verification harness** that
accompanies the v002 RTL. Functional / formal / silicon checks at the
system level are planned but not yet in place — their scope is listed at
the end of this page.

1. Current test suite
---------------------

All tests run under **Vivado xsim** via the unified runner
:file:`hw/sim/run_verification.sh` in the RTL repo. Each test generates a
``.pccx`` trace that pccx-lab can visualise on the Timeline.

.. list-table::
   :header-rows: 1
   :widths: 35 50 15

   * - Testbench
     - Scope
     - Status
   * - ``tb_GEMM_dsp_packer_sign_recovery``
     - Dual-channel W4A8 pack + post-MAC sign recovery, 1024 cycles
     - PASS
   * - ``tb_mat_result_normalizer``
     - BF16 alignment / exponent delay, 256 cycles
     - PASS
   * - ``tb_GEMM_weight_dispatcher``
     - HP weight stream → INT4 tile dispatch, 128 cycles
     - PASS
   * - ``tb_FROM_mat_result_packer``
     - 32 × 16-bit staggered capture → 128-bit AXIS pack, 4 cycles
     - PASS
   * - ``tb_barrel_shifter_BF16``
     - BF16 mantissa barrel shift, 512 cycles
     - PASS
   * - ``tb_ctrl_npu_decoder``
     - 64-bit VLIW decode → typed structs, 6 cycles
     - PASS

Running the suite
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd pccx-FPGA-NPU-LLM-kv260/hw/sim
   bash run_verification.sh

The script is idempotent — each tb writes to its own
:file:`hw/sim/work/<tb_name>/` directory so concurrent runs do not
stomp on each other. A one-line PASS / FAIL summary prints at the
end along with the path of each emitted ``.pccx`` trace.

.. admonition:: Last verified against
   :class: note

   Commit ``773bd82`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260``
   (2026-04-21). Six testbenches PASS; ``tb_GEMM_fmap_staggered_delay``
   is parked — see ``run_verification.sh`` for the reason.

2. Gaps (tracked as open items)
-------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Area
     - Planned next step
   * - **System-level smoke**
     - ``tb_NPU_top_smoke`` — AXI-Lite decode → MEMSET → MEMCPY →
       GEMV → MEMCPY readback, golden compare against ``llm-lite``
       reference. Blocked on the ACP fanout / writeback wiring (see
       :doc:`../RTL/npu_top`).
   * - **CVO bridge**
     - ``tb_cvo_bridge`` — cvo_uop → READ burst → CVO echo → WRITE
       burst; covers the L2 port-B direct-address path once the
       arbiter lands.
   * - **mem_dispatcher uop table**
     - Regression guard for MEMSET + LOAD + STORE + CVO routing.
   * - **Driver-RTL cross check**
     - Host-only test: encode via ``uca_*`` API, dump 64-bit VLIW,
       cross-check against ``isa_pkg.sv`` bit layout.
   * - **Formal**
     - SymbiYosys / JasperGold properties for the ISA decoder and
       memory arbitration (future).

3. Planned scope (system level)
-------------------------------

Once the unit-level gaps above are closed, the full verification
section will cover:

* **Verification plan** — per-module functional coverage targets and
  sign-off criteria.
* **Testbench architecture** — UVM / cocotb harness layout, reference
  model, and stimulus generators (golden data from the ``llm-lite``
  CPU reference).
* **Coverage dashboard** — functional + code + assertion coverage,
  rolled up by core (GEMM / GEMV / CVO / MEM).
* **Formal results** — SymbiYosys / JasperGold properties for the
  controller, ISA decoder, and memory arbitration.
* **Silicon-level checks** — post-implementation simulation, on-board
  bring-up scripts, and golden-trace comparison against the
  :doc:`host-side C driver </docs/v002/Drivers/api>`.

.. seealso::

   :doc:`/docs/v002/Architecture/index`
       The architectural contracts this section verifies.
   :doc:`/docs/v002/ISA/index`
       ISA-level invariants the testbench checks.
   :doc:`/docs/v002/RTL/index`
       RTL modules under test.
