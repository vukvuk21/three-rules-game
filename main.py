import os
import json
import time
import pygame
from player import Player
from rules import Rules
from level import Level
from enemy import Enemy

# ---------------- Config ----------------
WIDTH, HEIGHT = 640, 480
TILE = 32
PLAYER_SPEED = 2
ENEMY_SPEED  = 2
IDLE_LIMIT_FRAMES = 120
MAX_LIVES = 3

SCORES_FILE = "scores.json"
MAX_SCORES = 5

# ---------------- Pygame init ----------------
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Three Forbidden Rules")
CLOCK = pygame.time.Clock()
FONT     = pygame.font.Font(None, 28)
FONT_BIG = pygame.font.Font(None, 40)

# ---------------- UI colors (blue theme) ----------------
COLOR_UI_DIM     = (90, 140, 220)
COLOR_UI         = (120, 180, 255)
COLOR_UI_BRIGHT  = (160, 210, 255)
COLOR_WARN       = (255, 120, 120)

# ---------------- Assets ----------------
def load_menu_bg(width, height):
    base = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base, "assets")
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    if not os.path.isdir(assets_dir):
        print(f"[Menu BG] assets not found: {assets_dir}")
        return None
    try:
        files = os.listdir(assets_dir)
    except Exception as e:
        print(f"[Menu BG] cannot list assets/: {e}")
        return None
    chosen = None
    for f in files:
        r, e = os.path.splitext(f)
        if r.lower() == "menu_bg" and e.lower() in allowed_exts:
            chosen = os.path.join(assets_dir, f); break
    if not chosen:
        print(f"[Menu BG] Put menu_bg.(png|jpg|jpeg|webp|bmp) into {assets_dir}")
        return None
    try:
        img = pygame.image.load(chosen)
        img = img.convert_alpha() if img.get_alpha() else img.convert()
        return pygame.transform.smoothscale(img, (width, height))
    except Exception as e:
        print(f"[Menu BG] failed to load {chosen}: {e}")
        return None

MENU_BG = load_menu_bg(WIDTH, HEIGHT)

# ---------------- Scores ----------------
def load_scores():
    if not os.path.exists(SCORES_FILE): return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list): return data
    except Exception: pass
    return []

def save_score(name: str, score: int):
    scores = load_scores()
    scores.append({"name": name[:20], "score": int(score), "ts": int(time.time())})
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_SCORES]
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

# ---------------- States ----------------
STATE_MENU, STATE_NAME, STATE_PLAY, STATE_SCORES, STATE_WIN, STATE_GAMEOVER = (
    "menu","name","play","scores","win","gameover"
)

state = STATE_MENU
menu_index = 0
menu_items = ["Start Game", "High Scores", "Quit"]

player_name = ""
idle_frames = 0
lives = MAX_LIVES
won = False

# ---------------- World lifecycle ----------------
def start_new_run():
    global level, player, rules, enemy, idle_frames, won, lives
    level = Level(tile_size=TILE, seed=None)
    rules = Rules()                # score = 0 on brand-new run
    player = Player(level.start_x, level.start_y, speed=PLAYER_SPEED)
    enemy  = Enemy(start_px_x=TILE*15, start_px_y=TILE*3, tile_size=TILE, speed=ENEMY_SPEED)
    idle_frames = 0
    lives = MAX_LIVES
    won = False

def reset_after_break():
    global enemy, idle_frames, state, lives
    lives -= 1
    if lives > 0:
        rules.reset_run_state()    # keeps score
        level.reset_run_state()
        player.reset_position(level.start_x, level.start_y)
        enemy = Enemy(start_px_x=TILE*15, start_px_y=TILE*3, tile_size=TILE, speed=ENEMY_SPEED)
        idle_frames = 0
    else:
        save_score(player_name or "Player", rules.score)
        state = STATE_GAMEOVER

