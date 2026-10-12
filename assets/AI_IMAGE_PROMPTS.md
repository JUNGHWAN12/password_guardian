# 기체 이미지 생성형 AI 프롬프트

작성일: 2026-10-12. 플레이어 기체 1종과 적 4종(반복 추측 봇, 사전 공격 드론, 유출 계정 군단, 보스 ‘침입자’)을 생성형 AI로 제작할 때 쓰는 프롬프트다. 색·형태·문양은 [시각 제작 기준](VISUAL_DIRECTION.md) §2·§4를 따르고, 탄환 디자인(자물쇠, `?`, 사전, 열쇠)과 의미가 이어지도록 했다.

프롬프트는 대부분의 이미지 생성 도구에서 결과가 안정적인 영어로 작성했다. ChatGPT·Gemini처럼 한국어를 이해하는 도구에도 그대로 붙여 넣으면 된다.

## 1. 제작 순서

1. **플레이어 기체를 먼저 만든다.** 마음에 드는 결과를 고르면 그 이미지를 이후 모든 적 기체의 스타일 참고 이미지로 첨부한다(ChatGPT·Gemini는 이미지 첨부 후 “같은 화풍으로”, Midjourney는 `--sref`, Stable Diffusion은 IP-Adapter·img2img).
2. 기체마다 4장 이상 생성해 비교한다. 정사각형(1:1), 1024×1024 이상으로 만든다.
3. 고른 이미지를 §4 점검표로 확인한 뒤 §5 후처리를 거쳐 게임에 넣는다.
4. 사용한 도구·모델·날짜·프롬프트·시드를 §6에 따라 기록한다.

투명 배경을 직접 출력하는 도구(예: 투명 배경 옵션이 있는 이미지 모델)는 그 옵션을 켠다. 지원하지 않으면 프롬프트의 배경 지시를 단색 배경으로 바꾸고 후처리에서 배경을 지운다.

## 2. 공통 스타일

아래 문장은 각 프롬프트 끝에 이미 포함되어 있다. 도구가 별도의 스타일 입력란을 제공하면 이 부분만 그곳에 넣어도 된다.

