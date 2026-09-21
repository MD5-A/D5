"""Projectiles et règles de combat."""

import pygame


class Bullet(pygame.sprite.Sprite):
    """Projectile horizontal tiré par un joueur."""

    SPEED = 9
    DAMAGE = 10

    def __init__(self, position: tuple[int, int], direction: int, owner):
        super().__init__()
        self.image = pygame.Surface((14, 6))
        self.image.fill((255, 220, 80))
        self.rect = self.image.get_rect(center=position)
        self.direction = direction
        self.owner = owner

    def update(self, target_surface: pygame.Surface) -> None:
        self.rect.x += self.SPEED * self.direction
        if not target_surface.get_rect().colliderect(self.rect):
            self.kill()

