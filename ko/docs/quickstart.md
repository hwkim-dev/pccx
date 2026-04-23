---
myst:
  html_meta:
    description lang=ko: |
      pccx NPU 의 원-커맨드 재현기 — clone, build, 샘플 .pccx 트레이스
      로딩, Sail 형식 모델 실행, pccx-lab 프로파일러 열기.  Docker
      레시피 + 네이티브 bare-metal 경로 모두 Ubuntu 24.04 에서 검증.
---

# 퀵스타트

`git clone` 에서 "pccx 트레이스를 보고 있다" 까지의 최단 경로.
이 페이지는 **재현기** 로 NVIDIA 컨설팅 보고서 §6.5 가 요구한 것이다 —
`docker compose up` 한 번으로 샘플 캡처가 로딩된 프로파일러가 실행
상태로 떠야 한다.

```{contents}
:local:
:depth: 2
```

## 0. 얻게 되는 산출물

| 산출물 | 생성 주체 | 여는 도구 |
|---|---|---|
| `.pccx` 트레이스 (16-토큰 Gemma-3N 디코드) | `pccx-FPGA-NPU-LLM-kv260/hw/sim/run_verification.sh` | `pccx-lab` (Tauri 앱) |
| Sail ISA 모델 (타입체크 완료) | `pccx-FPGA-NPU-LLM-kv260/formal/sail/` | `sail`, `sail --doc` |
| Vivado synth + timing 리포트 | `pccx-FPGA-NPU-LLM-kv260/vivado/build.sh synth` | `pccx_analyze --synth` |
| AnalyzerDashboard 발견 | `pccx-lab` 워크스페이스 | 16 개 빌트인 분석기 |

## 1. 사전 조건

단일 64-bit Linux 머신 (Ubuntu 24.04 검증):

- `git` ≥ 2.40
- `opam` + `ocaml` ≥ 4.14 — Sail 용
- `docker` ≥ 24 — 재현기 컨테이너 용
- `rustup` (stable toolchain) — `pccx-core` + Tauri 용
- *(선택)* Xilinx Vivado 2024.1 — RTL 합성 경로
- *(선택)* Xilinx Kria KV260 보드 — 실측 토큰 생성

앞의 4 개만으로 **소프트웨어** 절반 재현 가능. 보드 접근은 선택.

## 2. 세 레포 클론

pccx 는 **3-레포 연합** 이다 ({doc}`index` 의 에코시스템 섹션 참고).
형제 디렉토리에 클론:

```bash
mkdir -p ~/pccx-ws && cd ~/pccx-ws
git clone https://github.com/hwkim-dev/pccx.git                    # docs (이 사이트)
git clone https://github.com/hwkim-dev/pccx-FPGA-NPU-LLM-kv260.git  # RTL + Sail 모델
git clone https://github.com/hwkim-dev/pccx-lab.git                 # 프로파일러 + UVM Copilot
```

## 3. 원-커맨드 재현기 (Docker)

```bash
cd ~/pccx-ws/pccx-lab
docker compose -f scripts/docker/quickstart.yml up
```

컨테이너:

1. `pccx-core` + `pccx_analyze` CLI 빌드.
2. 번들된 xsim smoke TB 실행 (최신 노트북에서 ~30 초).
3. 결과 `.pccx` 를 `./out/smoke.pccx` 에 기록.
4. 16 개 분석기 요약을 stdout 에 프린트.
5. 성공 시 exit 0 — CI 파이프 준비 완료.

리포트로 파이핑:

```bash
docker compose ... > report.txt 2>&1
```

## 4. 네이티브 경로 (Docker 없음)

```bash
# ── Sail 모델 ───────────────────────────────────────────────────
eval $(opam env)
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260/formal/sail
make check                           # 타입체크; < 5 초

# ── pccx-core + CLI ────────────────────────────────────────────
cd ~/pccx-ws/pccx-lab
cargo build -p pccx-core --bin pccx_cli --release
./target/release/pccx_cli \
    samples/gemma3n_16tok_smoke.pccx    # 헤더 + roofline + bottleneck

# ── pccx-lab (Tauri 데스크톱 앱) ────────────────────────────────
cd src/ui
npm ci && npm run tauri dev
```

``samples/`` 디렉토리는 두 개의 사전 캡처 트레이스를 제공한다 —
[`samples/README.md`](https://github.com/hwkim-dev/pccx-lab/blob/main/samples/README.md) 참고:

- ``gemma3n_16tok_smoke.pccx``   (101 KB, 2,568 events)  — CI smoke.
- ``gemma3n_128tok_decode.pccx`` (797 KB, 20,488 events) — steady-state decode.

## 5. 보드 경로 (선택)

```bash
# 비트스트림 플래시 후 KV260 에서 16-토큰 디코드.
cd ~/pccx-ws/pccx-FPGA-NPU-LLM-kv260/scripts/board
./bringup.sh kv260.local
# .pccx 를 호스트로 자동 pull; pccx-lab 에서 열기.
```

## 6. 다음 단계

- 프로파일러 API surface 는 [pccx-lab 핸드북](Lab/index).
- Sail 스캐폴드는 [형식 모델 페이지](v002/Formal/index).
- 실측 tok/s + 지연 수치는 [Evidence 페이지](Evidence/index) (보드
  실행 진행 중).

## 이 페이지 인용

```bibtex
@misc{pccx_quickstart_2026,
  title        = {pccx Quickstart: one-command reproducer for the open NPU},
  author       = {Kim, Hwangwoo},
  year         = {2026},
  howpublished = {\url{https://hwkim-dev.github.io/pccx/ko/docs/quickstart.html}},
  note         = {Part of pccx: \url{https://hwkim-dev.github.io/pccx/}}
}
```
