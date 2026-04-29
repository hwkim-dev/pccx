---
rtl_source: hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv,
            hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv,
            hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv,
            hw/rtl/NPU_Controller/npu_interfaces.svh
---

# NPU 프론트엔드 모듈

## 역할

NPU 프론트엔드는 PS↔PL 경계의 AXI-Lite 진입점이다.
호스트 드라이버 HAL은 `0x000` 주소에 ISA 워드를 기록하고 `0x008`에 kick을 기록하며,
완료 상태는 같은 인터페이스의 읽기 채널로 폴링한다.
`AXIL_CMD_IN`은 호스트 write 트랜잭션을 FIFO에 수신하고,
`AXIL_STAT_OUT`은 엔진 완료 상태를 FIFO를 통해 호스트 읽기로 반환한다.
계층적으로 `ctrl_npu_frontend`의 상위는 AXI-Lite 버스, 하위는 컨트롤러의
디코더/디스패처({doc}`/docs/v002/RTL/controller`)이다.

## AXIL_CMD_IN

호스트 write 트랜잭션을 수신하여 명령어를 CMD_IN FIFO에 저장한다.
파라미터 `FIFO_DEPTH`(기본값 8)가 FIFO 깊이를 결정한다.
FIFO가 가득 차면 `s_awready`가 자동으로 디어서트되어 호스트에 백프레셔를 건다.
등록 주소는 두 곳이다: `0x000`은 ISA 명령어 워드를 직접 FIFO에 삽입하고,
`0x008`은 `bit63 = 1`인 kick 마커를 삽입한다.
kick 마커는 하위 디스패처가 배치 경계를 감지하는 데 사용된다.
`OUT_valid && IN_decoder_ready` 핸드셰이크가 성립하는 사이클마다 FIFO에서 팝이 일어난다.

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/AXIL_CMD_IN.sv (AXI4-Lite Write Path)
:start-at: "  /*─────────────────────────────────────────────"
:end-before: "  /*─────────────────────────────────────────────"
```

## AXIL_STAT_OUT

엔진 완료 시 상위 모듈이 `IN_valid`를 어서트하여 상태 워드를 STAT_OUT FIFO에 푸시한다.
파라미터 `FIFO_DEPTH`(기본값 8)가 적용된다.
FIFO가 가득 차면 `IN_valid`가 무시된다. 완료 워드는 엔진에서 동일한 값으로 재전송되므로
누락은 재폴링으로 복구된다.
호스트가 AR 채널로 읽기를 요청하면 FIFO 헤드를 `rdata_r`에 래치하고 `s_rvalid`를
어서트한다. `s_rready`가 도착하면 `rvalid`를 해제한다.
`s_arready`는 FIFO가 비어 있거나 R 응답이 아직 진행 중일 때 디어서트된다.

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/AXIL_STAT_OUT.sv (AXI4-Lite Read Path)
:start-at: "  /*─────────────────────────────────────────────"
:end-before: "endmodule"
```

## ctrl_npu_frontend

`ctrl_npu_frontend`는 `axil_if.slave` 인터페이스를 통해 AXI-Lite 신호를
`AXIL_CMD_IN`(write 채널)과 `AXIL_STAT_OUT`(read 채널)에 배선하는 wrapper 모듈이다.
CMD_IN의 출력(`cmd_data`, `cmd_valid`)은 `OUT_RAW_instruction`과 `OUT_kick`으로
컨트롤러에 전달된다. `OUT_kick`은 `cmd_valid & IN_fetch_ready`의 조합논리로 생성된다.
STAT_OUT 방향은 `IN_enc_stat` / `IN_enc_valid`를 인코더 FSM으로부터 직접 수신한다.
`ctrl_npu_interface.sv`는 향후 코어별 인터페이스 집계를 위한 플레이스홀더다.

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv
:language: systemverilog
:caption: hw/rtl/NPU_Controller/NPU_frontend/ctrl_npu_frontend.sv (인스턴스 배선)
:start-at: "  AXIL_CMD_IN #("
:end-before: "endmodule"
```

## 인터페이스 명세

`npu_interfaces.svh`에 `axil_if`와 `axis_if` 두 인터페이스가 정의된다.
`axil_if`는 ADDR_W=12, DATA_W=64 기본값으로 AW/W/B/AR/R 5개 채널을 모두 포함하고,
`slave`와 `master` modport를 제공한다.
`ctrl_npu_frontend`는 `axil_if.slave` modport를 사용한다.
`axis_if`는 tdata/tvalid/tready/tlast/tkeep의 AXI-Stream 인터페이스로,
데이터 경로 모듈이 사용한다.

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: hw/rtl/NPU_Controller/npu_interfaces.svh (axis_if)
:start-at: "interface axis_if"
:end-before: "// axil_if.sv"
```

```{literalinclude} ../../../../codes/v002/hw/rtl/NPU_Controller/npu_interfaces.svh
:language: systemverilog
:caption: hw/rtl/NPU_Controller/npu_interfaces.svh (axil_if)
:start-at: "// axil_if.sv"
:end-before: "`endif"
```

:::{admonition} 마지막 검증 대상
:class: note

커밋 `8c09e5e` @ `hkimw/pccx-FPGA-NPU-LLM-kv260` (2026-04-29).
:::
