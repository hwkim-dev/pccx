# Mermaid — NPU 블록 다이어그램

Mermaid 는 클라이언트 사이드에서 렌더되므로, `conf_common.py` 에서 설정한
`neutral` 팔레트를 통해 Furo 의 다크/라이트 테마를 자연스럽게 따라갑니다.

```{mermaid}
flowchart LR
    HOST[Host CPU] -- AXI-Lite --> CTRL[NPU Controller]
    CTRL --> GEMM[GEMM Core<br/>32×16×2]
    CTRL --> GEMV[GEMV Core<br/>4 lanes × 8 MAC]
    CTRL --> SFU[SFU / CVO]
    CTRL --> DMA[DMA]
    GEMM <-- HP0/HP1 --> DDR[(DDR4)]
    GEMV <-- HP2/HP3 --> DDR
    DMA  <-- ACP    --> DDR
    GEMV -. 직결 FIFO .-> SFU
    GEMM --> L2[(공유 L2<br/>URAM ~1.5 MB)]
    GEMV --> L2
    SFU  --> L2
```

렌더 서비스 없이 바로 그려져야 정상입니다. 다이어그램 박스가 비어 있으면
브라우저 콘솔에서 Mermaid 파싱 에러를 먼저 확인하세요 (대부분 라벨 안에
예약어가 들어간 경우).

## Mermaid 선택 기준

- 플로우 · 상태 머신 · 시퀀스처럼 **텍스트로 diff 하기 쉬운** 다이어그램.
- 정확한 비율보다 작성 속도가 우선인 빠른 스케치.

데이터패스처럼 정밀한 치수 · 간격이 중요한 다이어그램은 인라인 SVG
({doc}`svg_themed_demo`) 를 우선 고려합니다. Mermaid 의 자동 레이아웃은
편리하지만 거친 편입니다.
