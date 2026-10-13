"""Turn the generative-AI images in assets/generated/ into game assets.

Ships: the generator baked a fake transparency checkerboard and an "AI" mark
into opaque JPGs. This removes both, keys the player's engine flames by their
cyan strength, trims each ship to its outline and resizes it for the game.

Backgrounds: drops the bottom-right corner that holds the "AI" mark and
resizes to 1920x1080.
"""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/generated"
TARGET = ROOT / "assets/images"
# Output width is twice the in-game display width (app.py `widths`).
SHIPS = {"player": 152, "guess_bot": 60, "dictionary_drone": 220, "leaked_swarm": 128, "intruder": 400}
FLAME_FROM = {"player": 862}  # rows below the nozzles hold engine flames drawn over the checkerboard
BADGE = (925, 935, 1023, 1023)  # the generator's "AI" mark, bottom right
BACKGROUNDS = {"bg_title": "bg_title.jpg", "bg_stage_1": "bg_stage_1.webp", "bg_stage_2": "bg_stage_2.webp",
               "bg_stage_3": "bg_stage_3.webp", "bg_result": "bg_result.webp"}
BG_SIZE = (1920, 1080)
BG_KEEP = 0.95  # keep the top-left 95%; the "AI" mark sits in the last 4% at the bottom right
BG_MIN, BG_CHROMA = 185, 24  # checkerboard squares are near-white and light grey
CHECKER_GREY = 233  # mean of the white and grey squares
CYAN_FULL = 120  # cyan strength of a fully opaque flame
HOT_FULL = 16  # brightness above the averaged checkerboard of the white-hot flame root


def _channels(im):
    r, g, b = im.split()
    hi = ImageChops.lighter(ImageChops.lighter(r, g), b)
    lo = ImageChops.darker(ImageChops.darker(r, g), b)
    return lo, ImageChops.subtract(hi, lo)


def _components(mask, value):
    """Yield (seed, component mask) for each region of `value` pixels; marks them visited."""
    px = mask.load()
    w, h = mask.size
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if px[x, y] == value:
                ImageDraw.floodfill(mask, (x, y), 77, thresh=0)
                yield (x, y), mask.point(lambda v: 255 if v == 77 else 0)
                ImageDraw.floodfill(mask, (x, y), 1, thresh=0)


