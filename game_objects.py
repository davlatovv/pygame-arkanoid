import pygame
import random

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Platform(Entity):
    def __init__(self, x, y, width=120, height=20, color=(50, 200, 50)):
        super().__init__(x, y, width, height, color)
        self.speed = 7
        self.laser_mode = False
        self.laser_cooldown = 0

    def update(self, keys, screen_width):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.x = max(0, min(self.rect.x, screen_width - self.rect.width))

    def enable_laser(self, duration=600):
        self.laser_mode = True
        self.laser_cooldown = duration

    def cooldown_tick(self):
        if self.laser_mode:
            self.laser_cooldown -= 1
            if self.laser_cooldown <= 0:
                self.laser_mode = False

class Sphere(Entity):
    def __init__(self, x, y, radius=10, color=(200, 200, 50)):
        super().__init__(x, y, radius * 2, radius * 2, color)
        self.radius = radius
        self.vx = random.choice([-4, 4])
        self.vy = -4

    def update(self, screen_width, screen_height):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Отскок от стен
        if self.rect.left <= 0 or self.rect.right >= screen_width:
            self.vx *= -1
        if self.rect.top <= 0:
            self.vy *= -1

    def bounce(self):
        self.vy *= -1

class Block(Entity):
    def __init__(self, x, y, width=60, height=20, hp=1):
        color = (random.randint(100, 255), random.randint(50, 200), random.randint(50, 200))
        super().__init__(x, y, width, height, color)
        self.hp = hp

    def hit(self):
        self.hp -= 1
        return self.hp <= 0  # True, если кирпич разрушен

class Bonus(Entity):
    def __init__(self, x, y, bonus_type="expand"):
        color_map = {
            "expand": (50, 150, 255),
            "shrink": (255, 100, 50),
            "laser": (255, 0, 0)
        }
        super().__init__(x, y, 20, 20, color_map.get(bonus_type, (255, 255, 255)))
        self.bonus_type = bonus_type
        self.speed = 3

    def update(self):
        self.rect.y += self.speed


class Beam(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 4, 15, (255, 0, 0))
        self.speed = -7

    def update(self):
        self.rect.y += self.speed


class Spark(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 4, 4, (255, 255, 0))
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = 30

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.life -= 1
        if self.life > 0:
            alpha = int((self.life / 30) * 255)
            self.image.set_alpha(alpha)

class LevelBuilder:
    @staticmethod
    def create_level(rows, cols, start_x=50, start_y=50, block_w=60, block_h=20, gap=5):
        bricks = pygame.sprite.Group()
        for r in range(rows):
            for c in range(cols):
                x = start_x + c * (block_w + gap)
                y = start_y + r * (block_h + gap)
                bricks.add(Block(x, y))
        return bricks
