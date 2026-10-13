# 에셋 확보·선정 목록

확인일: 2026-10-12. 상세 선정 이유는 [에셋 후보군](../에셋_후보군.md), 이미지 비교는 [갤러리](candidates/index.html)를 참고한다.

게임은 `assets/images/`의 기체 5종과 배경 5장(생성형 AI 이미지, 2026-10-13 적용)을 사용한다. 원본은 `generated/`, 변환 도구는 `tools/prepare_generated_assets.py`다. 이전 임시 에셋 `vault.png`(배경)와 `player_bullet.png`(레이저)는 쓰지 않는다. 실제 원본 경로와 편집 내역은 [게임 사용 에셋 목록](images/sources.json)에 기록했다. 이전에 쓰던 Kenney 기체와 원본 후보는 `candidates/`에 그대로 둔다. 탄환은 `assets.py`에서 코드로 그린다. 플레이어는 자물쇠, 적은 공격 의미에 따라 반복 추측 봇은 `?`, 사전 공격 드론은 사전, 유출 계정 군단은 열쇠를 쏘고 보스는 세 가지를 섞는다. 보호막, HUD도 코드로 그린다.

사용자 첨부 보드를 반영한 [시각 제작 기준](VISUAL_DIRECTION.md)을 최종 미술의 기준으로 사용한다. 아래 A안은 임시 구현용 추천이었다. 보드 화풍의 기체 5종과 배경 5장은 생성형 AI로 확보했고, 효과/아이콘 4종을 후속 제작 대상으로 관리한다. 탄환 4종은 코드로 그린다.

## 원본 팩

| 팩 ID | 출처·다운로드 증빙 | 원본 라이선스 | 상태 |
|---|---|---|---|
| `space-shooter-remastered` | [source.json](candidates/space-shooter-remastered/source.json) | [license.txt](candidates/space-shooter-remastered/pack/license.txt) | 확보·열람 완료, A안 추천 |
| `space-shooter-extension` | [source.json](candidates/space-shooter-extension/source.json) | [License.txt](candidates/space-shooter-extension/pack/License.txt) | 확보·열람 완료, A안 추천 |
| `simple-space` | [source.json](candidates/simple-space/source.json) | [License.txt](candidates/simple-space/pack/License.txt) | 확보·열람 완료, B안 |
| `pixel-shmup` | [source.json](candidates/pixel-shmup/source.json) | [License.txt](candidates/pixel-shmup/pack/License.txt) | 확보·열람 완료, C안 |
| `ui-pack-sci-fi` | [source.json](candidates/ui-pack-sci-fi/source.json) | [License.txt](candidates/ui-pack-sci-fi/pack/License.txt) | 확보·열람 완료, 보조 소재 |

## 추천 파일

아래는 원본 비교를 위한 임시 구현용 사본이다. 이 중 플레이어·적·보스·아군 탄환은 별도 게임 사용본으로 복사·편집하여 프로토타입에 연결했다. A안 추천 표시는 임시 구현에 대한 추천이다. 원본 경로, 크기, SHA-256은 [selection.json](candidates/review/selection.json)에 기록했다.

| 에셋 ID | 파일 | 용도·상태 |
|---|---|---|
| `player` | [player.png](candidates/review/player.png) | 플레이어, 문양 편집 예정 |
| `guess_bot` | [guess_bot.png](candidates/review/guess_bot.png) | 일반 적: 반복 추측 봇 |
| `dictionary_drone` | [dictionary_drone.png](candidates/review/dictionary_drone.png) | 일반 적: 사전 공격 드론 |
| `leaked_swarm` | [leaked_swarm.png](candidates/review/leaked_swarm.png) | 일반 적: 유출 계정 군단 |
| `intruder` | [intruder.png](candidates/review/intruder.png) | 보스 역할로 선정 |
| `player_bullet` | [player_bullet.png](candidates/review/player_bullet.png) | 아군 탄환 |
| `enemy_bullet` | [enemy_bullet.png](candidates/review/enemy_bullet.png) | 적 탄환 형태 검토용 |
| `shield` | [shield.png](candidates/review/shield.png) | 보호막 |
| `background_dark` | [background_dark.png](candidates/review/background_dark.png) | 256×256 원본 타일 |
| `background_blue` | [background_blue.png](candidates/review/background_blue.png) | 256×256 원본 타일 |
| `background_purple` | [background_purple.png](candidates/review/background_purple.png) | 256×256 원본 타일 |
| `rank_panel` | [rank_panel.png](candidates/review/rank_panel.png) | 랭킹 패널 소재, 9분할 적용 검토 |
| `health_bar` | [health_bar.png](candidates/review/health_bar.png) | 체력 바 소재 |

## 파생 검토 이미지

| 파일 | 제작 방식 | 상태 |
|---|---|---|
| [digital_vault_background_proposal.png](candidates/review/digital_vault_background_proposal.png) | Kenney black 타일 반복·밝기 조정 + 프로젝트에서 그린 회로·금고 도형 | 1920×1080 배경 시안 |
| [recommended_scene.png](candidates/review/recommended_scene.png) | 배경 시안 + 확보한 기체·아군 탄환 + 코드로 그린 UI·적 탄환 | 배치 검토용, 실행 화면 아님 |
| [recommended_characters.png](candidates/review/recommended_characters.png) | 기체 사본·파일명·규격 비교 | 후보 비교용 |
| [background_candidates.jpg](candidates/review/background_candidates.jpg) | 원본 타일 3종과 합성 시안 비교 | 후보 비교용 |

위 파생물은 원본 이미지와 분리되어 있다. 최종 에셋 편집 시 원본 경로·편집 내용·사용 위치를 이 목록에 추가한다.

## 글꼴

| 에셋 ID | 파일 | 용도·상태 |
|---|---|---|
| `font_regular` | [IBMPlexSansKR-Regular.ttf](fonts/IBMPlexSansKR-Regular.ttf) | 본문·숫자, 게임 적용 |
| `font_bold` | [IBMPlexSansKR-Bold.ttf](fonts/IBMPlexSansKR-Bold.ttf) | 제목·강조, 게임 적용 |

출처·해시는 [fonts/source.json](fonts/source.json), 이용 조건은 [LICENSE.txt](fonts/LICENSE.txt)와 [LICENSES.md](LICENSES.md)를 따른다.
