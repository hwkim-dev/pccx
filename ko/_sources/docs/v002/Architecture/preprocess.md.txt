# PREPROCESS 스테이지

PREPROCESS 스테이지는 ACP 포트에서 들어온 BF16 fmap 액티베이션을
W4A8 GEMM 어레이가 요구하는 형식으로 변환한다.
현재 운용 경로는 BF16 → 27-bit fixed-point 변환이며, signed INT8 양자화기
후보 두 개(Option A / Option B)는 TODO.md §A-1에 열린 결정으로 기록되어
있다.

## 데이터 흐름

ACP 포트에서 128-bit 스트림으로 유입된 BF16 fmap은
`preprocess_fmap` 내부의 XPM block FIFO에서 256-bit 폭으로
버퍼링된다. 이후 두 경로가 병렬로 실행된다.

1. **지수 사이드밴드**: 256-bit 워드 두 개를 한 쌍으로 묶어 32개 원소의
   `e_max` 그룹을 구성하고, 1024-깊이 `emax_cache_mem`에 저장한다.
   읽기 시작 신호(`i_rd_start`)가 들어오면 `o_cached_emax`로 브로드캐스트
   된다.

2. **가수 정렬 경로**: `preprocess_bf16_fixed_pipeline`이 16-비트 BF16
   원소 16개(256-bit)씩 두 클럭에 걸쳐 32개 블록을 수신하고, 블록 내
   global `e_max`를 기준으로 각 가수를 right-shift 정렬한 뒤
   27-bit two's-complement fixed-point 값 16개(432-bit)를 출력한다.
   이 파이프라인은 3단 `always_ff` 스테이지로 구성된다.

```{mermaid}
flowchart LR
    ACP["ACP AXIS\n128-bit BF16"] --> FIFO["XPM FIFO\n256-bit block"]
    FIFO --> EMAX["e_max 추출\n& emax_cache_mem"]
    FIFO --> PIPE["preprocess_bf16\n_fixed_pipeline\n3-stage"]
    PIPE --> CACHE["fmap_cache\nBRAM 27-bit×2048"]
    EMAX --> OUT["o_cached_emax\n→ MAT_CORE"]
    CACHE --> OUT2["o_fmap_broadcast\n→ MAT_CORE"]
```

`fmap_cache`에 전달된 432-bit 데이터(16 × 27-bit)는 7-bit 기록 주소를
통해 비대칭 포트 BRAM에 기록되고, `i_rd_start` 이후 2048 원소를
하나씩 읽어 `ARRAY_SIZE_H`개 레인에 동일하게 공급한다.

## 양자화 옵션

현재 `preprocess_bf16_fixed_pipeline.sv`가 출력하는 27-bit fixed-point
값은 하위 8비트를 truncate하여 GEMM systolic array에 임시로 공급하는
자리표시자 경로다. v002 W4A8 datapath가 요구하는 올바른 형식은
**signed INT8 activation**이다(DSP48E2 Port B signed 8-bit 입력).
TODO.md §A-1은 양자화기 교체를 위한 두 가지 후보를 정의한다.

**Option A — power-of-two scale (블록 부동소수점 기반)**

32-원소 블록의 global `e_max`를 재사용해 스케일을 2의 거듭제곱으로 결정한다.

$$
S_a \approx 2^{e_\text{max} - \text{bias} - \text{frac\_bits}}, \quad
a_q = \mathrm{sat\_int8}\!\left(\mathrm{round}\!\left(\frac{x}{S_a}\right)\right)
$$ (eq-preprocess-option-a)

기존 `e_max` 탐색 구조를 그대로 재사용하므로 RTL이 단순하고
400 MHz timing closure에 유리하다. 반면 스케일이 2의 거듭제곱으로
제한되어 activation 분포에 따라 saturation 또는 underflow가 증가할 수 있다.

**Option B — true symmetric INT8 양자화**

블록 내 `max_abs`를 기준으로 실수 스케일을 결정한다.

$$
S_a = \frac{\max|x_i|}{127}, \quad
a_q = \mathrm{sat\_int8}\!\left(\mathrm{round}\!\left(\frac{x_i}{S_a}\right)\right)
$$ (eq-preprocess-option-b)

INT8 표현 범위를 더 효율적으로 사용하며 Python golden model과의
bit-exact 비교가 명확하다. 다만 하드웨어에서 `max_abs`, 역수 연산,
곱셈/반올림을 처리해야 하므로 RTL 비용이 크다.
현실적으로는 driver/compiler가 `S_a`를 미리 계산해
Constant Cache에 `MEMSET`으로 적재하는 구조가 자연스럽다.

두 후보에 대한 결정은 `pccx-FPGA-NPU-LLM-kv260` 저장소의
`TODO.md` §A-1에서 추적된다. 현재 RTL의
`bf16_to_INT8_pipeline_power_of_two_scale.sv`와
`bf16_to_INT8_pipeline_true_symmetric_INT8.sv`는 각 옵션에 대응하는
자리표시자 파일이며 본문은 미구현 상태다.

## fmap 캐시

`fmap_cache`는 `preprocess_bf16_fixed_pipeline` 출력(432-bit, 16 × 27-bit)을
수신해 2048-깊이 BRAM에 스테이징하고, `i_rd_start` 이후 MAT_CORE(GEMM)에
1워드씩 순차적으로 공급하는 버퍼다.

```{list-table} fmap_cache 주요 파라미터
:header-rows: 1
:name: tbl-fmap-cache-params

* - 파라미터
  - 값
  - 설명
* - ``DATA_WIDTH``
  - 27
  - Fixed-point 가수 비트 폭
* - ``WRITE_LANES``
  - 16
  - 클럭당 기록 워드 수
* - ``CACHE_DEPTH``
  - 2048
  - 1 × 2048 feature map 수용
* - ``LANES``
  - 32
  - 읽기 브로드캐스트 레인 수
```

기록 포트 주소 폭은 7-bit(2048 ÷ 16 = 128), 읽기 포트 주소 폭은
11-bit(2048 원소 직접 접근)다. BRAM `READ_LATENCY_B = 2`이므로
유효 신호는 3단 파이프라인(`rd_valid_pipe_1 → rd_valid_pipe_2 → rd_valid`)을
거쳐 정렬된다.

:::{admonition} 마지막 검증 대상
:class: note

커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
