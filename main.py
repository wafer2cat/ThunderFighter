import math
import random
import time
import tkinter as tk


WIDTH, HEIGHT = 480, 760
FPS_MS = 16


class ThunderFighter:
    def __init__(self, root):
        self.root = root
        self.language = "zh"
        self.root.title("雷霆战机 · Thunder Fighter")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg="#050b1c",
            highlightthickness=0
        )
        self.canvas.pack()

        self.keys = set()
        self.state = "menu"
        self.paused = False
        self.last_time = time.perf_counter()
        self.best_score = 0

        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self.stars = []
        for _ in range(90):
            self.stars.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(0, HEIGHT),
                "speed": random.uniform(35, 165),
                "size": random.choice([1, 1, 1, 2]),
                "color": random.choice(["#5674a9", "#87b8ff", "#c3e4ff"]),
            })
        self.reset_game()
        self.loop()

    def t(self, chinese, english):
        """Return the current UI language without changing game logic."""
        return chinese if self.language == "zh" else english

    def toggle_language(self):
        self.language = "en" if self.language == "zh" else "zh"
        self.root.title(self.t("雷霆战机 · Thunder Fighter", "Thunder Fighter · 雷霆战机"))

    def reset_game(self):
        self.player = {
            "x": WIDTH / 2, "y": HEIGHT - 90, "speed": 310,
            "lives": 3, "cooldown": 0, "power": 1,
            "power_timer": 0, "invincible": 0,
        }
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = []
        self.powerups = []
        self.score = 0
        self.wave = 1
        self.wave_timer = 0
        self.spawn_timer = 0
        self.wave_banner = 2.5
        self.boss = None
        self.boss_shot_timer = 0
        self.shake = 0
        self.flash = 0

    def on_key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key in ("return", "space") and self.state in ("menu", "gameover"):
            self.reset_game()
            self.state = "playing"
            self.paused = False
        elif key == "p" and self.state == "playing":
            self.paused = not self.paused
        elif key == "l":
            self.toggle_language()
        elif key == "escape":
            self.root.destroy()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def loop(self):
        now = time.perf_counter()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now
        self.update_background(dt)
        if self.state == "playing" and not self.paused:
            self.update(dt)
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update_background(self, dt):
        for star in self.stars:
            star["y"] += star["speed"] * dt * (1.5 if self.state == "playing" else 0.45)
            if star["y"] > HEIGHT + 3:
                star["y"] = -3
                star["x"] = random.uniform(0, WIDTH)
        self.shake = max(0, self.shake - dt * 4)
        self.flash = max(0, self.flash - dt * 3)

    def update(self, dt):
        p = self.player
        if p["cooldown"] > 0:
            p["cooldown"] -= dt
        if p["power_timer"] > 0:
            p["power_timer"] -= dt
            if p["power_timer"] <= 0:
                p["power"] = 1
        if p["invincible"] > 0:
            p["invincible"] -= dt

        dx = (1 if "right" in self.keys or "d" in self.keys else 0) - \
             (1 if "left" in self.keys or "a" in self.keys else 0)
        dy = (1 if "down" in self.keys or "s" in self.keys else 0) - \
             (1 if "up" in self.keys or "w" in self.keys else 0)
        length = math.hypot(dx, dy) or 1
        p["x"] = max(24, min(WIDTH - 24, p["x"] + dx / length * p["speed"] * dt))
        p["y"] = max(70, min(HEIGHT - 28, p["y"] + dy / length * p["speed"] * dt))

        if ("space" in self.keys or "j" in self.keys) and p["cooldown"] <= 0:
            self.shoot()
            p["cooldown"] = 0.16 if p["power"] < 3 else 0.11

        self.wave_timer += dt
        if self.wave_timer > 25 and self.boss is None:
            self.wave_timer = 0
            self.wave += 1
            self.wave_banner = 2.5
            if self.wave % 5 == 0:
                self.spawn_boss()

        self.wave_banner = max(0, self.wave_banner - dt)
        if self.boss is None:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_enemy()
                self.spawn_timer = max(0.28, 0.85 - self.wave * 0.035)
        else:
            self.update_boss(dt)

        for bullet in self.bullets[:]:
            bullet["y"] -= bullet["speed"] * dt
            bullet["life"] -= dt
            if bullet["y"] < -20 or bullet["life"] <= 0:
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet["x"] += bullet["vx"] * dt
            bullet["y"] += bullet["vy"] * dt
            if bullet["y"] > HEIGHT + 20 or bullet["x"] < -20 or bullet["x"] > WIDTH + 20:
                self.enemy_bullets.remove(bullet)

        for enemy in self.enemies[:]:
            enemy["y"] += enemy["speed"] * dt
            enemy["phase"] += dt * enemy["wobble"]
            enemy["x"] += math.sin(enemy["phase"]) * enemy["wobble"] * dt
            enemy["shoot"] -= dt
            if enemy["shoot"] <= 0 and enemy["y"] > 40:
                self.enemy_shoot(enemy)
                enemy["shoot"] = random.uniform(1.1, 2.5)
            if enemy["y"] > HEIGHT + 45:
                self.enemies.remove(enemy)

        for power in self.powerups[:]:
            power["y"] += 100 * dt
            power["spin"] += dt * 5
            if power["y"] > HEIGHT + 30:
                self.powerups.remove(power)

        self.check_collisions()
        self.update_particles(dt)

    def shoot(self):
        p = self.player
        offsets = [0] if p["power"] == 1 else [-11, 11] if p["power"] == 2 else [-18, 0, 18]
        for offset in offsets:
            self.bullets.append({"x": p["x"] + offset, "y": p["y"] - 25,
                                 "speed": 620, "damage": 1, "life": 1.5})
        self.add_particles(p["x"], p["y"] - 27, "#8ff8ff", 2, 0.2)

    def spawn_enemy(self):
        kind = random.choices(["scout", "tank", "zigzag"], weights=[6, 2, 3])[0]
        size = {"scout": 16, "tank": 23, "zigzag": 18}[kind]
        hp = {"scout": 1, "tank": 4, "zigzag": 2}[kind] + self.wave // 6
        self.enemies.append({
            "x": random.randint(25, WIDTH - 25), "y": -35,
            "kind": kind, "size": size, "hp": hp,
            "max_hp": hp, "speed": random.uniform(75, 125) + self.wave * 2,
            "phase": random.random() * 6.28, "wobble": random.uniform(20, 75),
            "shoot": random.uniform(1.4, 3.5),
        })

    def spawn_boss(self):
        self.boss = {"x": WIDTH / 2, "y": -100, "hp": 100 + self.wave * 14,
                     "max_hp": 100 + self.wave * 14, "phase": 0, "entering": True}
        self.enemies.clear()
        self.wave_banner = 3.5

    def update_boss(self, dt):
        b = self.boss
        b["phase"] += dt
        if b["entering"]:
            b["y"] += 80 * dt
            if b["y"] >= 115:
                b["y"] = 115
                b["entering"] = False
        else:
            b["x"] = WIDTH / 2 + math.sin(b["phase"] * 0.75) * 145
            self.boss_shot_timer -= dt
            if self.boss_shot_timer <= 0:
                self.boss_shot_timer = 0.75
                for angle in (-0.45, -0.22, 0, 0.22, 0.45):
                    self.enemy_bullets.append({"x": b["x"], "y": b["y"] + 35,
                                               "vx": math.sin(angle) * 140,
                                               "vy": math.cos(angle) * 180 + 95})

    def enemy_shoot(self, enemy):
        dx = self.player["x"] - enemy["x"]
        dy = self.player["y"] - enemy["y"]
        distance = math.hypot(dx, dy) or 1
        self.enemy_bullets.append({"x": enemy["x"], "y": enemy["y"] + enemy["size"],
                                   "vx": dx / distance * 105, "vy": dy / distance * 105 + 85})

    def check_collisions(self):
        p = self.player
        for bullet in self.bullets[:]:
            target_hit = False
            if self.boss and abs(bullet["x"] - self.boss["x"]) < 55 and abs(bullet["y"] - self.boss["y"]) < 42:
                self.boss["hp"] -= bullet["damage"]
                target_hit = True
                self.add_particles(bullet["x"], bullet["y"], "#ffca6b", 3, 0.35)
                if self.boss["hp"] <= 0:
                    self.score += 5000
                    self.add_particles(self.boss["x"], self.boss["y"], "#ff698a", 45, 1.2)
                    self.powerups.append({"x": self.boss["x"], "y": self.boss["y"], "type": "power", "spin": 0})
                    self.boss = None
                    self.wave += 1
                    self.wave_timer = 0
                    self.wave_banner = 3
                    self.shake = 1
            if target_hit and bullet in self.bullets:
                self.bullets.remove(bullet)
                continue
            for enemy in self.enemies[:]:
                if abs(bullet["x"] - enemy["x"]) < enemy["size"] and abs(bullet["y"] - enemy["y"]) < enemy["size"]:
                    enemy["hp"] -= bullet["damage"]
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.add_particles(bullet["x"], bullet["y"], "#ffb35c", 3, 0.25)
                    if enemy["hp"] <= 0:
                        self.score += {"scout": 100, "tank": 250, "zigzag": 170}[enemy["kind"]]
                        self.add_particles(enemy["x"], enemy["y"], "#ff5c79", 12, 0.6)
                        if random.random() < 0.12:
                            self.powerups.append({"x": enemy["x"], "y": enemy["y"], "type": "power", "spin": 0})
                        self.enemies.remove(enemy)
                    break

        if p["invincible"] <= 0:
            for enemy in self.enemies[:]:
                if abs(p["x"] - enemy["x"]) < enemy["size"] + 12 and abs(p["y"] - enemy["y"]) < enemy["size"] + 14:
                    self.enemies.remove(enemy)
                    self.hit_player()
                    break
            for bullet in self.enemy_bullets[:]:
                if abs(p["x"] - bullet["x"]) < 13 and abs(p["y"] - bullet["y"]) < 16:
                    self.enemy_bullets.remove(bullet)
                    self.hit_player()
                    break

        for power in self.powerups[:]:
            if abs(p["x"] - power["x"]) < 24 and abs(p["y"] - power["y"]) < 25:
                p["power"] = min(3, p["power"] + 1)
                p["power_timer"] = 14
                self.score += 50
                self.powerups.remove(power)
                self.add_particles(power["x"], power["y"], "#58f4bd", 15, 0.6)

    def hit_player(self):
        self.player["lives"] -= 1
        self.player["invincible"] = 2
        self.shake = 0.8
        self.flash = 0.75
        self.add_particles(self.player["x"], self.player["y"], "#7bdcff", 25, 0.8)
        if self.player["lives"] <= 0:
            self.best_score = max(self.best_score, self.score)
            self.state = "gameover"

    def add_particles(self, x, y, color, count, life):
        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(35, 170)
            self.particles.append({"x": x, "y": y, "vx": math.cos(angle) * speed,
                                   "vy": math.sin(angle) * speed, "life": random.uniform(life * .45, life),
                                   "max_life": life, "size": random.uniform(1.5, 4), "color": color})

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["vx"] *= 0.97
            particle["vy"] *= 0.97
            particle["life"] -= dt
            if particle["life"] <= 0:
                self.particles.remove(particle)

    def draw(self):
        self.canvas.delete("all")
        offset_x = random.uniform(-self.shake * 5, self.shake * 5)
        offset_y = random.uniform(-self.shake * 5, self.shake * 5)
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050b1c", outline="")
        self.draw_stars(offset_x, offset_y)

        if self.state == "menu":
            self.draw_menu()
            return

        self.draw_hud()
        for power in self.powerups:
            self.draw_powerup(power, offset_x, offset_y)
        for bullet in self.bullets:
            x, y = bullet["x"] + offset_x, bullet["y"] + offset_y
            self.canvas.create_line(x, y + 8, x, y - 9, fill="#a7fbff", width=3)
            self.canvas.create_line(x, y + 2, x, y - 8, fill="#ffffff", width=1)
        for bullet in self.enemy_bullets:
            x, y = bullet["x"] + offset_x, bullet["y"] + offset_y
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#ff587e", outline="#ffc0cb")
        for enemy in self.enemies:
            self.draw_enemy(enemy, offset_x, offset_y)
        if self.boss:
            self.draw_boss(offset_x, offset_y)
        # draw_player 接收的是战机的绝对坐标，屏幕震动偏移需要叠加到玩家当前位置。
        self.draw_player(self.player["x"] + offset_x, self.player["y"] + offset_y)
        self.draw_particles(offset_x, offset_y)

        if self.wave_banner > 0:
            label = self.t("BOSS 来袭", "BOSS INCOMING") if self.boss else f"{self.t('波次', 'WAVE')}  {self.wave}"
            color = "#ff668c" if self.boss else "#8be9ff"
            self.canvas.create_text(WIDTH / 2, 170, text=label, fill=color,
                                    font=("Segoe UI", 24, "bold"))
            self.canvas.create_text(WIDTH / 2, 198, text=self.t("摧毁所有来犯敌机", "Destroy all incoming enemies"), fill="#718cbf",
                                    font=("Microsoft YaHei UI", 10))

        if self.paused:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#030715", stipple="gray50", outline="")
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=self.t("已暂停", "PAUSED"), fill="#e8f5ff",
                                    font=("Microsoft YaHei UI", 32, "bold"))
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 25, text=self.t("按 P 继续", "Press P to resume"), fill="#83a5c9",
                                    font=("Microsoft YaHei UI", 12))

        if self.state == "gameover":
            self.draw_gameover()

        if self.flash > 0:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#ffffff", stipple="gray50", outline="")

    def draw_stars(self, ox, oy):
        for star in self.stars:
            x, y = star["x"] + ox * 0.2, star["y"] + oy * 0.2
            self.canvas.create_oval(x, y, x + star["size"], y + star["size"], fill=star["color"], outline="")

    def draw_menu(self):
        self.canvas.create_text(WIDTH / 2, 125, text="雷霆战机", fill="#dffaff",
                                font=("Microsoft YaHei UI", 42, "bold"))
        self.canvas.create_text(WIDTH / 2, 172, text="THUNDER  FIGHTER", fill="#6ce8ff",
                                font=("Segoe UI", 13, "bold"))
        self.canvas.create_line(112, 195, 368, 195, fill="#1f7196", width=2)
        self.draw_player(WIDTH / 2, 285, preview=True)
        self.canvas.create_text(WIDTH / 2, 390, text=self.t("ENTER / SPACE  开始游戏", "ENTER / SPACE  START GAME"), fill="#f4f8ff",
                                font=("Microsoft YaHei UI", 15, "bold"))
        self.canvas.create_text(WIDTH / 2, 452, text=self.t("移动   WASD / 方向键", "MOVE   WASD / ARROW KEYS"), fill="#89a8d4",
                                font=("Microsoft YaHei UI", 12))
        self.canvas.create_text(WIDTH / 2, 480, text=self.t("射击   SPACE / J       暂停   P", "FIRE   SPACE / J       PAUSE   P"), fill="#89a8d4",
                                font=("Microsoft YaHei UI", 12))
        self.canvas.create_text(WIDTH / 2, 600, text=self.t("收集绿色能量核心，升级火力至三重射击", "Collect green cores to upgrade to triple-shot"), fill="#4d709f",
                                font=("Microsoft YaHei UI", 10))
        self.canvas.create_text(WIDTH / 2, 670, text=self.t("按 L 切换语言", "Press L to switch language"), fill="#6b8fc0",
                                font=("Microsoft YaHei UI", 10))
        self.canvas.create_text(WIDTH / 2, 718, text=self.t("ESC 退出", "ESC EXIT"), fill="#354b72", font=("Segoe UI", 9))

    def draw_hud(self):
        self.canvas.create_rectangle(0, 0, WIDTH, 55, fill="#09152e", outline="#1d3860")
        self.canvas.create_text(20, 18, anchor="w", text=self.t("分数", "SCORE"), fill="#587aa9", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(20, 38, anchor="w", text=f"{self.score:07d}", fill="#e6f8ff", font=("Segoe UI", 16, "bold"))
        self.canvas.create_text(WIDTH / 2, 18, text=f"{self.t('波次', 'WAVE')} {self.wave}", fill="#7c9bc9", font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(WIDTH / 2, 38, text=self.t("火力", "POWER") + " " + "◆" * self.player["power"] + "◇" * (3 - self.player["power"]),
                                fill="#67e9c0", font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(WIDTH - 20, 18, anchor="e", text=self.t("护盾", "SHIELD"), fill="#587aa9", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(WIDTH - 20, 38, anchor="e", text="♥ " * self.player["lives"], fill="#ff7895", font=("Segoe UI", 16, "bold"))
        if self.boss:
            self.canvas.create_rectangle(95, 64, WIDTH - 95, 70, fill="#19233e", outline="")
            ratio = max(0, self.boss["hp"] / self.boss["max_hp"])
            self.canvas.create_rectangle(95, 64, 95 + (WIDTH - 190) * ratio, 70, fill="#ff5477", outline="")

    def draw_player(self, x=None, y=None, preview=False):
        if x is None:
            x, y = self.player["x"], self.player["y"]
        if not preview and self.player["invincible"] > 0 and int(self.player["invincible"] * 10) % 2 == 0:
            return
        points = [x, y - 27, x - 22, y + 20, x - 7, y + 14, x, y + 28, x + 7, y + 14, x + 22, y + 20]
        self.canvas.create_polygon(points, fill="#2ad6f5", outline="#c8fbff", width=2)
        self.canvas.create_polygon([x, y - 18, x - 7, y + 8, x, y + 3, x + 7, y + 8], fill="#efffff", outline="")
        self.canvas.create_polygon([x - 15, y + 19, x - 8, y + 12, x - 6, y + 28, x - 13, y + 24], fill="#ffb44d", outline="")
        self.canvas.create_polygon([x + 15, y + 19, x + 8, y + 12, x + 6, y + 28, x + 13, y + 24], fill="#ffb44d", outline="")

    def draw_enemy(self, e, ox, oy):
        x, y, s = e["x"] + ox, e["y"] + oy, e["size"]
        color = {"scout": "#e84d73", "tank": "#ff8759", "zigzag": "#ad5ce8"}[e["kind"]]
        self.canvas.create_polygon([x, y + s, x - s, y - s * .65, x - s * .35, y - s * .35,
                                    x, y - s * 1.1, x + s * .35, y - s * .35, x + s, y - s * .65],
                                   fill=color, outline="#ffc5d2", width=1)
        self.canvas.create_oval(x - 4, y - 3, x + 4, y + 5, fill="#37182d", outline="#ffe1aa")
        if e["max_hp"] > 1:
            self.canvas.create_rectangle(x - s, y - s - 8, x + s, y - s - 5, fill="#311f3c", outline="")
            self.canvas.create_rectangle(x - s, y - s - 8, x - s + 2 * s * e["hp"] / e["max_hp"], y - s - 5, fill="#ffbd5a", outline="")

    def draw_boss(self, ox, oy):
        b = self.boss
        x, y = b["x"] + ox, b["y"] + oy
        self.canvas.create_polygon([x, y - 40, x - 58, y - 10, x - 72, y + 28, x - 28, y + 18,
                                    x, y + 50, x + 28, y + 18, x + 72, y + 28, x + 58, y - 10],
                                   fill="#6d2b70", outline="#ff91ab", width=2)
        self.canvas.create_oval(x - 19, y - 19, x + 19, y + 19, fill="#ff546f", outline="#ffe1f0", width=2)
        self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill="#fff2b0", outline="")
        self.canvas.create_line(x - 48, y + 14, x - 25, y + 3, fill="#ffbf5f", width=5)
        self.canvas.create_line(x + 48, y + 14, x + 25, y + 3, fill="#ffbf5f", width=5)

    def draw_powerup(self, power, ox, oy):
        x, y = power["x"] + ox, power["y"] + oy
        r = 13 + math.sin(power["spin"]) * 2
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#0f735f", outline="#74ffd0", width=2)
        self.canvas.create_text(x, y, text="+", fill="#eafff5", font=("Segoe UI", 15, "bold"))

    def draw_particles(self, ox, oy):
        for part in self.particles:
            ratio = max(0, part["life"] / part["max_life"])
            r = part["size"] * ratio
            x, y = part["x"] + ox, part["y"] + oy
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=part["color"], outline="")

    def draw_gameover(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#060916", stipple="gray50", outline="")
        self.canvas.create_text(WIDTH / 2, 260, text=self.t("任务失败", "MISSION FAILED"), fill="#ff6d8b",
                                font=("Microsoft YaHei UI", 35, "bold"))
        self.canvas.create_text(WIDTH / 2, 320, text=f"{self.t('最终分数', 'FINAL SCORE')}  {self.score:07d}", fill="#eaf7ff",
                                font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, 353, text=f"{self.t('最高分', 'BEST SCORE')}  {self.best_score:07d}", fill="#7f9fc8",
                                font=("Segoe UI", 11))
        self.canvas.create_text(WIDTH / 2, 430, text=self.t("ENTER / SPACE  再来一局", "ENTER / SPACE  PLAY AGAIN"), fill="#ffffff",
                                font=("Microsoft YaHei UI", 14, "bold"))
        self.canvas.create_text(WIDTH / 2, 470, text=self.t("ESC 退出", "ESC EXIT"), fill="#7187aa",
                                font=("Segoe UI", 10))


if __name__ == "__main__":
    root = tk.Tk()
    game = ThunderFighter(root)
    root.mainloop()
