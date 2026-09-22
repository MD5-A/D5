"""Classe représentant un combattant."""

import pygame


class Player(pygame.sprite.Sprite):
    """Joueur contrôlable avec déplacement, saut et points de vie."""

    SPEED = 5
    JUMP_FORCE = -12

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

    def handle_input(self, keys) -> bool:
        """Gère le déplacement et renvoie True lorsqu'une attaque est demandée."""
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
        return keys[self.controls["attack"]]

    def update_visual(self, dt: float) -> None:
        wanted = self.animations.get("run" if self.moving else "idle")
        if wanted is not None and wanted is not self.animation:
            self.animation = wanted
        if self.animation is not None:
            self.animation.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.animation is None:
            surface.blit(self.image, self.rect)
            return
        visual = self.animation.image
        if self.facing < 0:
            visual = pygame.transform.flip(visual, True, False)
        surface.blit(visual, visual.get_rect(midbottom=self.rect.midbottom))
