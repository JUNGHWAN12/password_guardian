# 에셋 출처와 이용 조건

확인일: 2026-10-12. 공식 페이지와 다운로드한 각 팩의 라이선스 원문을 확인했다.

| 팩 | 제작·배포자 | 라이선스 | 보관한 원문 |
|---|---|---|---|
| [Space Shooter Remastered](https://kenney.nl/assets/space-shooter-remastered) | Kenney / Kenney Vleugels | CC0 | [license.txt](candidates/space-shooter-remastered/pack/license.txt) |
| [Space Shooter Extension](https://kenney.nl/assets/space-shooter-extension) | Kenney / Kenney Vleugels | CC0 | [License.txt](candidates/space-shooter-extension/pack/License.txt) |
| [Simple Space](https://kenney.nl/assets/simple-space) | Kenney | CC0 | [License.txt](candidates/simple-space/pack/License.txt) |
| [Pixel Shmup](https://kenney.nl/assets/pixel-shmup) | Kenney | CC0 | [License.txt](candidates/pixel-shmup/pack/License.txt) |
| [UI Pack: Sci-fi](https://kenney.nl/assets/ui-pack-sci-fi) | Kenney | CC0 | [License.txt](candidates/ui-pack-sci-fi/pack/License.txt) |

CC0 안내: https://creativecommons.org/publicdomain/zero/1.0/

동봉 문서에는 개인·상업 프로젝트 사용 가능, 크레딧 표기는 선택이라고 명시되어 있다. Simple Space, Pixel Shmup, UI Pack 문서에는 교육 목적 사용도 명시되어 있다. CC0에 따라 수정·재배포할 수 있으며, 프로젝트에서는 추적 가능성을 위해 원문과 출처를 계속 보존한다.

권장 크레딧: `Game assets by Kenney (https://kenney.nl), CC0. Selected and adapted for Password Guardian.`

프로토타입에서 실제 사용하는 이미지는 `assets/images/`에 있으며 [sources.json](images/sources.json)에 원본과 색상 편집 내역을 기록했다. 봇·군단의 장갑을 주황색, 드론을 보라색으로 편집했다. 적 탄환·보호막·HUD는 프로젝트 코드로 렌더링한다. 게임 글꼴은 아래의 Galmuri11을 사용한다.

`candidates/review/`의 추천 원본 PNG 13개는 원본을 그대로 복사했다. 배경 시안·기체 비교·화면 시안은 기존 소재를 프로젝트에서 합성한 파생 검토 자료다. 다운로드 주소와 ZIP 해시는 각 팩의 `source.json`, 선정 이미지 해시는 `review/selection.json`에 있다.

후보 비교 이미지(`tools/build_asset_review.py`)의 한글은 로컬 Windows의 맑은 고딕으로 렌더링했으며, 맑은 고딕 파일은 이 프로젝트에 복사하지 않았다. 실제 배포에서는 선택한 이미지와 해당 출처 문서만 포함하고 후보 ZIP·공식 사이트 HTML 사본은 제외한다.

## 글꼴

| 글꼴 | 제작자 | 라이선스 | 보관한 원문 |
|---|---|---|---|
| [Galmuri11](https://github.com/quiple/galmuri) Regular·Bold, 2.40.3 | 이민서(quiple) | SIL OFL 1.1 | [LICENSE.txt](fonts/LICENSE.txt) |

npm 패키지 `galmuri@2.40.3`의 `dist/`에서 `Galmuri11.ttf`, `Galmuri11-Bold.ttf`, `LICENSE.txt`를 수정 없이 복사했다. 다운로드 주소와 SHA-256은 [fonts/source.json](fonts/source.json)에 기록했다.

OFL은 소프트웨어와 함께 번들·재배포하는 것을 허용하며, 글꼴 파일만 단독으로 판매하는 것은 금지한다. 배포본에는 글꼴과 함께 `LICENSE.txt`를 포함한다.

제작자 README의 법적 고지에 따르면 Galmuri11 Regular의 일부 글리프(라틴-1, 일부 기호, 한글 음절 2,355자)는 Nintendo DS 글꼴 디자인을 바탕으로 했고, Galmuri11 Bold의 글리프는 모두 제작자의 창작물이다. 윤곽선 글꼴 파일은 제작자의 저작물로 OFL에 따라 배포된다.
