"""Classe représentant un combattant."""

import pygame
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
    DASH_DURATION = 0.16
    DASH_SPEED = 18.0

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

        # Double saut
        self.max_jumps = 2
        self.jumps_left = 2

        # États d'entrée pour détection des fronts
        self._prev_attack_pressed = False
        self._prev_shield_pressed = False
        self._prev_left_pressed = False
        self._prev_right_pressed = False
        self._prev_jump_pressed = False

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
        # Effets attaque chargée
        self.charge_anim_time = 0.0
        self.charge_flash_timer = 0.0

        # Dash (double-tap)
        self.time_since_last_tap_left = 999.0
        self.time_since_last_tap_right = 999.0
        self.dash_time_remaining = 0.0
        self.dash_direction = 0

    def handle_input(self, keys, dt: float) -> dict | None:
        """
        Gère déplacement, saut, dash (double-tap), charge/relâchement d'attaque et bouclier.
        Retourne un dict avec les infos de tir quand un projectile doit être créé:
        {"fired": True, "damage": int, "speed": float, "charged": bool}
        Sinon retourne {"fired": False}.
        """
        # Timers
        self.since_last_shot += dt

        # Double-tap pour dash
        self.time_since_last_tap_left += dt
        self.time_since_last_tap_right += dt
        lp = keys[self.controls["left"]]
        rp = keys[self.controls["right"]]

        if lp and not self._prev_left_pressed:
            if self.time_since_last_tap_left <= self.DOUBLE_TAP_WINDOW and self.dash_time_remaining <= 0.0:
                self.dash_direction = -1
                self.dash_time_remaining = self.DASH_DURATION
            self.time_since_last_tap_left = 0.0
        if rp and not self._prev_right_pressed:
            if self.time_since_last_tap_right <= self.DOUBLE_TAP_WINDOW and self.dash_time_remaining <= 0.0:
                self.dash_direction = 1
                self.dash_time_remaining = self.DASH_DURATION
            self.time_since_last_tap_right = 0.0

        # Déplacement (priorité au dash)
        self.moving = False
        if self.dash_time_remaining > 0.0:
            self.rect.x += int(round(self.DASH_SPEED)) * self.dash_direction
            self.facing = self.dash_direction
            self.moving = True
            self.dash_time_remaining -= dt
        else:
            if lp:
                self.rect.x -= self.SPEED
                self.facing = -1
                self.moving = True
            if rp:
                self.rect.x += self.SPEED
                self.facing = 1
                self.moving = True

        # Double saut (détection de front)
        jp = keys[self.controls["jump"]]
        if jp and not self._prev_jump_pressed:
            if self.on_ground:
                self.velocity_y = self.JUMP_FORCE
                self.on_ground = False
                # Consomme le premier saut, garde le second
                self.jumps_left = max(0, getattr(self, "max_jumps", 2) - 1)
            elif getattr(self, "jumps_left", 0) > 0:
                self.velocity_y = self.JUMP_FORCE
                self.jumps_left -= 1

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
            # Flash visuel d'émission
            self.charge_flash_timer = 0.15
            fired_info = {"fired": True, "damage": damage, "speed": speed, "charged": charged}

        # Mémoriser états précédents
        self._prev_attack_pressed = ap
        self._prev_shield_pressed = sp
        self._prev_left_pressed = lp
        self._prev_right_pressed = rp
        self._prev_jump_pressed = jp

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
        # Effets visuels: attaque chargée
        if getattr(self, "charging", False):
            self.charge_anim_time += dt
        if getattr(self, "charge_flash_timer", 0.0) > 0.0:
            self.charge_flash_timer = max(0.0, self.charge_flash_timer - dt)

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

        def draw_dash_trail(image: pygame.Surface, base_rect: pygame.Rect) -> None:
            # Traînée du dash (afterimages)
            if self.dash_time_remaining <= 0.0 or image is None:
                return
            for i in range(1, 4):
                ghost = image.copy()
                alpha = max(0, 80 - i * 20)
                ghost.set_alpha(alpha)
                offset_x = -self.dash_direction * i * 12
                ghost_rect = base_rect.copy()
                ghost_rect.x += offset_x
                surface.blit(ghost, ghost_rect)

        def draw_charge_fx(base_rect: pygame.Rect) -> None:
            # Halo de charge devant le personnage + flash d'émission
            # Position approximative des mains/avant du corps
            center = base_rect.center
            fx_pos = (center[0] + 18 * self.facing, center[1] - 10)
            # Halo pendant la charge
            if getattr(self, "charging", False):
                ratio = 0.0 if self.CHARGE_MAX <= 0 else min(1.0, self.charge_time / self.CHARGE_MAX)
                radius = 10 + int(14 * ratio)
                alpha = 80 + int(120 * ratio)
                col = (255, 180, 80, max(0, min(255, alpha)))
                surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(surf, col, (surf.get_width() // 2, surf.get_height() // 2), radius)
                # Anneau externe léger
                ring_col = (255, 210, 120, max(0, min(255, alpha - 40)))
                pygame.draw.circle(surf, ring_col, (surf.get_width() // 2, surf.get_height() // 2), max(4, radius - 3), 2)
                surface.blit(surf, surf.get_rect(center=fx_pos))
            # Flash au relâchement
            if getattr(self, "charge_flash_timer", 0.0) > 0.0:
                t = self.charge_flash_timer / 0.15  # 1 -> 0
                radius = int(20 + (1.0 - t) * 30)
                alpha = int(180 * t)
                col = (255, 220, 120, max(0, min(255, alpha)))
                surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(surf, col, (surf.get_width() // 2, surf.get_height() // 2), radius, 4)
                surface.blit(surf, surf.get_rect(center=center))

        if self.animation is None:
            surface.blit(self.image, self.rect)
            # Dash trail rudimentaire si dash actif
            if self.dash_time_remaining > 0.0:
                for i in range(1, 4):
                    trail = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                    trail.fill((255, 255, 255, max(0, 60 - i * 15)))
                    tr_rect = self.rect.copy()
                    tr_rect.x += -self.dash_direction * i * 10
                    surface.blit(trail, tr_rect)
            # FX bouclier si actif
            if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
                draw_shield_fx(self.rect.center)
            # FX de charge
            if getattr(self, "charging", False) or getattr(self, "charge_flash_timer", 0.0) > 0.0:
                # approx. base rect sans anim
                base_rect = self.rect
                draw_charge_fx(base_rect)
            return

        visual = self.animation.image
        if self.facing < 0:
            visual = pygame.transform.flip(visual, True, False)
        sprite_rect = visual.get_rect(midbottom=self.rect.midbottom)

        # Dash: dessiner la traînée derrière
        draw_dash_trail(visual, sprite_rect)

        # Sprite principal
        surface.blit(visual, sprite_rect)

        # FX bouclier si actif
        if getattr(self, "shielding", False) and getattr(self, "shield_durability", 0) > 0:
            draw_shield_fx(sprite_rect.center)

        # FX de charge (pendant la charge et flash au tir)
        if getattr(self, "charging", False) or getattr(self, "charge_flash_timer", 0.0) > 0.0:
            draw_charge_fx(sprite_rect)
