# WaveDrom — AXI4 read transaction

`sphinxcontrib-wavedrom` renders RTL-style timing diagrams from inline JSON.
The `wavedrompy` Python backend ships with the repo's dependency set, so
rendering happens at build time and there is no runtime JS requirement.

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

The transaction above issues a burst of four beats against the HP0 read
channel; the consumer asserts `rready` for one cycle per beat and the
producer drops `rvalid` after `rlast`.

## When to reach for WaveDrom

- AXI/AXI-Stream/APB protocol illustrations.
- Handshake timing where cycle-level detail matters.

For micro-architectural pipeline stages, a Mermaid sequence or Graphviz
`digraph` is usually a better fit than a wave.
