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
    CONTROLS = "controls"
    PLAYING = "playing"
    PAUSED = "paused"
    VICTORY = "victory"
    GAME_OVER = "game_over"
    PLAYER_NAMES = ("Sam", "Emma")

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("D5")
        self.clock = pygame.time.Clock()
        self.sounds = self._load_sounds()
        self.audio_channel = None
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
        self.shield_break_effects = []
        self.player_was_hit = [False, False]
        self.flawless_victory = False
        self.victory_flash_remaining = 0.0
        self.match_stats = []
        self.fade_alpha = 0
        self.state = self.MENU
        self.menu_selection = 0
        self.pause_selection = 0
        self.running = True
        self.world = World(*SCREEN_SIZE)
        self.reset_match()

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound]:
        """Charge les effets audio une seule fois, avec un fallback silencieux."""
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return {}

        sounds = {}
        for name in ("flawless_victory", "game_over"):
            path = ASSETS_DIR / "sounds" / f"{name}.ogg"
            if path.exists():
                try:
                    sounds[name] = pygame.mixer.Sound(str(path))
                except pygame.error:
                    continue
        return sounds

    def _play_sound(self, name: str) -> float:
        """Joue un effet et retourne sa durée, ou une durée de fallback."""
        if self.audio_channel is not None:
            self.audio_channel.stop()
        sound = self.sounds.get(name)
        if sound is None:
            return 1.5
        self.audio_channel = sound.play()
        return max(0.1, sound.get_length())

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
        self.shield_break_effects = []
        self.player_was_hit = [False, False]
        self.flawless_victory = False
        self.victory_flash_remaining = 0.0
        self.match_stats = [
            {"shots": 0, "hits": 0, "damage": 0, "blocks": 0},
            {"shots": 0, "hits": 0, "damage": 0, "blocks": 0},
        ]
        if self.audio_channel is not None:
            self.audio_channel.stop()
            self.audio_channel = None
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

    def _change_state(self, state: str) -> None:
        """Change d'écran avec un fondu court."""
        self.state = state
        self.fade_alpha = 255
        if state == self.MENU:
            self.menu_selection = 0
        elif state == self.PAUSED:
            self.pause_selection = 0

    @staticmethod
    def _move_selection(selection: int, delta: int, count: int) -> int:
        return (selection + delta) % count

    def _activate_menu_selection(self) -> None:
        if self.menu_selection == 0:
            self.reset_match()
            self._change_state(self.PLAYING)
        elif self.menu_selection == 1:
            self._change_state(self.CONTROLS)
        else:
            self.running = False

    def _activate_pause_selection(self) -> None:
        if self.pause_selection == 0:
            self._change_state(self.PLAYING)
        elif self.pause_selection == 1:
            self.reset_match()
            self._change_state(self.PLAYING)
        else:
            self._change_state(self.MENU)

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
        for effect in self.shield_break_effects:
            effect["age"] += dt
        self.shield_break_effects = [
            effect for effect in self.shield_break_effects if effect["age"] < effect["duration"]
        ]

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == self.MENU:
                    buttons = self.hud.menu_button_rects(self.screen)
                    if buttons["play"].collidepoint(event.pos):
                        self.menu_selection = 0
                        self._activate_menu_selection()
                    elif buttons["controls"].collidepoint(event.pos):
                        self.menu_selection = 1
                        self._activate_menu_selection()
                    elif buttons["quit"].collidepoint(event.pos):
                        self.menu_selection = 2
                        self._activate_menu_selection()
                elif self.state == self.PAUSED:
                    buttons = self.hud.pause_button_rects(self.screen)
                    for index, key in enumerate(("resume", "restart", "menu")):
                        if buttons[key].collidepoint(event.pos):
                            self.pause_selection = index
                            self._activate_pause_selection()
                            break
            elif event.type == pygame.KEYDOWN:
                if self.state == self.MENU and event.key in (pygame.K_LEFT, pygame.K_UP):
                    self.menu_selection = self._move_selection(self.menu_selection, -1, 3)
                elif self.state == self.MENU and event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self.menu_selection = self._move_selection(self.menu_selection, 1, 3)
                elif self.state == self.MENU and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._activate_menu_selection()
                elif self.state == self.MENU and event.key == pygame.K_c:
                    self._change_state(self.CONTROLS)
                elif self.state == self.MENU and event.key == pygame.K_q:
                    self.running = False
                elif self.state == self.CONTROLS and event.key == pygame.K_ESCAPE:
                    self._change_state(self.MENU)
                elif self.state == self.PLAYING and event.key == pygame.K_ESCAPE:
                    self._change_state(self.PAUSED)
                elif self.state == self.PAUSED and event.key in (pygame.K_LEFT, pygame.K_UP):
                    self.pause_selection = self._move_selection(self.pause_selection, -1, 3)
                elif self.state == self.PAUSED and event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self.pause_selection = self._move_selection(self.pause_selection, 1, 3)
                elif self.state == self.PAUSED and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._activate_pause_selection()
                elif self.state == self.PAUSED and event.key == pygame.K_ESCAPE:
                    self._change_state(self.PLAYING)
                elif self.state == self.VICTORY:
                    self._finish_victory()
                elif self.state == self.GAME_OVER:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_match()
                        self._change_state(self.PLAYING)
                    elif event.key == pygame.K_ESCAPE:
                        self._change_state(self.MENU)

    def update(self, dt: float) -> None:
        self.fade_alpha = max(0, self.fade_alpha - int(720 * dt))
        self.hud.update(dt)
        for animation in self.menu_animations.values():
            animation.update(dt)

        if self.state in (self.VICTORY, self.GAME_OVER):
            if self.victory_animation is not None:
                self.victory_animation.update(dt)
            self._update_impacts(dt)
            if self.state == self.VICTORY:
                self.victory_flash_remaining = max(0.0, self.victory_flash_remaining - dt)
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
                shooter_index = 0 if player is self.players[0] else 1
                self.match_stats[shooter_index]["shots"] += 1
            self.world.apply_gravity(player)
            player.rect.clamp_ip(self.screen.get_rect())
            player.update_visual(dt)

        self.bullets.update(self.screen)
        for bullet in list(self.bullets):
            target_index = 1 if bullet.owner is self.players[0] else 0
            target = self.players[target_index]
            if bullet.rect.colliderect(target.rect):
                # Un contact avec un projectile compte même si le bouclier bloque.
                self.player_was_hit[target_index] = True
                self.match_stats[target_index]["hits"] += 1
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
                        previous_durability = target.shield_durability
                        target.shield_durability = max(0, target.shield_durability - Player.SHIELD_WEAR_BLOCK)
                        self.match_stats[target_index]["blocks"] += 1
                        self._add_impact(target.rect.center, (80, 170, 255))
                        if previous_durability > 0 and target.shield_durability == 0:
                            self.shield_break_effects.append(
                                {"position": target.rect.center, "age": 0.0, "duration": 0.55}
                            )
                        bullet.kill()
                else:
                    # Pas de bouclier (ou cassé): dégâts à la santé
                    damage = int(getattr(bullet, "damage", 10))
                    target.health = max(0, target.health - damage)
                    self.match_stats[target_index]["damage"] += damage
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
                        winner_index = 0 if self.winner is self.players[0] else 1
                        self.flawless_victory = not self.player_was_hit[winner_index]
                        self.victory_flash_remaining = 0.35
                        self._change_state(self.VICTORY)
                        if self.flawless_victory:
                            self._play_sound("flawless_victory")
                        break

    def _finish_victory(self) -> None:
        """Passe à l'écran final après l'appui du joueur."""
        self._change_state(self.GAME_OVER)
        self._play_sound("game_over")

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
                ("play", "controls", "quit")[self.menu_selection],
            )
        elif self.state == self.CONTROLS:
            self.screen.fill(COLOR_BACKGROUND)
            pygame.draw.circle(self.screen, (38, 48, 83), (self.screen.get_width() - 120, 120), 90)
            pygame.draw.circle(self.screen, (25, 32, 59), (100, 430), 150)
            self.hud.draw_controls(self.screen)
        else:
            if self.background is not None:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(COLOR_BACKGROUND)
            self.world.draw(self.screen)
            for player in self.players:
                player.draw(self.screen)
            self.hud.draw_shield_break_effects(self.screen, self.shield_break_effects)
            self.hud.draw_projectile_effects(self.screen, self.bullets)
            self.bullets.draw(self.screen)
            self.hud.draw_impacts(self.screen, self.impact_effects)
            self.hud.draw(self.screen, self.players, self.PLAYER_NAMES)
            if self.state == self.PAUSED:
                self.hud.draw_pause(self.screen, ("resume", "restart", "menu")[self.pause_selection])
            elif self.state == self.VICTORY:
                winner_index = 0 if self.winner is self.players[0] else 1
                self.hud.draw_victory(
                    self.screen,
                    self.PLAYER_NAMES[winner_index],
                    self.flawless_victory,
                    self.victory_animation,
                    self.victory_flash_remaining,
                )
            elif self.state == self.GAME_OVER:
                winner_index = 0 if self.winner is self.players[0] else 1
                self.hud.draw_game_over(
                    self.screen,
                    self.PLAYER_NAMES[winner_index],
                    self.victory_animation,
                    self.flawless_victory,
                    self.winner.health if self.winner is not None else 0,
                    self.match_stats[winner_index] if self.winner is not None else None,
                )
        if self.fade_alpha > 0:
            fade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            fade.fill((0, 0, 0, self.fade_alpha))
            self.screen.blit(fade, (0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
