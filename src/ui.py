"""Interface, HUD et effets visuels du jeu."""

import pygame


class HUD:
    """Affiche les informations de jeu et les écrans du Dev 5."""

    def __init__(self, font: pygame.font.Font, title_font: pygame.font.Font | None = None):
        self.font = font
        self.title_font = title_font or font
        self.effect_time = 0.0

    def update(self, dt: float) -> None:
        """Fait progresser les effets visuels sans toucher à la logique de jeu."""
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

    def draw_projectile_effects(self, surface, bullets) -> None:
        """Dessine un halo léger autour des projectiles existants."""
        for bullet in bullets:
            center = bullet.rect.center
            color = (255, 175, 75, 105) if getattr(bullet, "charged", False) else (255, 225, 110, 85)
            glow = pygame.Surface((34, 24), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, color, glow.get_rect(), 3)
            surface.blit(glow, glow.get_rect(center=center))

    def draw_impacts(self, surface, impacts) -> None:
        """Dessine les impacts temporaires transmis par l’intégrateur."""
        for impact in impacts:
            progress = impact["age"] / impact["duration"]
            radius = int(8 + progress * 26)
            alpha = max(0, int(190 * (1.0 - progress)))
            effect = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            center = (effect.get_width() // 2, effect.get_height() // 2)
            color = (*impact["color"], alpha)
            pygame.draw.circle(effect, color, center, radius, 3)
            pygame.draw.circle(effect, color, center, max(2, radius // 3))
            surface.blit(effect, effect.get_rect(center=impact["position"]))

    def draw_menu(self, surface, title, description, subtitle, previews=None) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 175))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        title_image = self.title_font.render(title, True, (255, 220, 110))
        description_image = self.font.render(description, True, (210, 218, 240))
        subtitle_image = self.font.render(subtitle, True, (240, 243, 255))
        surface.blit(title_image, title_image.get_rect(center=(center_x, 62)))
        surface.blit(description_image, description_image.get_rect(center=(center_x, 108)))

        if previews:
            cards = ((35, "Sam", "Q/D   Z   Shift gauche   S"), (605, "Emma", "←/→   ↑   Shift droit   ↓"))
            for x, name, controls in cards:
                card = pygame.Rect(x, 145, 320, 245)
                pygame.draw.rect(surface, (26, 35, 63, 220), card, border_radius=12)
                pygame.draw.rect(surface, (90, 110, 160), card, 2, border_radius=12)
                animation = previews.get(name)
                if animation is not None:
                    image = animation.image
                    surface.blit(image, image.get_rect(center=(card.centerx, 245)))
                name_image = self.title_font.render(name, True, (255, 220, 110))
                control_image = self.font.render(controls, True, (215, 222, 240))
                surface.blit(name_image, name_image.get_rect(center=(card.centerx, 175)))
                surface.blit(control_image, control_image.get_rect(center=(card.centerx, 365)))

        surface.blit(subtitle_image, subtitle_image.get_rect(center=(center_x, 450)))

    def draw_pause(self, surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 185))
        surface.blit(overlay, (0, 0))
        center = surface.get_rect().center
        title = self.title_font.render("PAUSE", True, (255, 220, 110))
        instruction = self.font.render("Échap : reprendre la partie", True, (240, 243, 255))
        surface.blit(title, title.get_rect(center=(center[0], center[1] - 35)))
        surface.blit(instruction, instruction.get_rect(center=(center[0], center[1] + 30)))

    def draw_game_over(self, surface, winner, victory_animation=None) -> None:
        """Affiche le résultat avec une animation du gagnant si disponible."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 195))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        if victory_animation is not None:
            image = victory_animation.image
            surface.blit(image, image.get_rect(center=(center_x, 170)))
        result = self.title_font.render(f"{winner} remporte la manche !", True, (255, 220, 110))
        restart = self.font.render("Entrée ou Espace : revanche", True, (240, 243, 255))
        menu = self.font.render("Échap : revenir au menu", True, (184, 194, 220))
        surface.blit(result, result.get_rect(center=(center_x, 275)))
        surface.blit(restart, restart.get_rect(center=(center_x, 335)))
        surface.blit(menu, menu.get_rect(center=(center_x, 370)))