def _square_size(gray):
    """Checkerboard square size, measured along the top row where the squares are bare."""
    row = [gray.getpixel((x, 3)) for x in range(gray.width // 4)]
    edges = [x for x in range(1, len(row)) if abs(row[x] - row[x - 1]) > 20]
    gaps = sorted(b - a for a, b in zip(edges, edges[1:]))
    return gaps[len(gaps) // 2]


def background(im):
    """Return an alpha mask: 0 for checkerboard (outside or enclosed) and the AI mark, 255 for the ship."""
    lo, chroma = _channels(im)
    mask = ImageChops.multiply(lo.point(lambda v: 255 if v >= BG_MIN else 0),
                               chroma.point(lambda v: 255 if v <= BG_CHROMA else 0))
    ImageDraw.Draw(mask).rectangle(BADGE, fill=255)
    w, h = mask.size
    px = mask.load()
    for p in [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]:
        if px[p] == 255:
            ImageDraw.floodfill(mask, p, 128, thresh=0)
    # Light regions enclosed by the hull: one square away, checkerboard flips between white and
    # grey while painted armour barely changes.
    gray = im.convert("L")
    size = _square_size(gray)
    shifts = [(size, 0), (0, size)]
    flips = [ImageChops.difference(gray, ImageChops.offset(gray, dx, dy)) for dx, dy in shifts]
    pockets = []
    for seed, comp in _components(mask, 255):
        total = count = 0
        for (dx, dy), flip in zip(shifts, flips):
            inside = ImageChops.multiply(comp, ImageChops.offset(comp, dx, dy))  # both pixels in the region
            hist = flip.histogram(mask=inside)
            total += sum(v * c for v, c in enumerate(hist))
            count += sum(hist)
        if count > 150 and total / count > 20:
            pockets.append(seed)
    for seed in pockets:
        ImageDraw.floodfill(mask, seed, 128, thresh=0)
    alpha = mask.point(lambda v: 0 if v == 128 else 255)
    return alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))  # drop specks


def keep_ship(alpha):
    """Drop detached background streaks: keep parts at least 1.5% of the largest part."""
    mask = alpha.point(lambda v: 255 if v > 8 else 0)  # semi-transparent flames count as part of the ship
    parts = [(comp.histogram()[255], comp) for _, comp in _components(mask, 255)]
    largest = max(n for n, _ in parts)
    keep = Image.new("L", alpha.size, 0)
    for n, comp in parts:
        if n >= largest * 0.015:
            keep = ImageChops.lighter(keep, comp)
    return ImageChops.multiply(alpha, keep)


def key_flames(im, alpha, top):
    """Below `top`, rebuild the alpha from cyan strength and white-hot brightness over the averaged checkerboard."""
    w, h = im.size
    box = (0, top, w, h)
    zone = im.crop(box).filter(ImageFilter.BoxBlur(12))  # average out the 12 px squares
    r, g, b = zone.split()
    cyan = ImageChops.subtract(ImageChops.add(g, b, scale=2), r).point(lambda v: min(255, v * 255 // CYAN_FULL))
    hot = zone.convert("L").point(lambda v: min(255, max(0, v - CHECKER_GREY - 3) * 255 // HOT_FULL))
    flame_alpha = ImageChops.lighter(cyan, hot).point(lambda v: 0 if v < 24 else v)  # drop residue
    hull = alpha.crop((0, 0, w, top)).getbbox()
    columns = Image.new("L", flame_alpha.size, 0)
    ImageDraw.Draw(columns).rectangle((hull[0], 0, hull[2], flame_alpha.height), fill=255)
    flame_alpha = ImageChops.multiply(flame_alpha, columns)  # flames stay under the hull
    # Un-blend the colour from the averaged checkerboard behind it.
    pixels = [tuple(max(0, min(255, round((c - (1 - a / 255) * CHECKER_GREY) / max(a / 255, 0.05)))) for c in rgb)
              for rgb, a in zip(zone.getdata(), flame_alpha.getdata())]
    zone.putdata(pixels)
    im = im.copy()
    im.paste(zone, box)
    alpha = alpha.copy()
    alpha.paste(flame_alpha, box)
    return im, alpha


def prepare():
    meta = json.loads((SOURCE / "source.json").read_text(encoding="utf-8"))
    records = [r for r in json.loads((TARGET / "sources.json").read_text(encoding="utf-8"))
               if Path(r["file"]).stem not in SHIPS and Path(r["file"]).stem not in BACKGROUNDS]
    for name, width in SHIPS.items():
        src = SOURCE / f"{name}.jpg"
        im = Image.open(src).convert("RGB")
        alpha = keep_ship(background(im))
        alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))  # trim light fringe
        if name in FLAME_FROM:
            im, alpha = key_flames(im, alpha, FLAME_FROM[name])
            alpha = keep_ship(alpha)
        sprite = im.convert("RGBA")
        sprite.putalpha(alpha)
        sprite = sprite.crop(alpha.point(lambda v: 255 if v > 8 else 0).getbbox())
        height = round(sprite.height * width / sprite.width)
        sprite = sprite.convert("RGBa").resize((width, height), Image.LANCZOS).convert("RGBA")
        dest = TARGET / f"{name}.png"
        sprite.save(dest, optimize=True)
        records.append({"file": dest.relative_to(ROOT).as_posix(), "original": src.relative_to(ROOT).as_posix(),
                        "tool": meta["tool"], "license": meta["license"],
                        "edit": f"checkerboard background and AI mark removed, trimmed, resized to {width}x{height}",
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
        print(f"{dest.relative_to(ROOT)}: {width}x{height}")
    for name, file in BACKGROUNDS.items():
        src = SOURCE / file
        im = Image.open(src).convert("RGB")
        keep = (0, 0, round(im.width * BG_KEEP), round(im.height * BG_KEEP))
        dest = TARGET / f"{name}.jpg"  # the originals are lossy already; PNG would only triple the size
        im.crop(keep).resize(BG_SIZE, Image.LANCZOS).save(dest, quality=95, subsampling=0)
        records.append({"file": dest.relative_to(ROOT).as_posix(), "original": src.relative_to(ROOT).as_posix(),
                        "tool": meta["tool"], "license": meta["license"],
                        "edit": f"cropped to {keep[2]}x{keep[3]} from the top left to drop the AI mark, resized to 1920x1080",
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
        print(f"{dest.relative_to(ROOT)}: 1920x1080")
    (TARGET / "sources.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    prepare()
