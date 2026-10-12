from PIL import Image, ImageDraw
import arcade
from .config import ROOT

FONT_FILES = ("Galmuri11.ttf", "Galmuri11-Bold.ttf")


def load_fonts():
    for name in FONT_FILES:
        path = ROOT / "assets/fonts" / name
        if not path.exists():
            raise FileNotFoundError(f"글꼴이 없습니다: {path}")
        arcade.load_font(path)


def load_textures():
    names = {"player": "player", "bot": "guess_bot", "drone": "dictionary_drone",
             "swarm": "leaked_swarm", "boss": "intruder", "player_bullet": "player_bullet", "vault": "vault"}
    textures = {}
    for key, name in names.items():
        path = ROOT / "assets/images" / f"{name}.png"
        if not path.exists():
            raise FileNotFoundError(f"에셋이 없습니다: {path}. python tools/prepare_prototype_assets.py를 실행하세요.")
        textures[key] = arcade.load_texture(path)
    for kind in ("round", "wedge"):
        im = Image.new("RGBA", (32, 32))
        draw = ImageDraw.Draw(im)
        if kind == "round":
            draw.ellipse((2, 2, 30, 30), fill=(255, 73, 100, 55))
            draw.ellipse((6, 6, 26, 26), fill=(255, 80, 105, 255))
            draw.ellipse((10, 10, 22, 22), fill=(255, 228, 223, 255))
        else:
            draw.polygon([(16, 2), (30, 28), (16, 21), (2, 28)], fill=(191, 103, 255, 255))
            draw.polygon([(16, 8), (22, 23), (16, 19), (10, 23)], fill=(248, 225, 255, 255))
        textures[kind] = arcade.Texture(im, hash=f"guardian-{kind}-v1")
    return textures
