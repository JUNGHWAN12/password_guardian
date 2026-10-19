"""Exercise the actual OpenGL UI and ten sessions without changing real rankings."""
from pathlib import Path
import json
import math
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import arcade
import pyglet
from password_guardian.app import FONT, GuardianWindow
from password_guardian.config import MANUAL_PAUSE_SECONDS
from password_guardian.engine import Entity
from password_guardian.rankings import RankingRepository


def main():
    out = ROOT / "runtime/screenshots"
    out.mkdir(parents=True, exist_ok=True)
    report = {"python": sys.version.split()[0], "arcade": arcade.__version__, "cycles": []}
    with tempfile.TemporaryDirectory(prefix="guardian-smoke-", dir=ROOT/"runtime") as directory:
        data = Path(directory)
        assert data.resolve().is_relative_to((ROOT/"runtime").resolve())
        window = GuardianWindow(data, visible=False, automated=True)
        try:
            window.switch_to()
            report["gpu"] = window.ctx.info.RENDERER
            # The bundled Korean font must win over system fallbacks.
            report["font"] = pyglet.font.load(FONT).name
            assert report["font"] == "IBM Plex Sans KR"

            def capture(name):
                window.sync_sprites()
                window.on_draw()
                arcade.get_image().save(out / f"{name}.png")

            def wait_jobs():
                for _, future in list(window.jobs):
                    future.result(timeout=5)
                window.poll_rankings()

            wait_jobs()
            capture("title")
            for cycle in range(10):
                window.on_key_press(arcade.key.ENTER, 0)
                assert window.engine.state == "TUTORIAL"
                assert window.engine.session.skills == 3
                if cycle == 0:
                    # Real input handling: held Space consumes only once.
                    window.on_key_press(arcade.key.SPACE, 0)
                    window.on_update(0.4)
                    window.on_key_press(arcade.key.SPACE, 0)
                    assert window.engine.session.skills == 2
                    window.on_key_release(arcade.key.SPACE, 0)
                    before = window.engine.elapsed
                    window.on_key_press(arcade.key.ESCAPE, 0)
                    window.on_key_press(arcade.key.ESCAPE, 0)
                    assert window.manual_paused
                    window.on_update(10)
                    assert window.engine.elapsed == before
                    window.on_key_release(arcade.key.ESCAPE, 0)
                    window.on_key_press(arcade.key.ESCAPE, 0)
                    window.on_key_release(arcade.key.ESCAPE, 0)
                    window.on_update(3)
                    assert window.engine.elapsed == before
                    # An abandoned Esc pause resumes by itself after the 3-second notice.
                    window.on_key_press(arcade.key.ESCAPE, 0)
                    window.on_key_release(arcade.key.ESCAPE, 0)
                    window.on_update(MANUAL_PAUSE_SECONDS-1)
                    assert window.manual_paused and window.engine.elapsed == before
                    window.on_update(1)
                    assert not window.manual_paused and window.resume_in == 3
                    window.on_update(3)
                    assert window.engine.elapsed == before and not window.paused
                    window.automated = False
                    window.on_key_press(arcade.key.RIGHT, 0)
                    window.on_deactivate()
                    window.on_update(10)
                    assert window.engine.elapsed == before and not window.keys
                    window.on_activate()
                    window.on_update(3)
                    window.automated = True
                    capture("tutorial")
                window.on_update(window.engine.remaining)
                assert window.engine.state == "CHOICE"
                for stage in range(3):
                    if cycle == 0 and stage == 0:
                        capture("choice")
                    # Alternate all correct, wrong, and no answers between runs.
                    if cycle % 3 != 2:
                        key = arcade.key.KEY_2 if cycle % 3 == 0 else arcade.key.KEY_1
                        window.on_key_press(key, 0)
                        window.on_key_release(key, 0)
                    window.on_update(8)
                    assert window.engine.state == "COMBAT"
                    for tick in range(52):
                        window.keys.discard(arcade.key.RIGHT)
                        window.keys.discard(arcade.key.LEFT)
                        window.keys.add(arcade.key.RIGHT if (tick//4)%2 == 0 else arcade.key.LEFT)
                        window.on_update(1)
                        if cycle == 0 and tick == 12:
                            capture(f"stage_{stage+1}")
                        assert len(window.engine.enemy_bullets) <= 250
                        assert len(window.engine.enemies) <= 20
                    assert window.engine.state == ("RESULT" if stage == 2 else "CHOICE")
                wait_jobs()
                # Each of the first ten games makes today's TOP 10 and asks for initials.
                assert window.entry == "typing", window.rank_status

                def press(key):
                    window.on_key_press(key, 0)
                    window.on_key_release(key, 0)
                if cycle == 0:
                    for key in (arcade.key.S, arcade.key.E, arcade.key.X, arcade.key.ENTER):
                        press(key)  # a banned name is refused, nothing saved
                    assert window.entry == "typing" and window.entry_warning
                    for _ in range(3):
                        press(arcade.key.BACKSPACE)
                    press(arcade.key.K)
                    press(arcade.key.ENTER)  # too short
                    assert window.entry == "typing" and window.entry_text == "K"
                    capture("initials")
                    press(arcade.key.BACKSPACE)
                for key in (arcade.key.K, arcade.key.A + cycle, arcade.key.M):
                    press(key)
                press(arcade.key.ENTER)
                assert window.entry == "saved"
                wait_jobs()
                assert window.board.own is not None and window.board.own["name"] == "K" + chr(65+cycle) + "M"
                assert window.board.total == cycle+1
                assert window.board.own["session_id"] == window.engine.result.session_id
                if cycle == 0:
                    capture("result")
                report["cycles"].append({"score": window.engine.result.score,
                                          "revives": window.engine.result.revive_count,
                                          "rank": window.board.own["rank"]})
                if cycle == 0:
                    # Paused on the result screen and left alone: still returns to the title.
                    window.on_key_press(arcade.key.ESCAPE, 0)
                    window.on_key_release(arcade.key.ESCAPE, 0)
                    window.on_update(MANUAL_PAUSE_SECONDS)
                    window.on_update(3)
                assert window.engine.state == "RESULT"
                window.on_update(40)
                assert window.engine.state == "TITLE"
                assert all(len(window.sprite_lists[n]) == 0 for n in ("enemies", "shots", "threats"))
                wait_jobs()
                print(f"Full session {cycle+1}/10 passed", flush=True)
            capture("leaderboard")
            assert RankingRepository(data/"ranking.json").board().total == 10
            # Staff keys on the title: hold F8 for the name editor, Enter twice turns a name into ???;
            # hold F9 to clear today's board; Ctrl+Shift+Q quits.
            assert window.engine.state == "TITLE"
            wait_jobs()
            window.on_key_press(arcade.key.F8, 0)
            window.on_update(2.0)
            window.on_key_release(arcade.key.F8, 0)  # let go too early: nothing happens
            assert not window.editing
            window.on_key_press(arcade.key.F8, 0)
            for _ in range(7):
                window.on_update(0.5)
            window.on_key_release(arcade.key.F8, 0)
            assert window.editing
            window.on_key_press(arcade.key.DOWN, 0)
            window.on_key_press(arcade.key.ENTER, 0)
            assert window.edit_armed and window.engine.state == "TITLE"
            capture("staff_editor")
            target = window.board.rows[1]["session_id"]
            window.on_key_press(arcade.key.ENTER, 0)
            wait_jobs()
            assert [r["name"] for r in window.board.rows if r["session_id"] == target] == ["???"]
            window.on_key_press(arcade.key.F8, 0)
            assert not window.editing
            window.on_key_press(arcade.key.F9, 0)
            for _ in range(7):
                window.on_update(0.5)
            window.on_key_release(arcade.key.F9, 0)
            wait_jobs()
            assert window.board.total == 0 and RankingRepository(data/"ranking.json").board().total == 0
            assert list(data.glob("ranking_reset_*.json"))

            # Rendering and frame timing with near-cap sprites. No ranking save.
            window.engine.start()
            window.engine.update(28)
            window.engine.enemies.clear()
            for _ in range(20):
                window.engine.spawn_enemy("drone")
            window.engine.enemy_bullets = [Entity(100000+i, "guess" if i%2 else "dict",
                130+(i%25)*50, 350+(i//25)*45, 8, vy=-150, ttl=12) for i in range(250)]
            window.sync_sprites()
            timings = []
            for _ in range(90):
                started = time.perf_counter()
                window.on_update(1/60)
                window.on_draw()
                window.ctx.finish()
                timings.append((time.perf_counter()-started)*1000)
            report["stress_frame_ms_mean"] = round(sum(timings[10:])/len(timings[10:]), 2)
            report["stress_frame_ms_p95"] = round(sorted(timings[10:])[int(len(timings[10:])*0.95)], 2)
            window.set_size(1024, 768)
            window.dispatch_events()
            window.fit_camera()
            capture("letterbox_4_3")
            # Booth launcher mode: Esc on the title or Shift+Esc mid-game quits; a finished game quits by itself
            # after its result is saved.
            for quit_how in ("title-esc", "shift-esc", "ctrl-shift-q", "finished"):
                booth = GuardianWindow(data, visible=False, automated=True, booth=True)
                booth.switch_to()
                if quit_how == "title-esc":
                    booth.on_key_press(arcade.key.ESCAPE, 0)
                elif quit_how == "ctrl-shift-q":
                    booth.on_key_press(arcade.key.Q, arcade.key.MOD_CTRL | arcade.key.MOD_SHIFT)
                else:
                    booth.on_key_press(arcade.key.ENTER, 0)
                    booth.on_key_release(arcade.key.ENTER, 0)
                    if quit_how == "shift-esc":
                        booth.on_update(5)
                        booth.on_key_press(arcade.key.ESCAPE, arcade.key.MOD_SHIFT)
                    else:
                        saved = RankingRepository(data/"ranking.json").board().total
                        for _ in range(int(240/0.5) + 2):
                            if booth.closed_worker:
                                break
                            booth.on_update(0.5)
                            for _, future in list(booth.jobs):  # real seconds pass between frames in a real game
                                future.result(timeout=5)
                        # Nobody typed initials (or it missed the TOP 10): the record is not kept.
                        assert RankingRepository(data/"ranking.json").board().total == saved
                        assert booth.entry == "closed", booth.entry
                        report["booth_result_message"] = booth.rank_status
                assert booth.closed_worker, quit_how
            window.switch_to()
            report["checks"] = ["10 complete 240-second simulated sessions", "initials entry and banned names", "staff F8 editor, F9 reset, Ctrl+Shift+Q", "booth mode quits", "correct/wrong/missing choices",
                                "restart persistence", "no duplicate registrations", "input debouncing",
                                "pause and focus recovery", "manual pause auto-resume", "bundled IBM Plex Sans KR font", "stage cleanup", "4:3 letterbox", "OpenGL render"]
        finally:
            window.worker.executor.shutdown(wait=True)
            window.shutdown()
    (ROOT / "runtime/smoke_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
