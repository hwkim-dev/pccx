호스트 API (C 드라이버)
========================

VLIW 명령어를 구성해 NPU 의 AXI-Lite 제어 서피스에 쓰는 호스트 측
C 라이브러리입니다. MMIO 레지스터 접근자 + IRQ 없는 ``wait_idle``
폴링의 얇은 HAL, 그리고 ISA 와 1:1 대응하는 공개 API 로 나뉩니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/v001_API`
      같은 API 의 사람이 읽기 쉬운 개발자 레퍼런스.

Public API
-----------

* ``uCA_v1_api.h`` — 공개 함수 프로토타입 (``pccx_init``,
  ``pccx_gemv``, ``pccx_gemm``, ``pccx_cvo``, ``pccx_memcpy``,
  ``pccx_memset``, ``pccx_sync``).
* ``uCA_v1_api.c`` — 구현. 오피코드별 ``build_*_instr`` 헬퍼가
  인자를 64 비트 VLIW 로 패킹해 HAL 에 전달.

.. dropdown:: ``uCA_v1_api.h``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/sw/driver/uCA_v1_api.h
      :language: c

.. dropdown:: ``uCA_v1_api.c``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/sw/driver/uCA_v1_api.c
      :language: c

하드웨어 추상화 계층 (HAL)
---------------------------

* ``uCA_v1_hal.h`` — HAL 프로토타입: ``pccx_hal_init`` / ``deinit`` /
  ``issue_instr`` / ``wait_idle``.
* ``uCA_v1_hal.c`` — MMIO 구현. ``/dev/mem`` (또는 device tree
  핸들) 을 열어 AXI-Lite 영역을 매핑하고, ``0x00`` / ``0x04`` 에
  32 비트 쓰기 한 쌍으로 VLIW 를 발행.

.. dropdown:: ``uCA_v1_hal.h``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/sw/driver/uCA_v1_hal.h
      :language: c

.. dropdown:: ``uCA_v1_hal.c``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/sw/driver/uCA_v1_hal.c
      :language: c
