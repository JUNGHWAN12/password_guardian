from pathlib import Path
import sys

# A PyInstaller build unpacks assets and data beside the modules, in sys._MEIPASS.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
WIDTH, HEIGHT = 1920, 1080
RULESET = "prototype-4"  # bump whenever enemies, scoring or hitboxes change
FIELD = (90, 1470, 135, 910)  # left, right, bottom, top
PLAYER_START = (780, 220)
STEP = 1 / 120
PLAYER_SPEED, PRECISE_SPEED = 620, 240  # px/s; hold Shift for the slow, precise speed
PLAYER_HIT_RADIUS = 7  # far smaller than the ship art, as in other bullet-dodging games
TUTORIAL_SECONDS = 20.0
# One stage is CHOICE + COMBAT = 60 seconds; the engine's game clock counts on that.
CHOICE_SECONDS = 14.0   # question screen: answer time plus a short look at the explanation
ANSWER_SECONDS = 12.0   # long enough for younger visitors to read both options
COMBAT_SECONDS = 46.0
RESULT_SECONDS = 25.0
RESULT_SKIP_LOCK = 1.5  # Enter on the result screen works after this, so keys held from combat do not skip it
MAX_ENEMIES, MAX_ENEMY_BULLETS, MAX_PLAYER_BULLETS = 30, 300, 120
MANUAL_PAUSE_SECONDS = 30.0  # Esc pause resumes by itself so an abandoned game still returns to TITLE
