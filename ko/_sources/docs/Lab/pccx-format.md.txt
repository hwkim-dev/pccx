# .pccx 바이너리 포맷

_최근 개정: 2026-04-29._

`.pccx` 는 pccx-lab 이 생성하는 NPU 프로파일링 트레이스, 하드웨어 설정,
세션 메타데이터의 공식 컨테이너 포맷이다.
소스 정의: `crates/core/src/pccx_format.rs`
([hkimw/pccx-lab](https://github.com/hkimw/pccx-lab)).
현재 버전: major `0x01`, minor `0x01`.

설계 목표 네 가지:

- **자기 서술적** — JSON 헤더에 페이로드 디코딩에 필요한 모든 메타데이터가
  포함되어 외부 스키마 파일이 필요 없다.
- **버전 관리** — major/minor 버전 바이트로 하위 호환 진화를 지원한다.
- **무결성 검사** — 선택적 FNV-1a 64-bit 체크섬으로 페이로드 손상을 탐지한다.
- **제로카피 IPC** — 페이로드가 재인코딩 없이 WebGL `ArrayBuffer` 에
  직접 매핑 가능한 raw 바이트 블롭이다.

## 파일 헤더

모든 멀티바이트 정수는 **리틀-엔디언**이다.

| 오프셋 | 크기 | 필드 | 설명 |
|--------|------|------|------|
| 0 | 4 | Magic | `PCCX` = `0x50 0x43 0x43 0x58` |
| 4 | 1 | Major version | 호환 불가 변경 카운터 (현재 `0x01`) |
| 5 | 1 | Minor version | 추가 변경 카운터 (현재 `0x01`) |
| 6 | 2 | Reserved | `0x00 0x00` — 쓰기 측은 반드시 0으로 채워야 함 |
| 8 | 8 | Header length | `u64` — JSON 헤더의 바이트 길이 |
| 16 | N | JSON header | UTF-8 JSON 오브젝트 |
| 16 + N | M | Binary payload | `payload.encoding` 에 선언된 인코딩 |

파서는 **major version** 이 기대값과 다르면 파일을 거부해야 한다(`MUST`).
**minor version** 은 어떤 값이든 수락해야 한다(`SHOULD`).

`PccxFile::read` (`crates/core/src/pccx_format.rs`) 는 magic 검증과
major version 검사를 순서대로 수행하며, minor version 은 읽되 검증하지 않는다:

```rust
pub const MAJOR_VERSION: u8 = 0x01;
pub const MINOR_VERSION: u8 = 0x01;

const MAGIC_NUMBER: &[u8; 4] = b"PCCX";
```

## JSON 헤더

JSON 헤더는 파싱에 필요한 모든 메타데이터를 담는 UTF-8 JSON 오브젝트다.
`PccxHeader` 구조체(동일 소스 파일)가 스키마를 정의한다:

```rust
pub struct PccxHeader {
    pub pccx_lab_version: String,

    pub arch: ArchConfig,    // mac_dims, isa_version, peak_tops
    pub trace: TraceConfig,  // cycles, cores, clock_mhz
    pub payload: PayloadConfig, // encoding, byte_length, checksum_fnv64

    pub format_minor: u8,
}
```

세 하위 구조체의 필드:

```rust
pub struct ArchConfig {
    pub mac_dims: (u32, u32),  // (rows, cols) — systolic array 크기
    pub isa_version: String,
    pub peak_tops: f64,        // 정보용, 파싱에 영향 없음
}

pub struct TraceConfig {
    pub cycles: u64,    // 시뮬레이션 총 사이클 수
    pub cores: u32,     // 활성 NPU 코어 수
    pub clock_mhz: u32, // 트레이스 생성 시의 클록 주파수 (기본값 1000)
}

pub struct PayloadConfig {
    pub encoding: String,           // "bincode" | "flatbuf" | "raw"
    pub byte_length: u64,           // 페이로드 블롭의 정확한 바이트 수
    pub checksum_fnv64: Option<u64>, // FNV-1a 64-bit 체크섬, null 허용
}
```

직렬화 예시:

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

## payload 인코딩

`payload.encoding` 필드가 세 값 중 하나를 선언한다:

| 값 | 설명 |
|----|------|
| `"bincode"` | Rust `bincode` v1 직렬화 — `NpuTrace` 구조체 |
| `"flatbuf"` | 24 B 패킹 구조체 배열 (아래 레이아웃 참고) |
| `"raw"` | 아키텍처 종속 raw 바이트 — 비표준 |

### flatbuf 레이아웃

`"flatbuf"` 인코딩에서 각 이벤트는 24 바이트, 전 필드 리틀-엔디언:

| 오프셋 | 크기 | 타입 | 필드 |
|--------|------|------|------|
| 0 | 4 | u32 | `core_id` |
| 4 | 8 | u64 | `start_cycle` |
| 12 | 8 | u64 | `duration` |
| 20 | 4 | u32 | `event_type_id` |

이벤트 타입 ID:

| ID | 이름 |
|----|------|
| 0 | `UNKNOWN` |
| 1 | `MAC_COMPUTE` |
| 2 | `DMA_READ` |
| 3 | `DMA_WRITE` |
| 4 | `SYSTOLIC_STALL` |
| 5 | `BARRIER_SYNC` |

### FNV-1a 체크섬

`checksum_fnv64` 가 존재하면 파서는 raw 페이로드 바이트에 대해 FNV-1a 64-bit
해시를 계산해 비교한다. 불일치는 기본적으로 경고만 발생시키며(비치명적)
향후 설정으로 제어 가능하다:

```rust
pub fn fnv1a_64(data: &[u8]) -> u64 {
    const BASIS: u64 = 0xcbf29ce484222325;
    const PRIME: u64 = 0x00000100000001b3;
    data.iter().fold(BASIS, |h, &b| (h ^ b as u64).wrapping_mul(PRIME))
}
```

## 제로카피 IPC

`.pccx` 레이아웃은 제로카피 IPC 에 맞게 설계되어 있다.
파일 헤더 16 바이트 뒤에 오는 8 바이트 `u64` 가 JSON 헤더의 정확한 크기를
제공하므로, 파서는 오프셋 `16 + header_length` 에서 곧바로 페이로드 블롭을
찾을 수 있다. `byte_length` 필드가 페이로드 크기를 명시하므로 파서가 파일
끝까지 스캔할 필요가 없다.

`"flatbuf"` 인코딩의 24 B 레코드 배열은 재인코딩 없이 WebGL `ArrayBuffer`
에 직접 매핑된다. Tauri IPC 에서 `fetch_trace_payload` 커맨드가 이 패턴을
따른다 — Rust 측 `Vec<u8>` 을 JS 측 `TypedArray` 로 전달.

## 호환성 정책

- **major version** 증가 — 레이아웃 호환 불가 변경 (예: 예약 필드 크기
  변경, 헤더 필드 제거). 파서는 불일치 시 파일을 거부해야 한다.
- **minor version** 증가 — 추가 변경 (새 선택적 헤더 필드, 새 이벤트 타입
  ID). 파서는 미지 필드를 무시해야 한다.
- `pccx_lab_version` 문자열은 정보용 — 파싱 동작에 영향을 미치지 않는다.

현재값: `MAJOR_VERSION = 0x01`, `MINOR_VERSION = 0x01`
(`crates/core/src/pccx_format.rs` 의 상수).

## 인용

```bibtex
@misc{pccx_lab_pccx_format_2026,
  title        = {.pccx Binary Format Specification: container format for NPU profiling traces},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/pccx-format.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```

소스 정의는 [hkimw/pccx-lab](https://github.com/hkimw/pccx-lab) 의
`crates/core/src/pccx_format.rs` 에 위치한다.
