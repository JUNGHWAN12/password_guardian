"""Prepare only the selected CC0 sprites; keep downloaded originals intact."""
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
    targets = {"player": None, "guess_bot": (255, 154, 48),
               "dictionary_drone": (188, 91, 245), "leaked_swarm": (255, 163, 55),
               "intruder": None, "player_bullet": None}
    records = []
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
    print(f"Prepared {len(records)} prototype assets.")


if __name__ == "__main__":
    prepare()
