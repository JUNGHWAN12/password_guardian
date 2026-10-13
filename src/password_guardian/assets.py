from PIL import Image, ImageDraw, ImageFont
import arcade
from .config import ROOT

FONT_FILES = ("IBMPlexSansKR-Regular.ttf", "IBMPlexSansKR-Bold.ttf")


def load_fonts():
    for name in FONT_FILES:
        path = ROOT / "assets/fonts" / name
        if not path.exists():
            raise FileNotFoundError(f"글꼴이 없습니다: {path}")
        arcade.load_font(path)


# Each attack fires what it stands for. Bullets are drawn at 1920x1080 screen size.
ORANGE, PURPLE, RED, CYAN = (255, 154, 48), (196, 120, 255), (255, 96, 120), (77, 221, 228)
INK = (18, 10, 26)
SS = 4  # supersampling for smooth edges


def _font(size):
    return ImageFont.truetype(str(ROOT / "assets/fonts" / FONT_FILES[1]), size * SS)


def _texture(im, key):
    w, h = im.size
    return arcade.Texture(im.resize((w // SS, h // SS), Image.LANCZOS), hash=f"guardian-{key}-v2")


def _canvas(w, h):
    im = Image.new("RGBA", (w * SS, h * SS))
    return im, ImageDraw.Draw(im)


def _label(draw, box, text, size, ink=INK):
    font = _font(size)
    left, top, right, bottom = font.getbbox(text)
    x0, y0, x1, y1 = box
    draw.text(((x0 + x1 - (right - left)) / 2 - left, (y0 + y1 - (bottom - top)) / 2 - top), text, font=font, fill=ink)


def _padlock():
    im, d = _canvas(18, 22)
    s = SS
    d.arc((4 * s, 1 * s, 14 * s, 13 * s), 180, 360, fill=CYAN, width=3 * s)
    d.line((4 * s + s, 7 * s, 4 * s + s, 10 * s), fill=CYAN, width=3 * s)
    d.line((14 * s - 2 * s, 7 * s, 14 * s - 2 * s, 10 * s), fill=CYAN, width=3 * s)
    d.rounded_rectangle((1 * s, 9 * s, 17 * s, 21 * s), radius=3 * s, fill=CYAN, outline=(225, 255, 255), width=s)
    d.ellipse((7 * s, 12 * s, 11 * s, 16 * s), fill=INK)
    d.rectangle((8 * s, 15 * s, 10 * s, 19 * s), fill=INK)
    return im


def _bubble(text, fill):
    im, d = _canvas(26, 26)
    d.ellipse((SS, SS, 25 * SS, 25 * SS), fill=fill, outline=(255, 255, 255, 170), width=2 * SS)
    _label(d, (0, 0, 26 * SS, 26 * SS), text, 17)
    return im


def _book(fill):
    im, d = _canvas(30, 24)
    s = SS
    d.rounded_rectangle((1 * s, 2 * s, 29 * s, 22 * s), radius=3 * s, fill=fill, outline=(255, 255, 255, 170), width=2 * s)
    d.line((15 * s, 3 * s, 15 * s, 21 * s), fill=INK, width=2 * s)
    _label(d, (1 * s, 2 * s, 15 * s, 22 * s), "A", 13)
    _label(d, (15 * s, 2 * s, 29 * s, 22 * s), "가", 12)
    return im


def _key(fill):
    im, d = _canvas(38, 22)
    s = SS
    d.ellipse((1 * s, 2 * s, 19 * s, 20 * s), fill=fill, outline=(255, 255, 255, 170), width=2 * s)
    d.ellipse((6 * s, 7 * s, 14 * s, 15 * s), fill=INK)
    d.rounded_rectangle((16 * s, 8 * s, 37 * s, 14 * s), radius=s, fill=fill)
    d.rectangle((27 * s, 14 * s, 31 * s, 20 * s), fill=fill)
    d.rectangle((33 * s, 14 * s, 37 * s, 18 * s), fill=fill)
    return im


def bullet_textures():
    # Padlock for the guardian; guess (?), dictionary and leaked key for the attacks.
    return {"player_bullet": _texture(_padlock(), "padlock"), "guess": _texture(_bubble("?", ORANGE), "guess"),
            "dict": _texture(_book(PURPLE), "dict"), "leak": _texture(_key(RED), "leak")}


def load_textures():
    names = {"player": "player.png", "bot": "guess_bot.png", "drone": "dictionary_drone.png",
             "swarm": "leaked_swarm.png", "boss": "intruder.png"}
    names.update({bg: f"{bg}.jpg" for bg in ("bg_title", "bg_stage_1", "bg_stage_2", "bg_stage_3", "bg_result")})
    textures = {}
    for key, name in names.items():
        path = ROOT / "assets/images" / name
        if not path.exists():
            raise FileNotFoundError(f"에셋이 없습니다: {path}. python tools/prepare_generated_assets.py를 실행하세요.")
        textures[key] = arcade.load_texture(path)
    textures.update(bullet_textures())
    return textures
