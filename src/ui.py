"""Interface, HUD et effets visuels du jeu."""

import pygame


class HUD:
    """Affiche les informations de jeu et les écrans."""

    def __init__(self, font: pygame.font.Font, title_font: pygame.font.Font | None = None):
        self.font = font
        self.title_font = title_font or font
        self.effect_time = 0.0
        self._projectile_glows = {
            False: self._make_projectile_glow((255, 225, 110, 85)),
            True: self._make_projectile_glow((255, 175, 75, 105)),
        }
        self._impact_surfaces = {}

    @staticmethod
    def _make_projectile_glow(color) -> pygame.Surface:
        glow = pygame.Surface((34, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, color, glow.get_rect(), 3)
        return glow

    def _get_impact_surface(self, radius, color, alpha) -> pygame.Surface:
        key = (radius, tuple(color), alpha)
        if key not in self._impact_surfaces:
            size = radius * 2 + 8
            effect = pygame.Surface((size, size), pygame.SRCALPHA)
            center = (size // 2, size // 2)
            rgba = (*color, alpha)
            pygame.draw.circle(effect, rgba, center, radius, 3)
            pygame.draw.circle(effect, rgba, center, max(2, radius // 3))
            self._impact_surfaces[key] = effect
        return self._impact_surfaces[key]

    def update(self, dt: float) -> None:
        """Fait progresser les effets visuels."""
        self.effect_time += dt

    def draw_health_bar(self, surface, player, position, reverse=False) -> None:
        background = pygame.Rect(*position, 220, 18)
        maximum = max(1, int(getattr(player, "max_health", 100)))
        current = max(0, min(maximum, int(getattr(player, "health", 0))))
        health_width = 220 * current // maximum
        health = pygame.Rect(*position, health_width, 18)
        if reverse:
            health.right = background.right
        pygame.draw.rect(surface, (75, 24, 35), background, border_radius=4)
        pygame.draw.rect(surface, (55, 205, 95), health, border_radius=4)
        label = self.font.render(f"{current}/{maximum}", True, (248, 248, 255))
        surface.blit(label, label.get_rect(center=background.center))

    def draw_shield_bar(self, surface, player, position, reverse=False) -> None:
        """Barre de durabilité du bouclier."""
        background = pygame.Rect(*position, 220, 8)
        maximum = max(1, int(getattr(player, "SHIELD_MAX", 100)))
        current = max(0, min(maximum, int(getattr(player, "shield_durability", 0))))
        width = 220 * current // maximum
        shield = pygame.Rect(*position, width, 8)
        if reverse:
            shield.right = background.right
        pygame.draw.rect(surface, (20, 34, 55), background, border_radius=3)
        pygame.draw.rect(surface, (75, 190, 255), shield, border_radius=3)

    def draw_charge_indicator(self, surface, player, position, reverse=False) -> None:
        """Montre visuellement la charge du prochain tir."""
        maximum = max(0.01, float(getattr(player, "CHARGE_MAX", 1.0)))
        charge = max(0.0, min(1.0, float(getattr(player, "charge_time", 0.0)) / maximum))
        background = pygame.Rect(*position, 220, 6)
        width = round(background.width * charge)
        fill = pygame.Rect(*position, width, background.height)
        if reverse:
            fill.right = background.right
        pygame.draw.rect(surface, (55, 42, 24), background, border_radius=3)
        pygame.draw.rect(surface, (255, 185, 75), fill, border_radius=3)
        # if getattr(player, "charging", False):
        #     text = self.font.render("CHARGE", True, (255, 215, 125))
        #     anchor = background.midright if reverse else background.midleft
        #     text_rect = text.get_rect(midleft=anchor) if not reverse else text.get_rect(midright=anchor)
        #     text_rect.y += 11
        #     surface.blit(text, text_rect)

    def draw(self, surface, players, player_names=("Sam", "Emma")) -> None:
        positions = ((20, 20), (surface.get_width() - 240, 20))
        for index, player in enumerate(players):
            reverse = index == 1
            x, y = positions[index]
            self.draw_health_bar(surface, player, (x, y), reverse=reverse)
            self.draw_shield_bar(surface, player, (x, y + 23), reverse=reverse)
            self.draw_charge_indicator(surface, player, (x, y + 34), reverse=reverse)
            name = self.font.render(player_names[index], True, (245, 247, 255))
            name_rect = name.get_rect(topright=(x + 220, y + 55)) if reverse else name.get_rect(topleft=(x, y + 55))
            surface.blit(name, name_rect)

    def draw_shield_break_effects(self, surface, effects) -> None:
        """Anime la rupture d'un bouclier sans créer un nouvel effet permanent."""
        offsets = ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1))
        for effect in effects:
            progress = effect["age"] / effect["duration"]
            radius = int(28 + progress * 38)
            alpha = max(0, int(220 * (1.0 - progress)))
            layer = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = (layer.get_width() // 2, layer.get_height() // 2)
            color = (120, 220, 255, alpha)
            pygame.draw.circle(layer, color, center, radius, 3)
            for offset_x, offset_y in offsets:
                start = (center[0] + offset_x * 12, center[1] + offset_y * 12)
                end = (center[0] + offset_x * (radius + 7), center[1] + offset_y * (radius + 7))
                pygame.draw.line(layer, color, start, end, 3)
            surface.blit(layer, layer.get_rect(center=effect["position"]))

    def draw_projectile_effects(self, surface, bullets) -> None:
        """Dessine un halo léger autour des projectiles."""
        for bullet in bullets:
            center = bullet.rect.center
            glow = self._projectile_glows[getattr(bullet, "charged", False)]
            surface.blit(glow, glow.get_rect(center=center))

    def draw_impacts(self, surface, impacts) -> None:
        """Dessine les impacts temporaires transmis par l’intégrateur."""
        for impact in impacts:
            progress = impact["age"] / impact["duration"]
            radius = int(8 + progress * 26)
            alpha = max(0, int(190 * (1.0 - progress)))
            effect = self._get_impact_surface(radius, impact["color"], alpha)
            surface.blit(effect, effect.get_rect(center=impact["position"]))

    @staticmethod
    def menu_button_rects(surface) -> dict[str, pygame.Rect]:
        """Retourne les zones interactives du menu principal."""
        center = surface.get_width() // 2
        return {
            "play": pygame.Rect(center - 270, 390, 160, 42),
            "controls": pygame.Rect(center - 80, 390, 160, 42),
            "quit": pygame.Rect(center + 110, 390, 160, 42),
        }

    @staticmethod
    def pause_button_rects(surface) -> dict[str, pygame.Rect]:
        """Retourne les zones interactives de l'écran de pause."""
        center = surface.get_width() // 2
        return {
            "resume": pygame.Rect(center - 270, 315, 160, 42),
            "restart": pygame.Rect(center - 80, 315, 160, 42),
            "menu": pygame.Rect(center + 110, 315, 160, 42),
        }

    def draw_logo(self, surface, center) -> None:
        """Dessine le logo D5 avec ombre et accent visuel."""
        shadow = self.title_font.render("D5", True, (5, 8, 18))
        logo = self.title_font.render("D5", True, (255, 220, 110))
        shadow_rect = shadow.get_rect(center=(center[0] + 4, center[1] + 5))
        logo_rect = logo.get_rect(center=center)
        surface.blit(shadow, shadow_rect)
        surface.blit(logo, logo_rect)
        pygame.draw.line(
            surface,
            (255, 220, 110),
            (logo_rect.left - 12, logo_rect.bottom + 7),
            (logo_rect.right + 12, logo_rect.bottom + 7),
            3,
        )

    def draw_menu(self, surface, title, description, subtitle, previews=None, selected="play") -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 175))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        description_image = self.font.render(description, True, (210, 218, 240))
        self.draw_logo(surface, (center_x, 55))
        surface.blit(description_image, description_image.get_rect(center=(center_x, 100)))

        if previews:
            cards = ((35, "Sam", "Q/D   Z   L-SHIFT   S"), (605, "Emma", "G/D   H   R-SHIFT   B"))
            for x, name, controls in cards:
                card = pygame.Rect(x, 125, 320, 215)
                pygame.draw.rect(surface, (26, 35, 63, 220), card, border_radius=12)
                pygame.draw.rect(surface, (90, 110, 160), card, 2, border_radius=12)
                animation = previews.get(name)
                if animation is not None:
                    image = animation.image
                    surface.blit(image, image.get_rect(center=(card.centerx, 220)))
                name_image = self.title_font.render(name, True, (255, 220, 110))
                control_image = self.font.render(controls, True, (215, 222, 240))
                surface.blit(name_image, name_image.get_rect(center=(card.centerx, 150)))
                surface.blit(control_image, control_image.get_rect(center=(card.centerx, 315)))

        buttons = self.menu_button_rects(surface)
        for key, label in (("play", "JOUER"), ("controls", "COMMANDES"), ("quit", "QUITTER")):
            button = buttons[key]
            highlighted = key == selected
            fill = (78, 92, 145) if highlighted else (42, 55, 92)
            border = (255, 220, 110) if highlighted else (125, 145, 200)
            pygame.draw.rect(surface, fill, button, border_radius=8)
            pygame.draw.rect(surface, border, button, 3 if highlighted else 2, border_radius=8)
            text = self.font.render(label, True, (240, 243, 255))
            surface.blit(text, text.get_rect(center=button.center))
            if highlighted:
                marker = self.font.render(">", True, (255, 220, 110))
                surface.blit(marker, marker.get_rect(midright=(button.left - 10, button.centery)))
        subtitle_image = self.font.render(subtitle, True, (184, 194, 220))
        surface.blit(subtitle_image, subtitle_image.get_rect(center=(center_x, 475)))

    def draw_controls(self, surface) -> None:
        """Affiche l'écran détaillé des commandes."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 175))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        title = self.title_font.render("COMMANDES", True, (255, 220, 110))
        surface.blit(title, title.get_rect(center=(center_x, 80)))
        rows = (
            ("Sam", "Q/D : bouger   Z : sauter   L-SHIFT : tirer   S : bouclier"),
            ("Emma", "gauche/droite : bouger   haut : sauter   R-SHIFT : tirer   bas : bouclier"),
        )
        for index, (name, controls) in enumerate(rows):
            y = 190 + index * 100
            panel = pygame.Rect(110, y - 35, 740, 70)
            pygame.draw.rect(surface, (26, 35, 63, 220), panel, border_radius=10)
            label = self.title_font.render(name, True, (255, 220, 110))
            text = self.font.render(controls, True, (225, 230, 245))
            surface.blit(label, label.get_rect(midleft=(panel.left + 20, panel.centery)))
            surface.blit(text, text.get_rect(midleft=(panel.left + 150, panel.centery)))
        back = self.font.render("Échap : revenir au menu", True, (184, 194, 220))
        surface.blit(back, back.get_rect(center=(center_x, 450)))

    def draw_pause(self, surface, selected="resume") -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 185))
        surface.blit(overlay, (0, 0))
        center = surface.get_rect().center
        title = self.title_font.render("PAUSE", True, (255, 220, 110))
        # instruction = self.font.render("Flèches : choisir   Entrée : valider   Échap : reprendre", True, (240, 243, 255))
        surface.blit(title, title.get_rect(center=(center[0], center[1] - 35)))
        # surface.blit(instruction, instruction.get_rect(center=(center[0], center[1] + 5)))
        buttons = self.pause_button_rects(surface)
        labels = (("resume", "REPRENDRE"), ("restart", "RECOMMENCER"), ("menu", "MENU"))
        for key, label in labels:
            button = buttons[key]
            highlighted = key == selected
            fill = (78, 92, 145) if highlighted else (42, 55, 92)
            border = (255, 220, 110) if highlighted else (125, 145, 200)
            pygame.draw.rect(surface, fill, button, border_radius=8)
            pygame.draw.rect(surface, border, button, 3 if highlighted else 2, border_radius=8)
            text = self.font.render(label, True, (240, 243, 255))
            surface.blit(text, text.get_rect(center=button.center))
            if highlighted:
                marker = self.font.render(">", True, (255, 220, 110))
                surface.blit(marker, marker.get_rect(midright=(button.left - 10, button.centery)))

    def draw_victory(self, surface, winner, flawless, victory_animation=None, flash_remaining=0.0) -> None:
        """Affiche l'annonce de victoire avant l'écran final."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 195))
        surface.blit(overlay, (0, 0))
        if flash_remaining > 0.0:
            alpha = min(180, int(600 * flash_remaining))
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((255, 240, 170, alpha))
            surface.blit(flash, (0, 0))
        center_x = surface.get_width() // 2
        if victory_animation is not None:
            image = victory_animation.image
            surface.blit(image, image.get_rect(center=(center_x, 170)))
        title = "FLAWLESS VICTORY !" if flawless else "VICTOIRE !"
        message = (
            f"{winner} gagne sans avoir été touché."
            if flawless
            else f"{winner} remporte la manche."
        )
        title_image = self.title_font.render(title, True, (255, 220, 110))
        message_image = self.font.render(message, True, (240, 243, 255))
        next_image = self.font.render("Appuyez sur une touche pour continuer", True, (184, 194, 220))
        surface.blit(title_image, title_image.get_rect(center=(center_x, 275)))
        surface.blit(message_image, message_image.get_rect(center=(center_x, 325)))
        surface.blit(next_image, next_image.get_rect(center=(center_x, 365)))

    def draw_game_over(
        self,
        surface,
        winner,
        victory_animation=None,
        flawless=False,
        remaining_hp=0,
        stats=None,
    ) -> None:
        """Affiche l'écran final et les détails de la manche."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 205))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        panel = pygame.Rect(120, 45, 720, 450)
        pygame.draw.rect(surface, (18, 25, 49, 235), panel, border_radius=18)
        pygame.draw.rect(surface, (110, 125, 185), panel, 2, border_radius=18)
        title = self.title_font.render("GAME OVER", True, (255, 220, 110))
        surface.blit(title, title.get_rect(center=(center_x, 82)))
        pygame.draw.line(surface, (110, 125, 185), (center_x, 125), (center_x, 440), 2)
        if victory_animation is not None:
            image = pygame.transform.smoothscale(victory_animation.image, (180, 180))
            surface.blit(image, image.get_rect(center=(300, 255)))
        # winner_label = self.font.render("GAGNANT", True, (184, 194, 220))
        result = self.title_font.render(winner, True, (240, 243, 255))
        status = "Victoire parfaite : oui" if flawless else "Victoire parfaite : non"
        details = self.font.render(f"{status}", True, (210, 218, 240))
        hp = self.font.render(f"HP restants : {remaining_hp}", True, (210, 218, 240))
        stats = stats or {"shots": 0, "hits": 0, "damage": 0, "blocks": 0}
        statistics = (
            f"Tirs : {stats['shots']}   Touches : {stats['hits']}\n"
            f"Dégâts infligés : {stats['damage']}   Blocages : {stats['blocks']}"
        )
        if flawless:
            badge = pygame.Rect(510, 135, 250, 34)
            pygame.draw.rect(surface, (170, 120, 35), badge, border_radius=10)
            badge_text = self.font.render("FLAWLESS VICTORY", True, (255, 245, 190))
            surface.blit(badge_text, badge_text.get_rect(center=badge.center))
        restart = self.font.render("Entrée ou Espace : Recommencer", True, (240, 243, 255))
        menu = self.font.render("Échap : revenir au menu", True, (184, 194, 220))
        # surface.blit(winner_label, winner_label.get_rect(center=(300, 365)))
        surface.blit(result, result.get_rect(center=(300, 400)))
        surface.blit(details, details.get_rect(topleft=(510, 175)))
        surface.blit(hp, hp.get_rect(topleft=(510, 215)))
        stat_lines = statistics.splitlines()
        for index, line in enumerate(stat_lines):
            stat_text = self.font.render(line, True, (210, 218, 240))
            surface.blit(stat_text, stat_text.get_rect(topleft=(510, 270 + index * 35)))
        surface.blit(restart, restart.get_rect(center=(center_x, 455)))
        surface.blit(menu, menu.get_rect(center=(center_x, 480)))
