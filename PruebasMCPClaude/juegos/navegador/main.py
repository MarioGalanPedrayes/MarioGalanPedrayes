"""SYNTH//SWARM — a bite-sized neon survival roguelite.

Desktop: WASD / arrows to move, SPACE to dash, 1-3 to pick upgrades.
Browser: Pygbag-compatible; touch the left side to steer and right side to dash.
"""
import asyncio
import math
import random
from datetime import date
import pygame

WIDTH, HEIGHT = 960, 640
FPS = 60
BG = (7, 9, 22)
WHITE = (240, 248, 255)
MUTED = (127, 145, 177)
CYAN = (49, 238, 235)
PINK = (255, 71, 179)
PURPLE = (155, 92, 255)
GOLD = (255, 202, 88)
RED = (255, 80, 104)
GREEN = (112, 255, 169)

pygame.init()
pygame.display.set_caption("SYNTH//SWARM")
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()
FONT_CACHE = {}
GLOW_CACHE = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in FONT_CACHE:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        FONT_CACHE[key] = f
    return FONT_CACHE[key]


def text(surface, value, x, y, size=24, color=WHITE, bold=False, center=False):
    image = font(size, bold).render(str(value), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    surface.blit(image, rect)
    return rect


def glow(surface, x, y, radius, color, strength=1.0):
    radius = max(2, int(radius))
    key = (radius, color, round(strength, 2))
    image = GLOW_CACHE.get(key)
    if image is None:
        image = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        cx = cy = radius * 2
        for ring in range(7, 0, -1):
            rr = max(1, int(radius * ring / 3.5))
            alpha = max(3, int(25 * strength * (1 - ring / 9)))
            pygame.draw.circle(image, (*color, alpha), (cx, cy), rr)
        pygame.draw.circle(image, (*color, min(255, int(90 * strength))), (cx, cy), radius)
        GLOW_CACHE[key] = image
    surface.blit(image, (int(x - image.get_width() / 2), int(y - image.get_height() / 2)))


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def unit(x, y):
    length = math.hypot(x, y)
    if length <= 0.0001:
        return 0.0, 0.0
    return x / length, y / length


def circle_hit(ax, ay, ar, bx, by, br):
    return (ax - bx) ** 2 + (ay - by) ** 2 <= (ar + br) ** 2


UPGRADES = [
    ("OVERDRIVE", "Fire 22% faster", CYAN),
    ("ION CORE", "+1 bullet damage", PURPLE),
    ("NEON ENGINE", "+16% movement speed", GREEN),
    ("MAGNET FIELD", "Collect energy from farther away", GOLD),
    ("DOUBLE TAP", "Fire an extra side shot", PINK),
    ("PHASE SKIN", "+1 max HP and heal 1", CYAN),
    ("QUICK SHIFT", "Dash recharges 25% faster", PURPLE),
    ("PIERCING BYTE", "Bullets pierce one more enemy", GOLD),
]


class Game:
    def __init__(self):
        self.scene = pygame.Surface((WIDTH, HEIGHT))
        self.stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 1, 1, 2))) for _ in range(110)]
        self.daily_seed = int(date.today().strftime("%Y%m%d"))
        self.reset_run()
        self.state = "menu"
        self.session_best = 0
        self.joy_active = False
        self.joy_origin = (100, HEIGHT - 100)
        self.joy_pos = self.joy_origin
        self.last_pointer = (0, 0)

    def reset_run(self):
        # Keep gameplay spawns and upgrade drafts on separate seeded streams.
        # Cosmetic particles use the unseeded global RNG and cannot affect the daily challenge.
        self.spawn_rng = random.Random(self.daily_seed)
        self.upgrade_rng = random.Random(self.daily_seed ^ 0x5A17C3)
        self.player = {
            "x": WIDTH / 2, "y": HEIGHT / 2, "r": 12, "speed": 245.0,
            "hp": 3, "max_hp": 3, "invuln": 0.0, "dash_cd": 0.0,
            "dash_time": 0.0, "dash_dir": (1.0, 0.0), "fire_cd": 0.0,
            "fire_interval": 0.30, "damage": 1, "extra_shots": 0,
            "magnet": 52.0, "dash_max": 2.4, "pierce": 0,
        }
        self.enemies = []
        self.bullets = []
        self.orbs = []
        self.particles = []
        self.elapsed = 0.0
        self.score = 0
        self.kills = 0
        self.bonus_score = 0
        self.level = 1
        self.xp = 0
        self.xp_needed = 7
        self.spawn_timer = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.upgrade_choices = []
        self.toast = ""
        self.toast_time = 0.0
        self.state = "playing"
        self.joy_active = False

    def add_burst(self, x, y, color, count=10, speed=150):
        for _ in range(count):
            a = random.random() * math.tau
            v = random.uniform(speed * 0.3, speed)
            life = random.uniform(0.20, 0.52)
            self.particles.append({"x": x, "y": y, "vx": math.cos(a)*v, "vy": math.sin(a)*v,
                                  "life": life, "max": life, "color": color, "r": random.uniform(1.5, 3.4)})

    def spawn_enemy(self):
        edge = self.spawn_rng.randrange(4)
        margin = 26
        if edge == 0: x, y = self.spawn_rng.uniform(0, WIDTH), -margin
        elif edge == 1: x, y = WIDTH + margin, self.spawn_rng.uniform(0, HEIGHT)
        elif edge == 2: x, y = self.spawn_rng.uniform(0, WIDTH), HEIGHT + margin
        else: x, y = -margin, self.spawn_rng.uniform(0, HEIGHT)
        t = self.spawn_rng.random()
        wave = 1 + int(self.elapsed // 22)
        if wave >= 3 and t < min(0.22, 0.07 + wave * 0.012):
            kind = "tank"
            hp = 5 + wave // 2
            speed = 48 + min(30, wave * 1.8)
            radius = 18
            color = GOLD
            score = 260
        elif wave >= 2 and t < 0.42:
            kind = "runner"
            hp = 1 + (1 if wave >= 6 and self.spawn_rng.random() < .18 else 0)
            speed = 112 + min(75, wave * 3.0)
            radius = 9
            color = PINK
            score = 150
        else:
            kind = "drone"
            hp = 2 if wave >= 5 and self.spawn_rng.random() < .18 else 1
            speed = 72 + min(55, wave * 2.2)
            radius = 12
            color = RED
            score = 100
        self.enemies.append({"x": x, "y": y, "r": radius, "hp": hp, "max_hp": hp, "speed": speed,
                             "kind": kind, "color": color, "score": score, "phase": random.random()*math.tau})

    def fire(self):
        p = self.player
        if not self.enemies:
            return
        target = min(self.enemies, key=lambda e: (e["x"]-p["x"])**2 + (e["y"]-p["y"])**2)
        dx, dy = unit(target["x"]-p["x"], target["y"]-p["y"])
        spread = [-0.12, 0.12] if p["extra_shots"] else []
        dirs = [(dx, dy)]
        for a in spread:
            ca, sa = math.cos(a), math.sin(a)
            dirs.append((dx*ca-dy*sa, dx*sa+dy*ca))
        for vx, vy in dirs:
            self.bullets.append({"x": p["x"]+vx*17, "y": p["y"]+vy*17, "vx": vx*570, "vy": vy*570,
                                 "r": 4, "damage": p["damage"], "pierce": p["pierce"], "life": 1.15})
        self.add_burst(p["x"]+dx*15, p["y"]+dy*15, CYAN, 2, 45)

    def trigger_dash(self, mx=0, my=0):
        p = self.player
        if p["dash_cd"] > 0 or self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if abs(mx) + abs(my) > 0.05:
            dx, dy = mx, my
        if dx == 0 and dy == 0:
            dx, dy = p["dash_dir"]
        dx, dy = unit(dx, dy)
        p["dash_dir"] = (dx, dy)
        p["dash_time"] = 0.16
        p["dash_cd"] = p["dash_max"]
        p["invuln"] = max(p["invuln"], 0.24)
        self.add_burst(p["x"], p["y"], CYAN, 12, 230)

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_needed
        self.xp_needed = int(7 + self.level * 2.6)
        self.upgrade_choices = self.upgrade_rng.sample(UPGRADES, 3)
        self.state = "upgrade"
        self.add_burst(self.player["x"], self.player["y"], PURPLE, 24, 200)

    def apply_upgrade(self, idx):
        if idx < 0 or idx >= len(self.upgrade_choices):
            return
        name = self.upgrade_choices[idx][0]
        p = self.player
        if name == "OVERDRIVE": p["fire_interval"] *= 0.78
        elif name == "ION CORE": p["damage"] += 1
        elif name == "NEON ENGINE": p["speed"] *= 1.16
        elif name == "MAGNET FIELD": p["magnet"] += 65
        elif name == "DOUBLE TAP": p["extra_shots"] += 1
        elif name == "PHASE SKIN": p["max_hp"] += 1; p["hp"] = min(p["max_hp"], p["hp"] + 1)
        elif name == "QUICK SHIFT": p["dash_max"] *= 0.75
        elif name == "PIERCING BYTE": p["pierce"] += 1
        self.state = "playing"
        self.toast = name + " ACQUIRED"
        self.toast_time = 1.4

    def handle_click(self, pos):
        x, y = pos
        self.last_pointer = pos
        if self.state == "menu":
            self.reset_run()
            return
        if self.state == "gameover":
            if 300 <= x <= 660 and 440 <= y <= 510:
                self.reset_run()
            return
        if self.state == "upgrade":
            for i in range(3):
                rect = pygame.Rect(65 + i*282, 250, 260, 220)
                if rect.collidepoint(pos):
                    self.apply_upgrade(i)
                    return
        elif self.state == "playing":
            if x > WIDTH * 0.55:
                self.trigger_dash()
            else:
                self.joy_active = True
                self.joy_origin = (x, y)
                self.joy_pos = (x, y)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.KEYDOWN:
            if self.state == "menu" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.reset_run()
            elif self.state == "gameover" and event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                self.reset_run()
            elif self.state == "playing" and event.key in (pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.trigger_dash()
            elif self.state == "upgrade" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.apply_upgrade(event.key - pygame.K_1)
            elif self.state == "playing" and event.key == pygame.K_ESCAPE:
                self.state = "paused"
            elif self.state == "paused" and event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                self.state = "playing"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_click(event.pos)
            elif event.button == 3 and self.state == "playing":
                self.trigger_dash()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.joy_active = False
        elif event.type == pygame.MOUSEMOTION:
            if self.joy_active:
                self.joy_pos = event.pos
        # Native finger events make the virtual joystick reliable on touch screens.
        elif hasattr(pygame, "FINGERDOWN") and event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))
            self.last_pointer = pos
            if self.state == "menu":
                self.reset_run()
            elif self.state == "gameover":
                if 300 <= pos[0] <= 660 and 440 <= pos[1] <= 510:
                    self.reset_run()
            elif self.state == "upgrade":
                self.handle_click(pos)
            elif self.state == "playing":
                if pos[0] > WIDTH * 0.55:
                    self.trigger_dash()
                else:
                    self.joy_active = True
                    self.joy_origin = pos
                    self.joy_pos = pos
        elif hasattr(pygame, "FINGERMOTION") and event.type == pygame.FINGERMOTION:
            if self.joy_active:
                self.joy_pos = (int(event.x * WIDTH), int(event.y * HEIGHT))
        elif hasattr(pygame, "FINGERUP") and event.type == pygame.FINGERUP:
            self.joy_active = False

    def update(self, dt):
        if self.state != "playing":
            return
        p = self.player
        self.elapsed += dt
        self.score = self.kills * 100 + self.bonus_score + int(self.elapsed * 8) + (self.level - 1) * 250
        wave = 1 + int(self.elapsed // 22)
        self.spawn_timer -= dt
        spawn_gap = max(0.19, 0.78 - self.elapsed * 0.008)
        if self.spawn_timer <= 0 and len(self.enemies) < 72:
            self.spawn_enemy()
            self.spawn_timer = spawn_gap * self.spawn_rng.uniform(.72, 1.18)
            if wave >= 4 and self.spawn_rng.random() < min(.45, (wave-2)*.07):
                self.spawn_enemy()

        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if self.joy_active:
            jx = self.joy_pos[0] - self.joy_origin[0]
            jy = self.joy_pos[1] - self.joy_origin[1]
            mag = math.hypot(jx, jy)
            if mag > 8:
                dx, dy = jx / max(mag, 1), jy / max(mag, 1)
                scale = min(1.0, mag / 52)
                dx, dy = dx*scale, dy*scale
        dx, dy = unit(dx, dy) if abs(dx)+abs(dy) > 1.02 else (dx, dy)
        p["dash_cd"] = max(0.0, p["dash_cd"] - dt)
        p["dash_time"] = max(0.0, p["dash_time"] - dt)
        p["invuln"] = max(0.0, p["invuln"] - dt)
        if p["dash_time"] > 0:
            dx, dy = p["dash_dir"]
            speed = 760
        else:
            speed = p["speed"]
        if abs(dx) + abs(dy) > .03:
            p["dash_dir"] = unit(dx, dy)
        p["x"] = clamp(p["x"] + dx*speed*dt, 18, WIDTH-18)
        p["y"] = clamp(p["y"] + dy*speed*dt, 26, HEIGHT-18)

        p["fire_cd"] -= dt
        if p["fire_cd"] <= 0 and self.enemies:
            self.fire()
            p["fire_cd"] = p["fire_interval"]

        for b in self.bullets[:]:
            b["x"] += b["vx"]*dt; b["y"] += b["vy"]*dt; b["life"] -= dt
            hit = None
            for e in self.enemies:
                if circle_hit(b["x"], b["y"], b["r"], e["x"], e["y"], e["r"]):
                    hit = e; break
            if hit:
                hit["hp"] -= b["damage"]
                self.add_burst(b["x"], b["y"], hit["color"], 4, 85)
                if b["pierce"] > 0:
                    b["pierce"] -= 1
                    b["damage"] = max(1, b["damage"] - 1)
                    b["x"] += b["vx"]*dt*1.8
                    b["y"] += b["vy"]*dt*1.8
                else:
                    if b in self.bullets: self.bullets.remove(b)
            elif b["life"] <= 0 or b["x"] < -30 or b["x"] > WIDTH+30 or b["y"] < -30 or b["y"] > HEIGHT+30:
                if b in self.bullets: self.bullets.remove(b)

        for e in self.enemies[:]:
            ex, ey = unit(p["x"]-e["x"], p["y"]-e["y"])
            e["phase"] += dt * (2.0 if e["kind"] == "runner" else 1.0)
            wobble = math.sin(e["phase"] * 2) * (18 if e["kind"] == "runner" else 5)
            e["x"] += (ex*e["speed"] - ey*wobble)*dt
            e["y"] += (ey*e["speed"] + ex*wobble)*dt
            if e["hp"] <= 0:
                self.kills += 1
                self.add_burst(e["x"], e["y"], e["color"], 15 if e["kind"] == "tank" else 9, 175)
                self.orbs.append({"x": e["x"], "y": e["y"], "r": 6, "value": 1, "phase": random.random()*math.tau})
                if e["kind"] == "tank":
                    self.orbs.append({"x": e["x"]+8, "y": e["y"]+4, "r": 6, "value": 1, "phase": random.random()*math.tau})
                self.bonus_score += max(0, e["score"] - 100)
                self.enemies.remove(e)
                continue
            if circle_hit(p["x"], p["y"], p["r"], e["x"], e["y"], e["r"]) and p["invuln"] <= 0:
                p["hp"] -= 1
                p["invuln"] = 1.15
                self.shake = 0.28
                self.flash = 0.14
                self.add_burst(p["x"], p["y"], RED, 18, 210)
                e["x"] -= ex*26; e["y"] -= ey*26
                if p["hp"] <= 0:
                    self.session_best = max(self.session_best, self.score)
                    self.state = "gameover"
                    return

        for orb in self.orbs[:]:
            orb["phase"] += dt*3
            vx, vy = p["x"]-orb["x"], p["y"]-orb["y"]
            dist = math.hypot(vx, vy)
            if dist < p["magnet"] + 38:
                nx, ny = unit(vx, vy)
                pull = 240 if dist < p["magnet"] else 115
                orb["x"] += nx*pull*dt; orb["y"] += ny*pull*dt
            if dist < p["r"] + orb["r"] + 4:
                self.xp += orb["value"]
                self.add_burst(orb["x"], orb["y"], CYAN, 5, 95)
                self.orbs.remove(orb)
                if self.xp >= self.xp_needed:
                    self.level_up()
                    break

        for pt in self.particles[:]:
            pt["x"] += pt["vx"]*dt; pt["y"] += pt["vy"]*dt
            pt["vx"] *= max(0, 1-2.3*dt); pt["vy"] *= max(0, 1-2.3*dt)
            pt["life"] -= dt
            if pt["life"] <= 0: self.particles.remove(pt)
        self.shake = max(0, self.shake-dt)
        self.flash = max(0, self.flash-dt)
        self.toast_time = max(0, self.toast_time-dt)

    def draw_background(self, surface):
        surface.fill(BG)
        # Subtle vertical colour wash, the grid is deliberately restrained.
        for y in range(0, HEIGHT, 4):
            shade = int(7 + 7 * (1 - y / HEIGHT))
            pygame.draw.line(surface, (shade, shade+1, shade+14), (0, y), (WIDTH, y))
        for x in range(0, WIDTH, 48):
            pygame.draw.line(surface, (17, 24, 47), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 48):
            pygame.draw.line(surface, (17, 24, 47), (0, y), (WIDTH, y), 1)
        for x, y, r in self.stars:
            surface.fill((29, 48, 76), (x, y, r, r))
        pygame.draw.rect(surface, (29, 55, 83), (9, 9, WIDTH-18, HEIGHT-18), 1, border_radius=14)

    def draw_enemy(self, surface, e):
        x, y, r, c = int(e["x"]), int(e["y"]), e["r"], e["color"]
        glow(surface, x, y, r*1.35, c, .75)
        if e["kind"] == "tank":
            points = [(x, y-r), (x+r, y-r//2), (x+r, y+r//2), (x, y+r), (x-r, y+r//2), (x-r, y-r//2)]
            pygame.draw.polygon(surface, (38, 31, 43), points)
            pygame.draw.polygon(surface, c, points, 2)
            pygame.draw.circle(surface, c, (x, y), 4)
        elif e["kind"] == "runner":
            points = [(x, y-r-2), (x+r+2, y), (x, y+r+2), (x-r-2, y)]
            pygame.draw.polygon(surface, (43, 23, 48), points)
            pygame.draw.polygon(surface, c, points, 2)
            pygame.draw.circle(surface, WHITE, (x, y), 2)
        else:
            pygame.draw.circle(surface, (40, 25, 39), (x, y), r)
            pygame.draw.circle(surface, c, (x, y), r, 2)
            pygame.draw.circle(surface, c, (x, y), 3)
        if e["hp"] < e["max_hp"]:
            w = r*2
            pygame.draw.rect(surface, (43, 39, 57), (x-w//2, y-r-9, w, 3), border_radius=2)
            pygame.draw.rect(surface, c, (x-w//2, y-r-9, int(w*max(0,e["hp"])/e["max_hp"]), 3), border_radius=2)

    def draw_player(self, surface):
        p = self.player
        x, y, r = int(p["x"]), int(p["y"]), p["r"]
        if p["invuln"] > 0 and int(p["invuln"]*16) % 2 == 0:
            return
        glow(surface, x, y, 24, CYAN, 1.0)
        angle = math.atan2(p["dash_dir"][1], p["dash_dir"][0])
        # Point the avatar toward its latest movement direction.
        vertices = []
        for a, rr in ((0, r+5), (2.35, r), (math.pi, r+2), (math.tau-2.35, r)):
            aa = angle + a
            vertices.append((x + math.cos(aa)*rr, y + math.sin(aa)*rr))
        pygame.draw.polygon(surface, (17, 48, 61), vertices)
        pygame.draw.polygon(surface, CYAN, vertices, 2)
        pygame.draw.circle(surface, WHITE, (x, y), 3)
        if p["dash_cd"] <= 0:
            pygame.draw.circle(surface, (40, 112, 125), (x, y), r+9, 1)

    def draw_hud(self, surface):
        p = self.player
        pygame.draw.rect(surface, (11, 16, 36), (24, 22, 236, 84), border_radius=12)
        pygame.draw.rect(surface, (38, 62, 95), (24, 22, 236, 84), 1, border_radius=12)
        text(surface, "SCORE", 40, 34, 17, MUTED, True)
        text(surface, f"{self.score:06d}", 40, 52, 34, WHITE, True)
        text(surface, f"LVL {self.level:02d}", 202, 39, 17, CYAN, True)
        wave = 1 + int(self.elapsed // 22)
        text(surface, f"WAVE {wave:02d}", WIDTH-140, 30, 18, PINK, True)
        text(surface, f"{int(self.elapsed//60):02d}:{int(self.elapsed%60):02d}", WIDTH-140, 52, 24, WHITE, True)
        # Health pips
        text(surface, "CORE", 30, 120, 15, MUTED, True)
        for i in range(p["max_hp"]):
            col = RED if i < p["hp"] else (43, 47, 69)
            pygame.draw.rect(surface, col, (83+i*20, 123, 13, 9), border_radius=3)
        # XP bar across the top
        bar = pygame.Rect(285, 27, 390, 7)
        pygame.draw.rect(surface, (30, 39, 65), bar, border_radius=4)
        fill = int(bar.width * min(1.0, self.xp / max(1, self.xp_needed)))
        if fill:
            pygame.draw.rect(surface, CYAN, (bar.x, bar.y, fill, bar.height), border_radius=4)
        text(surface, f"ENERGY  {self.xp}/{self.xp_needed}", 285, 40, 15, MUTED)
        # Dash cooldown marker
        pygame.draw.circle(surface, (23, 47, 65), (WIDTH-43, HEIGHT-42), 23)
        pygame.draw.circle(surface, CYAN if p["dash_cd"] <= 0 else (67, 100, 126), (WIDTH-43, HEIGHT-42), 23, 2)
        text(surface, "DASH" if p["dash_cd"] <= 0 else f"{p['dash_cd']:.1f}", WIDTH-43, HEIGHT-42, 15, CYAN if p["dash_cd"] <= 0 else MUTED, True, True)
        text(surface, "WASD / ARROWS · SPACE DASH", 30, HEIGHT-34, 15, (103, 126, 157), True)
        if self.toast_time > 0:
            text(surface, self.toast, WIDTH/2, 93, 19, GOLD, True, True)
        if self.joy_active:
            ox, oy = self.joy_origin; jx, jy = self.joy_pos
            pygame.draw.circle(surface, (32, 67, 86), (int(ox), int(oy)), 38, 2)
            pygame.draw.circle(surface, (*CYAN, 100), (int(jx), int(jy)), 14, 2)

    def draw_menu(self, surface):
        self.draw_background(surface)
        t = pygame.time.get_ticks() / 1000
        cx, cy = WIDTH/2, HEIGHT/2 - 48
        for i, r in enumerate((90, 125, 160)):
            pygame.draw.circle(surface, (28+i*4, 48+i*3, 76+i*2), (int(cx), int(cy)), r, 1)
        glow(surface, cx, cy, 60, CYAN, .65)
        for i in range(8):
            a = t*.45 + i*math.tau/8
            x, y = cx+math.cos(a)*124, cy+math.sin(a)*124
            glow(surface, x, y, 9, PINK if i%2 else CYAN, .8)
            pygame.draw.circle(surface, PINK if i%2 else CYAN, (int(x), int(y)), 3)
        text(surface, "SYNTH", cx, 167, 88, WHITE, True, True)
        text(surface, "// SWARM", cx, 222, 42, CYAN, True, True)
        text(surface, "ONE SEED. ENDLESS WAYS TO SURVIVE.", cx, 286, 19, MUTED, True, True)
        text(surface, f"DAILY SEED  {self.daily_seed}", cx, 319, 16, GOLD, True, True)
        btn = pygame.Rect(330, 370, 300, 64)
        pygame.draw.rect(surface, (17, 39, 58), btn, border_radius=13)
        pygame.draw.rect(surface, CYAN, btn, 2, border_radius=13)
        glow(surface, cx, 400, 40, CYAN, .4)
        text(surface, "ENTER THE SWARM  →", cx, 402, 24, WHITE, True, True)
        text(surface, "MOVE  WASD / ARROWS", cx, 475, 18, MUTED, True, True)
        text(surface, "AUTO-FIRE  ·  COLLECT ENERGY  ·  PICK YOUR UPGRADES", cx, 503, 15, MUTED, False, True)
        text(surface, "PHONE? HOLD LEFT SIDE TO MOVE · TAP RIGHT SIDE TO DASH", cx, 532, 15, (89, 132, 151), False, True)
        text(surface, "A tiny neon survival game built with Python + Pygame", cx, 592, 15, (61, 82, 111), False, True)

    def draw_upgrade(self, surface):
        self.draw_world(surface)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 7, 18, 205)); surface.blit(veil, (0, 0))
        text(surface, "LEVEL UP", WIDTH/2, 125, 51, WHITE, True, True)
        text(surface, "PICK ONE PROTOCOL · PRESS 1 / 2 / 3", WIDTH/2, 174, 18, CYAN, True, True)
        for i, (name, desc, color) in enumerate(self.upgrade_choices):
            rect = pygame.Rect(65 + i*282, 235, 260, 238)
            pygame.draw.rect(surface, (13, 19, 41), rect, border_radius=15)
            pygame.draw.rect(surface, color, rect, 2, border_radius=15)
            glow(surface, rect.centerx, rect.y+50, 37, color, .6)
            pygame.draw.circle(surface, color, (rect.centerx, rect.y+50), 9, 2)
            text(surface, f"0{i+1}", rect.x+20, rect.y+18, 18, color, True)
            text(surface, name, rect.centerx, rect.y+104, 21, WHITE, True, True)
            # Wrap short descriptions in two lines if needed.
            if len(desc) > 24:
                words = desc.split(); lines=[]; current=""
                for word in words:
                    if len(current + " " + word) > 24:
                        lines.append(current); current = word
                    else: current = (current + " " + word).strip()
                if current: lines.append(current)
            else:
                lines = [desc]
            for j, line in enumerate(lines[:2]): text(surface, line, rect.centerx, rect.y+143+j*22, 17, MUTED, False, True)
            text(surface, "SELECT", rect.centerx, rect.y+204, 16, color, True, True)
        text(surface, "YOUR BUILD. YOUR RULES.", WIDTH/2, 522, 17, MUTED, True, True)

    def draw_world(self, surface):
        self.draw_background(surface)
        for orb in self.orbs:
            x, y = int(orb["x"]), int(orb["y"])
            glow(surface, x, y, 12, CYAN, .65)
            a = orb["phase"]
            pts = [(x+math.cos(a+i*math.pi/2)*orb["r"], y+math.sin(a+i*math.pi/2)*orb["r"]) for i in range(4)]
            pygame.draw.polygon(surface, CYAN, pts, 2)
        for b in self.bullets:
            x, y = int(b["x"]), int(b["y"])
            tailx, taily = x-int(b["vx"]*.018), y-int(b["vy"]*.018)
            pygame.draw.line(surface, (32, 145, 172), (tailx, taily), (x, y), 3)
            glow(surface, x, y, 7, CYAN, .7)
            pygame.draw.circle(surface, WHITE, (x, y), 2)
        for e in self.enemies: self.draw_enemy(surface, e)
        for pt in self.particles:
            alpha = clamp(pt["life"] / max(.001, pt["max"]), 0, 1)
            rr = max(1, int(pt["r"]*alpha))
            pygame.draw.circle(surface, pt["color"], (int(pt["x"]), int(pt["y"])), rr)
        self.draw_player(surface)
        self.draw_hud(surface)
        if self.flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 65, 100, int(75*self.flash/.14)))
            surface.blit(overlay, (0, 0))

    def draw_pause(self, surface):
        self.draw_world(surface)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((4, 7, 18, 190)); surface.blit(veil, (0,0))
        text(surface, "PAUSED", WIDTH/2, HEIGHT/2-25, 54, WHITE, True, True)
        text(surface, "PRESS ESC OR SPACE TO RESUME", WIDTH/2, HEIGHT/2+27, 19, CYAN, True, True)

    def draw_gameover(self, surface):
        self.draw_world(surface)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((4, 7, 18, 210)); surface.blit(veil, (0,0))
        text(surface, "SIGNAL LOST", WIDTH/2, 130, 55, RED, True, True)
        text(surface, f"{self.score:06d}", WIDTH/2, 204, 68, WHITE, True, True)
        text(surface, "FINAL SCORE", WIDTH/2, 246, 17, MUTED, True, True)
        pygame.draw.line(surface, (48, 66, 94), (300, 280), (660, 280), 1)
        text(surface, f"WAVE  {1+int(self.elapsed//22):02d}", WIDTH/2-100, 315, 21, PINK, True, True)
        text(surface, f"LEVEL  {self.level:02d}", WIDTH/2+100, 315, 21, CYAN, True, True)
        text(surface, f"ELIMINATIONS  {self.kills:03d}", WIDTH/2, 354, 18, MUTED, True, True)
        text(surface, f"SESSION BEST  {self.session_best:06d}", WIDTH/2, 374, 15, (103, 139, 165), True, True)
        share = f"SYNTH//SWARM  |  {self.score:06d} PTS  |  WAVE {1+int(self.elapsed//22)}  |  LVL {self.level}  |  SEED {self.daily_seed}"
        pygame.draw.rect(surface, (13, 19, 37), (210, 385, 540, 35), border_radius=7)
        text(surface, share, WIDTH/2, 402, 14, GOLD, True, True)
        btn = pygame.Rect(330, 442, 300, 58)
        pygame.draw.rect(surface, (17, 39, 58), btn, border_radius=12)
        pygame.draw.rect(surface, CYAN, btn, 2, border_radius=12)
        text(surface, "RUN IT BACK  ↻", WIDTH/2, 470, 23, WHITE, True, True)
        text(surface, "PRESS R / ENTER OR CLICK TO RESTART", WIDTH/2, 528, 16, MUTED, True, True)
        text(surface, "TIP: DASH THROUGH DANGER. DON'T STOP MOVING.", WIDTH/2, 567, 16, (95, 132, 160), False, True)

    def render(self):
        if self.state == "menu": self.draw_menu(self.scene)
        elif self.state == "upgrade": self.draw_upgrade(self.scene)
        elif self.state == "paused": self.draw_pause(self.scene)
        elif self.state == "gameover": self.draw_gameover(self.scene)
        else: self.draw_world(self.scene)
        ox = oy = 0
        if self.shake > 0:
            mag = int(7 * self.shake / .28)
            ox, oy = random.randint(-mag, mag), random.randint(-mag, mag)
        SCREEN.fill(BG)
        SCREEN.blit(self.scene, (ox, oy))
        pygame.display.flip()


async def main():
    game = Game()
    running = True
    while running:
        dt = min(CLOCK.tick(FPS) / 1000.0, 0.035)
        for event in pygame.event.get():
            game.handle_event(event)
        if game.state == "paused":
            pass
        else:
            game.update(dt)
        game.render()
        # Pygbag requires yielding to the browser's event loop each frame.
        await asyncio.sleep(0)
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
