# UVM 브리지

_최근 개정: 2026-04-29._

`pccx-uvm-bridge` 크레이트는 `pccx-core` 사이클 추정기를 SystemVerilog
UVM 테스트벤치에 노출하는 **C ABI DPI-C 익스포트 모음**이다.
시뮬레이터는 공유 라이브러리(`cdylib`)를 링크하고, SV 쪽에서
`import "DPI-C"` 선언 하나로 Rust 분석기를 런타임에 호출한다.

소스: `crates/uvm_bridge/src/lib.rs`, 크레이트 매니페스트:
`crates/uvm_bridge/Cargo.toml`.

## 역할

`pccx-uvm-bridge` 는 두 레이어를 이어 준다.

**pccx-core 분석기 레이어** 는 하드웨어 모델(`HardwareModel::pccx_reference()`)
을 고정 레퍼런스로 인스턴스화하고, `CycleEstimator` 를 통해 GEMM 타일
연산·AXI DMA 전송의 사이클 수치를 계산한다.
입력이 유효하면 결과를 출력 포인터에 기록하고 `PCCX_OK(0)` 를 반환한다.
입력이 유효하지 않으면 출력 포인터를 건드리지 않고 `PCCX_ERROR(1)` 를
반환한다.

**UVM 테스트벤치 레이어** 는 공유 라이브러리가 링크된 시뮬레이터 환경에서
`import "DPI-C"` 로 임포트된 함수를 직접 호출한다.
UVM 시퀀스는 테스트 인자(`m`, `n`, `k`, `bpe` 등)를 채운 뒤
DPI-C 함수를 호출해 사이클 견적을 수신하고, 이를 assertion 임계값이나
커버리지 버킷 경계에 사용한다.

## C ABI 표면

`#[no_mangle] pub unsafe extern "C"` 로 선언된 모든 함수는 C ABI 를
통해 노출된다. 아래 표는 `crates/uvm_bridge/src/lib.rs` 에 정의된
전체 DPI-C 익스포트 목록이다.

```{list-table} DPI-C 익스포트 함수
:name: tbl-dpi-c-exports
:header-rows: 1
:widths: 35 45 20

* - 함수 이름
  - 인자
  - 반환
* - `pccx_estimate_gemm_cycles`
  - `m: u32, n: u32, k: u32, bpe: u32, out_cycles: *mut u64`
  - `i32` (에러 코드)
* - `pccx_estimate_dma_cycles`
  - `bytes: u32, out_cycles: *mut u64`
  - `i32` (에러 코드)
* - `pccx_estimate_dma_cycles_contended`
  - `bytes: u32, active_cores: u32, out_cycles: *mut u64`
  - `i32` (에러 코드)
* - `pccx_is_compute_bound`
  - `m: u32, n: u32, k: u32, bpe: u32`
  - `i32` (1=compute-bound, 0=memory-bound, PCCX_ERROR=무효)
* - `pccx_peak_tops_x100`
  - 없음
  - `u32` (TOPS × 100 정수, 예: 205 = 2.05 TOPS)
* - `pccx_clock_mhz`
  - 없음
  - `u32` (MHz)
```

**`bpe` 필드** 는 원소당 바이트를 뜻한다: `1` = INT8, `2` = BF16/FP16,
`4` = FP32.

**에러 코드** 는 다음 두 값만 존재한다: `PCCX_OK = 0`, `PCCX_ERROR = 1`.
`out_cycles` 가 null 이거나 크기 인자가 0 이면 `PCCX_ERROR` 가 반환된다.

`pccx_peak_tops_x100` 과 `pccx_clock_mhz` 는 출력 포인터를 갖지 않으므로
`unsafe` 를 생략하고 `pub extern "C"` 로 선언되었다.

## TileOperation 데이터 흐름

UVM 테스트벤치가 GEMM 사이클을 조회하는 전체 경로는 다음과 같다.

```
UVM testbench (SV)
  │  import "DPI-C" pccx_estimate_gemm_cycles(m, n, k, bpe, out_cycles)
  │
  ▼
pccx_estimate_gemm_cycles()        [crates/uvm_bridge/src/lib.rs]
  │  TileOperation { m, n, k, bytes_per_element: bpe } 생성
  │  HardwareModel::pccx_reference() 로 레퍼런스 HW 모델 인스턴스화
  │  CycleEstimator::new(&hw)
  │
  ▼
CycleEstimator::estimate_gemm_cycles(&op)   [crates/core/src/cycle_estimator.rs]
  │  산술 모델로 사이클 계산
  │
  ▼
*out_cycles 기록 → PCCX_OK 반환
  │
  ▼
UVM scoreboard / coverage model
  (사이클 수치를 assertion 또는 커버리지 버킷에 적용)
```

`pccx_estimate_dma_cycles_contended` 는 동일한 경로를 따르되
`active_cores` 를 추가로 받아 멀티코어 버스 경합을 반영한 사이클을
반환한다.

`pccx_is_compute_bound` 는 `out_cycles` 포인터 없이 compute/memory-bound
여부를 직접 반환하므로, UVM 시퀀스가 분기 조건으로 사용하기 편리하다.

## SV 측 import 계약

시뮬레이터는 공유 라이브러리(`libpccx_uvm_bridge.so`)를 링크할 때
SV 패키지에 다음과 같이 임포트한다.

```systemverilog
package pccx_dpi_pkg;

  import "DPI-C" function int pccx_estimate_gemm_cycles(
    input  int unsigned m,
    input  int unsigned n,
    input  int unsigned k,
    input  int unsigned bpe,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_estimate_dma_cycles(
    input  int unsigned bytes,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_estimate_dma_cycles_contended(
    input  int unsigned bytes,
    input  int unsigned active_cores,
    output longint unsigned cycles
  );

  import "DPI-C" function int pccx_is_compute_bound(
    input int unsigned m,
    input int unsigned n,
    input int unsigned k,
    input int unsigned bpe
  );

  import "DPI-C" function int unsigned pccx_peak_tops_x100();
  import "DPI-C" function int unsigned pccx_clock_mhz();

endpackage
```

`longint unsigned` ↔ Rust `u64`, `int unsigned` ↔ Rust `u32` 매핑은
IEEE 1800-2017 DPI-C 표준이 정의한다.

**출력 인자** (`output longint unsigned cycles`) 는 SV 관점에서 값이
반환된 후에만 유효하다. 반환 코드가 `PCCX_OK(0)` 임을 확인한 뒤
`cycles` 를 읽어야 한다.

크레이트 타입은 `cdylib` 와 `rlib` 를 모두 포함한다
(`crates/uvm_bridge/Cargo.toml` 참고). `rlib` 표면은 Rust 단위 테스트와
하이레벨 래퍼(`estimate_gemm`, `estimate_dma`)를 위해 제공된다.

## 인용

```bibtex
@misc{pccx_uvm_bridge_2026,
  title        = {pccx-lab UVM Bridge: DPI-C adapter exposing the pccx cycle estimator to SystemVerilog testbenches},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/ko/docs/Lab/uvm-bridge.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
