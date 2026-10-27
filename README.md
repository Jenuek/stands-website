# STANDS website

WHERE ART STANDS — STANDS 홈페이지. GitHub Pages로 배포합니다.

## 구조

- `content/` — 문구와 콘텐츠. **Pages CMS(https://app.pagescms.org)에서 편집합니다.**
  - `site.yml` 홈 · About · 연락처 · 사업자 정보, 홈 하이라이트 선택
  - `projects/`, `artists/`, `editorial/` 항목마다 파일 하나
- `img/` 사진 (CMS에서 올린 이미지도 여기에 저장)
- `assets/` 디자인 (CSS, 히어로 애니메이션, 분석 스크립트)
- `build/build.py` 콘텐츠로 페이지를 만드는 스크립트
- `.github/workflows/deploy.yml` main에 저장될 때마다 사이트를 다시 만들어 배포
- `.pages.yml` CMS 편집 화면 설정

루트에 남아 있는 예전 `*.html` 파일은 더 이상 쓰지 않습니다 (배포는 `_site`에서 만들어진 파일로 합니다).
