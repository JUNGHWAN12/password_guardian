"""Arcade presentation and input. Simulation and ranking rules live elsewhere."""
import math
import sys
from pathlib import Path
import arcade
from arcade.types import LBWH, LRBT

from .assets import load_fonts, load_textures
from .config import WIDTH, HEIGHT, FIELD, MANUAL_PAUSE_SECONDS
from .engine import Engine
from .rankings import Board, RankingWorker, participant_code

INK = (7, 14, 24)
PANEL = (13, 27, 42, 244)
EDGE = (37, 66, 82)
WHITE = (234, 245, 250)
MUTED = (139, 165, 181)
CYAN = (77, 221, 228)
GOLD = (255, 195, 104)
RED = (255, 109, 123)
PURPLE = (194, 141, 255)
FONT = ("IBM Plex Sans KR", "Malgun Gothic", "맑은 고딕", "Noto Sans KR", "Arial")  # bundled font first
STAGES = ("기본 방어", "복합 공격", "최종 방어")


class GuardianWindow(arcade.Window):
    def __init__(self, data_dir, *, fullscreen=False, practice=False, visible=True, automated=False):
        super().__init__(1280, 720, "패스워드 가디언 · Password Guardian", resizable=True,
                         fullscreen=fullscreen, visible=visible, antialiasing=True, vsync=True,
                         update_rate=1/60, draw_rate=1/60)
        self.set_minimum_size(960, 540)
        self.automated = automated
        self.engine = Engine(practice=practice)
        load_fonts()
        self.textures = load_textures()
        self.camera = arcade.Camera2D(window=self, position=(WIDTH/2, HEIGHT/2),
                                     projection=LRBT(-WIDTH/2, WIDTH/2, -HEIGHT/2, HEIGHT/2))
        self.fit_camera()
        self.labels = {}
        self.keys = set()
        self.control_keys = set()
        self.manual_paused = False
        self.manual_pause_left = 0.0
        self.focus_paused = False
        self.resume_in = 0.0
        self.last_revision = self.engine.revision
        self.seen_result = None
        self.clock = 0.0
        self.board = Board((), 0, None)
        self.rank_status = "기록을 불러오는 중"
        self.worker = RankingWorker(Path(data_dir) / "rankings.sqlite3")
        self.jobs = []
        self.request_board()
        self.sprite_maps = {name: {} for name in ("player", "enemies", "shots", "threats")}
        self.sprite_lists = {name: arcade.SpriteList() for name in self.sprite_maps}
        self.closed_worker = False
        self.sync_sprites()

    def fit_camera(self):
        scale = min(self.width/WIDTH, self.height/HEIGHT)
        w, h = round(WIDTH*scale), round(HEIGHT*scale)
        self.camera.viewport = LBWH((self.width-w)//2, (self.height-h)//2, w, h)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        if hasattr(self, "camera"):
            self.fit_camera()

    @property
    def paused(self):
        return self.manual_paused or self.focus_paused or self.resume_in > 0

    def on_deactivate(self):
        if hasattr(self, "keys"):
            self.keys.clear()
            self.control_keys.clear()
            if not self.automated and self.engine.state != "TITLE":
                self.focus_paused = True

    def on_activate(self):
        if getattr(self, "focus_paused", False):
            self.focus_paused = False
            self.resume_in = 0.0 if self.manual_paused else 3.0

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.F11, arcade.key.ESCAPE):
            if key in self.control_keys:
                return
            self.control_keys.add(key)
        if key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
            self.fit_camera()
            return
        if key == arcade.key.ESCAPE and self.engine.state != "TITLE":
            if not self.focus_paused:
                self.manual_paused = not self.manual_paused
                self.manual_pause_left = MANUAL_PAUSE_SECONDS
                self.resume_in = 0 if self.manual_paused else 3
                self.keys.clear()
            return
        if self.paused or key in self.keys:
            return
        self.keys.add(key)
        if self.engine.state == "TITLE" and key in (arcade.key.ENTER, arcade.key.RETURN):
            self.engine.start()
            self.state_changed()
        elif self.engine.state == "CHOICE":
            if key in (arcade.key.KEY_1, arcade.key.NUM_1):
                self.engine.choose(1)
            elif key in (arcade.key.KEY_2, arcade.key.NUM_2):
                self.engine.choose(2)
        elif key == arcade.key.SPACE:
            self.engine.skill()

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)
        self.control_keys.discard(key)

    def state_changed(self):
        if self.last_revision == self.engine.revision:
            return
        self.keys.clear()
        self.labels.clear()
        self.last_revision = self.engine.revision
        if self.engine.state == "TITLE":
            self.request_board()

    def request_board(self, result=None):
        token = result.session_id if result else None
        self.jobs.append((token, self.worker.submit(result)))
        self.rank_status = "기록 저장 중" if result else "기록을 불러오는 중"

    def poll_rankings(self):
        active = self.engine.result.session_id if self.engine.state == "RESULT" else None
        for token, future in self.jobs[:]:
            if not future.done():
                continue
            self.jobs.remove((token, future))
            try:
                board = future.result()
                if token == active:
                    self.board = board
                    self.rank_status = "기록 저장 완료" if token else "이 PC에 저장된 기록"
            except Exception as exc:
                print(f"Ranking unavailable: {exc}", file=sys.stderr)
                if token == active:
                    self.rank_status = "기록을 저장하지 못했습니다" if token else "랭킹을 불러오지 못했습니다"
                    self.board = Board((), 0, None)

    def on_update(self, delta_time):
        self.clock += delta_time
        self.poll_rankings()
        if self.focus_paused:
            return
        if self.manual_paused:
            # A visitor may pause and walk away; the session must still finish on its own.
            self.manual_pause_left = max(0, self.manual_pause_left-delta_time)
            if self.manual_pause_left > 0:
                return
            self.manual_paused = False
            self.resume_in = 3.0
            return
        if self.resume_in > 0:
            self.resume_in = max(0, self.resume_in-delta_time)
            return
        movement = (int(arcade.key.RIGHT in self.keys)-int(arcade.key.LEFT in self.keys),
                    int(arcade.key.UP in self.keys)-int(arcade.key.DOWN in self.keys))
        self.engine.update(delta_time, movement)
        if self.engine.result and self.seen_result != self.engine.result.session_id:
            self.seen_result = self.engine.result.session_id
            self.board = Board(self.board.rows, self.board.total, None)
            if self.engine.result.eligible:
                self.request_board(self.engine.result)
            else:
                self.rank_status = "연습 모드 · 기록을 저장하지 않습니다"
        self.state_changed()
        self.sync_sprites()

    def sync_sprites(self):
        e = self.engine
        groups = {"player": [e.player], "enemies": e.enemies, "shots": e.player_bullets, "threats": e.enemy_bullets}
        widths = {"player": 76, "bot": 30, "drone": 110, "swarm": 64, "boss": 200}  # bullets: drawn at size
        for group, entities in groups.items():
            mapping = self.sprite_maps[group]
            live = {entity.id for entity in entities}
            for entity_id in list(mapping):
                if entity_id not in live:
                    mapping.pop(entity_id).remove_from_sprite_lists()
            for entity in entities:
                sprite = mapping.get(entity.id)
                if sprite is None:
                    texture = self.textures[entity.kind]
                    sprite = arcade.Sprite(texture, scale=widths.get(entity.kind, texture.width)/texture.width)
                    self.sprite_lists[group].append(sprite)
                    mapping[entity.id] = sprite
                sprite.position = entity.x, entity.y
                if group == "player":
                    sprite.alpha = 100 if e.invulnerable and int(e.invulnerable*10)%2 else 255

    def txt(self, key, text, x, y, size=24, color=WHITE, *, width=None, bold=False, anchor="left", leading=1.3):
        label = self.labels.get(key)
        if label is None:
            label = arcade.Text(str(text), x, y, color, size, font_name=FONT, bold=bold,
                                anchor_x=anchor, anchor_y="top", width=width, multiline=width is not None)
            if width is not None:
                # Fixed baseline distance (multiple of font size) keeps wrapped text independent of font metrics.
                label.label.set_style("line_spacing", f"{size*leading:.1f}pt")
            self.labels[key] = label
        else:
            if label.text != str(text):
                label.text = str(text)
            if label.x != x:
                label.x = x
            if label.y != y:
                label.y = y
            if label.color != color:
                label.color = color
        label.draw()

    @staticmethod
    def panel(x, y, w, h, *, fill=PANEL, edge=EDGE):
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, fill)
        arcade.draw_lbwh_rectangle_outline(x, y, w, h, edge, 2)

    def image(self, key, x, y, w, h=None, alpha=255):
        texture = self.textures[key]
        if h is None:
            h = w*texture.height/texture.width
        arcade.draw_texture_rect(texture, LBWH(x-w/2, y-h/2, w, h), alpha=alpha)

    def background(self):
        self.image("vault", 960, 540, 1920, 1080)
        state = self.engine.state
        if state in ("TITLE", "RESULT"):
            arcade.draw_lbwh_rectangle_filled(0, 0, WIDTH, HEIGHT, (5, 13, 23, 110))
        else:
            self.panel(65, 110, 1430, 815, fill=(7, 17, 28, 160), edge=(26, 60, 75))
            cx, cy = 780, 515
            color = [(23, 63, 73), (51, 35, 69), (64, 35, 45)][self.engine.stage]
            for radius in (150, 195, 280):
                arcade.draw_circle_outline(cx, cy, radius, color, 2)
            for x in (120, 1435):
                for y in range(180, 900, 95):
                    arcade.draw_lbwh_rectangle_filled(x, y, 5, 40, color)

    def on_draw(self):
        self.clear(INK)
        self.camera.use()
        self.background()
        state = self.engine.state
        if state == "TITLE":
            self.draw_title()
        elif state == "RESULT":
            self.draw_result()
        else:
            self.draw_game()
            if state == "CHOICE":
                self.draw_choice()
            elif state == "TUTORIAL":
                self.draw_tutorial()
        if self.engine.practice:
            self.txt("practice", "연습 모드 · 랭킹 미등록", 1880, 1060, 16, GOLD, anchor="right")
        if self.paused:
            arcade.draw_lbwh_rectangle_filled(0, 0, WIDTH, HEIGHT, (4, 10, 19, 220))
            label = f"{math.ceil(self.resume_in)}초 후 다시 시작" if self.resume_in > 0 else "잠시 쉬어가요"
            self.txt("pause-title", label, 960, 620, 48, anchor="center", bold=True)
            detail = ("게임 창으로 돌아오면 계속됩니다" if self.focus_paused
                      else f"Esc 키로 이어서 플레이  ·  {math.ceil(self.manual_pause_left)}초 후 자동 재개")
            if self.resume_in > 0:
                detail = "이동 키를 준비하세요"
            self.txt("pause-detail", detail, 960, 530, 25, MUTED, anchor="center")

    def draw_title(self):
        self.txt("eyebrow", "DIGITAL SECURITY / INTERACTIVE MISSION", 100, 983, 18, CYAN)
        self.txt("title", "패스워드\n가디언", 94, 908, 76, width=850, bold=True, leading=1.1)
        self.txt("subtitle", "계정을 노리는 공격으로부터\n디지털 금고를 지켜라!", 102, 654, 30, MUTED, width=800)
        self.image("player", 895, 649 + math.sin(self.clock*1.5)*8, 190)
        arcade.draw_circle_outline(895, 652, 188, (40, 115, 134), 2)
        arcade.draw_circle_outline(895, 652, 213, (25, 55, 72), 1)
        self.panel(100, 358, 1010, 125)
        self.txt("start-key", "ENTER", 140, 445, 33, CYAN, bold=True)
        self.txt("start-label", "보안 수호 임무 시작", 330, 447, 29, bold=True)
        self.txt("start-time", "1인 플레이   /   약 4분   /   끝까지 체험 가능", 330, 399, 19, MUTED)
        for i, (key, action) in enumerate((("방향키", "이동"), ("자동", "발사"), ("SPACE", "방어 스킬"), ("1 · 2", "보안 선택"))):
            x = 104+i*260
            self.txt(f"control-key{i}", key, x, 297, 25, CYAN, bold=True)
            self.txt(f"control-label{i}", action, x, 251, 20, MUTED)
        self.txt("title-learning", "길게 만들고 · 다르게 쓰고 · 한 번 더 확인하세요", 100, 154, 23, WHITE)
        self.txt("footer", "F11 전체 화면    ·    Esc 일시정지    ·    실제 비밀번호는 입력하지 않습니다", 100, 87, 17, MUTED)
        self.draw_board(1200, 160, 620, 815)

    def draw_board(self, x, y, w, h, *, result=False):
        self.panel(x, y, w, h)
        self.txt("board-tag", "LOCAL LEADERBOARD", x+30, y+h-27, 16, CYAN)
        self.txt("board-title", "이 PC의 기록 TOP 10", x+30, y+h-65, 30, bold=True)
        self.txt("board-status", self.rank_status, x+30, y+h-118, 16, MUTED, width=int(w-60))
        self.txt("board-head", "순위     참가 코드", x+30, y+h-177, 18, MUTED)
        self.txt("board-score-head", "점수", x+w-30, y+h-177, 18, MUTED, anchor="right")
        if not self.board.rows:
            self.txt("board-empty", "첫 번째 기록에 도전하세요", x+30, y+h-253, 22, MUTED, width=int(w-60))
        own_id = (self.board.own["id"] if result and self.board.own
                  and self.board.own["session_id"] == self.engine.result.session_id else None)
        for i, row in enumerate(self.board.rows):
            row_y = y+h-225-i*47
            own = row["id"] == own_id
            if own:
                arcade.draw_lbwh_rectangle_filled(x+17, row_y-33, w-34, 43, (24, 73, 82, 255))
            self.txt(f"rank{i}", f"{row['rank']:02}", x+30, row_y, 20, CYAN if i < 3 else MUTED)
            self.txt(f"code{i}", participant_code(row["id"]), x+102, row_y, 19, WHITE)
            self.txt(f"score{i}", f"{row['score']:,}", x+w-30, row_y, 22, CYAN if own else WHITE, anchor="right")
        self.txt("board-bottom", "동점: 정답 수 → 적은 부활 → 먼저 등록", x+30, y+81, 15, MUTED)
        self.txt("board-total", f"총 {self.board.total}개 기록  ·  이 PC에만 저장", x+30, y+45, 16, MUTED)

    def draw_game(self):
        e, s = self.engine, self.engine.session
        self.panel(65, 947, 1790, 89)
        self.txt("game-name", "PASSWORD GUARDIAN", 95, 1009, 23, CYAN, bold=True)
        phase = "조작 연습" if e.state == "TUTORIAL" else f"0{e.stage+1} / {STAGES[e.stage]}"
        self.txt("game-phase", phase, 615, 1010, 24, WHITE)
        seconds = math.ceil(e.remaining if e.state == "TUTORIAL" else e.game_remaining)
        self.txt("game-time", f"{seconds//60:02}:{seconds%60:02}", 1130, 1015, 33, CYAN, bold=True)
        self.txt("game-score", f"{s.score:,} P", 1820, 1015, 33, WHITE, anchor="right")
        viewport = self.camera.viewport
        scale = viewport.width / WIDTH
        previous_scissor = self.ctx.scissor
        self.ctx.scissor = (round(viewport.left+65*scale), round(viewport.bottom+110*scale),
                            round(1430*scale), round(815*scale))
        for group in ("enemies", "shots", "threats", "player"):
            self.sprite_lists[group].draw()
        if s.shield or e.invulnerable:
            arcade.draw_circle_outline(e.player.x, e.player.y, 52, CYAN if s.shield else GOLD, 2)
        if e.skill_flash:
            progress = 1-e.skill_flash/0.45
            arcade.draw_circle_outline(*e.skill_center, max(5, 180*progress), (*CYAN, int(255*(1-progress))), 5)
        if e.damage_flash:
            arcade.draw_lbwh_rectangle_outline(65, 110, 1430, 815, (*RED, int(e.damage_flash/0.25*220)), 5)
        self.ctx.scissor = previous_scissor
        for enemy in e.enemies:
            if enemy.age < 0.8:
                arcade.draw_circle_outline(enemy.x, enemy.y, enemy.radius+18, GOLD, 2)
            if enemy.kind == "boss":
                self.panel(505, 865, 550, 31, fill=(35, 18, 31, 240), edge=(90, 48, 60))
                arcade.draw_lbwh_rectangle_filled(511, 871, 538*max(0, enemy.hp)/100, 19, RED)
                self.txt("boss-name", "침입자", 780, 937, 22, RED, anchor="center")
                if enemy.age % 8 < 0.6:
                    self.txt("boss-warning", "공격 패턴 전환", 780, 845, 26, GOLD, anchor="center")
        self.draw_sidebar()
        self.txt("game-footer", "방향키 이동     SPACE 주변 탄환 제거     Esc 일시정지", 83, 78, 19, MUTED)
        self.txt("auto-label", "자동 발사 ON", 1450, 78, 18, CYAN, anchor="right")

    def draw_sidebar(self):
        e, s = self.engine, self.engine.session
        self.panel(1520, 110, 335, 815)
        x = 1546
        self.txt("defense-label", "ACCOUNT STATUS", x, 891, 16, CYAN)
        self.txt("defense-title", "계정 보호 상태", x, 846, 26, bold=True)
        for i in range(3):
            self.panel(x+i*89, 751, 72, 37, fill=CYAN if i < s.hp else (30, 46, 57), edge=EDGE)
        self.txt("health-label", f"체력  {s.hp} / 3", x, 733, 20, WHITE)
        self.txt("shield-label", f"보호막       {s.shield}", x, 678, 22, CYAN)
        self.txt("skill-label", f"방어 스킬    {s.skills}", x, 626, 22, GOLD)
        self.txt("damage-label", f"공격력       ×{s.damage}", x, 574, 22, WHITE)
        self.txt("kills-label", f"적 처치      {s.enemy_kills}", x, 510, 20, MUTED)
        self.txt("revive-label", f"부활         {s.revive_count}", x, 466, 20, MUTED)
        arcade.draw_line(x, 420, 1820, 420, EDGE, 2)
        self.txt("tip-label", "오늘의 보안 습관", x, 392, 21, CYAN, bold=True)
        self.txt("tip-body", e.questions[e.stage]["short"], x, 345, 25, WHITE, width=270)
        self.txt("tip-foot", "체력이 없어져도 다시 부활해요. 끝까지 도전해 보세요!", x, 229, 18, MUTED, width=266)

    def draw_tutorial(self):
        self.panel(295, 546, 970, 305, fill=(10, 27, 41, 245), edge=(55, 126, 140))
        self.txt("tutorial-tag", f"조작 연습  ·  {math.ceil(self.engine.remaining)}초 후 시작", 335, 814, 23, CYAN)
        self.txt("tutorial-title", "움직이고, 피하고, 지켜요", 335, 759, 36, bold=True)
        self.txt("tutorial-body", "방향키로 이동하면 탄환은 자동으로 발사됩니다.\nSpace로 주변 탄환을 지워 보세요. 연습 기록은 저장되지 않아요.", 335, 691, 22, MUTED, width=890)
        self.txt("tutorial-note", "탄막은 공격의 압박을 표현한 비유입니다.", 335, 596, 18, MUTED)

    def draw_choice(self):
        e = self.engine
        q = e.questions[e.stage]
        record = e.session.choices[e.stage]
        arcade.draw_lbwh_rectangle_filled(65, 110, 1430, 815, (4, 12, 23, 235))
        self.txt("choice-tag", f"SECURITY UPGRADE  /  0{e.stage+1}", 145, 858, 20, CYAN)
        self.txt("choice-title", q["title"], 145, 788, 34, WHITE, width=1260, bold=True)
        self.txt("choice-instruction", "1 또는 2를 눌러 선택하세요", 145, 714, 23, MUTED)
        for i, option in enumerate(q["options"]):
            x = 145 + i*640
            selected = record is not None and record.selection == i+1
            correct_reveal = record is not None and q["correct"] == i+1
            edge = CYAN if correct_reveal else GOLD if selected else EDGE
            self.panel(x, 416, 585, 226, fill=(15, 35, 49, 255), edge=edge)
            self.txt(f"choice-number{i}", f"0{i+1}", x+30, 611, 30, edge if correct_reveal or selected else MUTED)
            self.txt(f"choice-option{i}", option, x+30, 548, 27, WHITE, width=510, bold=True)
            self.txt(f"choice-check{i}", "안전한 선택" if correct_reveal else "선택됨" if selected else f"키보드 {i+1}", x+30, 456, 18, edge if selected or correct_reveal else MUTED)
        if record is None:
            message = f"선택 시간  {max(0, math.ceil(6-e.elapsed))}초"
            self.txt("choice-feedback", message, 145, 354, 28, GOLD)
            self.txt("choice-explanation", "틀려도 괜찮아요. 안전한 습관을 배우고 계속 진행합니다.", 145, 294, 23, MUTED, width=1200)
        else:
            message = f"안전한 선택!  +200 P  ·  {q['effect']}" if record.correct else "미선택 · 안전한 습관을 확인해요" if record.selection is None else "괜찮아요. 안전한 선택을 함께 알아봐요"
            self.txt("choice-feedback", message, 145, 354, 27, CYAN if record.correct else GOLD)
            self.txt("choice-explanation", q["explanation"], 145, 297, 23, MUTED, width=1180)
        self.txt("choice-countdown", f"{math.ceil(e.remaining)}초 후 전투 시작", 1390, 172, 21, MUTED, anchor="right")

    def draw_result(self):
        result = self.engine.result
        self.txt("result-tag", "MISSION COMPLETE / ACCOUNT PROTECTED", 90, 1000, 19, CYAN)
        self.txt("result-title", "금고 수호 완료", 85, 938, 55, bold=True)
        self.panel(90, 596, 1045, 230)
        self.txt("result-score-label", "TOTAL SCORE", 125, 793, 18, MUTED)
        self.txt("result-score", f"{result.score:,}", 120, 746, 83, WHITE, bold=True)
        self.txt("result-grade", result.grade, 1055, 768, 89, CYAN, bold=True, anchor="right")
        self.txt("result-grade-caption", "게임 성과 등급", 1063, 628, 18, MUTED, anchor="right")
        summary = f"일반 적 {result.enemy_kills}기 처치   ·   부활 {result.revive_count}회   ·   보스 {'처치' if result.boss_defeated else '시간 방어 완료'}"
        self.txt("result-stats", summary, 93, 558, 23, WHITE)
        own = self.board.own
        if result.eligible and own and own["session_id"] == result.session_id:
            rank_message = f"{participant_code(own['id'])}   /   이번 기록 {own['rank']}위 · 총 {self.board.total}개"
        else:
            rank_message = self.rank_status
        self.txt("result-rank", rank_message, 93, 508, 23, CYAN)
        for i, record in enumerate(result.choices):
            y = 432-i*62
            label = "정답" if record.correct else "미선택" if record.selection is None else "다시 기억해요"
            self.txt(f"result-choice-num{i}", f"0{i+1}", 95, y, 23, CYAN)
            self.txt(f"result-choice{i}", self.engine.questions[i]["short"], 161, y, 24, WHITE)
            self.txt(f"result-choice-status{i}", label, 1085, y, 21, CYAN if record.correct else GOLD, anchor="right")
        self.txt("result-message", "길고 예측하기 어려운 비밀번호를 서비스마다 다르게 사용하고,\n다중 인증을 함께 설정하세요. 어떤 수단도 모든 공격을 막지는 못합니다.", 94, 221, 21, MUTED, width=1050)
        self.txt("result-timer", f"{math.ceil(self.engine.remaining)}초 후 시작 화면으로 돌아갑니다", 94, 114, 24, CYAN)
        self.txt("result-disclaimer", "등급은 실제 보안 진단이 아닙니다. 탄막과 강화는 학습을 위한 비유입니다.", 94, 63, 16, MUTED)
        self.draw_board(1200, 130, 620, 815, result=True)

    def on_close(self):
        if hasattr(self, "worker") and not self.closed_worker:
            self.worker.close()
            self.closed_worker = True
        super().on_close()

    def shutdown(self):
        if not self.closed_worker:
            self.worker.close()
            self.closed_worker = True
        self.close()
