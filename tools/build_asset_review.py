"""Build offline review artifacts from downloaded CC0 packs (requires Pillow)."""
from pathlib import Path
import hashlib
import html
import json
import shutil

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "assets/candidates"
REVIEW = CANDIDATES / "review"
REVIEW.mkdir(exist_ok=True)
FONT_PATH = Path("C:/Windows/Fonts/malgun.ttf")


def font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


items = [
    ("player", "보안 수호 기체", "space-shooter-remastered", "PNG/playerShip2_blue.png"),
    ("guess_bot", "반복 추측 봇", "space-shooter-extension", "PNG/Sprites X2/Ships/spaceShips_001.png"),
    ("dictionary_drone", "사전 공격 드론", "space-shooter-extension", "PNG/Sprites X2/Ships/spaceShips_003.png"),
    ("leaked_swarm", "유출 계정 군단", "space-shooter-extension", "PNG/Sprites X2/Ships/spaceShips_004.png"),
    ("intruder", "침입자 보스", "space-shooter-extension", "PNG/Sprites X2/Ships/spaceShips_005.png"),
    ("player_bullet", "아군 탄환", "space-shooter-remastered", "PNG/Lasers/laserBlue01.png"),
    ("enemy_bullet", "적 탄환 형태 검토용", "space-shooter-remastered", "PNG/Lasers/laserRed01.png"),
    ("shield", "보호막", "space-shooter-remastered", "PNG/Effects/shield3.png"),
    ("background_dark", "어두운 배경 타일", "space-shooter-remastered", "Backgrounds/black.png"),
    ("background_blue", "파란 배경 타일", "space-shooter-remastered", "Backgrounds/blue.png"),
    ("background_purple", "보라 배경 타일", "space-shooter-remastered", "Backgrounds/darkPurple.png"),
    ("rank_panel", "랭킹 패널 소재", "ui-pack-sci-fi", "PNG/Extra/Default/panel_glass.png"),
    ("health_bar", "체력 바 소재", "ui-pack-sci-fi", "PNG/Blue/Default/bar_square_large.png"),
]
records = []
for asset_id, role, pack, relative in items:
    source = CANDIDATES / pack / "pack" / relative
    destination = REVIEW / f"{asset_id}.png"
    shutil.copy2(source, destination)
    with Image.open(source) as im:
        dimensions = list(im.size)
    records.append({
        "id": asset_id, "role": role, "pack": pack,
        "source": source.relative_to(ROOT).as_posix(),
        "review_copy": destination.relative_to(ROOT).as_posix(),
        "size": dimensions, "license": "CC0-1.0", "modified": False,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    })
