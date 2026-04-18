Preprocess
===========

The preprocess stage consumes the raw BF16 feature map arriving from
the host via ACP, converts it into the 27-bit fixed-point representation
native to the DSP48E2 MACs, and stages it into per-core L1 caches.

.. seealso::

   :doc:`/docs/archive/experimental_v001/Architecture/v001_architecture`
      ``preprocess_fmap`` box in the top-level diagram.

Modules
--------

* ``preprocess_fmap.sv`` — top-level preprocess wrapper feeding both
  Matrix and Vector cores.
* ``fmap_cache.sv`` — L1 feature-map cache: one slice per consumer.
* ``preprocess_bf16_fixed_pipeline.sv`` — BF16 → 27-bit fixed-point
  conversion pipeline with Emax alignment.

Source
-------

.. dropdown:: ``preprocess_fmap.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/PREPROCESS/preprocess_fmap.sv
      :language: systemverilog

.. dropdown:: ``fmap_cache.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/PREPROCESS/fmap_cache.sv
      :language: systemverilog

.. dropdown:: ``preprocess_bf16_fixed_pipeline.sv``
   :icon: code
   :color: muted

   .. literalinclude:: ../../../../codes/v001/hw/rtl/PREPROCESS/preprocess_bf16_fixed_pipeline.sv
      :language: systemverilog
