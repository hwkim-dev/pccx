RTL 소스 레퍼런스 (v001)
==========================

이 섹션은 아카이브된 v001 NPU 를 구성하는 모든 SystemVerilog 모듈의
권위 있는 브라우저입니다 (8 카테고리 64 파일 + 호스트 측 C API).
``codes/v001/`` 아래 모든 파일은 여기서 언어 인식 ``literalinclude``
로 접근 가능합니다 — 클릭하면 syntax highlighting 된 실제 소스를
바로 읽을 수 있고, 별도 레포로 이동할 필요 없습니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      상위 블록도와 코어별 역할.
   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      이 RTL 이 구현하는 64 bit VLIW 명령어 집합.

v001 은 freeze 상태입니다. 활성 RTL 은
`hwkim-dev/pccx-FPGA-NPU-LLM-kv260 <https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260>`_
에 있으며 :doc:`/docs/v002/RTL/index` 에 문서화됩니다.

.. grid:: 2 2 3 3
   :gutter: 3

   .. grid-item-card:: :octicon:`cpu` 최상위
      :link: top
      :link-type: doc

      ``NPU_top`` 래퍼, BF16 배럴 시프터.

   .. grid-item-card:: :octicon:`package` 패키지 · 상수
      :link: packages
      :link-type: doc

      ISA 패키지, 디바이스 · 타입 · 아키텍처 패키지, 인터페이스 정의.

   .. grid-item-card:: :octicon:`command-palette` 컨트롤러
      :link: controller
      :link-type: doc

      AXI-Lite 프론트엔드, 디코더, 디스패처, 글로벌 스케줄러.

   .. grid-item-card:: :octicon:`grabber` 행렬 코어 (GEMM)
      :link: mat_core
      :link-type: doc

      DSP48E2 MAC 기반 32×32 시스톨릭 어레이.

   .. grid-item-card:: :octicon:`rows` 벡터 코어 (GEMV)
      :link: vec_core
      :link-type: doc

      병렬 μV-core 와 reduction tree.

   .. grid-item-card:: :octicon:`hubot` CVO 코어 (SFU)
      :link: cvo_core
      :link-type: doc

      Softmax · GELU · CORDIC 비선형 엔진.

   .. grid-item-card:: :octicon:`database` 메모리 제어
      :link: mem_control
      :link-type: doc

      L2 URAM 캐시, 디스패처, HP 버퍼, CVO 브리지.

   .. grid-item-card:: :octicon:`filter` 전처리
      :link: preprocess
      :link-type: doc

      피처맵 캐시 + BF16 → 고정소수점 파이프라인.

   .. grid-item-card:: :octicon:`tools` 라이브러리
      :link: library
      :link-type: doc

      BF16 수학, 범용 알고리즘, FIFO 큐 기본 블록.

   .. grid-item-card:: :octicon:`code` 호스트 API (C)
      :link: host_api
      :link-type: doc

      ``sw/driver/`` 의 ``pccx_v1`` HAL + 하이레벨 C 인터페이스.

.. toctree::
   :hidden:
   :maxdepth: 1

   top
   packages
   controller
   mat_core
   vec_core
   cvo_core
   mem_control
   preprocess
   library
   host_api
