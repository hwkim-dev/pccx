라이브러리
===========

연산 경로와 메모리 경로가 공유하는 재사용 primitive. BF16 수치 유틸리티와
모든 단간 핸드오프가 의존하는 FIFO 큐 계열입니다.

알고리즘
---------

* ``Algorithms.sv`` — 소형 알고리즘 유틸리티 (leading-zero detector,
  인코더, 소형 비교기).
* ``BF16_math.sv`` — BF16 전용 수학 헬퍼 (지수 비교, 정렬 시프트 카운트,
  정규화).

.. dropdown:: ``Algorithms.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Library/Algorithms/Algorithms.sv
      :language: systemverilog

.. dropdown:: ``BF16_math.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Library/Algorithms/BF16_math.sv
      :language: systemverilog

FIFO 계열
----------

* ``QUEUE.sv`` — depth · width 매개변수화된 동기 FIFO. 모든 엔진별
  디스패치 FIFO 의 기반.
* ``IF_queue.sv`` — ``QUEUE`` 를 감싼 SystemVerilog ``interface`` 래퍼.
  타입드 핸드셰이크 신호 노출.

.. dropdown:: ``QUEUE.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Library/Algorithms/QUEUE/QUEUE.sv
      :language: systemverilog

.. dropdown:: ``IF_queue.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../../codes/v001/hw/rtl/Library/Algorithms/QUEUE/IF_queue.sv
      :language: systemverilog
