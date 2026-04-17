============================
pccx v002 아키텍처
============================

.. rubric:: Parallel Compute Core eXecutor — 두 번째 세대

**pccx v002** 는 엣지 디바이스에서 Transformer 기반 대규모 언어 모델(LLM)의
**자기회귀 디코딩(Autoregressive Decoding)** 을 가속하기 위해 설계된
이기종(heterogeneous) NPU 아키텍처의 두 번째 세대입니다. v001의 GEMM 편중
설계를 전면 재검토하여, GEMV·CVO·GEMM 이 **동일한 액티베이션 버스를 공유**
하도록 L2 캐시를 아키텍처의 기하학적 중심에 배치하고, **데이터 이동 경로를
최소화** 하도록 재설계되었습니다.

----

.. toctree::
   :maxdepth: 2
   :caption: 개요

   overview

.. toctree::
   :maxdepth: 2
   :caption: 하드웨어 아키텍처

   Architecture/index

.. toctree::
   :maxdepth: 2
   :caption: 명령어 세트 아키텍처 (ISA)

   ISA/index

.. toctree::
   :maxdepth: 2
   :caption: 소프트웨어 스택

   Drivers/index
