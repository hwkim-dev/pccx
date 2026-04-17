==================
소프트웨어 스택
==================

pccx v002 드라이버는 C/C++ 하드웨어 추상화 레이어(HAL) 로 제공되며,
다음 책임을 가집니다.

- 64-bit 명령어 인코딩·디스패치
- MEMSET 을 통한 포인터/스케일 프리셋
- Host ↔ L2 Cache DMA 관리
- 비동기 실행 완료 상태 폴링/인터럽트 처리

.. toctree::
   :maxdepth: 1

   api

.. note::

   v002 드라이버 API 는 현재 설계 단계이며, v001 의
   :file:`docs/archive/experimental_v001/Drivers/uCA_v1_api.h` 및
   :file:`uCA_v1_api.c` 를 참고 구현으로 삼아 작성됩니다.
