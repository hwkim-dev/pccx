pccx-lab 핸드북
===============

**pccx-lab** 은 pccx v002 NPU 를 위한 데스크톱 프로파일러 + 검증 IDE 이다.
컴패니언 RTL 레포 ``pccx-FPGA-NPU-LLM-kv260`` 의 xsim 테스트벤치가
방출하는 ``.pccx`` 바이너리 트레이스를 수집하여 타임라인 / roofline /
bottleneck 윈도 / waveform / Vivado 합성 리포트 / AI 구동 UVM 전략을
단일 Tauri v2 창에 표면화한다.

이 섹션은 툴의 내부 표면 — ``TraceAnalyzer`` 레지스트리, ``Copilot``
자동화 파사드, 커맨드라인 바이너리, 그리고 각 분석기를 논문에 연결
시키는 연구 계보 — 를 문서화한다.

사용자 지향 데스크톱 앱 자체는 별도
`pccx-lab 사이트 <https://hwkim-dev.github.io/pccx/ko/lab/>`_ 참고.

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4

   .. grid-item-card:: :octicon:`book;1em;sd-mr-1` 아키텍처
      :link: architecture
      :link-type: doc

      레포 구조, 레이어 계약, 데이터 흐름, 확장 훅.

   .. grid-item-card:: :octicon:`terminal;1em;sd-mr-1` CLI 레퍼런스
      :link: cli
      :link-type: doc

      ``pccx_analyze`` 모드 (pretty / JSON / Markdown / synth /
      ``--compare`` / ``--research-list`` / ``--explain``),
      ``pccx_cli``, ``from_xsim_log``.

   .. grid-item-card:: :octicon:`graph;1em;sd-mr-1` 분석기 API
      :link: analyzer_api
      :link-type: doc

      ``TraceAnalyzer`` 트레이트, 16 개 빌트인 레지스트리,
      단일 파일로 신규 분석을 랜딩하는 법.

   .. grid-item-card:: :octicon:`beaker;1em;sd-mr-1` Copilot API
      :link: copilot
      :link-type: doc

      ``Copilot`` 구조체 — ``investigate()``, ``explain(id)``,
      ``rank_by_severity()``, ``suggest_fix(intent)`` — 와 의도
      키워드 라우팅 테이블.

   .. grid-item-card:: :octicon:`milestone;1em;sd-mr-1` 연구 계보
      :link: research
      :link-type: doc
      :columns: 12

      각 분석기 / UVM 전략이 구현하는 arxiv 논문의 자동 생성 테이블.
      ``pccx_analyze --research-list`` 로 갱신.

.. toctree::
   :hidden:
   :maxdepth: 1

   architecture
   cli
   analyzer_api
   copilot
   research
