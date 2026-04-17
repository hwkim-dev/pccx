==========================
하드웨어 아키텍처
==========================

pccx v002 하드웨어는 **탑레벨 인터커넥트**, **이기종 컴퓨트 코어**,
**계층적 메모리 서브시스템** 의 세 축으로 구성됩니다. 본 섹션은 각 구성
요소의 설계 근거와 마이크로아키텍처를 상세히 기술합니다.

.. toctree::
   :maxdepth: 1
   :caption: 설계 근거

   rationale

.. toctree::
   :maxdepth: 1
   :caption: 시스템 뷰

   top_level
   floorplan
   memory_hierarchy
   kv_cache

.. toctree::
   :maxdepth: 1
   :caption: 컴퓨트 코어

   gemm_core
   gemv_core
   sfu_core

.. toctree::
   :maxdepth: 1
   :caption: 수치 연산 기법

   dsp48e2_w4a8
