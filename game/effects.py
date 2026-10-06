import random
import pygame


class Debris:
    """A trimmed overhang that tumbles off the tower under gravity."""

    GRAVITY = 0.45

    def __init__(self, x, y, width, height, color, side):
        # Track the centre so rotation pivots around the middle of the piece.
        self.cx = x + width / 2
        self.cy = y + height / 2
        self.vx = side * random.uniform(1.2, 2.6)
        self.vy = random.uniform(-2.5, -0.5)
        self.angle = 0.0
        self.spin = side * -random.uniform(3.0, 7.0)

        self.surface = pygame.Surface((max(1, int(width)), int(height)), pygame.SRCALPHA)
        piece_rect = self.surface.get_rect()
        pygame.draw.rect(self.surface, color, piece_rect, border_radius=4)
        pygame.draw.rect(self.surface, (245, 245, 250), piece_rect, width=2, border_radius=4)

    def update(self):
        self.vy += self.GRAVITY
        self.cx += self.vx
        self.cy += self.vy
        self.angle += self.spin

    def is_offscreen(self, screen_height, camera_y):
        return self.cy + camera_y > screen_height + 80

    def render(self, surface, camera_y):
        rotated = pygame.transform.rotate(self.surface, self.angle)
        dest = rotated.get_rect(center=(int(self.cx), int(self.cy + camera_y)))
        surface.blit(rotated, dest)


class FloatingText:
    """Short-lived screen-space label that drifts upward and fades out."""

    def __init__(self, text, x, y, color, font, lifetime=55):
        self.image = font.render(text, True, color)
        self.shadow = font.render(text, True, (15, 15, 25))
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        self.age += 1
        self.y -= 0.35

    @property
    def alive(self):
        return self.age < self.lifetime

    def render(self, surface):
        fade = 1.0 - max(0.0, (self.age - self.lifetime * 0.5) / (self.lifetime * 0.5))
        alpha = int(255 * fade)
        self.image.set_alpha(alpha)
        self.shadow.set_alpha(alpha)

        pos_x = int(self.x - self.image.get_width() / 2)
        pos_y = int(self.y)
        surface.blit(self.shadow, (pos_x + 2, pos_y + 2))
        surface.blit(self.image, (pos_x, pos_y))
