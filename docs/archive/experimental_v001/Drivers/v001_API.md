# uCA v001 Host API

> [!NOTE]
> 이 문서는 호스트 애플리케이션이 NPU를 제어하기 위해 사용하는 High-Level C API를 다룹니다. NPU 아키텍처 v001 버전에 맞춰 설계되었으며, 하드웨어 레이어(HAL)를 직접 래핑(Wrapping)합니다.

## API 구조 설계 개요

현재의 API 레이어는 **"CUDA와 유사한 사용 경험"**을 추구합니다. 개발자는 64비트 VLIW 명령어 어셈블리를 몰라도 `uca_*` C 함수 호출 만으로 비동기 하드웨어 가속기를 다룰 수 있습니다.

- **Non-blocking (비동기)**: 모든 연산 함수는 HAL을 거쳐 NPU 명령어 FIFO에 명령을 쌓고 즉시(Immediately) 반환됩니다.
- **Sync Point (동기화 지점)**: 명시적으로 `uca_sync()` 함수를 호출할 때에만 호스트의 실행 흐름이 멈춰 모델 스케줄러와 하드웨어의 상태를 동기화합니다.

---

## API Reference

### 1. Initialization and Shutdown

NPU 디바이스의 핸들을 초기화하고 자원을 반납하는 단계별 기본 함수입니다.

=== "Header (uCA_v1_api.h)"

    ```c
    // NPU를 초기화하고 응답 상태를 검증합니다.
    int  uca_init(void);

    // NPU 자원을 해제합니다.
    void uca_deinit(void);
    ```

=== "Implementation (uCA_v1_api.c)"

    ```c
    int uca_init(void) {
        return uca_hal_init();
    }

    void uca_deinit(void) {
        uca_hal_deinit();
    }
    ```

### 2. Matrix Core and Vector Core

Vector Core (GEMV) 및 Matrix Core (GEMM) 연산을 수행합니다. 호스트가 C 타입으로 인자를 넘기면 내부에서는 64Bit VLIW 포맷으로 빌드 한 후 Hardware FIFO 로 밀어넣습니다.

=== "Header (uCA_v1_api.h)"

    ```c
    // Vector Core (GEMV): INT4 가중치 x BF16/INT8 활성 함수 연산을 수행합니다.
    // - dest_reg   : 대상 레지스터 및 L2 주소 (17-bit)
    // - src_addr   : Source Feature Map 버퍼의 시작 위치 (17-bit)
    // - flags      : OR of UCA_FLAG_* constants
    // - size_ptr   : pointer to size descriptor in shape cache (6-bit)
    // - shape_ptr  : pointer to shape descriptor in shape cache (6-bit)
    // - lanes      : 최대로 동원할 병렬 μV-Core 레인의 수 (1~4)
    void uca_gemv(uint32_t dest_reg,   uint32_t src_addr,
                  uint8_t  flags,      uint8_t  size_ptr,
                  uint8_t  shape_ptr,  uint8_t  lanes);

    // Matrix Core (GEMM): 32x32 Systolic Array 연산을 수행합니다.
    void uca_gemm(uint32_t dest_reg,   uint32_t src_addr,
                  uint8_t  flags,      uint8_t  size_ptr,
                  uint8_t  shape_ptr,  uint8_t  lanes);
    ```

=== "Implementation (uCA_v1_api.c)"

    ```c
    // 내부 래핑 함수 - 64Bit ISA 스펙으로 변환합니다.
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

    void uca_gemv(...) {
        uint64_t instr = build_compute_instr(UCA_OP_GEMV, dest_reg, src_addr, flags, size_ptr, shape_ptr, lanes);
        uca_hal_issue_instr(instr);
    }
    ```

### 3. CVO (Complex Vector Operations)

Softmax, RMSNorm, GELU, RoPE 등 어텐션 가중치 스케일링에 쓰이는 비선형 수학 함수(SFU 및 CORDIC)를 제어합니다.

=== "Header (uCA_v1_api.h)"

    ```c
    // μCVO-Core 에 연산을 지시합니다. (GELU, EXP, SQRT, SIN/COS 등)
    // - cvo_func   : UCA_CVO_EXP 등 Function 코드 상수
    // - src_addr   : 소스 주소
    // - dst_addr   : 목적지 주소
    // - length     : N Vector 연산 개수
    void uca_cvo(uint8_t  cvo_func,  uint32_t src_addr,
                 uint32_t dst_addr,  uint16_t length,
                 uint8_t  flags,     uint8_t  async);
    ```

=== "Implementation (uCA_v1_api.c)"

    ```c
    static uint64_t build_cvo_instr(...) {
        uint64_t instr = 0;
        instr |= ((uint64_t)(UCA_OP_CVO & 0xF)   << 60);
        instr |= ((uint64_t)(cvo_func  & 0xF)    << 56);
        instr |= ((uint64_t)(src_addr  & 0x1FFFF)<< 39);
        instr |= ((uint64_t)(dst_addr  & 0x1FFFF)<< 22);
        instr |= ((uint64_t)(length    & 0xFFFF) <<  6);
        instr |= ((uint64_t)(flags     & 0x1F)   <<  1);
        instr |= ((uint64_t)(async     & 0x1)    <<  0);
        return instr;
    }

    void uca_cvo(...) {
        uint64_t instr = build_cvo_instr(cvo_func, src_addr, dst_addr, length, flags, async);
        uca_hal_issue_instr(instr);
    }
    ```

### 4. Memory Control (DMA Transfers)

호스트와 NPU 간, 혹은 L2 캐시와 L1 엔진 내부 캐시 간의 버스 전송(Data Route)을 파이프라이닝합니다.

=== "Header (uCA_v1_api.h)"

    ```c
    // DMA 메모리 전송
    void uca_memcpy(uint8_t route, uint32_t dest_addr, uint32_t src_addr, uint8_t shape_ptr, uint8_t async);

    // 특정 Shape / Constant 레지스터 값 기록
    void uca_memset(uint8_t dest_cache, uint8_t dest_addr, uint16_t a, uint16_t b, uint16_t c);
    ```

=== "Implementation (uCA_v1_api.c)"

    ```c
    void uca_memcpy(...) {
        uint8_t from_dev = (route >> 4) & 0xF;
        uint8_t to_dev   = (route >> 0) & 0xF;

        uint64_t instr = 0;
        instr |= ((uint64_t)(UCA_OP_MEMCPY & 0xF) << 60);
        instr |= ((uint64_t)(from_dev  & 0x1)      << 59);
        instr |= ((uint64_t)(to_dev    & 0x1)      << 58);
        instr |= ((uint64_t)(dest_addr & 0x1FFFF)  << 41);
        instr |= ((uint64_t)(src_addr  & 0x1FFFF)  << 24);
        instr |= ((uint64_t)(shape_ptr & 0x3F)     <<  1);
        instr |= ((uint64_t)(async     & 0x1)      <<  0);
        uca_hal_issue_instr(instr);
    }
    ```

### 5. Synchronization

FIFO 큐에 올라간 모든 비동기 NPU 파이프라인의 작업이 완료될 때까지 Blocking 방식으로 대기합니다.

=== "Header (uCA_v1_api.h)"

    ```c
    // 작업 완료까지 호스트 대기 (Return 0 on success, -1 on timeout)
    int uca_sync(uint32_t timeout_us);
    ```

=== "Implementation (uCA_v1_api.c)"

    ```c
    int uca_sync(uint32_t timeout_us) {
        return uca_hal_wait_idle(timeout_us);
    }
    ```