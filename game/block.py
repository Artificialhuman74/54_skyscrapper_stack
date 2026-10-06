import pygame

class Block:
    def __init__(self, x, y, width, height, color, speed=0, direction=1):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.color = color
        self.speed = speed
        self.direction = direction

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def update(self, screen_width):
        if self.speed == 0:
            return

        self.x += self.speed * self.direction
        if self.x <= 20:
            self.x = 20
            self.direction = 1
        elif self.x + self.width >= screen_width - 20:
            self.x = screen_width - 20 - self.width
            self.direction = -1

    def render(self, surface, camera_y=0):
        # Blocks live in world space; the camera offset maps them onto the screen.
        draw_rect = self.rect.move(0, int(camera_y))
        pygame.draw.rect(surface, self.color, draw_rect, border_radius=4)
        pygame.draw.rect(surface, (245, 245, 250), draw_rect, width=2, border_radius=4)
