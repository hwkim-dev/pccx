# SVG — 테마 대응 4×4 PE 어레이

아래 그림은 색을 `currentColor` 와 Furo CSS 커스텀 프로퍼티로 표현한
수작업 SVG 입니다. 독자가 다크 모드를 켜면 팔레트가 자동으로 반전되며
별도 래스터 fallback 은 포함하지 않습니다.

```{figure} ../../../_static/diagrams/sample_pe_array.svg
:name: fig-sample-pe-array
:alt: 4×4 PE 격자. 활성은 좌→우로, 부분합은 상→하로 흐른다.
:width: 80%

{numref}`fig-sample-pe-array`: 장난감 4×4 PE 어레이의 weight-stationary
데이터플로. 활성(brand-primary 화살표)은 행을 따라 흐르고, 가중치(범례의
점선 accent 화살표)는 각 PE 내부에 상주하며, 부분합(foreground)은
열 방향으로 누적됩니다.
```

## currentColor + CSS 변수를 쓰는 이유

- **한 자산으로 두 테마.** stroke / fill 이 `--color-foreground-primary`,
  `--color-brand-primary`, 그리고 `conf_common.py` 에 선언된 커스텀
  `--pccx-accent` 로 해결됩니다.
- **Diff 친화적.** 텍스트 파일이라 SVG 를 수정한 PR 이 **실제 diff** 로
  리뷰됩니다 — 바이너리 델타가 아님.
- **네트워크 의존 0.** SVG 가 사이트와 함께 서빙되고 로컬에서 파싱되므로
  배포·버전 관리해야 할 클라이언트 렌더러가 없습니다.

새 SVG 자산이 지켜야 하는 절대 규칙 (색 하드코딩 금지, `viewBox` 만 사용,
접근성용 `<title>` + `<desc>`) 은 `CLAUDE.md` §5.2 를 참고.
