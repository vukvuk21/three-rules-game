import os
import pygame

TILE_VISUAL = 32      # visual size to draw (same as lava tile)
HITBOX_SIZE = 30      # collision box (kept smaller for smooth movement)

def _load_sprite(basename: str, size):
    """Load assets/<basename>.(png|jpg|jpeg|webp|bmp), scaled to size."""
    base = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(base, "assets")
    if not os.path.isdir(assets):
        return None
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    for fname in os.listdir(assets):
        root, ext = os.path.splitext(fname)
        if root.lower() == basename.lower() and ext.lower() in exts:
            path = os.path.join(assets, fname)
            try:
                img = pygame.image.load(path)
                img = img.convert_alpha() if img.get_alpha() else img.convert()
                return pygame.transform.smoothscale(img, size)
            except Exception:
                return None
    return None

class Player:
    """Top-down player; axis-locked movement (no diagonals)."""

    def __init__(self, x: int, y: int, speed: int = 2):
        self.start_x = x
        self.start_y = y

        # Collision rect (smaller), but we draw a bigger 32x32 sprite centered on it.
        self.rect = pygame.Rect(x, y, HITBOX_SIZE, HITBOX_SIZE)

        self.speed = speed
        self.moved_this_frame = False
        # Sprite used for drawing (full tile size):
        self.sprite = _load_sprite("player", (TILE_VISUAL, TILE_VISUAL))
        self.fallback_color = (0, 200, 255)

    def reset_position(self, x: int, y: int) -> None:
        self.rect.x = x
        self.rect.y = y

    def _move_axis(self, dx: int, dy: int, level) -> None:
        if dx:
            self.rect.x += dx
            if level.collides_with_wall(self.rect):
                self.rect.x -= dx
        if dy:
            self.rect.y += dy
            if level.collides_with_wall(self.rect):
                self.rect.y -= dy

    def update(self, keys, rules, level) -> None:
        old_x, old_y = self.rect.x, self.rect.y

        horizontal = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        vertical   = (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * self.speed
        # Lock to one axis per frame
        if horizontal != 0:
            vertical = 0

        self._move_axis(horizontal, 0, level)
        self._move_axis(0, vertical, level)

        if level.check_pickup(self.rect):
            rules.on_item_picked()

        self.moved_this_frame = (self.rect.x != old_x) or (self.rect.y != old_y)

    def draw(self, screen) -> None:
        if self.sprite:
            # Center 32x32 sprite on the (smaller) hitbox center
            top_left = (self.rect.centerx - TILE_VISUAL // 2,
                        self.rect.centery - TILE_VISUAL // 2)
            screen.blit(self.sprite, top_left)
        else:
            pygame.draw.rect(screen, self.fallback_color, self.rect)
