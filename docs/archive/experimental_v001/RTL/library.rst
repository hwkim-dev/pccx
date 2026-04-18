Library
========

Re-usable primitives shared across compute and memory paths: BF16
numerics utilities and a FIFO queue family that all inter-stage
hand-offs rely on.

Algorithms
-----------

* ``Algorithms.sv`` — small algorithmic utilities (leading-zero
  detectors, encoders, small comparators).
* ``BF16_math.sv`` — BF16-specific math helpers (exponent compare,
  alignment shift counts, normalization).

.. dropdown:: ``Algorithms.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Library/Algorithms/Algorithms.sv
      :language: systemverilog

.. dropdown:: ``BF16_math.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Library/Algorithms/BF16_math.sv
      :language: systemverilog

FIFO family
------------

* ``QUEUE.sv`` — parameterized synchronous FIFO with configurable
  depth and width; underlies every per-engine dispatch FIFO.
* ``IF_queue.sv`` — SystemVerilog-interface wrapper around ``QUEUE``
  exposing typed handshake signals.

.. dropdown:: ``QUEUE.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Library/Algorithms/QUEUE/QUEUE.sv
      :language: systemverilog

.. dropdown:: ``IF_queue.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/Library/Algorithms/QUEUE/IF_queue.sv
      :language: systemverilog
