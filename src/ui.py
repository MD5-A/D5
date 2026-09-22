"""Affichage de l'interface de combat."""

import pygame


class HUD:
    """Affiche les barres de vie des deux joueurs."""

    def __init__(self, font: pygame.font.Font):
        self.font = font

    def draw_health_bar(self, surface, player, position, reverse=False) -> None:
        background = pygame.Rect(*position, 220, 18)
        health_width = max(0, 220 * player.health // 100)
        health = pygame.Rect(*position, health_width, 18)
        if reverse:
            health.right = background.right
        pygame.draw.rect(surface, (90, 30, 30), background)
        pygame.draw.rect(surface, (50, 210, 80), health)

    def draw(self, surface, players) -> None:
        self.draw_health_bar(surface, players[0], (20, 20))
        self.draw_health_bar(surface, players[1], (surface.get_width() - 240, 20), reverse=True)
        label = self.font.render("Joueur 1        Joueur 2", True, (240, 240, 240))
        surface.blit(label, label.get_rect(center=(surface.get_width() // 2, 28)))

    def draw_menu(self, surface, title, description, subtitle) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 150))
        surface.blit(overlay, (0, 0))
        title_image = self.font.render(title, True, (255, 220, 110))
        description_image = self.font.render(description, True, (210, 218, 240))
        subtitle_image = self.font.render(subtitle, True, (240, 243, 255))
        center_x = surface.get_width() // 2
        surface.blit(title_image, title_image.get_rect(center=(center_x, 190)))
        surface.blit(description_image, description_image.get_rect(center=(center_x, 255)))
        surface.blit(subtitle_image, subtitle_image.get_rect(center=(center_x, 320)))
