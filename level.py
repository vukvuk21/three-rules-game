import os
import pygame
import random

# Tweakables za veličinu itema
LEMON_PAD_VISUAL = 2          # koliko piksela margine ostaviti oko limuna (vizuelno)
LEMON_PAD_COLLISION = 2       # koliko manji da bude collision box (prijatniji pickup)

def _load_sprite(name: str, size) -> pygame.Surface | None:
    """Load assets/<name>.(png|jpg|jpeg|webp|bmp), scaled to size."""
    base = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(base, "assets")
    if not os.path.isdir(assets):
        return None
    for fname in os.listdir(assets):
        root, ext = os.path.splitext(fname)
        if root.lower() == name.lower() and ext.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
            path = os.path.join(assets, fname)
            try:
                img = pygame.image.load(path)
                img = img.convert_alpha() if img.get_alpha() else img.convert()
                return pygame.transform.smoothscale(img, size)
            except Exception:
                return None
    return None

class Level:
    """
    Tiles:
      0 = floor, 1 = wall, 2 = lemon (score), 3 = lava (forbidden), 4 = finish (green tile)
    20x15 grid with outer walls, scattered lava & lemons.
    """

    def __init__(self, tile_size=32, seed=None):
        self.TILE = tile_size
        self.cols, self.rows = 20, 15

        if seed is not None:
            random.seed(seed)

        # Start/finish tiles (grid positions)
        self.start_tile  = (2, 2)
        self.finish_tile = (self.cols - 2, 2)

        # Map: walls around, floor inside
        self.map_data = [[1]*self.cols]
        for _ in range(self.rows - 2):
            self.map_data.append([1] + [0]*(self.cols - 2) + [1])
        self.map_data.append([1]*self.cols)

        # Scatter lava & lemons
        for y in range(1, self.rows - 1):
            for x in range(1, self.cols - 1):
                if (x, y) in (self.start_tile, self.finish_tile):
                    continue
                r = random.random()
                if r < 0.08:
                    self.map_data[y][x] = 3  # lava
                elif r < 0.13:
                    self.map_data[y][x] = 2  # lemon

        # Put finish and clear danger around start/finish
        sx, sy = self.start_tile
        fx, fy = self.finish_tile
        self.map_data[fy][fx] = 4
        for (cx, cy) in [(sx, sy), (fx, fy)]:
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    tx, ty = cx+dx, cy+dy
                    if 0 <= ty < self.rows and 0 <= tx < self.cols:
                        if self.map_data[ty][tx] == 3:
                            self.map_data[ty][tx] = 0

        # Start position in pixels
        self.start_x = self.TILE * self.start_tile[0]
        self.start_y = self.TILE * self.start_tile[1]

        # Fallback colors
        self.colors = {
            0: (50, 50, 50),      # floor
            1: (100, 100, 100),   # wall
            2: (230, 200, 40),    # lemon
            3: (170, 40, 40),     # lava
            4: (60, 200, 80),     # finish GREEN (traženo)
        }

        # Load sprites (None -> fallback)
        ts = (self.TILE, self.TILE)
        self.tex_floor  = _load_sprite("tile_floor", ts)
        self.tex_wall   = _load_sprite("tile_wall", ts)
        self.tex_lava   = _load_sprite("tile_lava", ts)

        # Forsiramo “finish” kao zelenu pločicu — ne koristimo finish.png više
        self.tex_finish = None

        # Veći limun: skoro pun tile (ostavimo tanak border)
        lemon_size = (self.TILE - 2*LEMON_PAD_VISUAL, self.TILE - 2*LEMON_PAD_VISUAL)
        self.tex_lemon  = _load_sprite("item_lemon", lemon_size)

        # Items tracked separately (so we can remove on pickup and respawn on reset)
        self.initial_items = self._extract_items()
        self.items = list(self.initial_items)

    # ---- Drawing & collisions ----
    def draw(self, screen):
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                dst = pygame.Rect(x*self.TILE, y*self.TILE, self.TILE, self.TILE)

                # choose texture / color
                if tile == 1:
                    tex, color = self.tex_wall, self.colors[1]
                elif tile == 3:
                    tex, color = self.tex_lava, self.colors[3]
                elif tile == 4:
                    tex, color = self.tex_finish, self.colors[4]  # tex_finish je None -> crtajmo zeleno
                else:
                    tex, color = self.tex_floor, self.colors[0]

                if tex is not None:
                    screen.blit(tex, dst)
                else:
                    pygame.draw.rect(screen, color, dst)

        # lemons (centered; sada veliki)
        for (ix, iy) in self.items:
            if self.tex_lemon is not None:
                pos = (ix*self.TILE + LEMON_PAD_VISUAL,
                       iy*self.TILE + LEMON_PAD_VISUAL)
                screen.blit(self.tex_lemon, pos)
            else:
                rect = pygame.Rect(ix*self.TILE+LEMON_PAD_VISUAL, iy*self.TILE+LEMON_PAD_VISUAL,
                                   self.TILE-2*LEMON_PAD_VISUAL, self.TILE-2*LEMON_PAD_VISUAL)
                pygame.draw.rect(screen, self.colors[2], rect)

    def collides_with_wall(self, rect: pygame.Rect) -> bool:
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    if rect.colliderect(pygame.Rect(x*self.TILE, y*self.TILE, self.TILE, self.TILE)):
                        return True
        return False

    # ---- Interactions ----
    def _extract_items(self):
        return [(x, y) for y, row in enumerate(self.map_data) for x, t in enumerate(row) if t == 2]

    def reset_run_state(self):
        self.items = list(self.initial_items)

    def check_pickup(self, rect: pygame.Rect) -> bool:
        hit = None
        # Collision box malo manji od celog tile-a da je “prijatniji”
        for (ix, iy) in self.items:
            item_rect = pygame.Rect(ix*self.TILE+LEMON_PAD_COLLISION,
                                    iy*self.TILE+LEMON_PAD_COLLISION,
                                    self.TILE-2*LEMON_PAD_COLLISION,
                                    self.TILE-2*LEMON_PAD_COLLISION)
            if rect.colliderect(item_rect):
                hit = (ix, iy); break
        if hit:
            self.items.remove(hit)
            return True
        return False

    def tile_at_pixel_center(self, rect: pygame.Rect) -> int:
        cx = rect.centerx // self.TILE
        cy = rect.centery // self.TILE
        if 0 <= cy < self.rows and 0 <= cx < self.cols:
            return self.map_data[cy][cx]
        return 1  # out of bounds -> wall

    def is_on_red(self, rect: pygame.Rect) -> bool:
        return self.tile_at_pixel_center(rect) == 3

    def touches_exit(self, rect: pygame.Rect) -> bool:
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 4:
                    if rect.colliderect(pygame.Rect(x*self.TILE, y*self.TILE, self.TILE, self.TILE)):
                        return True
        return False
