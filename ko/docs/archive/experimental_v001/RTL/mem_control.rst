메모리 제어
=============

호스트 DDR ↔ L2 URAM 캐시 ↔ 코어별 L1 캐시 ↔ CVO 스트림 인제스트 사이의
모든 경로를 맡습니다. 전용 디스패처가 ISA §5 에 열거된 8 개 ``data_route_e``
경로를 중재하고, 두 개의 상수 메모리 어레이가 행렬/벡터 코어에 shape 와
size 디스크립터를 공급합니다.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Drivers/ISA`
      ``OP_MEMCPY`` · ``OP_MEMSET`` 인코딩과 라우팅 enum.

최상위 플러밍
--------------

* ``mem_dispatcher.sv`` — 중앙 중재기. 사이클마다 8 개 경로 중 하나를
  선택해 대응하는 source/destination 쌍을 구동.
* ``mem_L2_cache_fmap.sv`` — 피처맵 전용 L2 URAM 캐시
  (114,688 × 128 비트).
* ``mem_HP_buffer.sv`` — HP-AXI 슬레이브와 컴퓨트 코어 가중치 FIFO
  사이의 더블 버퍼 큐.
* ``mem_CVO_stream_bridge.sv`` — L2 캐시에서 CVO 코어의 스트리밍
  입력으로 가는 브리지.

.. dropdown:: ``mem_dispatcher.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/top/mem_dispatcher.sv
      :language: systemverilog

.. dropdown:: ``mem_L2_cache_fmap.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/top/mem_L2_cache_fmap.sv
      :language: systemverilog

.. dropdown:: ``mem_HP_buffer.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/top/mem_HP_buffer.sv
      :language: systemverilog

.. dropdown:: ``mem_CVO_stream_bridge.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/top/mem_CVO_stream_bridge.sv
      :language: systemverilog

메모리 모듈
------------

* ``mem_GLOBAL_cache.sv`` — L2 URAM 의 물리적 백킹으로 쓰이는
  매개변수화된 글로벌 캐시 블록.
* ``mem_BUFFER.sv`` — HP 버퍼와 CVO 브리지가 사용하는 범용 ping-pong
  버퍼.

.. dropdown:: ``mem_GLOBAL_cache.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
      :language: systemverilog

.. dropdown:: ``mem_BUFFER.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/memory/mem_BUFFER.sv
      :language: systemverilog

상수 메모리 (shape · size)
----------------------------

* ``fmap_array_shape.sv`` — ``shape_ptr_addr`` 가 참조하는 피처맵
  shape 디스크립터 상수 메모리.
* ``weight_array_shape.sv`` — 가중치 shape 용으로 같은 구조.

.. dropdown:: ``fmap_array_shape.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/memory/Constant_Memory/fmap_array_shape.sv
      :language: systemverilog

.. dropdown:: ``weight_array_shape.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/memory/Constant_Memory/weight_array_shape.sv
      :language: systemverilog

IO
---

* ``mem_IO.svh`` — AXI / ACP 핀 단위 타입과 매개변수.
* ``mem_u_operation_queue.sv`` — 컨트롤러와 메모리 디스패처 사이의
  마이크로 옵 큐.

.. dropdown:: ``mem_IO.svh``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/IO/mem_IO.svh
      :language: systemverilog

.. dropdown:: ``mem_u_operation_queue.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/MEM_control/IO/mem_u_operation_queue.sv
      :language: systemverilog
