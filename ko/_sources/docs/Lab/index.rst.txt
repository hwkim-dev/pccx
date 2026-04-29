pccx-lab 핸드북
===============

**pccx-lab** 은 pccx v002 NPU 를 위한 데스크톱 프로파일러 + 검증 IDE 이다.
컴패니언 RTL 레포 ``pccx-FPGA-NPU-LLM-kv260`` 의 xsim 테스트벤치가
방출하는 ``.pccx`` 바이너리 트레이스를 수집하여 타임라인 / roofline /
bottleneck 윈도 / waveform / Vivado 합성 리포트 / 자연어 UVM-시퀀스
전략을 단일 Tauri v2 창에 표면화한다.

이 섹션은 툴의 내부 표면 — 모든 크레이트가 trait object 를 걸기 위해
사용하는 Phase 1 플러그인 레지스트리 프리미티브, 현재
``pccx-ai-copilot`` + ``pccx-lsp`` LSP 파사드, 워크스페이스 분할 이후
크레이트에 분산된 커맨드라인 바이너리, 그리고 인용 레지스트리가 새
홈에 착륙할 때 갱신될 연구 계보 플레이스홀더 — 를 문서화한다.

사용자 지향 데스크톱 앱 자체는 별도
`pccx-lab 사이트 <https://hkimw.github.io/pccx/ko/lab/>`_ 참고.

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4

   .. grid-item-card:: :octicon:`book;1em;sd-mr-1` 아키텍처
      :link: architecture
      :link-type: doc

      레포 구조, 레이어 계약, 데이터 흐름, 확장 훅.

   .. grid-item-card:: :octicon:`terminal;1em;sd-mr-1` CLI 레퍼런스
      :link: cli
      :link-type: doc

      ``pccx_cli``, ``generator``, ``from_xsim_log``,
      ``pccx_golden_diff`` — 오늘 pccx-lab 이 출하하는 네 바이너리와
      재착륙 대기 중인 표면.

   .. grid-item-card:: :octicon:`graph;1em;sd-mr-1` 분석기 API
      :link: analyzer_api
      :link-type: doc

      ``PluginRegistry<P>`` 프리미티브, ``Plugin`` /
      ``PluginMetadata`` 슈퍼트레이트, 각 크레이트가 자체 플러그인
      트레이트를 거기에 거는 방법.

   .. grid-item-card:: :octicon:`beaker;1em;sd-mr-1` Copilot API
      :link: copilot
      :link-type: doc

      ``pccx-ai-copilot`` 정적 헬퍼 (``compress_context``,
      ``generate_uvm_sequence``, ``list_uvm_strategies``) 와
      Phase 2 ``pccx-lsp`` provider 트레이트 + ``LspMultiplexer``.

   .. grid-item-card:: :octicon:`milestone;1em;sd-mr-1` 연구 계보
      :link: research
      :link-type: doc
      :columns: 12

      인용 레지스트리 재구축 동안의 플레이스홀더 — Phase 1 이전의
      ``pccx_core::research::CITATIONS`` 모듈은 모듈 이주에서 제거되어
      아직 재착륙하지 않았다.

.. toctree::
   :hidden:
   :maxdepth: 1

   architecture
   cli
   analyzer_api
   copilot
   research
   panels
   ipc
   verification-workflow
   pccx-format
   uvm-bridge
   self-evolution
   quickstart
   core-modules
