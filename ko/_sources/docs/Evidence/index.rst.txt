Evidence
========

.. rubric:: "설계" → "검증된 시스템"

이 페이지는 회의적인 리뷰어가 던지는 단 하나의 질문에 답한다:
**"이게 실제로 돌아가는가?"**  각 행은 재현 가능한 산출물 (캡처된
``.pccx`` 트레이스, Vivado utilisation 리포트, 보드 로그 발췌) 로
링크되어 있어 숫자를 독립적으로 검증할 수 있다.

측정치가 아직 없는 행은 **pending** 으로 명시하며, 차단 요소를
항상 명시한다 — 추정치는 기록하지 않는다.

측정 완료 (재현 가능)
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 30

   * - 메트릭
     - 값
     - 소스
     - 재현기
   * - Sail 모델 타입체크
     - clean
     - ``formal/sail/`` (64-bit / 4-bit opcode)
     - ``make check`` (< 5 초)
   * - pccx-core 테스트 스위트
     - 7/7 ISA + 16 분석기 테스트
     - ``cargo test -p pccx-core``
     - pccx-lab 루트에서 ``cargo test``
   * - ``.pccx`` 바이너리 포맷 디코드 라운드트립
     - 비트-정확
     - ``pccx_format.rs``
     - ``pccx_analyze sample.pccx``
   * - Sphinx zero-warning 빌드
     - EN + KO
     - ``_ext/*.py`` + ``docs/**``
     - ``make strict``
   * - Golden-diff 회귀 게이트 (self-calibrated)
     - 8 / 8 스텝 + 128 / 128 스텝 ±15 % 이내
     - pccx-lab 의 ``samples/*.ref.jsonl``
     - ``pccx_golden_diff --check samples/gemma3n_16tok_smoke.ref.jsonl samples/gemma3n_16tok_smoke.pccx``

보류 중 (보드 / synth)
----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - 메트릭
     - 상태
     - 차단 요소
   * - End-to-end Gemma-3N E4B 디코드 tok/s
     - 보드 실행 대기
     - §4.1 RTL dispatcher + Global_Scheduler 와이어링
       (:doc:`../v002/Architecture/index`)
   * - KV260 자원 사용량 (LUT / DSP / URAM / BRAM)
     - Vivado impl 대기
     - ``pccx_analyze --run-synth <rtl_repo>`` 랜딩
       (:doc:`../Lab/cli`)
   * - Timing closure @ 400 MHz core / 250 MHz AXI
     - Vivado impl 대기
     - 위와 동일
   * - Layer-by-layer 골든 모델 diff (PyTorch 레퍼런스 대비)
     - ``tools/pytorch_reference.py`` 랜딩 대기
     - 스캐폴드 (``pccx_golden_diff`` CLI + ``.ref.jsonl`` 스키마)
       이미 랜딩 — 위의 measured 행 참고. PyTorch 쪽이
       self-calibrated 레퍼런스를 시맨틱 기반 기대치로 교체할 예정.
   * - 지속 부하 하 P99 디코드 지연
     - 보드 캡처 대기
     - 실제 DDR 트래픽으로 512-토큰 실행 필요.
   * - W4A8KV4 디코드 중 7 W TDP 헤드룸
     - Vivado impl + 보드 pmbus 대기
     - 자원 사용량과 동일 차단.

베이스라인 (향후 비교용)
------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - 베이스라인
     - 타겟
     - 방법
   * - CPU (Ryzen 4500U, llama.cpp Q4_K_M)
     - Gemma-3N E4B tok/s
     - ``llama.cpp`` + 고정 스레드 (4 × 2 GHz Zen 2).
   * - GPU (RTX 4060, HF Transformers bf16)
     - Gemma-3N E4B tok/s
     - PyTorch 2.4, generate() + KV cache, batch = 1.
   * - On-device (pccx v002 @ KV260)
     - Gemma-3N E4B tok/s
     - ``pccx_analyze --board kv260.local`` (큐 중).

이 페이지의 갱신 방법
---------------------

1. ``pccx-FPGA-NPU-LLM-kv260`` 가 새 ``.pccx`` 또는 Vivado 리포트를
   캡처.
2. ``pccx-lab`` 이 ``pccx_analyze --json`` 으로 필드 export.
3. 본 레포 커밋이 테이블에 숫자를 랜딩 — 소스 링크 + 영구
   ``samples/`` 산출물 포함.
4. ``make strict`` 통과, CI 가 페이지 재배포.

추정치 없음. 모든 행은 재현 가능한 산출물로 연결되거나 명명된 차단
요소와 함께 **pending** 으로 표시된다.

.. toctree::
   :hidden:
   :maxdepth: 1

이 페이지 인용
--------------

.. code-block:: bibtex

   @misc{pccx_evidence_2026,
     title        = {pccx Evidence: reproducible measurement log for an open W4A8 NPU},
     author       = {Kim, Hyunwoo},
     year         = {2026},
     howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Evidence/index.html}},
     note         = {Tracks the "설계 → 검증된 시스템" closure plan.  Part of pccx: \url{https://hkimw.github.io/pccx/}}
   }
