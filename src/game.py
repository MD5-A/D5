"""Boucle principale et états du jeu."""

import random

import pygame

from .assets import load_character_animations
from .combat import Bullet
from .player import Player
from .settings import ASSETS_DIR, COLOR_BACKGROUND, FPS, SCREEN_SIZE
from .ui import HUD
from .world import World


class Game:
    """Orchestre le menu, la partie et les composants du jeu."""

    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    PLAYER_NAMES = ("Sam", "Emma")

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("D5")
        self.clock = pygame.time.Clock()
        self.hud = HUD(pygame.font.Font(None, 26), pygame.font.Font(None, 42))
        self.character_animations = {
            "Sam": load_character_animations("alchemist", "alchemist"),
            "Emma": load_character_animations("arcane-mage", "arcane-mage"),
        }
        self.menu_animations = {
            name: animations["idle"].clone()
            for name, animations in self.character_animations.items()
            if "idle" in animations
        }
        self.backgrounds = self._load_backgrounds()
        self.background = None
        self.background_name = None
        self.victory_animation = None
        self.impact_effects = []
        self.state = self.MENU
        self.running = True
        self.world = World(*SCREEN_SIZE)
        self.reset_match()

    def _load_backgrounds(self) -> list[tuple[str, pygame.Surface]]:
        """Charge et adapte les backgrounds disponibles pour l'arène."""
        backgrounds = []
        background_dir = ASSETS_DIR / "bg"
        for path in sorted(background_dir.glob("*.png")):
            image = pygame.image.load(str(path)).convert()
            scale = max(
                SCREEN_SIZE[0] / image.get_width(),
                SCREEN_SIZE[1] / image.get_height(),
            )
            scaled_size = (
                round(image.get_width() * scale),
                round(image.get_height() * scale),
            )
            scaled = pygame.transform.smoothscale(image, scaled_size)
            crop_rect = pygame.Rect(0, 0, *SCREEN_SIZE)
            crop_rect.center = scaled.get_rect().center
            backgrounds.append((path.stem, scaled.subsurface(crop_rect).copy()))
        return backgrounds

    def reset_match(self) -> None:
        """Recrée les objets dépendant d'une manche."""
        self.winner = None
        self.victory_animation = None
        self.impact_effects = []
        if self.backgrounds:
            self.background_name, self.background = random.choice(self.backgrounds)
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
                self._clone_character_animations("Sam"),
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
                self._clone_character_animations("Emma"),
            ),
        ]
        self.bullets = pygame.sprite.Group()

    def _clone_character_animations(self, name: str) -> dict:
        """Retourne des animations indépendantes à partir du cache mémoire."""
        return {key: animation.clone() for key, animation in self.character_animations[name].items()}

    def _add_impact(self, position, color) -> None:
        """Ajoute un effet visuel sans modifier les règles de combat."""
        self.impact_effects.append({"position": position, "color": color, "age": 0.0, "duration": 0.24})

    def _update_impacts(self, dt: float) -> None:
        for impact in self.impact_effects:
            impact["age"] += dt
        self.impact_effects = [
            impact for impact in self.impact_effects if impact["age"] < impact["duration"]
        ]

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == self.MENU and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset_match()
                    self.state = self.PLAYING
                elif self.state == self.PLAYING and event.key == pygame.K_ESCAPE:
                    self.state = self.PAUSED
                elif self.state == self.PAUSED and event.key == pygame.K_ESCAPE:
                    self.state = self.PLAYING
                elif self.state == self.GAME_OVER:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_match()
                        self.state = self.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU

    def update(self, dt: float) -> None:
        self.hud.update(dt)
        for animation in self.menu_animations.values():
            animation.update(dt)

        if self.state == self.GAME_OVER:
            if self.victory_animation is not None:
                self.victory_animation.update(dt)
            self._update_impacts(dt)
            return
        if self.state != self.PLAYING:
            return
        self._update_impacts(dt)
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
                        self._add_impact(target.rect.center, (120, 220, 255))
                        # Décaler légèrement pour éviter collision immédiate
                        bullet.rect.x += bullet.direction * 8
                    else:
                        # Blocage: le projectile est annulé, usure du bouclier
                        target.shield_durability = max(0, target.shield_durability - Player.SHIELD_WEAR_BLOCK)
                        self._add_impact(target.rect.center, (80, 170, 255))
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
                    self._add_impact(target.rect.center, (255, 170, 70))
                    if target.health == 0:
                        self.winner = bullet.owner
                        winner_name = self.PLAYER_NAMES[0] if self.winner is self.players[0] else self.PLAYER_NAMES[1]
                        animations = self.character_animations[winner_name]
                        victory_source = animations.get("dance", animations.get("idle"))
                        self.victory_animation = victory_source.clone() if victory_source else None
                        self.state = self.GAME_OVER
                        break

    def draw(self) -> None:
        if self.state == self.MENU:
            self.screen.fill(COLOR_BACKGROUND)
            pygame.draw.circle(self.screen, (38, 48, 83), (self.screen.get_width() - 120, 120), 90)
            pygame.draw.circle(self.screen, (25, 32, 59), (100, 430), 150)
            self.hud.draw_menu(
                self.screen,
                "D5",
                "Un jeu de combat PvP en arène pour deux joueurs.",
                "Entrée ou Espace pour commencer",
                self.menu_animations,
            )
        else:
            if self.background is not None:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(COLOR_BACKGROUND)
            self.world.draw(self.screen)
            for player in self.players:
                player.draw(self.screen)
            self.hud.draw_projectile_effects(self.screen, self.bullets)
            self.bullets.draw(self.screen)
            self.hud.draw_impacts(self.screen, self.impact_effects)
            self.hud.draw(self.screen, self.players, self.PLAYER_NAMES)
            if self.state == self.PAUSED:
                self.hud.draw_pause(self.screen)
            elif self.state == self.GAME_OVER:
                winner_index = 0 if self.winner is self.players[0] else 1
                self.hud.draw_game_over(
                    self.screen,
                    self.PLAYER_NAMES[winner_index],
                    self.victory_animation,
                )
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
