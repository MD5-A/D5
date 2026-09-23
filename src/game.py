"""Boucle principale et états du jeu."""

import pygame

from .assets import load_character_animations
from .combat import Bullet
from .player import Player
from .settings import COLOR_BACKGROUND, FPS, SCREEN_SIZE
from .ui import HUD
from .world import World


class Game:
    """Orchestre le menu, la partie et les composants du jeu."""

    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("D5")
        self.clock = pygame.time.Clock()
        self.hud = HUD(pygame.font.Font(None, 26))
        self.state = self.MENU
        self.running = True
        self.world = World(*SCREEN_SIZE)
        self.reset_match()

    def reset_match(self) -> None:
        """Recrée les objets dépendant d'une manche."""
        self.winner = None
        self.players = [
            Player(
                (140, 300),
                (70, 150, 255),
                {"left": pygame.K_q, "right": pygame.K_d, "jump": pygame.K_SPACE, "attack": pygame.K_e},
                load_character_animations("alchemist", "alchemist"),
            ),
            Player(
                (780, 300),
                (240, 80, 80),
                {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP, "attack": pygame.K_RETURN},
                load_character_animations("arcane-mage", "arcane-mage"),
            ),
        ]
        self.bullets = pygame.sprite.Group()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == self.MENU and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset_match()
                    self.state = self.PLAYING
                elif self.state == self.PLAYING and event.key == pygame.K_ESCAPE:
                    self.state = self.MENU
                elif self.state == self.GAME_OVER:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_match()
                        self.state = self.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU

    def update(self, dt: float) -> None:
        if self.state != self.PLAYING:
            return
        keys = pygame.key.get_pressed()
        for player in self.players:
            if player.handle_input(keys):
                self.bullets.add(Bullet(player.rect.center, player.facing, player))
            self.world.apply_gravity(player)
            player.rect.clamp_ip(self.screen.get_rect())
            player.update_visual(dt)

        self.bullets.update(self.screen)
        for bullet in list(self.bullets):
            target = self.players[1] if bullet.owner is self.players[0] else self.players[0]
            if bullet.rect.colliderect(target.rect):
                target.health = max(0, target.health - Bullet.DAMAGE)
                bullet.kill()
                if target.health == 0:
                    self.winner = bullet.owner
                    self.state = self.GAME_OVER
                    break

    def draw(self) -> None:
        self.screen.fill(COLOR_BACKGROUND)
        pygame.draw.circle(self.screen, (38, 48, 83), (self.screen.get_width() - 120, 120), 90)
        pygame.draw.circle(self.screen, (25, 32, 59), (100, 430), 150)
        if self.state == self.MENU:
            self.hud.draw_menu(
                self.screen,
                "D5",
                "Un jeu de combat PvP en arène pour deux joueurs.",
                "Entrée ou Espace pour commencer",
            )
        else:
            self.world.draw(self.screen)
            for player in self.players:
                player.draw(self.screen)
            self.bullets.draw(self.screen)
            self.hud.draw(self.screen, self.players)
            if self.state == self.GAME_OVER:
                winner_number = 1 if self.winner is self.players[0] else 2
                self.hud.draw_game_over(self.screen, f"Joueur {winner_number}")
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
