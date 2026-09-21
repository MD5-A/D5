"""Boucle principale et coordination des objets du jeu."""

import pygame

from .combat import Bullet
from .player import Player
from .ui import HUD
from .world import World


class Game:
    """Orchestre le monde, les joueurs, les projectiles et l'affichage."""

    SIZE = (960, 540)

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption("Plateforme PvP")
        self.clock = pygame.time.Clock()
        self.world = World(*self.SIZE)
        self.players = [
            Player((140, 300), (70, 150, 255), {
                "left": pygame.K_q, "right": pygame.K_d,
                "jump": pygame.K_SPACE, "attack": pygame.K_e,
            }),
            Player((780, 300), (240, 80, 80), {
                "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
                "jump": pygame.K_UP, "attack": pygame.K_RETURN,
            }),
        ]
        self.bullets = pygame.sprite.Group()
        self.hud = HUD(pygame.font.Font(None, 26))
        self.running = True

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self) -> None:
        keys = pygame.key.get_pressed()
        for player in self.players:
            if player.handle_input(keys):
                self.bullets.add(Bullet(player.rect.center, player.facing, player))
            self.world.apply_gravity(player)
            player.rect.clamp_ip(self.screen.get_rect())

        self.bullets.update(self.screen)
        for bullet in list(self.bullets):
            target = self.players[1] if bullet.owner is self.players[0] else self.players[0]
            if bullet.rect.colliderect(target.rect):
                target.health = max(0, target.health - Bullet.DAMAGE)
                bullet.kill()

    def draw(self) -> None:
        self.screen.fill((25, 30, 50))
        self.world.draw(self.screen)
        for player in self.players:
            player.draw(self.screen)
        self.bullets.draw(self.screen)
        self.hud.draw(self.screen, self.players)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

