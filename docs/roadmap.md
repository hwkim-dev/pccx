# Roadmap

The detailed execution board lives in [GitHub Projects][project]. This page
only summarizes the current release direction across the pccx ecosystem.

## Now — v0.2.0: FPGA bring-up and closure

- finish remaining RTL integration on `pccx-FPGA-NPU-LLM-kv260`
- trace-driven verification on `pccx-lab`
- Sail execute increments
- xsim / KV260 bring-up logs
- no production-ready or timing-closed claim until the verification
  evidence is published

Tracking issue: [pccxai/pccx#28 — v0.2.0 umbrella][v020].

## Next — v0.3.0: Lab extensibility and user workflow split

- pccx-lab plugin system (CLI-first, GUI second)
- controlled MCP interface for AI workers
- spin out `pccx-systemverilog-ide` from pccx-lab
- `pccx-llm-launcher` MVP planning
- pccx-lab ↔ IDE handoff format
- pccx-lab ↔ launcher workflow boundary

## Later — v0.4+: AI-assisted hardware/software workflows

- AI-assisted SystemVerilog development workflow
- evolutionary generate / simulate / evaluate / refine loop
- testbench / log / waveform feedback loop
- VS Code extension path
- broader model and device support
- paper-quality reproducible artifacts

## Links

- GitHub Project (source of truth): <https://github.com/orgs/pccxai/projects/1>
- v0.2.0 umbrella: <https://github.com/pccxai/pccx/issues/28>

[project]: https://github.com/orgs/pccxai/projects/1
[v020]: https://github.com/pccxai/pccx/issues/28
