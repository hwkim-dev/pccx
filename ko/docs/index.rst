pccx: 병렬 컴퓨트 코어 익스큐터
=================================

|License| |Architecture| |Target| |Precision|

   **공지: 현재 활발히 개발 중이다** > pccx는 리소스 제약이 있는 엣지 환경에서
   트랜스포머 기반 대규모 언어 모델(LLM) 가속을 위해 설계된
   확장 가능하고 모듈화된 신경망 처리 장치(NPU) 아키텍처다.

--------------

1. 아키텍처 개요
----------------

pccx는 디바이스 독립성을 갖춘 하드웨어-소프트웨어 공동 설계 프레임워크다.
타겟 디바이스의 제한된 물리적 리소스에 맞춰 코어 아키텍처를 스케일링함으로써
엣지 환경 특유의 메모리 대역폭 및 연산 병목 현상 해소에 주력한다.

1.1 에코시스템 구조
~~~~~~~~~~~~~~~~~~~

이 프로젝트는 극대화된 이식성과 확장성을 확보하기 위해 세 개의 레이어로 엄격히 분리된다:

-  ``/architecture`` **(로직 레이어)** — 핵심 RTL(Register Transfer Level) 로직과
   생성 파라미터를 포함한다.

   -  논리 데이터 파이프라인, 명령어 스케줄러 및 **커스텀 64비트 ISA**\ 를 정의한다.
   -  특정 하드웨어 벤더나 인터페이스 프로토콜에 종속되지 않는다.

-  ``/device`` **(구현 레이어)** — 특정 하드웨어 환경에 pccx 아키텍처를 매핑한다.

   -  가용 리소스 예산(예: DSP 슬라이스 수, 로컬 메모리 용량)에 따라
      연산 코어의 수, 시스톨릭 어레이 규격, 메모리 포트 대역폭을 동적으로 조율한다.

-  ``/driver`` **(소프트웨어 레이어)** — C/C++ 기반의 하드웨어 추상화 계층(HAL)과
   고수준 API를 제공한다.

   -  명령어 디스패치 및 메모리 매핑을 전담하며, 고차원 AI 모델 프레임워크와 pccx 하드웨어를
      연결하는 브릿지 역할을 수행한다.

--------------

2. 주요 기술 기능
-----------------

2.1 분리형 데이터플로우 & 커스텀 ISA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

이 아키텍처는 행렬 및 벡터 연산에 최적화된 **커스텀 64비트 ISA**\ 를 채택했다.
명령어 디코딩과 실행 단계를 분리하는 **분리형(Decoupled) 데이터플로우** 구조를 도입하여
파이프라인 스톨(stall)을 근본적으로 제거하고 시스템 처리량을 극대화한다.

2.2 W4A8 동적 정밀도 상향 (Dynamic Precision Promotion)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

연산 효율성과 모델 정확도를 동시에 충족하기 위해 다음 기법을 적용한다:

-  **연산:** 병렬 2D 시스톨릭 어레이가 고밀도 INT4(가중치) × INT8(활성값) 행렬 곱을 수행한다.
-  **상향:** 비선형 함수(Softmax, RMSNorm, GeLU 등) 연산 시 수치적 정밀도를 잃지 않도록
   복합 벡터 연산(CVO) 코어 내부에서 자동으로 데이터 포맷을 BF16 또는 FP32로 승격시켜 처리한다.

2.3 계층적 메모리 아키텍처
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **매트릭스 코어:** 확장성을 지닌 어레이 크기를 바탕으로 GEMM 연산만을 전담한다.
-  **벡터 코어:** GEMV 및 Element-wise 연산을 효율적으로 분담하여 처리한다.
-  **공용 인터커넥트:** 중재 오버헤드 없이 각 코어와 로컬 캐시 간 동시 엑세스를 지원하는
   유연한 데이터 버스 구조를 갖췄다.

--------------

3. 문서
-------

상세한 기술 스펙은 :doc:`v002/index` 문서를 참조한다:

1. :doc:`v002/ISA/index` — 64비트 커스텀 명령어 집합(ISA) 명세.
2. :doc:`v002/Architecture/index` — 하드웨어 아키텍처 및 물리적 플로어플랜 설계.
3. :doc:`v002/Drivers/index` — pccx 드라이버 및 SDK 가이드런스.

v001 레퍼런스 아키텍처는 :doc:`archive/experimental_v001/index` 에 보존되어 있다.

--------------

4. 라이선스
-----------

본 프로젝트는 **Apache License 2.0** 라이선스를 적용받는다.
개방형 하드웨어 파편화 방지와 생태계 보호를 지향하는 동시에, 특허 소송의 위험으로부터
아키텍처를 보호하여 학계 및 산업계 연구자들이 자유롭게 목적에 맞게 수정하고 사용할 수 있도록 한다.

--------------

5. 에코시스템
-------------

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

      활성 상태의 **v002** SystemVerilog 컴포넌트 — ISA 패키지, 제어 유닛,
      연산 파이프라인 (GEMM / GEMV / CVO), 및 메모리 스토리지 계층 구성을 관장한다.
      운영 타겟 하드웨어는 Xilinx Kria **KV260** (Zynq UltraScale+ ZU5EV)이다.

      본 문서 사이트의 모든 v002 RTL 참조 페이지는
      GitHub 프로젝트의 최신 ``.sv`` 코드로 직접 라우팅된다.

   .. grid-item::
      :columns: 12 12 4 4

      .. grid:: 1
         :gutter: 3

         .. grid-item-card:: :octicon:`book;1em;sd-mr-1` 문서 소스
            :link: https://github.com/hwkim-dev/pccx
            :link-type: url
            :link-alt: pccx 문서 저장소를 GitHub 에서 열기

            **github.com/hwkim-dev/pccx** — 본 문서 사이트를 빌드하기 위한 Sphinx 프로젝트.

         .. grid-item-card:: :octicon:`person;1em;sd-mr-1` 저자 포트폴리오
            :link: https://hwkim-dev.github.io/hwkim-dev/
            :link-type: url
            :link-alt: hwkim-dev 포트폴리오 사이트 열기

            **hwkim-dev.github.io/hwkim-dev** — 블로그, 다른 프로젝트, 소개.

.. |License| image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
.. |Architecture| image:: https://img.shields.io/badge/Architecture-Scalable_NPU-purple
.. |Target| image:: https://img.shields.io/badge/Target-Edge_AI-orange
.. |Precision| image:: https://img.shields.io/badge/Precision-W4A8_Promotion-green
