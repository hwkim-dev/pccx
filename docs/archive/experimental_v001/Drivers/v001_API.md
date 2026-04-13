# 🔌 uCA v001 Host API

> [!NOTE]
> 이 문서는 호스트 애플리케이션(Ex: `llm-lite`)이 NPU를 제어하기 위해 사용하는 High-Level C API를 다룹니다. NPU 아키텍처 v001 버전에 맞춰 설계되었으며, 하드웨어 레이어(HAL)를 직접 래핑(Wrapping)합니다.

## 📌 API 구조 설계 개요

현재의 API 레이어는 **"CUDA와 유사한 사용 경험"**을 추구합니다. 개발자는 64비트 VLIW 명령어 어셈블리를 몰라도 `uca_*` C 함수 호출 만으로 비동기 하드웨어 가속기를 다룰 수 있습니다.

- **Non-blocking (비동기)**: 모든 `uca_gemm`, `uca_gemv` 호출 등 산술 연산 함수는 HAL을 거쳐 NPU 명령어 FIFO에 명령을 쌓고 즉시(Immediately) 반환됩니다.
- **Sync Point (동기화 지점)**: 명시적으로 `uca_sync()` 함수를 호출할 때에만 호스트의 실행 흐름이 멈춰 모델 스케줄러와 하드웨어의 State를 동기화합니다.

---

## 💻 API Reference

자세한 소스코드는 `uCA_v1_api.h` 및 `uCA_v1_api.c`를 참고하십시오.

### 1. Initialization & Shutdown

```c
// NPU를 초기화하고 응답 상태를 검증합니다.
int uca_init(void);

// NPU 자원을 해제합니다.
void uca_deinit(void);
```

### 2. Matrix Core & Vector Core 연산

```c
// Vector Core (GEMV): INT4 가중치 × BF16/INT8 활성 함수 연산을 수행합니다.
// - dest_reg: 대상 레지스터 및 L2 주소 (17-bit)
// - src_addr: Source Feature Map 버퍼의 시작 위치 (17-bit)
// - lanes: 최대로 동원할 병렬 μV-Core 레인의 수 (1~4)
void uca_gemv(uint32_t dest_reg,   uint32_t src_addr,
              uint8_t  flags,      uint8_t  size_ptr,
              uint8_t  shape_ptr,  uint8_t  lanes);

// Matrix Core (GEMM): 32x32 Systolic Array 연산을 수행합니다. (파라미터 포맷은 GEMV와 동일)
void uca_gemm(uint32_t dest_reg,   uint32_t src_addr,
              uint8_t  flags,      uint8_t  size_ptr,
              uint8_t  shape_ptr,  uint8_t  lanes);
```

### 3. CVO (Complex Vector Operations)

Softmax, RMSNorm, GELU, RoPE 등 어텐션 가중치 스케일링에 쓰이는 비선형 수학 함수(SFU 및 CORDIC)를 제어합니다.

```c
// μCVO-Core 에 연산을 지시합니다. (GELU, EXP, SQRT, SIN/COS 등)
void uca_cvo(uint8_t  cvo_func,  uint32_t src_addr,
             uint32_t dst_addr,  uint16_t length,
             uint8_t  flags,     uint8_t  async);
```

> **📌 주요 CVO Function Code:**
> - `UCA_CVO_EXP` / `UCA_CVO_SQRT` / `UCA_CVO_GELU`: 비선형 활성함수
> - `UCA_CVO_SIN` / `UCA_CVO_COS`: RoPE 계산용 CORDIC 오퍼레이션
> - `UCA_CVO_REDUCE_SUM` / `UCA_CVO_SCALE` / `UCA_CVO_RECIP`: Softmax 및 정규화(Normalization)

### 4. Memory Control (DMA Transfers)

호스트와 NPU 간, 혹은 L2 캐시와 L1 엔진 내부 캐시 간의 버스 전송(Data Route)을 담당합니다.

```c
// DMA 메모리 전송
void uca_memcpy(uint8_t route, uint32_t dest_addr, uint32_t src_addr, uint8_t shape_ptr, uint8_t async);

// 특정 Shape / Constant 레지스터 값 기록
void uca_memset(uint8_t dest_cache, uint8_t dest_addr, uint16_t a, uint16_t b, uint16_t c);
```

### 5. Synchronization

FIFO 큐에 올라간 모든 비동기 NPU 파이프라인의 작업이 완료될 때까지 Blocking 대기합니다.

```c
// 작업 완료까지 호스트 대기 (Return 0 on success, -1 on timeout)
int uca_sync(uint32_t timeout_us);
```

---

## 🛠️ Internal Implementation 

C API는 실제로 어떻게 동작하나요? `uca_gemm` 구현의 내부를 살펴보면, 인자로 받은 모든 C 데이터 타입을 Packing 해서 64비트 정수(VLIW 래퍼) 형태로 만들고 HAL 로 내리는 것을 볼 수 있습니다:

```c
static uint64_t build_compute_instr(...) {
    uint64_t instr = 0;
    instr |= ((uint64_t)(opcode    & 0xF)     << 60);
    instr |= ((uint64_t)(dest_reg  & 0x1FFFF) << 43);
    instr |= ((uint64_t)(src_addr  & 0x1FFFF) << 26);
    instr |= ((uint64_t)(flags     & 0x3F)    << 20);
    instr |= ((uint64_t)(size_ptr  & 0x3F)    << 14);
    instr |= ((uint64_t)(shape_ptr & 0x3F)    <<  8);
    instr |= ((uint64_t)(lanes     & 0x1F)    <<  3);
    return instr;
}

void uca_gemm(...) {
    uint64_t instr = build_compute_instr(UCA_OP_GEMM, dest_reg, src_addr, flags, size_ptr, shape_ptr, lanes);
    uca_hal_issue_instr(instr); // HPM(Axial-Lite) Port로 하드웨어 전송
}
```