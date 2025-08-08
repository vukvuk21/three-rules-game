import os
import pygame
from collections import deque

TILE_VISUAL = 32
HITBOX_SIZE = 30

def _load_sprite(basename: str, size):
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

class Enemy:
    """BFS pathfinding monster that chases the player around walls."""
    def __init__(self, start_px_x: int, start_px_y: int, tile_size: int, speed: float = 2.0):
        self.tile = tile_size

        # Collision box smaller for smooth wall sliding
        self.rect = pygame.Rect(start_px_x, start_px_y, HITBOX_SIZE, HITBOX_SIZE)

        self.speed = speed
        self._path = []
        self._repath_cooldown = 0
        # Draw sprite at full 32x32 (visual)
        self.sprite = _load_sprite("monster", (TILE_VISUAL, TILE_VISUAL))
        self.fallback_color = (200, 60, 200)

    def _tile_from_px(self, x, y): return x // self.tile, y // self.tile
    def _center_for_tile(self, tx, ty): return tx*self.tile + self.tile//2, ty*self.tile + self.tile//2

    def _bfs(self, level, start_t, goal_t):
        rows, cols = len(level.map_data), len(level.map_data[0])
        inb = lambda t: 0 <= t[1] < rows and 0 <= t[0] < cols
        passable = lambda t: level.map_data[t[1]][t[0]] != 1

        q, prev = deque([start_t]), {start_t: None}
        while q:
            cur = q.popleft()
            if cur == goal_t: break
            x, y = cur
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                nt = (nx, ny)
                if inb(nt) and passable(nt) and nt not in prev:
                    prev[nt] = cur
                    q.append(nt)

        if goal_t not in prev: return []
        path, t = [], goal_t
        while t is not None:
            path.append(t); t = prev[t]
        path.reverse()
        return path

    def _ensure_path(self, level, player_rect):
        if self._repath_cooldown > 0 and self._path:
            self._repath_cooldown -= 1; return
        my_t  = self._tile_from_px(self.rect.centerx, self.rect.centery)
        ply_t = self._tile_from_px(player_rect.centerx, player_rect.centery)
        self._path = self._bfs(level, my_t, ply_t)
        self._repath_cooldown = 12

    def update(self, level, player_rect):
        self._ensure_path(level, player_rect)
        if len(self._path) < 2: return

        nxt_t = self._path[1]
        target_cx, target_cy = self._center_for_tile(*nxt_t)

        dx = target_cx - self.rect.centerx
        dy = target_cy - self.rect.centery
        dist = max(1, (dx*dx + dy*dy) ** 0.5)
        step_x = int(self.speed * dx / dist)
        step_y = int(self.speed * dy / dist)

        old_x, old_y = self.rect.x, self.rect.y
        self.rect.x += step_x
        if level.collides_with_wall(self.rect): self.rect.x = old_x
        self.rect.y += step_y
        if level.collides_with_wall(self.rect): self.rect.y = old_y

        if abs(self.rect.centerx - target_cx) <= 1 and abs(self.rect.centery - target_cy) <= 1:
            if self._path and self._path[0] != nxt_t:
                self._path.pop(0)

    def draw(self, screen):
        if self.sprite:
            top_left = (self.rect.centerx - TILE_VISUAL // 2,
                        self.rect.centery - TILE_VISUAL // 2)
            screen.blit(self.sprite, top_left)
        else:
            pygame.draw.rect(screen, self.fallback_color, self.rect, border_radius=4)
