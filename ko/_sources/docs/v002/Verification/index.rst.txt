검증
=====

본 섹션은 v002 RTL 에 딸린 **유닛 레벨 검증 harness** 의 현 상태를
추적합니다. 시스템 레벨 기능 · formal · 실리콘 검증은 계획 단계이며 아직
자리 잡지 않았습니다 — 범위는 페이지 끝에 따로 정리되어 있습니다.

1. 현재 테스트 스위트
-----------------------

모든 테스트는 RTL 리포의
:file:`hw/sim/run_verification.sh` 통합 러너로 **Vivado xsim** 위에서
실행됩니다. 각 테스트는 pccx-lab Timeline 에서 시각화할 수 있는
``.pccx`` 트레이스를 생성합니다.

.. list-table::
   :header-rows: 1
   :widths: 35 50 15

   * - 테스트벤치
     - 범위
     - 상태
   * - ``tb_GEMM_dsp_packer_sign_recovery``
     - 듀얼 채널 W4A8 pack + post-MAC 부호 복원, 1024 사이클
     - PASS
   * - ``tb_mat_result_normalizer``
     - BF16 alignment / exponent delay, 256 사이클
     - PASS
   * - ``tb_GEMM_weight_dispatcher``
     - HP weight stream → INT4 tile dispatch, 128 사이클
     - PASS
   * - ``tb_FROM_mat_result_packer``
     - 32 × 16-bit staggered capture → 128-bit AXIS pack, 4 사이클
     - PASS
   * - ``tb_barrel_shifter_BF16``
     - BF16 mantissa barrel shift, 512 사이클
     - PASS
   * - ``tb_ctrl_npu_decoder``
     - 64-bit VLIW 디코드 → 타입 구조체, 6 사이클
     - PASS

스위트 실행
~~~~~~~~~~~

.. code-block:: bash

   cd pccx-FPGA-NPU-LLM-kv260/hw/sim
   bash run_verification.sh

스크립트는 idempotent 합니다 — 각 tb 는
:file:`hw/sim/work/<tb_name>/` 하위에 독립된 작업 디렉토리를 써서 반복
실행·동시 실행이 서로 덮어쓰지 않습니다. 끝에 한 줄 PASS / FAIL 요약과
생성된 각 ``.pccx`` 트레이스 경로가 출력됩니다.

.. admonition:: 마지막 검증 대상
   :class: note

   커밋 ``773bd82`` @ ``hkimw/pccx-FPGA-NPU-LLM-kv260``
   (2026-04-21). 6개 테스트벤치 PASS; ``tb_GEMM_fmap_staggered_delay`` 는
   park 상태 — 사유는 ``run_verification.sh`` 참고.

2. 갭 (공개 항목으로 관리)
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 영역
     - 다음 단계 계획
   * - **시스템 레벨 smoke**
     - ``tb_NPU_top_smoke`` — AXI-Lite 디코드 → MEMSET → MEMCPY →
       GEMV → MEMCPY readback, ``llm-lite`` 참조와 골든 비교.
       ACP fanout / writeback 배선 (:doc:`../RTL/npu_top` 참고) 해결
       전까지 블록.
   * - **CVO 브리지**
     - ``tb_cvo_bridge`` — cvo_uop → READ 버스트 → CVO echo → WRITE
       버스트; L2 포트-B 직결 주소 경로 테스트 (arbiter 랜딩 후).
   * - **mem_dispatcher uop 표**
     - MEMSET + LOAD + STORE + CVO 라우팅 regression guard.
   * - **드라이버-RTL 교차 검증**
     - 호스트 전용 테스트: ``uca_*`` API 로 인코딩 → 64-bit VLIW
       덤프 → ``isa_pkg.sv`` 비트 레이아웃과 교차 확인.
   * - **Formal**
     - ISA 디코더와 메모리 중재기의 SymbiYosys / JasperGold property
       (향후).

3. 계획된 범위 (시스템 레벨)
-----------------------------

위 유닛 레벨 갭이 채워지면 전체 섹션은 다음을 다룹니다:

* **검증 계획** — 모듈별 기능 커버리지 목표와 sign-off 기준.
* **테스트벤치 아키텍처** — UVM / cocotb harness 레이아웃, 참조 모델,
  자극 생성기 (``llm-lite`` CPU 참조 구현에서 가져온 골든 데이터).
* **커버리지 대시보드** — 기능 · 코드 · 단언 커버리지를 코어별
  (GEMM / GEMV / CVO / MEM) 롤업.
* **Formal 결과** — 컨트롤러, ISA 디코더, 메모리 중재기에 대한
  SymbiYosys / JasperGold property.
* **실리콘 레벨 검증** — post-implementation 시뮬레이션, 보드 bring-up
  스크립트, :doc:`호스트 C 드라이버 </docs/v002/Drivers/api>` 대비
  골든 트레이스 비교.

.. seealso::

   :doc:`/docs/v002/Architecture/index`
       이 섹션이 검증하는 아키텍처 계약.
   :doc:`/docs/v002/ISA/index`
       테스트벤치가 확인하는 ISA 레벨 불변식.
   :doc:`/docs/v002/RTL/index`
       검증 대상 RTL 모듈.