(REVIEW / "selection.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def sprite(canvas, path, center, bounds, pixel=False):
    im = Image.open(path).convert("RGBA")
    ratio = min(bounds[0] / im.width, bounds[1] / im.height)
    im = im.resize((round(im.width * ratio), round(im.height * ratio)),
                   Image.Resampling.NEAREST if pixel else Image.Resampling.LANCZOS)
    canvas.paste(im, (round(center[0] - im.width / 2), round(center[1] - im.height / 2)), im)


def tiled_background(name):
    tile = Image.open(REVIEW / name).convert("RGB")
    result = Image.new("RGB", (1920, 1080))
    for y in range(0, 1080, tile.height):
        for x in range(0, 1920, tile.width):
            result.paste(tile, (x, y))
    return result


# These are review compositions, not finished game backgrounds or screenshots.
bg = ImageEnhance.Brightness(tiled_background("background_dark.png")).enhance(0.42)
d = ImageDraw.Draw(bg)
for x in range(0, 1920, 96):
    d.line((x, 0, x, 1080), fill=(16, 32, 46), width=1)
for y in range(0, 1080, 96):
    d.line((0, y, 1920, y), fill=(16, 32, 46), width=1)
for inset in (120, 155):
    d.rounded_rectangle((inset, 160, 1920-inset, 960), radius=45, outline=(22, 55, 65), width=3)
d.regular_polygon((960, 510, 200), n_sides=8, rotation=22.5, outline=(27, 63, 74), width=4)
d.ellipse((845, 395, 1075, 625), outline=(27, 63, 74), width=4)
bg.save(REVIEW / "digital_vault_background_proposal.png")

scene = bg.copy()
d = ImageDraw.Draw(scene)
d.rounded_rectangle((45, 24, 1875, 126), radius=18, fill=(13, 25, 40), outline=(42, 80, 99), width=2)
d.text((75, 46), "PASSWORD GUARDIAN", font=font(32), fill="#eef8ff")
d.text((615, 52), "점수 1,250     보호막 2     스킬 3", font=font(25), fill="#79d4ed")
d.text((1410, 52), "에셋 배치 예시", font=font(25), fill="#ffcb8c")
sprite(scene, REVIEW / "player.png", (960, 885), (96, 80))
sprite(scene, REVIEW / "intruder.png", (960, 285), (260, 235))
for aid, centers in [("guess_bot", [(470, 340), (1450, 340)]),
                     ("dictionary_drone", [(650, 490), (1270, 490)]),
                     ("leaked_swarm", [(350, 650), (1550, 650)])]:
    for c in centers:
        sprite(scene, REVIEW / f"{aid}.png", c, (90, 82))
for y in (680, 735, 790):
    sprite(scene, REVIEW / "player_bullet.png", (960, y), (7, 28))
for x, y in [(780, 610), (860, 640), (1040, 640), (1120, 610), (510, 750), (1410, 750)]:
    d.ellipse((x-7, y-7, x+7, y+7), fill="#ffba66", outline="#fff0d7", width=2)
d.text((60, 1022), "임시 A · 확보한 기체 + 배치 검토 시안 / 최종 미술은 사용자 참고 보드 기준", font=font(25), fill="#aabccb")
scene.save(REVIEW / "recommended_scene.png")

board = Image.new("RGB", (1500, 620), "#0d1726")
d = ImageDraw.Draw(board)
d.text((32, 22), "임시 A | 플레이어와 적 역할별 후보", font=font(32), fill="white")
for i, (aid, role, pack, relative) in enumerate(items[:5]):
    x = 30 + i * 294
    d.rounded_rectangle((x, 95, x+278, 575), radius=16, fill="#19273a", outline="#32465c")
    sprite(board, REVIEW / f"{aid}.png", (x+139, 263), (225, 240))
    record = records[i]
    d.text((x+15, 425), role, font=font(23), fill="#edf7ff")
    d.text((x+15, 470), Path(relative).stem, font=font(17), fill="#8dd9ef")
    d.text((x+15, 505), f"{record['size'][0]} × {record['size'][1]} PNG", font=font(18), fill="#a6b5c7")
board.save(REVIEW / "recommended_characters.png")

background_board = Image.new("RGB", (1600, 680), "#0d1726")
d = ImageDraw.Draw(background_board)
d.text((25, 16), "배경 후보 | 원본 타일 3종과 디지털 금고 합성 시안", font=font(30), fill="white")
for i, (filename, label) in enumerate([
    ("background_dark.png", "원본 · Black / 256×256 반복"),
    ("background_blue.png", "원본 · Blue / 256×256 반복"),
    ("background_purple.png", "원본 · Dark purple / 256×256 반복"),
    ("digital_vault_background_proposal.png", "임시 · 회로 격자 + 금고 시안 / 1920×1080"),
]):
    x = 20 + (i % 2) * 800
    y = 80 + (i // 2) * 300
    im = tiled_background(filename) if i < 3 else bg
    im = im.resize((760, 245), Image.Resampling.LANCZOS)
    background_board.paste(im, (x, y))
    d.text((x, y+251), label, font=font(20), fill="#b9d0e4")
background_board.save(REVIEW / "background_candidates.jpg")

packs = [
    ("space-shooter-remastered", "A 추천 · 기본 기체 / 탄환 / 배경", "파란 플레이어와 배경 타일을 사용합니다."),
    ("space-shooter-extension", "A 추천 · 적 / 보스", "붉은 적 3종과 대형 보스 후보를 선택했습니다."),
    ("simple-space", "B 대안 · 단순한 실루엣", "128px Retina 기체. 색상 적용과 별도 배경 구성이 필요합니다."),
    ("pixel-shmup", "C 대안 · 픽셀 아케이드", "32px 기체와 16px 지형 타일. 전체 화면을 픽셀 스타일로 통일할 때 적합합니다."),
    ("ui-pack-sci-fi", "보조 · HUD / 로컬 랭킹", "패널과 체력 바 소재. 한글은 별도 UI 텍스트로 표시합니다."),
]
cards = []
for slug, title, note in packs:
    meta = json.loads((CANDIDATES / slug / "source.json").read_text(encoding="utf-8"))
    cards.append(f'<article><h3>{html.escape(title)}</h3><a href="{slug}/preview.png"><img src="{slug}/preview.png" alt="{slug}"></a><p>{html.escape(note)}</p><p><a href="{meta["page_url"]}">공식 출처</a> · <a href="{slug}/original.zip">원본 ZIP</a> · CC0</p></article>')
gallery = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>패스워드 가디언 에셋 후보</title><style>body{background:#0b1422;color:#e3eefb;font:17px/1.7 system-ui,sans-serif;margin:0}main{max-width:1280px;margin:auto;padding:40px 24px}h1{font-size:36px}h2{margin-top:48px}a{color:#88dafa}p{color:#b9cce1}img{max-width:100%;height:auto;border-radius:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}article{background:#17263a;border:1px solid #2c425c;padding:20px;border-radius:16px}article img{max-height:400px;display:block;margin:auto}.tag{color:#6ae0c0}</style><main><p class="tag">PASSWORD GUARDIAN / ASSET REVIEW</p><h1>에셋 후보와 추천 조합</h1><p>2026-10-12 · 5개 팩 다운로드 및 동봉 CC0 라이선스 확인. 추천 A는 Space Shooter 계열입니다. 아래 합성 이미지는 에셋 배치 검토용이며 실제 게임 화면이 아닙니다.</p><h2>추천 A · 역할별 기체</h2><a href="review/recommended_characters.png"><img src="review/recommended_characters.png" alt="추천 기체 5종"></a><h2>추천 A · 화면 적용 시안</h2><a href="review/recommended_scene.png"><img src="review/recommended_scene.png" alt="디지털 금고와 기체 배치 시안"></a><p>기체·배경 타일은 확보한 Kenney 원본, 회로 격자·금고 도형·HUD·원형 적 탄환은 비교용 코드 합성입니다. 보안 문양과 최종 화면은 후속 편집 대상입니다.</p><h2>배경 비교</h2><a href="review/background_candidates.jpg"><img src="review/background_candidates.jpg" alt="배경 후보 4종"></a><h2>확보한 팩</h2><div class="grid">''' + "".join(cards) + '''</div><p>모든 미리보기는 로컬에서 열립니다. 공식 출처 링크만 인터넷 연결이 필요합니다.</p></main></html>'''
gallery = gallery.replace("A 추천", "A 임시 구현용").replace("추천 A", "임시 A")
gallery = gallery.replace("추천 조합", "임시 구현 조합")
gallery = gallery.replace("<h1>에셋 후보와 임시 구현 조합</h1>", '<h1>에셋 후보와 임시 구현 조합</h1><article><h2>최종 미술 참고 방향</h2><p>사용자 첨부 보드의 금속 질감·청록 조명·디지털 금고를 기준으로 합니다. 플레이어는 청록, 적은 주황·보라, 보스는 붉은 코어로 구분합니다. 아래 확보한 Kenney 조합은 기능 검증용 임시 소재이며, 보드 화풍의 완성 에셋은 아직 미확보입니다.</p><a href="../VISUAL_DIRECTION.md">시각 제작 기준</a></article>')
(CANDIDATES / "index.html").write_text(gallery, encoding="utf-8")
print(f"Created {len(records)} source-verified selections, 4 review images, and offline gallery.")
