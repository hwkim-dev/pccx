# scienceplots — batch size 대비 대역폭

`sphinx-gallery` 는 레포 루트 `plots/` 디렉토리에서 `plot_*.py` 스크립트를
모두 스캔해 페이지를 자동 생성합니다. 파이썬 스크립트가 어떤 matplotlib
스타일을 택하든 그대로 반영되며, pccx 의 규약은
[`scienceplots`](https://github.com/garrettj403/SciencePlots) 의 IEEE
스타일입니다.

생성된 갤러리 카드는 [자동 생성 플롯 갤러리](../../auto_plots/index.rst) 에
등록되며 {doc}`샘플 인덱스 <index>` 의 toctree 가 끌어옵니다.

## 작성 패턴

플롯 소스 파일 하나가 PNG 프리뷰(소셜 공유용)와 SVG 임베드(문서용)의
단일 진실 원천입니다. 표준 헤더:

```python
"""
플롯 제목
=========

갤러리 카드 부제목이 되는 한 줄 설명.
"""
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

plt.style.use(["science", "ieee", "no-latex"])

# ... 데이터 준비 ...
fig, ax = plt.subplots(figsize=(3.4, 2.1))
# ... 플로팅 ...
fig.tight_layout()
plt.show()
```

`plots/plot_bandwidth.py` 에 실제 동작하는 예시가 있고, 전체 플롯 규약은
`CLAUDE.md` §6 에 있습니다 (결정성 원칙: 난수 시드는 전부 고정).
