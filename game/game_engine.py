import math
import random
import pygame
from game.block import Block
from game.effects import Debris, FloatingText


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


class GameEngine:
    # Pixels of misalignment still counted as a perfect drop.
    PERFECT_TOLERANCE = 5
    # Width regained per perfect drop once a streak of 2+ is running.
    RESTORE_AMOUNT = 10
    # Keep the top of the tower at least this far down the screen.
    CAMERA_THRESHOLD = 210
    # Ignore restart input briefly so a rapid drop key doesn't skip the collapse screen.
    RESTART_DELAY_FRAMES = 30

    # (altitude in blocks, sky colour at top of screen, sky colour at bottom)
    SKY_STAGES = [
        (0,  (120, 175, 230), (250, 200, 150)),   # Hazy sunrise near street level
        (8,  (60, 135, 225),  (160, 205, 245)),   # Clear daytime sky
        (16, (35, 70, 160),   (105, 150, 220)),   # Upper atmosphere
        (26, (40, 25, 90),    (120, 70, 150)),    # Violet stratosphere
        (38, (6, 6, 20),      (25, 20, 55)),      # Edge of space
    ]

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.block_gap = 4
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        self.stars = [
            (random.randint(0, width), random.randint(0, height), random.choice([1, 1, 2]), random.random() * 6.28)
            for _ in range(70)
        ]
        self.frame = 0

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.tower_height = 0
        self.game_over = False
        self.game_over_timer = 0

        self.perfect_streak = 0
        self.debris = []
        self.popups = []

        self.camera_y = 0.0
        self.altitude = 0.0

        base_x = (self.width - self.base_width) // 2
        self.ground_y = self.height - 60
        base_block = Block(base_x, self.ground_y, self.base_width, self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - self.block_gap
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        # Head toward the tower from whichever side the block spawns on.
        if random.choice([True, False]):
            start_x, direction = 25, 1
        else:
            start_x, direction = self.width - 25 - top_block.width, -1
        self.active_block = Block(start_x, next_y, top_block.width, self.block_height, color,
                                  speed=speed, direction=direction)

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        is_successful_drop = overlap > 0

        if is_successful_drop:
            if abs(act.x - top_block.x) <= self.PERFECT_TOLERANCE:
                new_block = self.place_perfect(top_block, act)
            else:
                self.perfect_streak = 0
                trimmed_width = max(10.0, overlap)
                new_block = Block(left, act.y, trimmed_width, self.block_height, act.color, speed=0)
                self.spawn_debris(act, left, right)
                self.score += 1

            self.stack.append(new_block)
            self.tower_height += 1
            self.spawn_active_block()
        else:
            # Complete miss: the whole block tumbles away and the tower collapses.
            side = -1 if act.x + act.width / 2 < top_block.x + top_block.width / 2 else 1
            self.debris.append(Debris(act.x, act.y, act.width, act.height, act.color, side))
            self.game_over = True
            self.game_over_timer = 0

    def place_perfect(self, top_block, act):
        """Snap a near-flush drop onto the tower without trimming, and reward streaks."""
        self.perfect_streak += 1
        bonus = 2 * min(self.perfect_streak, 5)
        self.score += 1 + bonus

        x, width = top_block.x, top_block.width
        restored = False
        if self.perfect_streak >= 2 and width < self.base_width:
            grow = min(self.RESTORE_AMOUNT, self.base_width - width)
            x -= grow / 2
            width += grow
            # Keep the widened block inside the arena walls.
            x = max(20, min(x, self.width - 20 - width))
            restored = True

        # Shown just under the HUD so the prompt never covers the block being aimed.
        label = "PERFECT!" if self.perfect_streak < 2 else f"PERFECT! x{self.perfect_streak}"
        detail = f"+{bonus} bonus" + ("  -  width restored" if restored else "")
        self.popups = [
            FloatingText(label, self.width / 2, 96, (255, 235, 120), self.font_big),
            FloatingText(detail, self.width / 2, 130, (255, 255, 255), self.font_hud),
        ]

        return Block(x, act.y, width, self.block_height, act.color, speed=0)

    def spawn_debris(self, act, left, right):
        """Turn each overhanging slice of the dropped block into a falling piece."""
        if act.x < left:
            self.debris.append(Debris(act.x, act.y, left - act.x, act.height, act.color, side=-1))
        act_right = act.x + act.width
        if act_right > right:
            self.debris.append(Debris(right, act.y, act_right - right, act.height, act.color, side=1))

    def handle_event(self, event):
        if self.game_over:
            if self.game_over_timer < self.RESTART_DELAY_FRAMES:
                return
            if (event.type == pygame.KEYDOWN and event.key in (pygame.K_r, pygame.K_SPACE)) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        self.frame += 1

        if self.game_over:
            self.game_over_timer += 1
        else:
            self.active_block.update(self.width)

        # Ease the camera toward keeping the top of the tower below the threshold line.
        target_camera = max(0.0, self.CAMERA_THRESHOLD - self.stack[-1].y)
        self.camera_y = lerp(self.camera_y, target_camera, 0.12)
        self.altitude = lerp(self.altitude, float(self.tower_height), 0.04)

        for d in self.debris:
            d.update()
        self.debris = [d for d in self.debris if not d.is_offscreen(self.height, self.camera_y)]

        for p in self.popups:
            p.update()
        self.popups = [p for p in self.popups if p.alive]

    def sky_colors(self):
        stages = self.SKY_STAGES
        if self.altitude >= stages[-1][0]:
            return stages[-1][1], stages[-1][2]
        for (a0, top0, bot0), (a1, top1, bot1) in zip(stages, stages[1:]):
            if self.altitude < a1:
                t = (self.altitude - a0) / (a1 - a0)
                return lerp_color(top0, top1, t), lerp_color(bot0, bot1, t)
        return stages[0][1], stages[0][2]

    def render_background(self, screen):
        top, bottom = self.sky_colors()
        for y in range(self.height):
            pygame.draw.line(screen, lerp_color(top, bottom, y / self.height), (0, y), (self.width, y))

        # Stars fade in as the climb approaches the edge of space.
        star_strength = max(0.0, min(1.0, (self.altitude - 18) / 18))
        if star_strength > 0:
            for sx, sy, size, phase in self.stars:
                screen_y = int(sy + self.camera_y * 0.15) % self.height
                twinkle = 0.75 + 0.25 * math.sin(phase + self.frame * 0.05)
                sky = lerp_color(top, bottom, screen_y / self.height)
                color = lerp_color(sky, (255, 255, 255), star_strength * twinkle)
                pygame.draw.circle(screen, color, (sx, screen_y), size)

        # Street level sits beneath the foundation and scrolls away as the camera rises.
        ground_top = int(self.ground_y + self.block_height + self.camera_y)
        if ground_top < self.height:
            pygame.draw.rect(screen, (45, 48, 60), (0, ground_top, self.width, self.height - ground_top))
            pygame.draw.line(screen, (90, 95, 110), (0, ground_top), (self.width, ground_top), 2)

    def blit_centered(self, screen, surf, y):
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))

    def render(self, screen):
        self.render_background(screen)

        for b in self.stack:
            b.render(screen, self.camera_y)

        if not self.game_over:
            self.active_block.render(screen, self.camera_y)

        for d in self.debris:
            d.render(screen, self.camera_y)

        for p in self.popups:
            p.render(screen)

        # Translucent HUD panel keeps text readable against every sky colour.
        hud = pygame.Surface((240, 72), pygame.SRCALPHA)
        pygame.draw.rect(hud, (10, 12, 20, 140), hud.get_rect(), border_radius=10)
        screen.blit(hud, (self.width // 2 - 120, 10))

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        self.blit_centered(screen, title_surf, 16)

        hud_text = f"Height: {self.tower_height}    Score: {self.score}"
        score_surf = self.font_hud.render(hud_text, True, (255, 220, 80))
        self.blit_centered(screen, score_surf, 52)

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            self.blit_centered(screen, over_surf, self.height // 2 - 50)

            final_surf = self.font_hud.render(f"Final Height: {self.tower_height}", True, (255, 255, 255))
            self.blit_centered(screen, final_surf, self.height // 2)

            final_score = self.font_hud.render(f"Score: {self.score}", True, (255, 220, 80))
            self.blit_centered(screen, final_score, self.height // 2 + 28)

            if self.game_over_timer >= self.RESTART_DELAY_FRAMES:
                restart_surf = self.font_hud.render("Press [Space] or [R] to Play Again", True, (200, 200, 200))
                self.blit_centered(screen, restart_surf, self.height // 2 + 70)
