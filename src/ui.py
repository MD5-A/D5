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

    def draw(self, surface, players, player_names=("Sam", "Emma")) -> None:
        self.draw_health_bar(surface, players[0], (20, 20))
        self.draw_health_bar(surface, players[1], (surface.get_width() - 240, 20), reverse=True)
        player_one = self.font.render(player_names[0], True, (240, 240, 240))
        player_two = self.font.render(player_names[1], True, (240, 240, 240))
        surface.blit(player_one, (20, 43))
        surface.blit(player_two, (surface.get_width() - 95, 43))

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

    def draw_game_over(self, surface, winner) -> None:
        """Affiche le résultat de la manche et les actions disponibles."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 10, 24, 185))
        surface.blit(overlay, (0, 0))
        center_x = surface.get_width() // 2
        result = self.font.render(f"{winner} remporte la manche !", True, (255, 220, 110))
        restart = self.font.render("Entrée ou Espace : revanche", True, (240, 243, 255))
        menu = self.font.render("Échap : revenir au menu", True, (184, 194, 220))
        surface.blit(result, result.get_rect(center=(center_x, 220)))
        surface.blit(restart, restart.get_rect(center=(center_x, 285)))
        surface.blit(menu, menu.get_rect(center=(center_x, 325)))
