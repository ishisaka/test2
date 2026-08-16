import random
import tkinter as tk

try:
    import winsound
except ImportError:
    winsound = None

WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 7
PLAYER_WIDTH = 36
PLAYER_HEIGHT = 24
PLAYER_Y = HEIGHT - 52
BULLET_SPEED = 11
BULLET_COOLDOWN = 60
ENEMY_BULLET_SPEED = 5
STAR_COUNT = 90


class Game:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#050b18", highlightthickness=0)
        self.canvas.pack()

        self.state = {
            "running": False,
            "game_over": False,
            "score": 0,
            "lives": 3,
            "level": 1,
            "player_x": WIDTH // 2,
            "player_y": PLAYER_Y,
            "bullets": [],
            "enemy_bullets": [],
            "enemies": [],
            "enemy_direction": 1,
            "enemy_step": 1.3,
            "fire_cooldown": 0,
            "enemy_shot_timer": 0,
            "hit_flash": 0,
            "stars": [],
            "message": "Press SPACE to start",
        }

        self.keys = set()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

        self.reset_stars()
        self.spawn_enemies()
        self.tick()

    def reset_stars(self):
        self.state["stars"] = [
            {
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.randint(1, 3),
                "speed": random.randint(1, 3),
            }
            for _ in range(STAR_COUNT)
        ]

    def on_key_press(self, event):
        if event.keysym == "Left":
            self.keys.add("left")
        elif event.keysym == "Right":
            self.keys.add("right")
        elif event.keysym == "space":
            self.keys.add("shoot")
            if not self.state["running"] and not self.state["game_over"]:
                self.start_game()
            elif self.state["game_over"]:
                self.restart_game()

            if self.state["running"] and self.state["fire_cooldown"] <= 0:
                self.fire_player_bullet()
                self.state["fire_cooldown"] = BULLET_COOLDOWN
        elif event.keysym == "r" and self.state["game_over"]:
            self.restart_game()

    def on_key_release(self, event):
        if event.keysym == "Left":
            self.keys.discard("left")
        elif event.keysym == "Right":
            self.keys.discard("right")
        elif event.keysym == "space":
            self.keys.discard("shoot")

    def play_sound(self, kind):
        if winsound is None:
            return

        tones = {
            "start": (660, 120),
            "shoot": (740, 55),
            "enemy_hit": (220, 55),
            "enemy_shot": (180, 50),
            "hit": (120, 100),
            "game_over": (110, 220),
        }
        if kind in tones:
            frequency, duration_ms = tones[kind]
            winsound.Beep(frequency, duration_ms)

    def start_game(self):
        self.state["running"] = True
        self.state["game_over"] = False
        self.state["message"] = ""
        self.play_sound("start")

    def restart_game(self):
        self.state.update(
            {
                "running": True,
                "game_over": False,
                "score": 0,
                "lives": 3,
                "level": 1,
                "player_x": WIDTH // 2,
                "player_y": PLAYER_Y,
                "bullets": [],
                "enemy_bullets": [],
                "enemy_direction": 1,
                "enemy_step": 1.3,
                "fire_cooldown": 0,
                "enemy_shot_timer": 0,
                "hit_flash": 0,
                "message": "",
            }
        )
        self.spawn_enemies()
        self.play_sound("start")

    def spawn_enemies(self):
        cols = 8 + min(2, self.state["level"] // 2)
        rows = 4 + min(2, self.state["level"] // 3)
        enemies = []
        spacing_x = 52
        spacing_y = 42
        offset_x = (WIDTH - (cols - 1) * spacing_x) / 2
        offset_y = 80

        for row in range(rows):
            for col in range(cols):
                enemies.append(
                    {
                        "x": offset_x + col * spacing_x,
                        "y": offset_y + row * spacing_y,
                        "w": 26,
                        "h": 18,
                        "alive": True,
                        "color": self.enemy_color(row),
                    }
                )
        self.state["enemies"] = enemies
        self.state["enemy_direction"] = 1

    def enemy_color(self, row):
        palette = ["#3bf0ff", "#6dff7d", "#ffde59", "#ff7a7a", "#d08cff"]
        return palette[row % len(palette)]

    def tick(self):
        self.update_game()
        self.draw()
        self.root.after(16, self.tick)

    def update_game(self):
        if not self.state["running"]:
            self.animate_stars()
            return

        if self.state["fire_cooldown"] > 0:
            self.state["fire_cooldown"] -= 1
        if self.state["hit_flash"] > 0:
            self.state["hit_flash"] -= 1

        if "shoot" in self.keys and self.state["fire_cooldown"] <= 0:
            self.fire_player_bullet()
            self.state["fire_cooldown"] = BULLET_COOLDOWN

        self.move_player()
        self.move_bullets()
        self.update_enemies()
        self.update_enemy_bullets()
        self.handle_collisions()

        if not self.state["enemies"]:
            self.state["level"] += 1
            self.state["enemy_step"] = min(3.5, self.state["enemy_step"] + 0.25)
            self.spawn_enemies()

        if self.state["lives"] <= 0:
            self.state["running"] = False
            self.state["game_over"] = True
            self.state["message"] = "Game Over! Press R or SPACE to restart"
            self.play_sound("game_over")

        self.animate_stars()

    def animate_stars(self):
        for star in self.state["stars"]:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = -5
                star["x"] = random.randint(0, WIDTH)

    def move_player(self):
        if "left" in self.keys:
            self.state["player_x"] -= PLAYER_SPEED
        if "right" in self.keys:
            self.state["player_x"] += PLAYER_SPEED
        self.state["player_x"] = max(30, min(WIDTH - 30, self.state["player_x"]))

    def fire_player_bullet(self):
        self.state["bullets"].append(
            {
                "x": self.state["player_x"],
                "y": self.state["player_y"] - 10,
                "vx": 0,
                "vy": -BULLET_SPEED,
                "w": 4,
                "h": 12,
                "color": "#5af3ff",
            }
        )
        self.play_sound("shoot")

    def move_bullets(self):
        alive = []
        for bullet in self.state["bullets"]:
            bullet["y"] += bullet["vy"]
            if bullet["y"] > -20 and bullet["y"] < HEIGHT + 20:
                alive.append(bullet)
        self.state["bullets"] = alive

    def update_enemies(self):
        if not self.state["enemies"]:
            return

        min_x = min(enemy["x"] for enemy in self.state["enemies"] if enemy["alive"])
        max_x = max(enemy["x"] + enemy["w"] for enemy in self.state["enemies"] if enemy["alive"])

        if min_x <= 25 or max_x >= WIDTH - 25:
            self.state["enemy_direction"] *= -1
            for enemy in self.state["enemies"]:
                if enemy["alive"]:
                    enemy["y"] += 14

        for enemy in self.state["enemies"]:
            if enemy["alive"]:
                enemy["x"] += self.state["enemy_direction"] * self.state["enemy_step"]

        if any(enemy["alive"] and enemy["y"] + enemy["h"] >= self.state["player_y"] - 12 for enemy in self.state["enemies"]):
            self.state["lives"] = 0
            self.state["running"] = False
            self.state["game_over"] = True
            self.state["message"] = "Game Over! Press R or SPACE to restart"
            return

        self.state["enemy_shot_timer"] += 1
        if self.state["enemy_shot_timer"] >= max(12, 52 - self.state["level"] * 4):
            self.fire_enemy_bullet()
            self.state["enemy_shot_timer"] = 0

    def fire_enemy_bullet(self):
        alive_enemies = [enemy for enemy in self.state["enemies"] if enemy["alive"]]
        if not alive_enemies:
            return
        target = random.choice(alive_enemies)
        self.state["enemy_bullets"].append(
            {
                "x": target["x"] + target["w"] / 2,
                "y": target["y"] + target["h"] + 4,
                "vx": 0,
                "vy": ENEMY_BULLET_SPEED,
                "w": 4,
                "h": 12,
                "color": "#ff8b4d",
            }
        )
        self.play_sound("enemy_shot")

    def update_enemy_bullets(self):
        alive = []
        for bullet in self.state["enemy_bullets"]:
            bullet["y"] += bullet["vy"]
            if bullet["y"] < HEIGHT + 20 and bullet["y"] > -20:
                alive.append(bullet)
        self.state["enemy_bullets"] = alive

    def handle_collisions(self):
        remaining = []
        for enemy in self.state["enemies"]:
            if not enemy["alive"]:
                continue

            for bullet in self.state["bullets"]:
                if (
                    bullet["x"] >= enemy["x"]
                    and bullet["x"] <= enemy["x"] + enemy["w"]
                    and bullet["y"] >= enemy["y"]
                    and bullet["y"] <= enemy["y"] + enemy["h"]
                ):
                    enemy["alive"] = False
                    bullet["y"] = -100
                    self.state["score"] += 10
                    self.play_sound("enemy_hit")
                    break

            if enemy["alive"]:
                remaining.append(enemy)

        self.state["enemies"] = remaining

        if self.state["hit_flash"] <= 0:
            for bullet in self.state["enemy_bullets"]:
                if (
                    bullet["x"] >= self.state["player_x"] - PLAYER_WIDTH / 2
                    and bullet["x"] <= self.state["player_x"] + PLAYER_WIDTH / 2
                    and bullet["y"] >= self.state["player_y"] - PLAYER_HEIGHT / 2
                    and bullet["y"] <= self.state["player_y"] + PLAYER_HEIGHT / 2
                ):
                    self.state["lives"] -= 1
                    self.state["hit_flash"] = 70
                    self.play_sound("hit")
                    bullet["y"] = HEIGHT + 100
                    break

        for bullet in self.state["bullets"]:
            if bullet["y"] < -30:
                bullet["y"] = -100

        self.state["bullets"] = [
            bullet for bullet in self.state["bullets"] if bullet["y"] > -100 and bullet["y"] < HEIGHT + 100
        ]
        self.state["enemy_bullets"] = [
            bullet for bullet in self.state["enemy_bullets"] if bullet["y"] > -100 and bullet["y"] < HEIGHT + 100
        ]

    def draw(self):
        self.canvas.delete("all")
        self.draw_background()
        self.draw_player()
        self.draw_bullets()
        self.draw_enemies()
        self.draw_hud()

    def draw_background(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050b18", outline="")
        for star in self.state["stars"]:
            self.canvas.create_oval(
                star["x"],
                star["y"],
                star["x"] + star["r"],
                star["y"] + star["r"],
                fill="#dfeaff",
                outline=""
            )

    def draw_player(self):
        x = self.state["player_x"]
        y = self.state["player_y"]
        color = "#b3f2ff" if self.state["hit_flash"] == 0 or self.state["hit_flash"] % 10 < 5 else "#ffffff"
        self.canvas.create_polygon(
            x, y - 18,
            x - 18, y + 16,
            x - 6, y + 10,
            x + 6, y + 10,
            x + 18, y + 16,
            fill=color,
            outline="#e6feff",
            width=2,
        )
        self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#fdffb5", outline="#ffffff")

    def draw_bullets(self):
        for bullet in self.state["bullets"]:
            self.canvas.create_rectangle(
                bullet["x"] - 2,
                bullet["y"],
                bullet["x"] + 2,
                bullet["y"] + bullet["h"],
                fill=bullet["color"],
                outline=""
            )
        for bullet in self.state["enemy_bullets"]:
            self.canvas.create_rectangle(
                bullet["x"] - 2,
                bullet["y"],
                bullet["x"] + 2,
                bullet["y"] + bullet["h"],
                fill=bullet["color"],
                outline=""
            )

    def draw_enemies(self):
        for enemy in self.state["enemies"]:
            if not enemy["alive"]:
                continue
            x = enemy["x"]
            y = enemy["y"]
            self.canvas.create_rectangle(x + 5, y + 2, x + enemy["w"] - 5, y + enemy["h"] - 2, fill=enemy["color"], outline="#dff7ff")
            self.canvas.create_oval(x + 5, y + 5, x + 10, y + 10, fill="#0a1430", outline="")
            self.canvas.create_oval(x + enemy["w"] - 10, y + 5, x + enemy["w"] - 5, y + 10, fill="#0a1430", outline="")
            self.canvas.create_rectangle(x + 8, y + enemy["h"] - 6, x + enemy["w"] - 8, y + enemy["h"] - 2, fill="#ffffff", outline="")

    def draw_hud(self):
        self.canvas.create_text(20, 18, anchor="w", text=f"Score: {self.state['score']}", fill="#dfeaff", font=("Courier", 16, "bold"))
        self.canvas.create_text(WIDTH - 120, 18, anchor="w", text=f"Lives: {self.state['lives']}", fill="#ffdd88", font=("Courier", 16, "bold"))
        self.canvas.create_text(WIDTH // 2, 24, text=f"Level {self.state['level']}", fill="#b8c7ff", font=("Courier", 18, "bold"))

        if not self.state["running"]:
            self.canvas.create_rectangle(WIDTH / 2 - 200, HEIGHT / 2 - 70, WIDTH / 2 + 200, HEIGHT / 2 + 70, fill="#091620", outline="#6ed5ff", width=2)
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text=self.state["message"], fill="#f0fbff", font=("Courier", 22, "bold"))
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 45, text="Move: ← →  Shoot: SPACE", fill="#7ef7d1", font=("Courier", 14))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Star Defender")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.resizable(False, False)
    game = Game(root)
    root.mainloop()
