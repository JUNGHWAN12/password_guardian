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

프로토타입에서 실제 사용하는 이미지는 `assets/images/`에 있으며 [sources.json](images/sources.json)에 원본과 편집 내역을 기록했다. 기체 5종, 추가 적 5장과 배경 5장은 아래 ‘생성형 AI 이미지’다. 이전에 쓰던 Kenney 기체와 Kenney 타일 합성 배경(`images/vault.png`)은 게임에서 쓰지 않으며 `candidates/`와 함께 보관한다. 탄환·보호막·HUD는 프로젝트 코드로 렌더링한다(탄환 글자는 IBM Plex Sans KR). 게임 글꼴은 아래의 IBM Plex Sans KR을 사용한다.

`candidates/review/`의 추천 원본 PNG 13개는 원본을 그대로 복사했다. 배경 시안·기체 비교·화면 시안은 기존 소재를 프로젝트에서 합성한 파생 검토 자료다. 다운로드 주소와 ZIP 해시는 각 팩의 `source.json`, 선정 이미지 해시는 `review/selection.json`에 있다.

후보 비교 이미지(`tools/build_asset_review.py`)의 한글은 로컬 Windows의 맑은 고딕으로 렌더링했으며, 맑은 고딕 파일은 이 프로젝트에 복사하지 않았다. 실제 배포에서는 선택한 이미지와 해당 출처 문서만 포함하고 후보 ZIP·공식 사이트 HTML 사본은 제외한다.

## 글꼴

| 글꼴 | 제작자 | 라이선스 | 보관한 원문 |
|---|---|---|---|
| [IBM Plex Sans KR](https://github.com/IBM/plex) Regular·Bold, 1.1.0 | IBM Corp. | SIL OFL 1.1, 예약 글꼴 이름 "Plex" | [LICENSE.txt](fonts/LICENSE.txt) |

IBM 공식 GitHub 릴리스 `@ibm/plex-sans-kr@1.1.0`의 `ibm-plex-sans-kr.zip`에서 `fonts/complete/ttf/hinted/`의 `IBMPlexSansKR-Regular.ttf`, `IBMPlexSansKR-Bold.ttf`, `license.txt`를 수정 없이 복사했다. 다운로드 주소와 SHA-256은 [fonts/source.json](fonts/source.json)에 기록했다.

OFL은 소프트웨어와 함께 번들·재배포하는 것을 허용하며, 글꼴 파일만 단독으로 판매하는 것은 금지한다. 배포본에는 글꼴과 함께 `LICENSE.txt`를 포함한다. 글꼴을 수정(서브셋 포함)해 배포하면 예약 글꼴 이름 "Plex"를 쓸 수 없으므로, 현재처럼 원본 파일을 그대로 사용한다.

## 생성형 AI 이미지

| 파일 | 원본 | 도구 | 이용 조건 |
|---|---|---|---|
| `images/player.png`, `guess_bot.png`, `dictionary_drone.png`, `leaked_swarm.png`, `intruder.png` | [generated/](generated/)의 같은 이름 JPG | 확인 필요 | 확인 필요 |
| `images/keylogger.png`, `phishing_lure_disguise.png`, `phishing_lure.png`, `mfa_bomber.png`, `password_sprayer.png` | [generated/](generated/)의 같은 이름 WebP | 확인 필요 | 확인 필요 |
| `images/bg_title.jpg`, `bg_stage_1.jpg`, `bg_stage_2.jpg`, `bg_stage_3.jpg`, `bg_result.jpg` | [generated/](generated/)의 같은 이름 JPG·WebP | 확인 필요 | 확인 필요 |

2026-10-13에 받은 기체 5장(1024×1024 JPG), 추가 적 5장(같은 형식의 WebP)과 배경 5장(2000×1125 JPG·WebP)이다. 프롬프트는 [AI_IMAGE_PROMPTS.md](AI_IMAGE_PROMPTS.md) §3·§7과 [적군 추가 설계안](../적군_추가설계안.md) §7을 썼다. 원본 해시는 [generated/source.json](generated/source.json)에 있다. 원본에는 오른쪽 아래 ‘AI’ 표시가 있고, 기체 원본에는 가짜 투명 체크무늬 배경도 있다. `tools/prepare_generated_assets.py`가 기체를 잘라내거나 배경의 해당 모서리를 뺄 때 함께 지워진다.

- 사용한 도구·모델 이름과 그 이용 약관에서 교육·전시 사용이 허용되는지 확인해 위 표와 `generated/source.json`에 기록한다.
- 이미지 안의 ‘AI’ 표시를 지웠으므로, 생성형 AI 이미지를 사용했다는 사실은 README와 부스 안내물 등에 별도로 밝힌다. 도구 약관이 표시를 그대로 두도록 요구하면 그 조건을 따른다.
