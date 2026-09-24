"""Chargement des spritesheets décrits par les fichiers JSON."""

import json
from pathlib import Path

import pygame


class SpriteAnimation:
    """Animation extraite d'un spritesheet et de ses métadonnées JSON."""

    def __init__(self, image_path: Path, data_path: Path, size=(96, 96)):
        self.sheet = pygame.image.load(str(image_path)).convert_alpha()
        with data_path.open(encoding="utf-8") as file:
            metadata = json.load(file)

        self.frames = []
        for frame_data in metadata["frames"].values():
            frame = self.sheet.subsurface(
                pygame.Rect(frame_data["x"], frame_data["y"], frame_data["w"], frame_data["h"])
            ).copy()
            # Les spritesheets contiennent une marge transparente sous les pieds.
            # On la repositionne sans recadrer le personnage afin que son bas
            # visible coïncide avec le bas du rectangle physique du joueur.
            visible_bounds = frame.get_bounding_rect(min_alpha=1)
            if visible_bounds.height > 0:
                aligned = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                aligned.blit(frame, (0, frame.get_height() - visible_bounds.bottom))
                frame = aligned
            self.frames.append(pygame.transform.smoothscale(frame, size))

        self.index = 0
        self.elapsed = 0.0
        self.frame_duration = 0.08

    @property
    def image(self) -> pygame.Surface:
        return self.frames[self.index]

    def clone(self) -> "SpriteAnimation":
        """Crée une animation indépendante sans recharger les images."""
        animation = object.__new__(SpriteAnimation)
        animation.sheet = self.sheet
        animation.frames = self.frames
        animation.index = 0
        animation.elapsed = 0.0
        animation.frame_duration = self.frame_duration
        return animation

    def update(self, dt: float) -> None:
        if len(self.frames) < 2:
            return
        self.elapsed += dt
        while self.elapsed >= self.frame_duration:
            self.elapsed -= self.frame_duration
            self.index = (self.index + 1) % len(self.frames)


def load_character_animations(folder_name: str, character_name: str) -> dict[str, SpriteAnimation]:
    """Charge les animations disponibles pour un personnage."""
    folder = Path(__file__).resolve().parent.parent / "assets" / folder_name
    animations = {}
    for animation_name in ("idle", "run", "walk", "dance"):
        image_path = folder / f"{character_name}-{animation_name}.png"
        data_path = folder / f"{character_name}-{animation_name}.json"
        if image_path.exists() and data_path.exists():
            animations[animation_name] = SpriteAnimation(image_path, data_path)
    return animations
