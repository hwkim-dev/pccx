# 공유 라이브러리

v002 RTL은 공통 수치 연산과 데이터 구조를 `Library/` 디렉터리에 분리한다. 컴파일
순서(`filelist.f`)상 이 파일들은 패키지 계층(A–D) 직후, `isa_pkg` 이전에 위치한다.
컴퓨트 코어가 공통 라이브러리에 의존함으로써 동일 연산의 중복 구현을 막는다.

## Algorithms 패키지

**`algorithms_pkg`** (`Library/Algorithms/Algorithms.sv`)
QUEUE 상태 구조체 `queue_stat_t`를 정의한다. `empty` / `full` 두 필드로 구성된
packed struct이며, QUEUE 모듈 외부에서 상태를 참조할 때 사용한다. STACK 지원은
스텁(stub)으로 예약되어 있다.

```{literalinclude} ../../../../codes/v002/hw/rtl/Library/Algorithms/Algorithms.sv
:language: systemverilog
:caption: Library/Algorithms/Algorithms.sv
:start-at: package algorithms_pkg;
:end-before: endpackage
```

**`bf16_math_pkg`** (`Library/Algorithms/BF16_math.sv`)
BF16 산술 함수를 패키지로 제공한다. 파일 상단에서 BF16 비트 레이아웃을
`[15]=sign`, `[14:7]=exp(8b)`, `[6:0]=mantissa(7b)`로 명시한다. 은닉 비트(hidden
bit)는 저장하지 않는다.

노출되는 타입과 함수:

- `bf16_t` — 부호 1비트, 지수 8비트, 가수 7비트의 packed struct.
- `bf16_aligned_t` — emax 기준으로 정렬된 24비트 2의 보수 값과 8비트 `emax` 필드를
  보유하는 packed struct.
- `to_bf16(raw[15:0])` — 16비트 원시값을 `bf16_t`로 캐스팅하는 자동 함수.
- `align_to_emax(val, emax)` — BF16 값을 주어진 emax에 맞춰 정렬하여 24비트 2의
  보수로 반환한다. 지수 차(diff)만큼 가수를 오른쪽으로 시프트한 뒤 부호 확장한다.
- `bf16_add(a[15:0], b[15:0])` — 두 BF16 값을 더해 BF16 결과를 반환한다. 큰 쪽
  지수로 정렬 후 24비트 부호합산, 선행 1 탐색으로 재정규화한다. 비정규화/NaN/Inf
  처리는 포함하지 않는다(autoregressive 디코딩 경로의 정규화 BF16 피연산자 전제).

```{literalinclude} ../../../../codes/v002/hw/rtl/Library/Algorithms/BF16_math.sv
:language: systemverilog
:caption: Library/Algorithms/BF16_math.sv
:start-at: package bf16_math_pkg;
:end-before: endpackage
```

## QUEUE 인터페이스

QUEUE는 인터페이스(`IF_queue`)와 모듈(`QUEUE`) 두 파일로 구성된다.

**`IF_queue`** (`Library/Algorithms/QUEUE/IF_queue.sv`)
파라미터 `DATA_WIDTH`(기본 32)와 `DEPTH`(기본 8)를 받는 SystemVerilog 인터페이스다.
`clk`, `rst_n`을 인터페이스 포트로 받는다. `PTR_W = $clog2(DEPTH)` 비트의
포인터(`wr_ptr`, `rd_ptr`)와 `mem[0:DEPTH-1]` 스토리지를 인터페이스 내부에서 선언한다.
`empty`/`full` 플래그는 순수 조합 논리로 할당된다.

세 modport:

- `producer` — `push()` 태스크만 import. `push_data`/`push_en`을 출력, `empty`/`full`을 입력.
- `consumer` — `pop()` 태스크만 import. `pop_data`/`empty`/`full`을 입력, `pop_en`을 출력.
- `owner` — QUEUE 모듈 자신이 사용. 핸드셰이크 신호를 입력으로 받고, 포인터와 `ref mem`을
  출력한다.

```{literalinclude} ../../../../codes/v002/hw/rtl/Library/Algorithms/QUEUE/IF_queue.sv
:language: systemverilog
:caption: Library/Algorithms/QUEUE/IF_queue.sv
:start-at: modport producer
:end-before: endinterface
```

**`QUEUE`** (`Library/Algorithms/QUEUE/QUEUE.sv`)
`IF_queue.owner q`를 단일 포트로 받는 모듈이다. `PTR_W = $clog2($size(q.mem))`로
포인터 폭을 재유도한다. `always_ff` 블록에서 리셋 시 양쪽 포인터를 0으로 초기화하고,
`push_en && !full` 조건에서 데이터를 기록하며, `pop_en && !empty` 조건에서 읽기
포인터를 증가시킨다.

## Quantizations

**`Quantize_BF16.sv`** (`Library/Quantizations/BF16/Quantize_BF16.sv`)
현재 내용이 없는 자리 표시자 파일이다. BF16 양자화 헬퍼를 위해 예약된 위치로,
향후 오프라인 양자화 파이프라인에서 RTL과 소프트웨어 스택 간 공통 변환 로직을 이곳에
배치할 계획이다.

## 사용 패턴

아래 표는 소스에서 직접 확인된 `import` 구문과 인터페이스 인스턴스화를 기준으로
컴퓨트 코어와 라이브러리 파일 간 의존 관계를 보여준다.

```{list-table} 컴퓨트 코어별 라이브러리 의존성
:name: tbl-lib-usage
:header-rows: 1
:widths: 32 22 22 12 12

* - 모듈 (코어)
  - `algorithms_pkg`
  - `bf16_math_pkg`
  - `IF_queue`
  - `QUEUE`
* - `CVO_top` (CVO_CORE)
  - —
  - o
  - —
  - —
* - `AXIL_CMD_IN` (ctrl_npu_frontend 하위)
  - o
  - —
  - o
  - o
```

`o` = 소스에서 직접 확인된 import 또는 인스턴스화. `—` = 해당 파일에 없음.

`bf16_math_pkg`는 `CVO_top`이 `import bf16_math_pkg::*;`로 직접 가져온다. 소스 주석에
따르면 `FLAG_SUB_EMAX` 경로(softmax의 sub-emax 스테이지)가 이 패키지의 BF16 산술을
사용한다. `algorithms_pkg`와 `IF_queue` / `QUEUE`는 `AXIL_CMD_IN`에서 인스턴스화된다.
`AXIL_CMD_IN`은 AXI4-Lite 커맨드 채널의 FIFO 버퍼로, `ctrl_npu_frontend`가 내부에서
인스턴스화한다. `GEMM_systolic_top`, `GEMV_top`, PREPROCESS 모듈은 라이브러리 패키지를
직접 import하지 않고 `` `define `` 헤더만 사용한다.

---

```{admonition} 마지막 검증 대상
:class: note

커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
```
