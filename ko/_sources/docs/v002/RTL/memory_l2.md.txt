# L2 캐시 (URAM)

`mem_GLOBAL_cache` → `mem_L2_cache_fmap` → `mem_BUFFER` 세 모듈이 v002의
1.75 MiB UltraRAM L2 캐시를 구성한다. 최상위 래퍼인 `mem_GLOBAL_cache`가
ACP 포트와 NPU 포트 양쪽의 상태 기계를 구동하고, 내부에 `mem_L2_cache_fmap`
인스턴스(URAM)와 ACP CDC 브리지인 `mem_BUFFER`를 포함한다.

## 역할

L2 캐시는 NPU 클럭 도메인(400 MHz) 쪽에 위치한 True Dual-Port URAM 블록이다.
Port A는 PS의 ACP 경로를 통해 DDR4 ↔ L2 DMA를 수행하고, Port B는 컴퓨트
엔진(GEMM / GEMV / CVO)이 직접 접근한다. fmap과 weight 데이터를 동일 주소 공간에
보관하며, 어떤 영역이 fmap이고 어떤 영역이 weight인지는 소프트웨어 규약과
`mem_dispatcher`가 관리하는 shape 상수 RAM의 주소 범위로 결정된다.
하드웨어는 두 영역을 구분하지 않는다.

## 저장 구조

`mem_L2_cache_fmap`은 `Depth = 114_688`로 인스턴스화되고, 데이터 폭은 128비트다.

$$\text{총 용량} = 114{,}688 \times 128\ \text{bit} = 14{,}680{,}064\ \text{bit} = 1.75\ \text{MiB}$$ (eq-l2-capacity-ko)

주소 단위는 128비트 워드다. 워드 주소 $N$은 바이트 오프셋 $[16N,\ 16N+15]$에
해당한다. 17비트 주소 버스가 사용되므로 표현 가능한 최대 워드 수는 131,072이며,
현재 용량(114,688 워드)은 그 범위 안에 있다.

URAM 읽기 레이턴시는 3클럭이다. Port A 읽기 경로는 3비트 시프트 레지스터
`acp_rd_valid_pipe`로 데이터 유효 시점을 추적한다. 전송이 진행되는 동안
`OUT_acp_rdata`는 3클럭 지연 이후에 유효해지며, `core_acp_tx_bus.tvalid`가
함께 어서트된다. Port B 읽기도 동일한 3클럭 레이턴시 특성을 가진다.

## 포트 인터페이스

Port A(ACP)와 Port B(NPU) 제어 신호는 아래와 같다.

```{literalinclude} ../../../../codes/v002/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
:language: systemverilog
:start-at: // ===| Port A — ACP DMA control |
:end-before: // ===| Port B — NPU compute direct access |
```

```{literalinclude} ../../../../codes/v002/hw/rtl/MEM_control/memory/mem_GLOBAL_cache.sv
:language: systemverilog
:start-at: // ===| Port B — NPU compute direct access |
:end-before: );
```

포트 계약:

- `IN_acp_rx_start` 또는 `IN_npu_rx_start`가 1로 어서트되면, 해당 포트의
  상태 기계가 `base_addr`에서 `end_addr - 1`까지 순차 전송을 시작한다.
- `write_en = 1`이면 외부(DDR4 또는 NPU 엔진)에서 L2로 쓰고,
  `write_en = 0`이면 L2에서 외부로 읽는다.
- `OUT_acp_is_busy` / `OUT_npu_is_busy`가 1인 동안 해당 포트는 새 커맨드를
  받지 않는다. 커맨드 큐잉은 `mem_u_operation_queue`가 담당한다.

두 포트는 독립 상태 기계를 가지며 동시에 동작할 수 있다. Port B 중재는
`mem_dispatcher`가 수행하며, `mem_CVO_stream_bridge`가 활성인 경우
CVO 브리지가 Port B를 선점한다. 선점 기간에는 NPU DMA 커맨드가 대기 상태를
유지하고, 브리지 완료 후 재개된다.

## 하부 모듈

```{table} L2 캐시 하부 모듈
:name: tbl-l2-submodules-ko

| 모듈 | 역할 |
|---|---|
| `mem_L2_cache_fmap` | 114,688 × 128비트 URAM 배열. Port A/B 읽기·쓰기 인터페이스 제공. |
| `mem_BUFFER` | ACP AXI 250 MHz ↔ Core 400 MHz CDC 브리지. RX/TX 각각 깊이 32의 BRAM `xpm_fifo_axis` 2개로 구성. |
| `mem_GLOBAL_cache` | 두 모듈을 포함하는 최상위 래퍼. Port A/B 상태 기계 구동. |
```

```{admonition} 마지막 검증 대상
:class: note
커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29)
```
