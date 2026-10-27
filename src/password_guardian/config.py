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
# 2026-10-21 QA: children needed longer to read the question, so a stage gives the choice 14 s (12 s to answer)
# and combat 46 s. CHOICE + COMBAT must stay 60 s: the 3-minute clock counts down by stage.
CHOICE_SECONDS = 14.0
ANSWER_SECONDS = 12.0
COMBAT_SECONDS = 46.0
RESULT_SECONDS = 25.0  # QA: waiting 40 s to get back to the launcher felt long; Enter/Space also skip it
RESULT_SKIP_LOCK = 2.0  # Enter/Space cannot end the result screen this early, so a held skill key does not skip it
OPERATOR_HOLD, EDITOR_IDLE = 3.0, 30.0  # staff keys F8/F9 need a 3-second hold; the editor closes after 30 s idle
NAME_SECONDS = 18.0  # initials must be saved this far into the result screen, or the record is not kept
MAX_ENEMIES, MAX_ENEMY_BULLETS, MAX_PLAYER_BULLETS = 30, 300, 120
MANUAL_PAUSE_SECONDS = 30.0  # Esc pause resumes by itself so an abandoned game still returns to TITLE
