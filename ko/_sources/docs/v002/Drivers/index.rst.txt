==================
소프트웨어 스택
==================

pccx v002 드라이버는 C/C++ 하드웨어 추상화 레이어 (HAL) 와 얇은
공개 API 로 이루어져 있으며, 다음 책임을 가진다.

- CMD_IN FIFO 를 통한 64-bit VLIW 명령어 인코딩·디스패치.
- ``MEMSET`` 을 통한 shape / size 포인터, 스케일 팩터 프리셋.
- 호스트 DDR4 ↔ NPU L2 캐시 DMA 구동.
- ``STAT_OUT`` 폴링으로 비동기 완료 처리.

실구현은 :file:`codes/v002/sw/driver/uCA_v1_api.h` /
:file:`uCA_v1_api.c` 에 위치하며, v001 설계를 그대로 계승하되
ISA 참조 URL 만 pccx v002 기준으로 갱신.

.. admonition:: 구현 상태
   :class: warning

   v002 드라이버는 **bring-up** 단계이다. 공개 ``uca_*`` API 표면은
   컴파일되고 AXI-Lite HAL 스켈레톤은 존재하지만, end-to-end 흐름
   ``MEMSET → MEMCPY → GEMV → MEMCPY readback`` 은 아직 실 하드웨어
   상에서 RTL 과 검증되지 않았다. 미해결 검증 항목은
   :doc:`../Verification/index` §2 참고.

.. toctree::
   :maxdepth: 1

   api
   hal
