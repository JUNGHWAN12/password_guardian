# 패스워드 가디언 — 프로토타입 0.1

Python Arcade로 만든 오프라인 1인용 보안 체험 게임입니다. 임시 에셋으로 안내 → 보안 선택 → 3단계 전투 → 결과 → 시작 화면까지 플레이할 수 있습니다.

## 실행

현재 개발 PC에는 실행에 필요한 Arcade가 설치되어 있습니다. **`start_game.bat`를 더블클릭**하거나 프로젝트 폴더에서 실행하세요.

```powershell
python run_game.py
```

| 조작 | 동작 |
|---|---|
| Enter | 시작 화면에서 게임 시작 |
| 방향키 | 이동(초당 620px), 공격은 자동 발사 |
| Shift (누르는 동안) | 정밀 이동(초당 240px), 실제 피격 점 표시 |
| Space | 주변 탄환 제거, 기본 3회 |
| 1 / 2 또는 숫자패드 1 / 2 | 보안 선택 |
| Esc | 일시정지 / 재개, 재개 전 3초 안내. 30초가 지나면 자동 재개 |
| F11 | 전체 화면 전환 |
| 창 닫기 / Alt+F4 | 프로그램 종료 |

```powershell
python run_game.py --fullscreen
python run_game.py --practice
python run_game.py --data-dir .\runtime\local-play
```

`--practice`는 전체 게임을 동일하게 플레이하되 결과를 랭킹에 등록하지 않습니다. 기본 창은 1280×720이며 화면 내부는 1920×1080 좌표를 사용합니다. 창 크기를 바꿔도 종횡비를 유지하고 남는 영역에 여백을 둡니다. 창을 다른 프로그램으로 전환하면 게임과 타이머가 멈춥니다.

## 다른 PC에 설치

