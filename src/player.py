"""Classe représentant un combattant."""

import pygame
import math
import math


class Player(pygame.sprite.Sprite):
    """Joueur contrôlable avec déplacement, saut, attaques chargées et bouclier."""

    SPEED = 5
    JUMP_FORCE = -12

    # Paramètres d'attaque chargée
    BASE_DAMAGE = 6
    BONUS_DAMAGE = 12          # dégâts max supplémentaires à charge pleine
    BASE_BULLET_SPEED = 8.0
    BONUS_BULLET_SPEED = 5.0   # vitesse sup. à charge pleine
    CHARGE_MAX = 1.2           # secondes pour charge pleine
    FIRE_COOLDOWN = 0.15       # délai mini entre tirs

    # Paramètres de bouclier
    SHIELD_MAX = 100
    PARRY_WINDOW = 0.12        # fenêtre de parade (renvoi) en secondes après levée
    SHIELD_WEAR_BLOCK = 18     # usure lors d'un blocage simple
    SHIELD_WEAR_PARRY = 8      # usure lors d'une parade (renvoi)
    SHIELD_RECHARGE_ON_HIT = 8  # recharge légère quand on touche l'adversaire

    # Paramètres de dash (double-tap)
    DOUBLE_TAP_WINDOW = 0.25   # secondes entre 2 appuis pour dash
    DASH_DURATION = 0.12
    DASH_SPEED = 16.0
    SHIELD_RECHARGE_ON_HIT = 8  # recharge légère du bouclier quand on touche l'adversaire

    def __init__(
        self,
        position: tuple[int, int],
        color: tuple[int, int, int],
        controls: dict,
        animations: dict | None = None,
    ):
        super().__init__()
        self.image = pygame.Surface((42, 64))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=position)
        self.animations = animations or {}
        self.animation = self.animations.get("idle")
        self.controls = controls
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing = 1
        self.health = 100
        self.moving = False

        # États d'entrée pour détection des fronts
        self._prev_attack_pressed = False
        self._prev_shield_pressed = False
        self._prev_left_pressed = False
        self._prev_right_pressed = False

        # Attaque chargée
        self.charging = False
        self.charge_time = 0.0
        self.since_last_shot = self.FIRE_COOLDOWN

        # Bouclier
        self.shielding = False
        self.shield_active_for = 0.0
        self.shield_durability = self.SHIELD_MAX
        # Effets bouclier
        self.parry_flash_timer = 0.0
        self.shield_anim_time = 0.0

        # Dash (double-tap)
        self.time_since_last_tap_left = 999.0
        self.time_since_last_tap_right = 999.0
        self.dash_time_remaining = 0.0
        self.dash_direction = 0
        # Animation/flash du bouclier
        self.parry_flash_timer = 0.0
        self.shield_anim_time = 0.0

    def handle_input(self, keys, dt: float) -> dict | None:
        """
        Gère déplacement, saut, charge/relâchement d'attaque et bouclier.
        Retourne un dict avec les infos de tir quand un projectile doit être créé:
        {"fired": True, "damage": int, "speed": float, "charged": bool}
        Sinon retourne {"fired": False}.
        """
        # Déplacement
        self.moving = False
        if keys[self.controls["left"]]:
            self.rect.x -= self.SPEED
            self.facing = -1
            self.moving = True
        if keys[self.controls["right"]]:
            self.rect.x += self.SPEED
            self.facing = 1
            self.moving = True
        if keys[self.controls["jump"]] and self.on_ground:
            self.velocity_y = self.JUMP_FORCE
            self.on_ground = False

        self.since_last_shot += dt

        # Gestion du bouclier
        shield_pressed = self.controls.get("shield")
        sp = keys[shield_pressed] if shield_pressed is not None else False
        fired_info: dict | None = None

        if sp and not self._prev_shield_pressed:
            # Levée du bouclier
            self.shielding = True
            self.shield_active_for = 0.0
            self.shield_anim_time = 0.0
        elif sp and self._prev_shield_pressed and self.shielding:
            # Bouclier maintenu
            self.shield_active_for += dt
        elif not sp and self._prev_shield_pressed:
            # Repos du bouclier
            self.shielding = False

        # Gestion de l'attaque chargée
        ap = keys[self.controls["attack"]]
        if ap and not self._prev_attack_pressed and self.since_last_shot >= self.FIRE_COOLDOWN:
            # Début de charge
            self.charging = True
            self.charge_time = 0.0
        elif ap and self._prev_attack_pressed and self.charging:
            # Charge en cours
            self.charge_time = min(self.CHARGE_MAX, self.charge_time + dt)
        elif not ap and self._prev_attack_pressed and self.charging:
            # Relâchement: tirer
            ratio = 0.0 if self.CHARGE_MAX <= 0 else min(1.0, self.charge_time / self.CHARGE_MAX)
            damage = int(round(self.BASE_DAMAGE + ratio * self.BONUS_DAMAGE))
            speed = self.BASE_BULLET_SPEED + ratio * self.BONUS_BULLET_SPEED
            charged = ratio >= 0.5
            self.since_last_shot = 0.0
            self.charging = False
            fired_info = {"fired": True, "damage": damage, "speed": speed, "charged": charged}

        # Mémoriser états précédents
        self._prev_attack_pressed = ap
        self._prev_shield_pressed = sp

        return fired_info or {"fired": False}

    def update_visual(self, dt: float) -> None:
        wanted = self.animations.get("run" if self.moving else "idle")
        if wanted is not None and wanted is not self.animation:
            self.animation = wanted
        if self.animation is not None:
            self.animation.update(dt)
        # Effets visuels: bouclier (flash et progression)
        if getattr(self, "parry_flash_timer", 0.0) > 0.0:
            self.parry_flash_timer = max(0.0, self.parry_flash_timer - dt)
        if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
            self.shield_anim_time += dt
        # Effets bouclier
        if hasattr(self, "parry_flash_timer") and self.parry_flash_timer > 0.0:
            self.parry_flash_timer = max(0.0, self.parry_flash_timer - dt)
        if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
            self.shield_anim_time += dt

    def draw(self, surface: pygame.Surface) -> None:
        def draw_shield_fx(center_pos: tuple[int, int]) -> None:
            # Halo pulsant + étincelles en orbite
            t = getattr(self, "shield_anim_time", 0.0)
            # Intensité (plus vif en fenêtre de parade ou pendant flash)
            bright = (self.shield_active_for <= self.PARRY_WINDOW) or (getattr(self, "parry_flash_timer", 0.0) > 0.0)
            base_color = (80, 180, 255, 90)
            strong_color = (150, 230, 255, 160)
            col = strong_color if bright else base_color

            # Pulsation du rayon
            base_radius = 34
            puls = 0.85 + 0.15 * math.sin(t * 6.0)
            radius = int(base_radius * puls)
            thickness = 4

            # Surface alpha pour dessiner l'effet
            size = (radius * 2 + 12, radius * 2 + 12)
            halo = pygame.Surface(size, pygame.SRCALPHA)

            # Anneaux (léger dégradé)
            pygame.draw.circle(halo, col, (size[0] // 2, size[1] // 2), radius, thickness)
            inner_col = (col[0], col[1], col[2], max(0, col[3] - 60))
            pygame.draw.circle(halo, inner_col, (size[0] // 2, size[1] // 2), max(8, radius - 6), 1)

            # Étincelles en orbite
            sparks = 4
            orbit_r = max(10, radius - 10)
            for i in range(sparks):
                ang = t * 5.0 + i * (2 * math.pi / sparks)
                px = size[0] // 2 + int(orbit_r * math.cos(ang))
                py = size[1] // 2 + int(orbit_r * math.sin(ang))
                spark_col = (col[0], col[1], col[2], min(255, col[3] + 40))
                pygame.draw.circle(halo, spark_col, (px, py), 2)

            surface.blit(halo, halo.get_rect(center=center_pos))

        if self.animation is None:
            surface.blit(self.image, self.rect)
            # FX bouclier si actif
            if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
                draw_shield_fx(self.rect.center)
            return

        visual = self.animation.image
        if self.facing < 0:
            visual = pygame.transform.flip(visual, True, False)
        sprite_rect = visual.get_rect(midbottom=self.rect.midbottom)
        surface.blit(visual, sprite_rect)

        # FX bouclier si actif
        if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
            draw_shield_fx(sprite_rect.center)
