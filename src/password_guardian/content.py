import json
from .config import ROOT


def load_content():
    choices = json.loads((ROOT / "data/choices.json").read_text(encoding="utf-8"))
    waves = json.loads((ROOT / "data/waves.json").read_text(encoding="utf-8"))
    if len(choices) != 3:
        raise ValueError("보안 문항은 3개여야 합니다.")
    for choice in choices:
        if len(choice["options"]) != 2 or choice["correct"] not in (1, 2):
            raise ValueError("보안 문항의 선택지·정답 설정이 잘못되었습니다.")
        for key in ("title", "effect", "explanation", "short"):
            if not isinstance(choice[key], str) or not choice[key].strip():
                raise ValueError(f"문항의 {key} 항목이 비어 있습니다.")
    for wave in waves:
        if not (wave["stage"] in (0, 1, 2) and 0 <= wave["start"] < wave["end"] <= 52
                and wave["interval"] > 0 and 1 <= wave["count"] <= 20
                and wave["kinds"] and set(wave["kinds"]) <= {"bot", "drone", "swarm"}):
            raise ValueError("웨이브 설정이 잘못되었습니다.")
    return choices, waves