# ---------------- Draw helpers ----------------
def draw_text_center(surf, text, y, font, color=(240,240,240)):
    t = font.render(text, True, color)
    surf.blit(t, (WIDTH//2 - t.get_width()//2, y))

def draw_heart(surf, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surf, color, (x + size//3,   y + size//3), r)
    pygame.draw.circle(surf, color, (x + 2*size//3, y + size//3), r)
    pygame.draw.polygon(surf, color, [(x, y + size//3), (x + size, y + size//3), (x + size//2, y + size)])

def draw_hearts():
    margin, size = 8, 18
    spacing = size + 6
    for i in range(MAX_LIVES):
        x = WIDTH - margin - (MAX_LIVES - i) * spacing
        y = margin
        color = (220, 60, 60) if i < lives else (90, 90, 90)
        draw_heart(SCREEN, x, y, size, color)

def draw_hud():
    info = f"Score: {rules.score}"
    text = FONT.render(info, True, COLOR_UI)
    pad = 6
    bg = pygame.Surface((text.get_width()+pad*2, text.get_height()+pad*2), pygame.SRCALPHA)
    bg.fill((0,0,0,140))
    SCREEN.blit(bg, (8, 8))
    SCREEN.blit(text, (8+pad, 8+pad))
    draw_hearts()
    if rules.last_broken_msg:
        warn = FONT.render(rules.last_broken_msg, True, COLOR_WARN)
        SCREEN.blit(warn, (8, 8 + bg.get_height() + 6))

# ---------------- Main loop ----------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if state == STATE_MENU and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):   menu_index = (menu_index - 1) % len(menu_items)
            elif event.key in (pygame.K_DOWN, pygame.K_s): menu_index = (menu_index + 1) % len(menu_items)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = menu_items[menu_index]
                if choice == "Start Game":
                    player_name = ""; state = STATE_NAME
                elif choice == "High Scores":
                    state = STATE_SCORES
                elif choice == "Quit":
                    running = False

        elif state == STATE_NAME and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and len(player_name) > 0:
                start_new_run(); state = STATE_PLAY
            elif event.key == pygame.K_BACKSPACE:
                player_name = player_name[:-1]
            else:
                ch = event.unicode
                if ch and (ch.isalnum() or ch == " "):
                    if len(player_name) < 20: player_name += ch

        elif state == STATE_SCORES and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_SPACE):
                state = STATE_MENU

        elif state in (STATE_WIN, STATE_GAMEOVER) and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                state = STATE_MENU

    # ---- States ----
    if state == STATE_MENU:
        if MENU_BG:
            SCREEN.blit(MENU_BG, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,120)); SCREEN.blit(overlay, (0,0))
        else:
            SCREEN.fill((12,12,12))
        draw_text_center(SCREEN, "Three Forbidden Acts", 80, FONT_BIG, COLOR_UI_BRIGHT)
        for i, item in enumerate(menu_items):
            color = COLOR_UI_BRIGHT if i == menu_index else COLOR_UI_DIM
            draw_text_center(SCREEN, item, 170 + i*40, FONT, color)

    elif state == STATE_NAME:
        SCREEN.fill((0,0,0))
        draw_text_center(SCREEN, "Enter your name", 120, FONT_BIG, COLOR_UI_BRIGHT)
        box_w = 360
        box = pygame.Rect(WIDTH//2 - box_w//2, 200, box_w, 40)
        pygame.draw.rect(SCREEN, (40,40,40), box, border_radius=6)
        pygame.draw.rect(SCREEN, (120,120,120), box, width=2, border_radius=6)
        name_surf = FONT.render(player_name or "_", True, COLOR_UI)
        SCREEN.blit(name_surf, (box.x + 10, box.y + 8))
        hint = FONT.render("Press ENTER to start", True, COLOR_UI_DIM)
        SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, 260))

    elif state == STATE_SCORES:
        SCREEN.fill((0,0,0))
        draw_text_center(SCREEN, "High Scores (Top 5)", 80, FONT_BIG, COLOR_UI_BRIGHT)
        scores = load_scores()
        if not scores:
            draw_text_center(SCREEN, "No scores yet. Play a game!", 160, FONT, COLOR_UI)
        else:
            y = 150
            for i, s in enumerate(scores[:MAX_SCORES], 1):
                line = f"{i:2}. {s['name']:<20}  {s['score']} pts"
                t = FONT.render(line, True, COLOR_UI)
                SCREEN.blit(t, (WIDTH//2 - 200, y)); y += 30
        draw_text_center(SCREEN, "Press ESC to return", 420, FONT, COLOR_UI_DIM)

    elif state == STATE_PLAY:
        SCREEN.fill((0,0,0))
        keys = pygame.key.get_pressed()

        # Update entities
        player.update(keys, rules, level)
        enemy.update(level, player.rect)

        # Rule 1: lava
        if level.is_on_red(player.rect):
            rules.break_rule(1, "Stepped on a lava tile.")

        # Rule 2: monster caught you
        if enemy.rect.colliderect(player.rect):
            rules.break_rule(2, "Caught by the Sentinel.")

        # Rule 3: no camping
        idle_frames = 0 if getattr(player, "moved_this_frame", False) else idle_frames + 1
        if idle_frames > IDLE_LIMIT_FRAMES:
            rules.break_rule(3, "Stayed still for too long.")

        # Handle penalties / lives
        if rules.any_broken():
            reset_after_break()

        # Win condition
        if state == STATE_PLAY and level.touches_exit(player.rect):
            save_score(player_name or "Player", rules.score)
            state = STATE_WIN

        # Draw world + HUD
        level.draw(SCREEN)
        enemy.draw(SCREEN)
        player.draw(SCREEN)
        draw_hud()

    elif state == STATE_WIN:
        SCREEN.fill((0,0,0))
        draw_text_center(SCREEN, "YOU WIN!", 150, FONT_BIG, COLOR_UI_BRIGHT)
        draw_text_center(SCREEN, f"Score saved for {player_name or 'Player'}: {rules.score} pts", 200, FONT, COLOR_UI)
        draw_text_center(SCREEN, "Press ENTER to return to menu", 260, FONT, COLOR_UI_DIM)

    elif state == STATE_GAMEOVER:
        SCREEN.fill((0,0,0))
        draw_text_center(SCREEN, "GAME OVER", 150, FONT_BIG, COLOR_UI_BRIGHT)
        draw_text_center(SCREEN, f"Score saved for {player_name or 'Player'}: {rules.score} pts", 200, FONT, COLOR_UI)
        draw_text_center(SCREEN, "Press ENTER to return to menu", 260, FONT, COLOR_UI_DIM)

    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
