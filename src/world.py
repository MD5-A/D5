"""Éléments du monde et gestion de la gravité."""

import pygame


class Platform(pygame.sprite.Sprite):
    """Plateforme rectangulaire solide."""

    def __init__(self, rect: pygame.Rect, color: tuple[int, int, int] = (80, 80, 90)):
        super().__init__()
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=rect.topleft)


class World:
    """Contient les plateformes et applique les collisions verticales."""

    GRAVITY = 0.6

    def __init__(self, width: int, height: int):
        self.platforms = pygame.sprite.Group(
            Platform(pygame.Rect(0, height - 40, width, 40)),
            Platform(pygame.Rect(width // 2 - 110, height - 170, 220, 20)),
        )

    def draw(self, surface: pygame.Surface) -> None:
        self.platforms.draw(surface)

    def apply_gravity(self, player) -> None:
        """Déplace un joueur vers le bas et le pose sur une plateforme."""
        player.velocity_y += self.GRAVITY
        player.rect.y += round(player.velocity_y)
        player.on_ground = False

        for platform in self.platforms:
            if player.rect.colliderect(platform.rect) and player.velocity_y >= 0:
                player.rect.bottom = platform.rect.top
                player.velocity_y = 0
                player.on_ground = True

