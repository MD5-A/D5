"""Classe représentant un combattant."""

import pygame


class Player(pygame.sprite.Sprite):
    """Joueur contrôlable avec déplacement, saut et points de vie."""

    SPEED = 5
    JUMP_FORCE = -12

    def __init__(self, position: tuple[int, int], color: tuple[int, int, int], controls: dict):
        super().__init__()
        self.image = pygame.Surface((42, 64))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=position)
        self.controls = controls
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing = 1
        self.health = 100

    def handle_input(self, keys) -> bool:
        """Gère le déplacement et renvoie True lorsqu'une attaque est demandée."""
        if keys[self.controls["left"]]:
            self.rect.x -= self.SPEED
            self.facing = -1
        if keys[self.controls["right"]]:
            self.rect.x += self.SPEED
            self.facing = 1
        if keys[self.controls["jump"]] and self.on_ground:
            self.velocity_y = self.JUMP_FORCE
            self.on_ground = False
        return keys[self.controls["attack"]]

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)

