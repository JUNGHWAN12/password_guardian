"""Prepare the remaining Kenney-based prototype assets; keep downloaded originals intact.

Ships and backgrounds now come from tools/prepare_generated_assets.py; the game no longer uses these files.
"""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/candidates/review"
TARGET = ROOT / "assets/images"


def prepare():
    TARGET.mkdir(parents=True, exist_ok=True)
    targets = {"player_bullet": None}
    records = [r for r in json.loads((TARGET / "sources.json").read_text(encoding="utf-8"))
               if r["file"] not in ("assets/images/player_bullet.png", "assets/images/vault.png")]
    selected = json.loads((SOURCE / "selection.json").read_text(encoding="utf-8"))
    for name, tint in targets.items():
        src = SOURCE / f"{name}.png"
        dest = TARGET / f"{name}.png"
        if tint:
            im = Image.open(src).convert("RGBA")
            pixels = []
            for r, g, b, a in im.getdata():
                if r > g*1.35 and r > b*1.2:
                    brightness = r/255
                    pixels.append(tuple(round(c*brightness) for c in tint)+(a,))
                else:
                    pixels.append((r, g, b, a))
            im.putdata(pixels)
            im.save(dest)
        else:
            shutil.copy2(src, dest)
        original = next(r for r in selected if r["id"] == name)
        records.append({"file": dest.relative_to(ROOT).as_posix(), "original": original["source"],
                        "license": "CC0-1.0", "edit": f"red armor recolored to {tint}" if tint else "unchanged",
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
    shutil.copy2(SOURCE / "digital_vault_background_proposal.png", TARGET / "vault.png")
    records.append({"file": "assets/images/vault.png", "original": "assets/candidates/review/digital_vault_background_proposal.png",
                    "edit": "prototype composite, see ASSET_MANIFEST.md", "license": "Kenney base tile CC0 + project geometry"})
    (TARGET / "sources.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(targets) + 1} prototype assets.")


if __name__ == "__main__":
    prepare()
