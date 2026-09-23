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
    PLAYER_NAMES = ("Sam", "Emma")

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
                {
                    "left": pygame.K_q,
                    "right": pygame.K_d,
                    "jump": pygame.K_z,
                    "attack": pygame.K_LSHIFT,
                    "shield": pygame.K_s,
                },
                load_character_animations("alchemist", "alchemist"),
            ),
            Player(
                (780, 300),
                (240, 80, 80),
                {
                    "left": pygame.K_LEFT,
                    "right": pygame.K_RIGHT,
                    "jump": pygame.K_UP,
                    "attack": pygame.K_RSHIFT,
                    "shield": pygame.K_DOWN,
                },
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
            fired = player.handle_input(keys, dt)
            if fired and fired.get("fired"):
                self.bullets.add(
                    Bullet(
                        player.rect.center,
                        player.facing,
                        player,
                        damage=fired["damage"],
                        speed=fired["speed"],
                        charged=fired["charged"],
                    )
                )
            self.world.apply_gravity(player)
            player.rect.clamp_ip(self.screen.get_rect())
            player.update_visual(dt)

        self.bullets.update(self.screen)
        for bullet in list(self.bullets):
            target = self.players[1] if bullet.owner is self.players[0] else self.players[0]
            if bullet.rect.colliderect(target.rect):
                # Gestion bouclier: parade (renvoi) ou blocage simple
                if getattr(target, "shielding", False) and getattr(target, "shield_durability", 0) > 0:
                    if target.shield_active_for <= Player.PARRY_WINDOW:
                        # Parade: renvoi du projectile + flash visuel
                        target.shield_durability = max(0, target.shield_durability - Player.SHIELD_WEAR_PARRY)
                        # Déclenche un petit flash visuel côté défenseur
                        if hasattr(target, "parry_flash_timer"):
                            target.parry_flash_timer = 0.12
                        bullet.owner = target
                        bullet.direction *= -1
                        # Décaler légèrement pour éviter collision immédiate
                        bullet.rect.x += bullet.direction * 8
                    else:
                        # Blocage: le projectile est annulé, usure du bouclier
                        target.shield_durability = max(0, target.shield_durability - Player.SHIELD_WEAR_BLOCK)
                        bullet.kill()
                else:
                    # Pas de bouclier (ou cassé): dégâts à la santé
                    target.health = max(0, target.health - int(getattr(bullet, "damage", 10)))
                    # Recharge légère du bouclier de l'attaquant sur coup réussi
                    owner = bullet.owner
                    if hasattr(owner, "shield_durability"):
                        owner.shield_durability = min(
                            owner.SHIELD_MAX, owner.shield_durability + Player.SHIELD_RECHARGE_ON_HIT
                        )
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
            self.hud.draw(self.screen, self.players, self.PLAYER_NAMES)
            if self.state == self.GAME_OVER:
                winner_index = 0 if self.winner is self.players[0] else 1
                self.hud.draw_game_over(self.screen, self.PLAYER_NAMES[winner_index])
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
