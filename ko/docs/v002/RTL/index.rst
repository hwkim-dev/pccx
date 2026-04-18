==============================
RTL 소스 레퍼런스 (v002)
==============================

이 섹션은 pccx v002 RTL 레포지토리의 핵심 SystemVerilog 모듈을
직접 임베드합니다: `hwkim-dev/pccx-FPGA-NPU-LLM-kv260
<https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260>`_.

RTL은 CI 빌드 시 :file:`codes/v002/` 에 자동 clone됩니다. 로컬 개발에서는
아래 명령으로 직접 clone하세요:

.. code-block:: bash

   git clone https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260 codes/v002

.. toctree::
   :maxdepth: 1

   isa_pkg
   npu_top
   compute_cores
   controller
