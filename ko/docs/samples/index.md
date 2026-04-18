# 툴체인 데모

pccx Sphinx 빌드에 연결된 모든 다이어그램 · 플롯 파이프라인을 한 번씩 쓰는
레퍼런스 페이지 모음입니다. 실제 아키텍처 챕터 안에서 툴체인이 망가지기
전에, 전용 페이지 위에서 바로 감지할 수 있도록 유지합니다.

```{toctree}
:maxdepth: 1

mermaid_blockdiagram
wavedrom_axi_read
svg_themed_demo
plot_bandwidth
../../auto_plots/index
```

**커버리지 매트릭스.**

| 데모                               | 검증 대상 파이프라인         | 테마 대응 |
| ---------------------------------- | ---------------------------- | :---: |
| [](mermaid_blockdiagram)           | `sphinxcontrib-mermaid`      | ✓ (neutral) |
| [](wavedrom_axi_read)              | `sphinxcontrib-wavedrom`     | — (래스터) |
| [](svg_themed_demo)                | 수작업 SVG + Furo CSS 변수   | ✓     |
| [](plot_bandwidth)                 | `scienceplots` + `sphinx-gallery` | ✓ (팔레트) |

작성 규약은 `CLAUDE.md` §5 (Diagram Authoring Rules) 와 §6 (Plotting
Conventions) 를 참고.
