# .pccx Binary Format

_Last revised: 2026-04-29._

`.pccx` is the official container format for NPU profiling traces, hardware
configurations, and session metadata produced by pccx-lab.
Source of truth: `crates/core/src/pccx_format.rs`
([hkimw/pccx-lab](https://github.com/hkimw/pccx-lab)).
Current version: major `0x01`, minor `0x01`.

Four design properties:

- **Self-describing** — the JSON header contains all metadata needed to decode
  the payload; no out-of-band schema files are required.
- **Versioned** — major/minor version bytes support backward-compatible
  evolution.
- **Integrity-checked** — an optional FNV-1a 64-bit checksum detects payload
  corruption.
- **Zero-copy IPC** — the payload is a raw byte blob that can be mapped directly
  into a WebGL `ArrayBuffer` without re-encoding.

## File header

All multi-byte integers are **little-endian**.

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | Magic | `PCCX` = `0x50 0x43 0x43 0x58` |
| 4 | 1 | Major version | Breaking-change counter (currently `0x01`) |
| 5 | 1 | Minor version | Additive-change counter (currently `0x01`) |
| 6 | 2 | Reserved | `0x00 0x00` — writers must zero these bytes |
| 8 | 8 | Header length | `u64` — byte length of the JSON header |
| 16 | N | JSON header | UTF-8 JSON object |
| 16 + N | M | Binary payload | Encoding declared in `payload.encoding` |

Parsers MUST reject files whose **major version** does not match the expected
value.  Parsers SHOULD accept any **minor version**.

`PccxFile::read` (`crates/core/src/pccx_format.rs`) performs magic validation
and major-version check in order; minor version is read but not validated:

```rust
pub const MAJOR_VERSION: u8 = 0x01;
pub const MINOR_VERSION: u8 = 0x01;

const MAGIC_NUMBER: &[u8; 4] = b"PCCX";
```

## JSON header

The JSON header is a UTF-8 JSON object that carries all metadata required to
decode the payload.  `PccxHeader` (same source file) defines the schema:

```rust
pub struct PccxHeader {
    pub pccx_lab_version: String,

    pub arch: ArchConfig,       // mac_dims, isa_version, peak_tops
    pub trace: TraceConfig,     // cycles, cores, clock_mhz
    pub payload: PayloadConfig, // encoding, byte_length, checksum_fnv64

    pub format_minor: u8,
}
```

The three sub-structs:

```rust
pub struct ArchConfig {
    pub mac_dims: (u32, u32), // (rows, cols) — systolic array dimensions
    pub isa_version: String,
    pub peak_tops: f64,       // informational; does not affect parsing
}

pub struct TraceConfig {
    pub cycles: u64,    // total simulation cycles
    pub cores: u32,     // number of active NPU cores
    pub clock_mhz: u32, // clock frequency when trace was generated (default 1000)
}

pub struct PayloadConfig {
    pub encoding: String,            // "bincode" | "flatbuf" | "raw"
    pub byte_length: u64,            // exact payload byte count
    pub checksum_fnv64: Option<u64>, // FNV-1a 64-bit checksum; null if absent
}
```

Serialisation example:

```json
{
  "pccx_lab_version": "v0.4.0-contention-aware",
  "format_minor": 1,
  "arch": { "mac_dims": [32, 32], "isa_version": "1.1", "peak_tops": 2.05 },
  "trace": { "cycles": 12345678, "cores": 32, "clock_mhz": 1000 },
  "payload": {
    "encoding": "flatbuf",
    "byte_length": 4096000,
    "checksum_fnv64": "0xcbf29ce484222325"
  }
}
```

## Payload encoding

The `payload.encoding` field declares one of three values:

| Value | Description |
|-------|-------------|
| `"bincode"` | Rust `bincode` v1 serialisation of the `NpuTrace` struct |
| `"flatbuf"` | 24-byte packed struct array (see layout below) |
| `"raw"` | Architecture-specific raw bytes — not standardised |

### flatbuf layout

For `"flatbuf"` encoding, each event is 24 bytes, all fields little-endian:

| Offset | Size | Type | Field |
|--------|------|------|-------|
| 0 | 4 | u32 | `core_id` |
| 4 | 8 | u64 | `start_cycle` |
| 12 | 8 | u64 | `duration` |
| 20 | 4 | u32 | `event_type_id` |

Event type IDs:

| ID | Name |
|----|------|
| 0 | `UNKNOWN` |
| 1 | `MAC_COMPUTE` |
| 2 | `DMA_READ` |
| 3 | `DMA_WRITE` |
| 4 | `SYSTOLIC_STALL` |
| 5 | `BARRIER_SYNC` |

### FNV-1a checksum

When `checksum_fnv64` is present, the parser computes the FNV-1a 64-bit hash of
the raw payload bytes and compares.  A mismatch produces a warning but is not
fatal by default (configurable in future):

```rust
pub fn fnv1a_64(data: &[u8]) -> u64 {
    const BASIS: u64 = 0xcbf29ce484222325;
    const PRIME: u64 = 0x00000100000001b3;
    data.iter().fold(BASIS, |h, &b| (h ^ b as u64).wrapping_mul(PRIME))
}
```

## Zero-copy IPC

The `.pccx` layout is structured for zero-copy IPC.  The 8-byte `u64` at
offset 8 gives the exact size of the JSON header, so a parser can locate the
payload blob at offset `16 + header_length` without scanning.  The
`byte_length` field in `PayloadConfig` specifies the exact payload size,
eliminating any need to read to end-of-file.

The `"flatbuf"` encoding's 24-byte record array maps directly into a WebGL
`ArrayBuffer` without re-encoding.  The Tauri `fetch_trace_payload` IPC
command follows this pattern — `Vec<u8>` on the Rust side, `TypedArray` on the
JavaScript side.

## Compatibility policy

- **Major version** increment — incompatible layout change (e.g. changing the
  reserved field size, removing a header field).  Parsers must reject
  mismatches.
- **Minor version** increment — additive change (new optional header fields,
  new event type IDs).  Parsers must ignore unknown fields gracefully.
- `pccx_lab_version` is informational and does not affect parsing behaviour.

Current values: `MAJOR_VERSION = 0x01`, `MINOR_VERSION = 0x01`
(constants in `crates/core/src/pccx_format.rs`).

## Cite this page

```bibtex
@misc{pccx_lab_pccx_format_2026,
  title        = {.pccx Binary Format Specification: container format for NPU profiling traces},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/pccx-format.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

Source definition lives at `crates/core/src/pccx_format.rs` in
[hkimw/pccx-lab](https://github.com/hkimw/pccx-lab).
