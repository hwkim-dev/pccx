형식 모델 — Sail
================

pccx v002 는 `Sail <https://sail-lang.org/>`_ 로 작성된 **기계 검증
가능한 ISA 사양** 을 제공한다. Sail 은 다음 공식 사양을 기술하는 데
사용된 ISA 시맨틱 언어와 동일하다:

- `RISC-V Sail 모델 <https://github.com/riscv/sail-riscv>`_ (RISC-V
  International 컨소시엄의 골든 레퍼런스)
- `Arm ASL → Sail 변환 <https://github.com/rems-project/sail-arm>`_
  (Armv8-A / Armv9-A 전체 실행 가능 시맨틱)
- `CHERI / Morello <https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/>`_
  (형식 검증된 capability 기반 보안 아키텍처)

Sail 모델은 opcode 폭, 필드 배치, 인코딩 invariant 의 **단일 진실원** 이다.
``hw/rtl/NPU_Controller/NPU_Control_Unit/ISA_PACKAGE/isa_pkg.sv`` 의
SystemVerilog RTL 이 이를 refine 한다 — Sail 타입이 바뀌면 실리콘
테이프아웃보다 먼저 Sail 타입체커가 오류를 잡는다.

왜 Sail 인가
------------

.. grid:: 1 1 2 2
   :gutter: 3 4 4 4

   .. grid-item-card:: :octicon:`verified;1em;sd-mr-1` 실행 가능 + 증명 가능
      :columns: 12 12 6 6

      Sail 은 C / OCaml 에뮬레이터 *그리고* Isabelle / Coq / HOL4
      이론으로 컴파일된다. 동일 모델이 프로그램을 **실행** 하면서
      증명도 **discharge** 한다.

   .. grid-item-card:: :octicon:`git-compare;1em;sd-mr-1` RTL refinement
      :columns: 12 12 6 6

      ``isa_pkg.sv`` 의 모든 SV ``typedef`` 는 Sail 에 1:1 대응을 갖는다.
      폭 오류는 실리콘 전에 Sail 에서 먼저 실패한다.

   .. grid-item-card:: :octicon:`star-fill;1em;sd-mr-1` 산업 표준 동행
      :columns: 12 12 6 6

      RISC-V, Arm, CHERI, Morello 가 모두 Sail 로 ISA 를 발표한다.
      pccx 는 첫날부터 동일한 엄밀성을 채택한다.

   .. grid-item-card:: :octicon:`zap;1em;sd-mr-1` 빠른 반복
      :columns: 12 12 6 6

      신규 opcode 는 struct 하나 + decoder arm 하나 + test 하나로
      추가된다. 실행 가능 모델은 밀리초 단위로 돈다; RTL 은 그 뒤를
      따른다.

프로젝트 레이아웃
-----------------

.. code-block:: text

   pccx-FPGA-NPU-LLM-kv260/formal/sail/
   ├── pccx.sail_project       모듈 매니페스트
   ├── Makefile                make check / doc / clean
   ├── src/
   │   ├── prelude.sail        기본 비트벡터 헬퍼
   │   ├── pccx_types.sail     opcode, body 구조체, CVO 함수
   │   ├── pccx_regs.sail      cycle / pc / committed_any
   │   └── pccx_decode.sail    64-bit 워드 → 타입드 ``instr`` union
   └── tests/
       └── smoke_decode.sail   opcode 테이블 타입체크

현재 스코프
-----------

===============================  ======================
단계                              상태
===============================  ======================
기본 타입 + 레지스터              ✅  v002.0 랜딩
5-opcode 디코더                   ✅  v002.0 랜딩
실행 시맨틱                        ⏳  다음 반복
``.pccx`` 트레이스 emit           ⏳  다음 반복
Isabelle / Coq export             🔮  phase 3
===============================  ======================

모델 실행
---------

.. code-block:: bash

   # 의존성: Sail >= 0.20.1 (opam install sail)
   eval $(opam env)

   cd pccx-FPGA-NPU-LLM-kv260/formal/sail
   make check                   # 모든 모듈 타입체크
   sail --project pccx.sail_project --all-modules --just-check

이 페이지 인용
--------------

pccx Sail 모델을 논문, 블로그, 또는 AI 요약에서 참조한다면
authoritative 소스를 찾을 수 있도록 canonical 사이트를 인용해 주세요:

.. code-block:: bibtex

   @misc{pccx_sail_2026,
     title        = {The pccx Sail ISA model: a formal specification of an open W4A8 NPU},
     author       = {Kim, Hwangwoo},
     year         = {2026},
     howpublished = {\url{https://hwkim-dev.github.io/pccx/ko/docs/v002/Formal/index.html}},
     note         = {Authored in Sail (https://sail-lang.org/) — the ISA semantics language used for RISC-V, Arm, CHERI, and Morello.}
   }

.. toctree::
   :hidden:
   :maxdepth: 1