검증 환경은 Windows, Python **3.14.3**, Arcade **3.3.3**, NVIDIA RTX 3090입니다. Python 3.11 이상을 설치한 Windows PC에서 아래와 같이 별도 가상환경을 만들 수 있습니다. 다른 Python 버전·그래픽 환경은 실제 부스 PC에서 다시 확인하세요.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_game.py
```

첫 의존성 설치에는 인터넷이 필요합니다. 설치 후 플레이와 랭킹은 인터넷 없이 동작합니다. `run.ps1`과 `start_game.bat`는 `.venv`가 있으면 그 Python을 우선 사용합니다. 이미지·글꼴 경로는 실행 파일 위치를 기준으로 하므로 다른 폴더에서 실행해도 됩니다.

`src/`, `data/`, `assets/images/`, `assets/fonts/`, 실행 파일과 라이선스 문서를 함께 옮겨야 합니다. 한글은 함께 포함한 IBM Plex Sans KR 글꼴(SIL OFL 1.1)로 표시하므로 PC에 글꼴을 따로 설치하지 않아도 됩니다. EXE 패키징은 후속 작업입니다.

## 구현된 플레이

- 조작 연습 20초 + 본게임 180초 + 결과 40초. 일시정지와 시작 화면 대기 시간은 제외합니다.
- 각 단계는 선택·설명 8초와 전투 52초입니다. 6초 안에 선택하지 않으면 미선택으로 기록하고 정답을 설명합니다.
- 직선 공격 봇, 부채꼴 드론, 다방향 군단, 패턴이 바뀌는 보스가 등장합니다. 생성 시 테두리로 위치를 표시합니다.
- 보안 공격 적 6종이 단계마다 섞여 나옵니다. 1단계 비밀번호 스프레이 포대(한 비밀번호를 부채꼴로 쓸어 쏨)와 키로거 그림자(1.2초 전 위치를 노림), 2단계 트로이 선물 상자(열리기 전에 부수지 않으면 군단과 탄이 쏟아짐)·피싱 미끼선(아군처럼 보이다 정체를 드러냄)·어깨너머 감시자(노란 시야에 0.8초 머물면 쏨), 3단계 알림 폭탄 드론(로그인 승인 알림 8연발, 보스 처치 후 증원)과 어깨너머 감시자입니다. 판에서 처음 나올 때 전투 영역 위쪽에 이름과 보안 습관을 3초 동안 띄웁니다.
- 체력 소진 시 즉시 부활하고 100점 차감, 2초 무적을 적용합니다. 점수는 0 미만이 되지 않습니다.
- 무기는 1~4단계로, 단계가 오를수록 발사 수가 늘고 4단계에서 유도탄이 더해집니다. 맞거나 부활해도 단계는 유지됩니다.
- 정답마다 200점과 보호막·공격력·스킬 강화가 적용됩니다. 틀려도 진행하고 이전 강화는 유지합니다.
- 일반 적 50점, 보스 500점. 보스를 일찍 잡으면 약한 적이 이어서 등장하며 전체 진행 시간은 유지됩니다.
- 결과에는 점수·게임 등급·처치·부활·선택 기록·학습 메시지와 로컬 순위가 나옵니다.

기체 5종, 추가 적 6종과 배경 5장은 생성형 AI로 만든 이미지입니다. 효과음·음악은 아직 적용하지 않았습니다.

## 로컬 랭킹

기본 DB 위치:

```text
%LOCALAPPDATA%\PasswordGuardian\rankings.sqlite3
```

이름 입력 없이 `수호자-000001` 같은 참가 코드를 부여합니다. 완료한 게임만 저장하며 같은 사람의 재도전은 별도 기록입니다. 점수 → 정답 수 → 적은 부활 → 먼저 등록한 순서로 정렬하고, 현재 규칙 버전 `prototype-3`의 TOP 10과 이번 순위를 보여줍니다. 새 게임이나 앱 재시작으로 기록이 삭제되지 않습니다.

DB 접근은 별도 작업 스레드에서 수행합니다. 저장 실패 시 결과 점수·학습 메시지·자동 복귀는 유지되며 저장 실패 안내가 나옵니다. 손상된 DB는 자동 삭제하지 않습니다. 개발 검증에는 별도의 임시 DB를 사용하여 실제 랭킹에 테스트 점수를 섞지 않습니다.

앱을 종료한 뒤 백업합니다. 기존 파일이 없는 새 백업 경로를 지정해야 합니다.

```powershell
python run_game.py --backup .\runtime\ranking-backup-01.sqlite3
```

백업 검증 후 기록을 초기화하려면 아래 명령을 사용합니다. `--confirm-reset`과 `--backup`이 모두 있어야 실행됩니다. `--data-dir`로 운영했다면 같은 옵션을 추가하세요.

```powershell
python run_game.py --reset-rankings --backup .\runtime\before-reset-01.sqlite3 --confirm-reset
```

복원할 때는 앱을 종료하고 현재 DB를 먼저 백업한 다음, 백업 DB를 운영 DB 경로에 복사합니다. 다음 실행에서 TOP 10을 확인합니다. 프로토타입 규칙이 바뀌면 `config.py`의 규칙 버전도 올려 이전 기록과 분리합니다.

## 검증과 개발

```powershell
python -m unittest discover -s tests -v
python tools/smoke_test.py
```

첫 명령은 그래픽 창 없이 실행하는 규칙·DB 테스트 31개입니다. 두 번째는 실제 OpenGL 창을 보이지 않게 생성하여 240초 흐름을 10회 빠르게 시뮬레이션하고 화면을 캡처합니다. 약 40분의 실제 대기 시간을 측정하는 테스트는 아닙니다.

- 실행 기록: `runtime/smoke_report.json`
- 실제 렌더링 캡처: `runtime/screenshots/`
- 상세 검증 결과: [프로토타입 검증 기록](docs/PROTOTYPE_VALIDATION.md)

| 파일 | 역할 |
|---|---|
| `src/password_guardian/engine.py` | 타이머·웨이브·이동·탄막·충돌·부활 |
| `src/password_guardian/session.py` | 선택·점수·변경 불가능한 결과 데이터 |
| `src/password_guardian/app.py` | 화면·키보드 입력·SpriteList·창 크기 대응 |
| `src/password_guardian/rankings.py` | SQLite·백그라운드 저장·백업·초기화 |
| `data/choices.json`, `data/waves.json`, `data/attacks.json` | 보안 문항, 적 생성 시간표, 추가 적의 첫 등장 안내 문구 |
| `assets/images/sources.json` | 실제 사용한 임시 에셋의 원본·편집 내역 |
| `assets/fonts/` | 한글 글꼴 IBM Plex Sans KR 일반·굵게, 라이선스와 출처(`source.json`) |
| `assets/generated/` | 생성형 AI 기체·배경 원본과 출처(`source.json`) |

생성형 AI 원본(`assets/generated/`)에서 게임용 파일을 다시 만들 때는 `python tools/prepare_generated_assets.py`를 실행합니다. 기체는 생성 도구가 그려 넣은 가짜 체크무늬 배경과 'AI' 표시를 지우고 기체 경계로 잘라 표시 폭의 2배 크기 PNG로 저장합니다. 배경은 'AI' 표시가 있는 오른쪽 아래를 빼고(왼쪽 위 95%) 1920×1080 JPEG로 저장합니다. 이전 임시 에셋(`vault.png`, `player_bullet.png`)은 게임에서 쓰지 않으며 `python tools/prepare_prototype_assets.py`로 다시 만들 수 있습니다. 두 도구 모두 Pillow가 필요하며 게임 실행 시에는 필요하지 않습니다.

다음 개선 대상은 실제 초보 플레이어를 통한 난이도 조정, 최종 원화·배경·사운드, 부스 PC에서의 장시간 운영 확인입니다. 남은 작업의 우선순위와 순서는 [추후 구현계획서](추후_구현계획서.md)에 정리했습니다. 참조 문서는 [구현계획서](프로그램_구현계획서.md), [시각 제작 기준](assets/VISUAL_DIRECTION.md), [에셋 라이선스](assets/LICENSES.md)입니다.
