# Cycle Loop

_Last revised: 2026-04-29._

The `cycle/` directory is the artefact store for a **4-role loop** that
iteratively improves pccx-lab without user intervention between rounds.
The loop completes one round in Judge → Research → Plan → Implement order;
the next round's Judge re-evaluates the prior implementation.
Round artefact layout, grade history, and current state are collected here.

Loop driver specification: `cycle/driver.md`.
Round summary index: `cycle/ROUNDS.md`.

## Loop structure

The loop is composed of four roles. Each role has a dedicated agent prompt
file under `cycle/agents/`.

**Judge** (`agents/judge.md`) compares pccx-lab's current state objectively
against a reference set of commercial RTL simulators, GPU profilers, and
FPGA vendor synthesis tools.
It scores individual dimensions — UI, ISA validation, API integrity, UVM
coverage, FPGA/ASIC verification, and documentation — independently, then
writes the aggregate grade and top-five issues to `round_NNN/judge_report.md`.
The round-N+1 Judge receives both the prior `judge_report_N` and
`implemented_N`, so it grades absolute quality and round-over-round progress
simultaneously.

**Research** (`agents/research.md`) surveys arxiv, IEEE, ACM, and official
vendor documentation to collect prior-art citations and SOTA references for
every weakness the Judge identifies.
Every claim is backed by a canonical citation before the findings are
written to `round_NNN/research_findings.md`.

**Planner** (`agents/planner.md`) reads the Judge and Research outputs and
converts weaknesses into concrete implementation tickets, each specifying
target file paths, patch direction, and acceptance criteria.
Output: `round_NNN/roadmap.md`.

**Implementer** splits into three specialised prompts
(`implementer_ui.md`, `implementer_core.md`, `implementer_bridge.md`).
The top tickets from `roadmap.md` are executed in parallel in isolated
worktrees; diff and test results are recorded in `round_NNN/implemented_T*.md`.
No commit is made without a passing build and test run.

## Round artefacts

Each round directory (`cycle/round_NNN/`) contains the following standard
file set.

```{list-table} Standard file set per round directory
:name: tbl-round-artefacts
:header-rows: 1
:widths: 30 20 50

* - File
  - Producing role
  - Contents
* - `judge_report.md`
  - Judge
  - Per-dimension scores, overall grade, top-five issues
* - `research_findings.md`
  - Research
  - Canonical citations + SOTA summary per issue
* - `roadmap.md`
  - Planner
  - T-1/T-2/T-3 tickets (file paths, patch, acceptance criteria)
* - `implemented_T1.md`
  - Implementer
  - T-1 diff + test results
* - `implemented_T2.md`
  - Implementer
  - T-2 diff + test results
* - `implemented_T3.md`
  - Implementer
  - T-3 diff + test results
```

After round completion, a one-line summary is appended to `cycle/ROUNDS.md`,
`cycle/STATE.json` is updated to the new round and phase, and the next
wake-up is scheduled.

## Grade progression

The table below summarises rounds 1–6 based on `cycle/ROUNDS.md`.

```{list-table} Judge grade and key deliverables by round
:name: tbl-round-grades
:header-rows: 1
:widths: 10 15 75

* - Round
  - Judge grade
  - Key deliverables
* - 001
  - C-
  - T-1 real VCD/.pccx ingest in WaveformViewer, T-2 coverage merge, T-3 flame-graph bottleneck; 5 hardcoded-data gaps resolved with 3 real IPC tickets, all landed
* - 002
  - C
  - T-1/T-2 core+UI registration and rename fixes, T-3 docs+accessibility; implementer agents hit API limit mid-work, main thread completed
* - 003
  - C+
  - T-1 synthetic_fallback killed + resolveResource fixed, T-2 ELK auto-layout, T-3 real second-trace file picker; 6 fake fixes identified and called out
* - 004
  - B-
  - T-1 fake-telemetry dragnet removed (Math.random 20→9), T-2 Vivado parser, T-3 flat-buf v2; tests 39→51
* - 005
  - B
  - T-1 SynthStatusCard, T-2 Monaco+Monarch syntax highlighting, T-3 useLiveWindow hook; 4-round Monaco technical debt paid
* - 006
  - B-
  - T-1 step_to_cycle + useCycleCursor, T-2 Roofline 2.0 + resizable-panels v4 fix, T-3 scheduler/visibility hooks + panel rewire; cycle-granular UI + 60 fps target
```

Round 7 is pending Judge evaluation as of 2026-04-29 (`cycle/STATE.json`).

## Current state

Current contents of `cycle/STATE.json`:

```json
{
  "round": 7,
  "phase": "judge",
  "r1_grade": "C-",
  "r2_grade": "C",
  "r3_grade": "C+",
  "r4_grade": "B-",
  "r5_grade": "B",
  "r6_grade": "B-",
  "max_rounds": 50,
  "heartbeat_every": 10
}
```

`round: 7`, `phase: "judge"` indicates that round 6 implementation is
complete and the next Judge evaluation has not yet run.

**Halt conditions** (see `cycle/driver.md`):

- If the file `cycle/HALT` exists the loop stops immediately.
  Activate from the shell: `touch cycle/HALT`.
- Reaching `max_rounds: 50` suspends the loop until the user unblocks it.
- Two consecutive rounds with zero implementation commits cause an
  automatic halt — the loop does not silently retry.
- Three consecutive rounds sharing the same top-ranked Judge issue trigger
  a halt and escalation.

A heartbeat summarising the prior ten rounds' grade trajectory and landed
tickets is emitted at every tenth round (10, 20, 30, 40).

## Cite this page

```bibtex
@misc{pccx_self_evolution_2026,
  title        = {pccx-lab cyclic self-evolution loop: 4-role iterative design refinement},
  author       = {Kim, Hyunwoo},
  year         = {2026},
  howpublished = {\url{https://hkimw.github.io/pccx/en/docs/Lab/self-evolution.html}},
  note         = {Part of pccx: \url{https://hkimw.github.io/pccx/}}
}
```
