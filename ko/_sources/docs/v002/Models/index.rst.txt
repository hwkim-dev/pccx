=======================
타깃 모델
=======================

이 섹션은 실제 Transformer 모델이 **pccx v002 위에서 어떻게 매핑되는지**
를 문서화합니다. 구체적으로 하드웨어 관점에서 중요한 구조적 선택,
반드시 존중해야 하는 비표준 수치 트릭, 그리고 연산자 그래프가 다섯 개의
pccx 명령어 (``GEMV``, ``GEMM``, ``MEMCPY``, ``MEMSET``, ``CVO``)
로 어떻게 분해되는지를 다룹니다.

주 참조 모델은 **Google Gemma 3N E4B** 입니다. 이 모델이 GEMV 코어 수,
KV 캐시 예산, SFU 함수 목록의 크기 기준을 정하는 데 사용되었습니다.

.. toctree::
   :maxdepth: 2
   :caption: Gemma 3N E4B

   gemma3n_overview
   gemma3n_pipeline
   gemma3n_attention_rope
   gemma3n_ple_laurel
   gemma3n_ffn_sparsity
   gemma3n_execution

.. note::

   이 파이프라인을 구동하는 호스트 측 애플리케이션은 FPGA 레포의
   서브모듈 ``sw/gemma3NE4B/`` →
   `hkimw/llm-lite <https://github.com/hkimw/llm-lite>`_ 에 위치한다.
   검증용 골든 CPU 레퍼런스이자 xsim 테스트벤치 스위트의 stimulus
   생성기 역할을 함께 한다.
