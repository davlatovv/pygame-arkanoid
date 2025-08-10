import pygame
import sys
import random
from game_objects import Platform, Sphere, Block, Bonus, Beam, Spark, LevelBuilder

pygame.init()
clock = pygame.time.Clock()
FPS = 60

SCREEN_W, SCREEN_H = 800, 600
SCREEN = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("PyGame Arkanoid")

BG = pygame.Color("midnightblue")
HUD_FONT = pygame.font.Font(None, 36)
TITLE_FONT = pygame.font.Font(None, 72)
SMALL_FONT = pygame.font.Font(None, 24)

sound_enabled = True
try:
    s_bounce = pygame.mixer.Sound("bounce.wav")
    s_block = pygame.mixer.Sound("block_break.wav")
    s_gameover = pygame.mixer.Sound("game_over.wav")
    s_laser = pygame.mixer.Sound('laser.wav')
except Exception:
    class _Dummy:
        def play(self): pass


    s_bounce = s_block = s_gameover = s_laser = _Dummy()


def play(sound):
    if sound_enabled:
        sound.play()


class GameManager:
    def __init__(self):
        self.reset_all()

    def reset_all(self):
        self.score = 0
        self.lives = 3
        self.level_index = 1
        self.max_levels = 3

        self.platform = Platform(SCREEN_W // 2 - 60, SCREEN_H - 40, width=120, height=14, color=(180, 180, 220))
        self.ball = Sphere(SCREEN_W // 2 - 10, SCREEN_H // 2, radius=10, color=(240, 200, 60))
        self.blocks = LevelBuilder.create_level(rows=4, cols=10, start_x=30, start_y=60, block_w=70, block_h=22, gap=6)
        self.bonuses = []
        self.beams = []
        self.sparks = []

        self.state = "title"
        self.message = ""
        self.message_timer = 0

    def start_level(self, level=None):
        if level is not None:
            self.level_index = level
        rows = 3 + min(6, 1 + self.level_index)  # чуть меняем форму уровней
        cols = 9 + (self.level_index % 2)
        self.blocks = LevelBuilder.create_level(rows=rows, cols=cols, start_x=20, start_y=60, block_w=70, block_h=20,
                                                gap=5)
        self.ball = Sphere(SCREEN_W // 2 - 10, SCREEN_H // 2, radius=10)
        self.platform = Platform(SCREEN_W // 2 - 60, SCREEN_H - 40)
        self.bonuses.clear()
        self.beams.clear()
        self.sparks.clear()
        self.state = "playing"

    def spawn_bonus(self, x, y):
        roll = random.random()
        if roll < 0.12:
            t = random.choice(["expand", "laser", "extra"])
            self.bonuses.append(Bonus(x, y, bonus_type=t))

    def update(self):
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        self.platform.update(keys, SCREEN_W)
        self.platform.cooldown_tick()
        self.ball.update(SCREEN_W, SCREEN_H)

        # Отскок мяча от платформы
        if self.ball.rect.colliderect(self.platform.rect) and self.ball.vy > 0:
            offset = (self.ball.rect.centerx - self.platform.rect.centerx) / (self.platform.rect.width / 2)
            self.ball.vx = self.ball.vx + offset * 2
            self.ball.vy = -abs(self.ball.vy)
            play(s_bounce)
            for _ in range(6):
                self.sparks.append(Spark(self.ball.rect.centerx, self.ball.rect.centery))

        if self.ball.rect.top > SCREEN_H:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "lost"
                play(s_gameover)
            else:
                self.ball = Sphere(SCREEN_W // 2 - 10, SCREEN_H // 2, radius=10)

        for block in list(self.blocks):
            if self.ball.rect.colliderect(block.rect):
                destroyed = block.hit()
                self.ball.vy *= -1
                for _ in range(10):
                    self.sparks.append(Spark(block.rect.centerx, block.rect.centery))
                if destroyed:
                    self.score += 10
                    try:
                        self.blocks.remove(block)
                    except Exception:
                        pass
                    play(s_block)

                    if random.random() < 0.25:
                        self.spawn_bonus(block.rect.centerx, block.rect.centery)

        for bonus in list(self.bonuses):
            bonus.update()
            if bonus.rect.top > SCREEN_H:
                try:
                    self.bonuses.remove(bonus)
                except Exception:
                    pass
            elif bonus.rect.colliderect(self.platform.rect):
                self.apply_bonus(bonus)
                try:
                    self.bonuses.remove(bonus)
                except Exception:
                    pass

        for beam in list(self.beams):
            beam.update()
            if beam.rect.bottom < 0:
                try:
                    self.beams.remove(beam)
                except Exception:
                    pass
            else:
                for block in list(self.blocks):
                    if beam.rect.colliderect(block.rect):
                        destroyed = block.hit()
                        for _ in range(6):
                            self.sparks.append(Spark(block.rect.centerx, block.rect.centery))
                        try:
                            self.beams.remove(beam)
                        except Exception:
                            pass
                        if destroyed:
                            self.score += 10
                            try:
                                self.blocks.remove(block)
                            except Exception:
                                pass
                        break

        for sp in list(self.sparks):
            sp.update()
            if getattr(sp, "life", 0) <= 0:
                try:
                    self.sparks.remove(sp)
                except Exception:
                    pass

        if len(self.blocks) == 0:
            self.level_index += 1
            if self.level_index > self.max_levels:
                self.state = "won"
            else:
                self.start_level(self.level_index)

        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""

    def apply_bonus(self, bonus):
        if bonus.bonus_type == "expand":
            current_center = self.platform.rect.centerx
            self.platform.rect.width = min(SCREEN_W - 20, self.platform.rect.width + 60)
            self.platform.rect.centerx = current_center
            self.message = "Platform expanded!"
            self.message_timer = FPS * 3
        elif bonus.bonus_type == "laser":
            self.platform.enable_laser(duration=FPS * 8)
            self.message = "Laser enabled!"
            self.message_timer = FPS * 3
        elif bonus.bonus_type == "extra":
            self.lives += 1
            self.message = "Extra life!"
            self.message_timer = FPS * 3

    def fire_lasers(self):
        if self.platform.laser_mode:
            left_x = self.platform.rect.left + 8
            right_x = self.platform.rect.right - 12
            self.beams.append(Beam(left_x, self.platform.rect.top - 10))
            self.beams.append(Beam(right_x, self.platform.rect.top - 10))

    def draw(self, surface):
        surface.fill(BG)
        for block in self.blocks:
            block.draw(surface)

        self.platform.draw(surface)
        self.ball.draw(surface)
        for b in self.bonuses:
            b.draw(surface)
        for beam in self.beams:
            beam.draw(surface)
        for sp in self.sparks:
            sp.draw(surface)

        score_surf = HUD_FONT.render(f"Score: {self.score}", True, (255, 255, 255))
        lives_surf = HUD_FONT.render(f"Lives: {self.lives}", True, (255, 255, 255))
        level_surf = HUD_FONT.render(f"Level: {self.level_index}", True, (255, 255, 255))
        surface.blit(score_surf, (12, 8))
        surface.blit(lives_surf, (SCREEN_W - lives_surf.get_width() - 12, 8))
        surface.blit(level_surf, (SCREEN_W // 2 - level_surf.get_width() // 2, 8))

        if self.message:
            msg = SMALL_FONT.render(self.message, True, (255, 240, 180))
            surface.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H - 30))

        if self.state == "title":
            title = TITLE_FONT.render("PyGame Arkanoid", True, (255, 255, 255))
            hint = SMALL_FONT.render("Press SPACE to begin — Left/Right to move — L to toggle sound", True,
                                     (230, 230, 230))
            surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))
            surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 10))
        elif self.state == "paused":
            p = TITLE_FONT.render("PAUSED", True, (255, 255, 255))
            surface.blit(p, (SCREEN_W // 2 - p.get_width() // 2, SCREEN_H // 2 - 20))
        elif self.state == "won":
            w = TITLE_FONT.render("YOU WIN!", True, (255, 220, 100))
            surface.blit(w, (SCREEN_W // 2 - w.get_width() // 2, SCREEN_H // 2 - 20))
        elif self.state == "lost":
            l = TITLE_FONT.render("GAME OVER", True, (255, 80, 80))
            surface.blit(l, (SCREEN_W // 2 - l.get_width() // 2, SCREEN_H // 2 - 20))


def main():
    global sound_enabled
    gm = GameManager()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if gm.state == "title":
                        gm.start_level(1)
                    elif gm.state in ("won", "lost"):
                        gm.reset_all()
                    elif gm.state == "playing":
                        gm.state = "paused"
                    elif gm.state == "paused":
                        gm.state = "playing"

                if event.key == pygame.K_l:
                    sound_enabled = not sound_enabled

                if event.key == pygame.K_f and gm.platform.laser_mode and gm.state == "playing":
                    gm.fire_lasers()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if gm.state == "title":
                    gm.start_level(1)

        gm.update()

        gm.draw(SCREEN)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