```text
2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

투명 배경을 지원하지 않는 도구는 마지막 줄의 `Plain transparent background`를 `Plain flat solid pure green (#00FF00) background`로 바꾼다. 초록은 다섯 기체 어디에도 쓰지 않는 색이라 배경을 지우기 쉽다.

## 3. 기체별 프롬프트

모든 적은 플레이어 쪽인 **아래를 향한다**. 플레이어만 **위를 향한다**.

### 3.1 플레이어 ‘보안 수호 기체’ (`player.png`)

흰색·회색 장갑과 청록 조명, 방패를 반으로 나눈 듯한 좌우 날개, 중앙의 자물쇠 문양. 보호하는 영웅 기체의 인상을 준다.

```text
Player spaceship named "Security Guardian", nose pointing straight up. White and light grey armor plates with cyan teal light strips. Two wide wings shaped like a heater shield split down the middle, one on each side. A clear padlock emblem in the center of the hull, softly glowing cyan. Two short engines at the bottom with small cyan exhaust flames. Friendly, protective, heroic feel. 2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

### 3.2 반복 추측 봇 (`guess_bot.png`)

길쭉하고 단순한 회색 동체, 좁은 좌우 장갑, 주황색 포구 하나와 둥근 주황 감지 눈. 같은 동작을 반복하는 기계의 인상을 준다. `?` 탄환을 쏜다.

```text
Enemy spaceship named "Repeat-Guess Bot", nose pointing straight down toward the player. A long, simple, narrow grey hull like a drill or a battering ram, with narrow armor plates on both sides. One single cannon at the front tip with an orange glowing muzzle, and one round orange sensor eye on the hull. Orange accent lights. Mechanical, repetitive, robotic feel, compact shape. 2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

### 3.3 사전 공격 드론 (`dictionary_drone.png`)

펼친 책장처럼 넓게 퍼진 부채꼴 날개, 날개 앞쪽을 따라 부채꼴로 놓인 포구 5개, 어두운 장갑과 보라색 발광. 사전 탄환을 부채꼴로 쏜다.

```text
Enemy spaceship named "Dictionary Attack Drone", nose pointing straight down toward the player. Very wide fan-shaped wings spread like the pages of an open book, clearly wider than tall. Five small cannons spaced along the front edge of the wings in a fan arrangement. Dark gunmetal armor with violet purple glowing lights and purple muzzles. 2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

### 3.4 유출 계정 군단 (`leaked_swarm.png`)

작고 각진 세 갈래 삼각형 실루엣, 주황색 장갑 끝, 중앙의 연결 고리 문양. 여러 기가 함께 등장하므로 아주 작게 보여도 형태가 읽혀야 한다. 열쇠 탄환을 쏜다.

```text
Small enemy spaceship named "Leaked Account Swarm" unit, nose pointing straight down toward the player. Small, angular, three-pronged triangular silhouette like a sharp arrowhead with three points. Dark armor with bright orange tips, and a chain-link emblem in the center glowing orange. Light and agile, designed to appear in groups. Extremely simple shape that is still recognizable at a tiny size. 2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

### 3.5 보스 ‘침입자’ (`intruder.png`)

넓고 날카로운 검은 장갑, 붉은 경계광, 중앙의 큰 붉은 원형 코어. 코어를 열쇠 구멍 모양으로 해 ‘금고를 노리는 침입자’를 표현한다. 학생 대상이므로 위협적이되 잔인한 표현은 넣지 않는다.

```text
Large boss spaceship named "Intruder", nose pointing straight down toward the player. A wide, heavy warship with sharp, angular, blade-like black armor plates and thin red edge lights. One large circular red core in the center, shaped like a glowing keyhole, the brightest point of the ship. Menacing and powerful but not gory, suitable for a student audience. More detailed and imposing than the smaller enemies, yet still a clear silhouette. 2D game sprite for a top-down shoot 'em up, strict top-down orthographic view looking straight down, no perspective tilt. One single spaceship, perfectly centered and symmetrical. Bold, readable silhouette that stays clear when shrunk to 64 pixels: a few large shapes, limited small details. Sci-fi "digital vault security" theme: dark gunmetal armor with crisp panel lines, small mechanical parts, restrained glow lights. Polished semi-realistic painted game art with soft metallic shading and clean edges. Plain transparent background, no shadow, no scenery, no stars, no text, no letters, no logo, no watermark, no frame.
```

### 3.6 제외 프롬프트

Stable Diffusion처럼 제외 프롬프트(negative prompt) 입력란이 있는 도구에 넣는다.

```text
perspective, three-quarter view, side view, isometric, tilted, cropped, cut off, multiple ships, duplicate, asymmetrical, background, scenery, stars, planet, ground shadow, drop shadow, text, letters, numbers, logo, watermark, signature, frame, border, blurry, low contrast, photograph, cluttered tiny details, heavy glow, lens flare, smoke, explosion, gore
```

## 4. 고르기 전 점검표

- 실제 게임 크기(아래 표의 표시 폭)로 줄여도 기체 종류가 구분되는가. 흑백으로 바꿔도 모양으로 구분되는가.
- 위에서 내려다본 시점인가. 기울어진 3D 시점이나 측면이 섞이지 않았는가.
- 플레이어는 위, 적은 아래를 향하는가. 좌우 대칭인가.
- 색 역할이 맞는가: 플레이어 청록·흰색, 봇·군단 주황, 드론 보라, 보스 검정·빨강. 적 탄환(주황 `?`, 보라 사전, 빨간 열쇠)보다 기체가 어둡고, 탄환이 먼저 눈에 띄는가.
- 글자·로고·워터마크가 섞이지 않았는가.
- 충돌 원 안이 기체 몸통으로 채워지는가. 충돌 원은 기체 중앙에 있으며, 날개 끝·추진광은 원 밖이어도 된다.

| 기체 | 게임 표시 폭 | 충돌 반지름 | 몸통이 채워야 할 중앙 원 |
|---|---:|---:|---|
| 플레이어 | 88px | 18px | 지름 36px, 표시 폭의 약 40% |
| 반복 추측 봇 | 78px | 25px | 지름 50px, 약 64% |
| 사전 공격 드론 | 108px | 31px | 지름 62px, 약 57% |
| 유출 계정 군단 | 58px | 21px | 지름 42px, 약 72% |
| 보스 ‘침입자’ | 240px | 95px | 지름 190px, 약 79% |

표시 폭은 `src/password_guardian/app.py`의 `widths`, 충돌 반지름은 `engine.py`에 있다. 몸통이 원보다 많이 작으면 빈 곳에 맞아도 피격되어 불공정하게 느껴지므로, 그림을 고치거나 충돌 반지름을 줄인다. 충돌 반지름을 바꾸면 `config.py`의 `RULESET`을 올린다.

## 5. 후처리와 게임 적용

1. 배경을 지운다(투명 배경으로 출력했다면 생략). 가장자리에 남은 초록·흰색 테두리가 없는지 확대해 확인한다.
2. **기체 경계에 맞춰 잘라낸다(여백 0~2px).** 게임은 이미지의 폭을 위 표의 표시 폭에 맞춰 줄이므로, 여백이 있으면 화면에서 기체가 그만큼 작아진다. 현재 임시 이미지도 모두 여백 없이 잘려 있다.
3. 원본 비율을 유지한 채 가로 폭을 표시 폭의 2배 안팎으로 줄여 저장한다(플레이어 176px, 봇 156px, 드론 216px, 군단 116px, 보스 480px). 정사각형으로 늘리지 않는다. 너무 크게 두면 게임에서 줄일 때 가장자리가 거칠어질 수 있다. 작업 원본(1024px 이상)은 별도 보관한다.
4. RGBA PNG로 `assets/images/`의 같은 이름 파일(`player.png`, `guess_bot.png`, `dictionary_drone.png`, `leaked_swarm.png`, `intruder.png`)을 교체한다. 코드 수정 없이 게임에 반영된다.
5. `python tools/smoke_test.py`를 실행하고 `runtime/screenshots/`의 전투 화면에서 크기·대비·탄환 식별을 확인한다.

## 6. 출처 기록

- `assets/images/sources.json`에서 교체한 파일의 항목을 `tool`(도구·모델명과 버전), `created`(생성일), `prompt`(사용한 프롬프트 전문), `seed`(있으면), `edit`(배경 제거·자르기 등 후처리), `sha256`으로 갱신한다.
- `assets/LICENSES.md`에 사용한 도구와 그 이용 약관에서 확인한 사용 범위(교육·전시 사용 가능 여부)를 기록한다. `ASSET_MANIFEST.md`의 해당 행 상태도 바꾼다.
- 특정 작품·브랜드·작가 이름을 프롬프트에 넣지 않는다. 다른 저작물을 닮은 결과가 나오면 쓰지 않는다.
- 외형만 바꾸면 규칙 버전(`RULESET`)은 그대로 둔다. 충돌 반지름이나 표시 크기를 바꿀 때만 올린다.
