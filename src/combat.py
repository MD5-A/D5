"""Projectiles et règles de combat."""

import pygame


class Bullet(pygame.sprite.Sprite):
    """Projectile horizontal tiré par un joueur."""

    DEFAULT_SPEED = 9
    DEFAULT_DAMAGE = 10

    def __init__(
        self,
        position: tuple[int, int],
        direction: int,
        owner,
        damage: int | None = None,
        speed: float | None = None,
        charged: bool = False,
    ):
        super().__init__()
        self.damage = int(damage if damage is not None else self.DEFAULT_DAMAGE)
        self.speed = float(speed if speed is not None else self.DEFAULT_SPEED)
        # Légère variation visuelle si tir chargé
        width = 14 + (6 if charged else 0)
        height = 6 + (2 if charged else 0)
        self.image = pygame.Surface((width, height))
        color = (255, 120, 60) if charged else (255, 220, 80)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=position)
        self.direction = direction
        self.owner = owner
        self.charged = charged

    def update(self, target_surface: pygame.Surface) -> None:
        self.rect.x += round(self.speed) * self.direction
        if not target_surface.get_rect().colliderect(self.rect):
            self.kill()

