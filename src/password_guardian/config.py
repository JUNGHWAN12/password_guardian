from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1920, 1080
RULESET = "prototype-2"  # bump whenever enemies, scoring or hitboxes change
FIELD = (90, 1470, 135, 910)  # left, right, bottom, top
PLAYER_START = (780, 220)
STEP = 1 / 120
TUTORIAL_SECONDS = 20.0
CHOICE_SECONDS = 8.0
ANSWER_SECONDS = 6.0
COMBAT_SECONDS = 52.0
RESULT_SECONDS = 40.0
MAX_ENEMIES, MAX_ENEMY_BULLETS, MAX_PLAYER_BULLETS = 20, 250, 100
MANUAL_PAUSE_SECONDS = 30.0  # Esc pause resumes by itself so an abandoned game still returns to TITLE
