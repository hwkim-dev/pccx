# WaveDrom — AXI4 read 트랜잭션

`sphinxcontrib-wavedrom` 은 인라인 JSON 으로 RTL 스타일 타이밍 다이어그램을
그립니다. `wavedrompy` Python 백엔드가 의존성에 포함돼 있어 **빌드 타임에
SVG 로 생성**되고 런타임 JS 는 필요하지 않습니다.

```{wavedrom}
{ signal: [
    { name: "aclk",      wave: "p........." },
    {},
    { name: "arvalid",   wave: "0.1.0....."                },
    { name: "arready",   wave: "1...0....."                },
    { name: "araddr",    wave: "x.3.x.....", data: ["A0"]  },
    { name: "arlen",     wave: "x.4.x.....", data: ["4"]   },
    {},
    { name: "rvalid",    wave: "0....1..0."                },
    { name: "rready",    wave: "1......0.."                },
    { name: "rdata",     wave: "x....7.89x", data: ["D0", "D1", "D2", "D3"] },
    { name: "rlast",     wave: "0......10."                },
    { name: "rresp",     wave: "x....5..x.", data: ["OKAY"] }
], head: { tick: 0 } }
```

위 트랜잭션은 HP0 read 채널에 4-beat burst 하나를 발행하고, 소비자는 각
beat 마다 `rready` 를 한 사이클씩 어설트하며, 생산자는 `rlast` 뒤 `rvalid`
를 내립니다.

## WaveDrom 선택 기준

- AXI · AXI-Stream · APB 프로토콜 illustration.
- 사이클 단위 핸드셰이크 타이밍이 중요한 경우.

파이프라인 단계 자체를 보여주는 그림이라면 Mermaid sequence 나 Graphviz
`digraph` 가 더 적합합니다.
