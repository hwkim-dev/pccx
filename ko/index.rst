================================
pccx 문서
================================

**pccx** (Parallel Compute Core eXecutor) 문서에 오신 것을 환영합니다.
pccx는 엣지 디바이스에서 Transformer 기반 LLM을 가속하기 위한
확장 가능한 NPU 아키텍처입니다. 사이드바에서 섹션을 선택하세요.

에코시스템
----------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4
   :class-container: pccx-ecosystem-grid

   .. grid-item-card:: :octicon:`cpu;1.5em;sd-mr-2` RTL 구현체
      :columns: 12 12 8 8
      :class-card: pccx-hero-card
      :link: https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260
      :link-type: url
      :link-alt: pccx-FPGA-NPU-LLM-kv260 저장소를 GitHub 에서 열기

      **github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260**

      활성 **v002** SystemVerilog 원본 — ISA 패키지, 컨트롤러,
      컴퓨트 코어 (GEMM / GEMV / CVO), 메모리 계층. 타겟 디바이스는
      Xilinx Kria **KV260** (Zynq UltraScale+ ZU5EV).

      이 사이트의 모든 v002 RTL 레퍼런스 페이지는 해당 ``.sv`` 파일로
      직접 연결됩니다.

   .. grid-item::
      :columns: 12 12 4 4

      .. grid:: 1
         :gutter: 3

         .. grid-item-card:: :octicon:`book;1em;sd-mr-1` 문서 소스
            :link: https://github.com/hwkim-dev/pccx
            :link-type: url
            :link-alt: pccx 문서 저장소를 GitHub 에서 열기

            **github.com/hwkim-dev/pccx** — 이 사이트를 빌드하는 Sphinx 프로젝트.

         .. grid-item-card:: :octicon:`telescope;1em;sd-mr-1` pccx-lab (검증 / 프로파일)
            :link: https://hwkim-dev.github.io/pccx/ko/lab/
            :link-type: url
            :link-alt: pccx-lab 검증·프로파일링 허브 열기

            **pccx-lab** — Tauri 2 IDE. ``.pccx`` 트레이스 로딩,
            ``run_verification`` 러너, Roofline / Bottleneck 카드,
            Vivado synth 리포트 뷰.
            `검증 워크플로우 가이드 <https://hwkim-dev.github.io/pccx/ko/lab/verification-workflow.html>`_

         .. grid-item-card:: :octicon:`person;1em;sd-mr-1` 저자 포트폴리오
            :link: https://hwkim-dev.github.io/hwkim-dev/
            :link-type: url
            :link-alt: hwkim-dev 포트폴리오 사이트 열기

            **hwkim-dev.github.io/hwkim-dev** — 블로그, 다른 프로젝트, 소개.

도구 & 랩
---------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4
   :class-container: pccx-toolchain-grid

   .. grid-item-card:: :octicon:`beaker;1.2em;sd-mr-1` pccx-lab
      :link: https://hwkim-dev.github.io/pccx/ko/lab/
      :link-type: url
      :link-alt: pccx-lab 시뮬레이터 & 프로파일러 열기
      :class-card: pccx-lab-card

      pccx NPU 전용 성능 시뮬레이터 + AI 통합 프로파일러.
      RTL 이전 병목 탐지, UVM co-simulation, LLM 기반 테스트벤치 생성을
      한 워크플로우로 통합.

      :bdg-warning:`Work in Progress`

      소스: github.com/hwkim-dev/pccx-lab

   .. grid-item-card:: :octicon:`project-roadmap;1.2em;sd-mr-1` 설계 근거
      :link: https://hwkim-dev.github.io/pccx/ko/lab/design/rationale.html
      :link-type: url
      :link-alt: pccx-lab 설계 근거 읽기

      왜 pccx-lab은 다섯 개가 아닌 한 레포인가. 모듈 경계 규칙
      (``core/``, ``ui/``, ``uvm_bridge/``, ``ai_copilot/``).

.. toctree::
   :maxdepth: 2
   :caption: 소개

   docs/index
   docs/roadmap

.. toctree::
   :maxdepth: 1
   :caption: v002 아키텍처

   docs/v002/index

.. toctree::
   :maxdepth: 1
   :caption: 타겟 하드웨어

   docs/Devices/index

.. toctree::
   :maxdepth: 1
   :caption: pccx-lab 핸드북

   docs/Lab/index

.. toctree::
   :maxdepth: 1
   :caption: 아카이브

   docs/archive/index

.. toctree::
   :maxdepth: 1
   :caption: 툴체인 데모

   docs/samples/index

.. toctree::
   :maxdepth: 1
   :caption: 도구

   pccx-lab — 시뮬레이터 & AI 프로파일러 <https://hwkim-dev.github.io/pccx/ko/lab/>
