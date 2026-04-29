# PREPROCESS Stage

The PREPROCESS stage converts BF16 fmap activations arriving from the
ACP port into the format required by the W4A8 GEMM array.
The active path produces 27-bit fixed-point values. Two candidate INT8
quantizers (Option A / Option B) remain as open stubs tracked in
`TODO.md` §A-1.

## Data Flow

BF16 fmap arrives as a 128-bit ACP stream and is buffered inside
`preprocess_fmap` by an XPM block FIFO into 256-bit words.
Two paths then run in parallel.

1. **Exponent sideband**: consecutive 256-bit words are paired into
   32-element groups, the global `e_max` is extracted per group and
   written into a 1024-entry `emax_cache_mem`.
   On `i_rd_start` the cache drives `o_cached_emax` to MAT_CORE.

2. **Mantissa alignment path**: `preprocess_bf16_fixed_pipeline` accepts
   sixteen 16-bit BF16 elements (256 bits) per clock, accumulates two
   beats to form a 32-element block, finds the block-global `e_max`,
   and right-shifts each mantissa to align it. The output is sixteen
   27-bit two's-complement fixed-point values (432 bits). The pipeline
   spans 3 `always_ff` stages.

```{mermaid}
flowchart LR
    ACP["ACP AXIS\n128-bit BF16"] --> FIFO["XPM FIFO\n256-bit block"]
    FIFO --> EMAX["e_max extraction\n& emax_cache_mem"]
    FIFO --> PIPE["preprocess_bf16\n_fixed_pipeline\n3-stage"]
    PIPE --> CACHE["fmap_cache\nBRAM 27-bit×2048"]
    EMAX --> OUT["o_cached_emax\n→ MAT_CORE"]
    CACHE --> OUT2["o_fmap_broadcast\n→ MAT_CORE"]
```

The 432-bit output (16 × 27-bit) is written into the asymmetric-port
BRAM of `fmap_cache` via a 7-bit write address. After `i_rd_start`, the
cache reads 2048 elements sequentially and supplies each one to all
`ARRAY_SIZE_H` lanes simultaneously.

## Quantizer Options

The 27-bit fixed-point values currently produced by
`preprocess_bf16_fixed_pipeline.sv` are fed to the GEMM systolic array
by truncating the lower 8 bits — a placeholder path. The correct v002
W4A8 format requires **signed INT8 activations** (DSP48E2 Port B
signed 8-bit input). `TODO.md` §A-1 defines two replacement candidates.

**Option A — power-of-two scale (block floating-point)**

Reuses the existing block-global `e_max` to derive a power-of-two scale.

$$
S_a \approx 2^{e_\text{max} - \text{bias} - \text{frac\_bits}}, \quad
a_q = \mathrm{sat\_int8}\!\left(\mathrm{round}\!\left(\frac{x}{S_a}\right)\right)
$$ (eq-preprocess-option-a)

Reusing the existing `e_max` logic keeps the RTL simple and favours
400 MHz timing closure. The power-of-two constraint limits quantization
precision and may increase saturation or underflow for peaked activation
distributions.

**Option B — true symmetric INT8 quantization**

Computes a real-valued scale from the block's `max_abs`.

$$
S_a = \frac{\max|x_i|}{127}, \quad
a_q = \mathrm{sat\_int8}\!\left(\mathrm{round}\!\left(\frac{x_i}{S_a}\right)\right)
$$ (eq-preprocess-option-b)

Uses the INT8 dynamic range more efficiently and produces a clear
bit-exact comparison with a Python golden model. The hardware cost is
higher: `max_abs`, reciprocal, and multiply-round must be computed on-chip,
or `S_a` must be pre-computed by the driver and stored in the Constant
Cache via `MEMSET`.

The open decision is tracked in `TODO.md` §A-1 in the
`pccx-FPGA-NPU-LLM-kv260` repository. The files
`bf16_to_INT8_pipeline_power_of_two_scale.sv` and
`bf16_to_INT8_pipeline_true_symmetric_INT8.sv` are placeholder stubs
corresponding to each option; neither is implemented.

## fmap Cache

`fmap_cache` accepts the 432-bit output (16 × 27-bit) from
`preprocess_bf16_fixed_pipeline`, stages it in a 2048-deep BRAM, and
after `i_rd_start` supplies one word per clock to MAT_CORE (GEMM).

```{list-table} fmap_cache key parameters
:header-rows: 1
:name: tbl-fmap-cache-params

* - Parameter
  - Value
  - Description
* - ``DATA_WIDTH``
  - 27
  - Fixed-point mantissa width in bits
* - ``WRITE_LANES``
  - 16
  - Words written per clock
* - ``CACHE_DEPTH``
  - 2048
  - Accommodates one 1 × 2048 feature map
* - ``LANES``
  - 32
  - Read broadcast lane count
```

The write-port address is 7 bits wide (2048 ÷ 16 = 128 locations);
the read-port address is 11 bits (2048 elements directly indexed).
`READ_LATENCY_B = 2`, so the valid signal propagates through a 3-stage
pipeline (`rd_valid_pipe_1 → rd_valid_pipe_2 → rd_valid`) before
reaching the downstream consumer.

:::{admonition} Last verified against
:class: note

Commit `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
