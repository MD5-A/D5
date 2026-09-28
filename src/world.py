"""Éléments du monde, plateformes et gestion de la physique verticale."""

import pygame


class Platform(pygame.sprite.Sprite):
    """Plateforme rectangulaire solide."""

    def __init__(
        self,
        rect: pygame.Rect,
        color: tuple[int, int, int] = (0, 250, 0),
    ):
        super().__init__()
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=rect.topleft)


class World:
    """Contient les plateformes et gère la physique verticale des joueurs."""

    GRAVITY = 0.7

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.platforms = pygame.sprite.Group()

        self.create_level()

    def create_level(self) -> None:
        """Crée l'arène principale avec plusieurs plateformes."""

        platform_data = [
            # Sol principal
            (0, self.height - 1, self.width, 5),

            # Plateforme centrale
            (self.width // 2 - 110, self.height - 170, 220, 20),

            # Plateforme gauche
            (100, self.height - 280, 180, 20),

            # Plateforme droite
            (self.width - 280, self.height - 280, 180, 20),

            # Plateforme supérieure centrale
            (self.width // 2 - 80, self.height - 390, 160, 20),
        ]

        for x, y, width, height in platform_data:
            rect = pygame.Rect(x, y, width, height)
            self.platforms.add(Platform(rect))

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine toutes les plateformes du monde."""
        self.platforms.draw(surface)

    def apply_gravity(self, player) -> None:
        """Applique la gravité puis gère les collisions verticales."""
        player.velocity_y += self.GRAVITY
        player.rect.y += round(player.velocity_y)

        player.on_ground = False

        self.handle_vertical_collisions(player)

    def handle_vertical_collisions(self, player) -> None:
        """Pose le joueur sur une plateforme lorsqu'il tombe dessus."""

        # On ne cherche une plateforme que lorsque le joueur descend.
        if player.velocity_y < 0:
            return

        # Position verticale des pieds avant le déplacement.
        previous_bottom = player.rect.bottom - round(player.velocity_y)

        # Point de référence sous le joueur.
        foot_x = player.rect.centerx

        for platform in self.platforms:
            # Le joueur doit être horizontalement au-dessus de la plateforme.
            over_platform = (
                platform.rect.left < foot_x < platform.rect.right
            )

            # Vérifie que le joueur était au-dessus de la plateforme
            # avant de la traverser.
            crossed_platform = (
                previous_bottom <= platform.rect.top
                and player.rect.bottom >= platform.rect.top
            )

            if over_platform and crossed_platform:
                player.rect.bottom = platform.rect.top
                player.velocity_y = 0
                player.on_ground = True

                if hasattr(player, "max_jumps") and hasattr(player, "jumps_left"):
                    player.jumps_left = player.max_jumps

                break
    def keep_inside_world(self, player) -> None:
        """Empêche le joueur de sortir horizontalement de l'arène."""
        if player.rect.left < 0:
            player.rect.left = 0

        if player.rect.right > self.width:
            player.rect.right = self.width
