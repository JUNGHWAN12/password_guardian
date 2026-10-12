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
from password_guardian.app import GuardianWindow
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
                assert window.board.own is not None
                assert window.board.total == cycle+1
                assert window.board.own["session_id"] == window.engine.result.session_id
                if cycle == 0:
                    capture("result")
                report["cycles"].append({"score": window.engine.result.score,
                                          "revives": window.engine.result.revive_count,
                                          "rank": window.board.own["rank"]})
                window.on_update(40)
                assert window.engine.state == "TITLE"
                assert all(len(window.sprite_lists[n]) == 0 for n in ("enemies", "shots", "threats"))
                wait_jobs()
                print(f"Full session {cycle+1}/10 passed", flush=True)
            capture("leaderboard")
            assert RankingRepository(data/"rankings.sqlite3").board().total == 10

            # Rendering and frame timing with near-cap sprites. No ranking save.
            window.engine.start()
            window.engine.update(28)
            window.engine.enemies.clear()
            for _ in range(20):
                window.engine.spawn_enemy("drone")
            window.engine.enemy_bullets = [Entity(100000+i, "round" if i%2 else "wedge",
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
            report["checks"] = ["10 complete 240-second simulated sessions", "correct/wrong/missing choices",
                                "restart persistence", "no duplicate registrations", "input debouncing",
                                "pause and focus recovery", "stage cleanup", "4:3 letterbox", "OpenGL render"]
        finally:
            window.worker.executor.shutdown(wait=True)
            window.shutdown()
    (ROOT / "runtime/smoke_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
