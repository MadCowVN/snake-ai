import glob
import os
import pygame
import sys

from game import Snake, Food, COLS, ROWS, CELL_SIZE, flat_map, load_map, rocks_of
from ai import ALGORITHMS

# --- basic setup ---
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass  # no sound card: play without sound

#--- setup screen ---
HUD = 84  # bar at the top (3 lines) for score, time, AI, map, search info and keys
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE + HUD  # 20 x 15 tiles + HUD
FPS = 10
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cute Neon Snake 🐍✨")
clock = pygame.time.Clock()
# the board is drawn on this part of the screen, below the HUD
board = screen.subsurface((0, HUD, WIDTH, ROWS * CELL_SIZE))

# pictures and sounds are in the assets folder, next to this file
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(ASSETS, name))
    except (pygame.error, FileNotFoundError):
        return None  # file missing or no sound card: play without sound


def play(sound):
    if sound:
        sound.play()


# --- sound setup ---
sfx_eat = load_sound('eat.wav')
sfx_gameover = load_sound('gameover.wav')
# --- image setup ---
snake_head_img = pygame.image.load(os.path.join(ASSETS, "snakehead.png"))
snake_head_img = pygame.transform.scale(snake_head_img, (CELL_SIZE, CELL_SIZE))
snake_icon = pygame.image.load(os.path.join(ASSETS, "snake_icon.png")).convert_alpha()


# COLORS
BLACK = (0, 0, 0)
GRID_COLOR = (40, 40, 40)
SCORE_COLOR = (255, 182, 193)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)
RED = (255, 80, 80)
EXPLORED_COLOR = (60, 120, 255, 70)  # see-through blue (last number = transparency)
PATH_COLOR = (120, 255, 160)         # green dots for the planned path
# terrain cost -> tile color (dark, so the neon snake stays easy to see)
TERRAIN_COLOR = {
    1: (25, 60, 30),      # grass
    2: (95, 80, 40),      # sand
    5: (70, 40, 20),      # mud
    None: (105, 105, 115),  # rock
}

# maps: "flat" (no terrain, like the core game) + every .txt file in the maps folder
MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
MAPS = [("flat", flat_map())]
for map_path in sorted(glob.glob(os.path.join(MAPS_DIR, "*.txt"))):
    MAPS.append((os.path.splitext(os.path.basename(map_path))[0], load_map(map_path)))


font = pygame.font.SysFont("Comic Sans MS", 32)
small_font = pygame.font.Font(None, 40)
hud_font = pygame.font.SysFont("Consolas", 20)

# --- show menu ---
def show_menu():
    global snake_icon
    while True:
        screen.fill(BLACK)

        # Title
        title = font.render("Snake Game - Ngan Nghiem", True, YELLOW)
        start_text = small_font.render("Press S to Start", True, WHITE)
        quit_text = small_font.render("Press Q to Quit", True, RED)

        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2))
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, HEIGHT//2 + 50))

        snake_icon = pygame.transform.scale(snake_icon, (64, 64))
        screen.blit(snake_icon, (WIDTH//2 - title.get_width()//2 - 60, HEIGHT//3 - 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:  # press S to Start
                    return "start"
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):  # press Q or ESC to Quit
                    pygame.quit()
                    return "quit"


# --- setup game ---
choice = show_menu()
if choice == "quit":
    sys.exit()

paused = False
algo_name = "Greedy"
map_index = 0         # M key: next map
map_name, terrain = MAPS[map_index]
rocks = rocks_of(terrain)
show_search = True    # V key: show/hide explored tiles and path
explored = []         # tiles the AI looked at in the last move
path = []             # tiles the AI plans to walk
total_explored = 0    # for the average explored tiles per move

# one see-through square, reused to draw every explored tile
explored_tile = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
explored_tile.fill(EXPLORED_COLOR)


def restart():
    global snake, food, score, moves, game_over, won, explored, path, total_explored
    global time_used, head_cost
    snake = Snake()
    food = Food(snake.body, rocks=rocks)
    score = 0
    moves = 0
    time_used = 0         # every move costs the time of the tile the snake moves onto
    head_cost = 1         # cost of the tile under the head (the snake is slower on mud)
    game_over = False
    won = False
    explored = []
    path = []
    total_explored = 0


restart()

# --- main loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # quit
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_SPACE:  # pause / continue
                paused = not paused
            elif event.key == pygame.K_UP:  # faster
                FPS = min(FPS + 5, 120)
            elif event.key == pygame.K_DOWN:  # slower
                FPS = max(FPS - 5, 5)
            elif event.key == pygame.K_r:  # restart game
                restart()
            elif event.key == pygame.K_v:  # show / hide the search
                show_search = not show_search
            elif event.key == pygame.K_1:  # switch AI
                algo_name = "Greedy"
            elif event.key == pygame.K_2:
                algo_name = "BFS"
            elif event.key == pygame.K_3:
                algo_name = "DFS"
            elif event.key == pygame.K_4:
                algo_name = "Dijkstra"
            elif event.key == pygame.K_5:
                algo_name = "A*"
            elif event.key == pygame.K_m:  # next map, and start again on it
                map_index = (map_index + 1) % len(MAPS)
                map_name, terrain = MAPS[map_index]
                rocks = rocks_of(terrain)
                restart()

    if not game_over and not paused:
        # the AI chooses the direction instead of the arrow keys
        ai = ALGORITHMS[algo_name]
        direction, explored, path = ai(snake.body, food.position, COLS, ROWS, terrain)
        total_explored += len(explored)
        if direction is None:  # no safe move left
            play(sfx_gameover)
            game_over = True
        else:
            snake.change_direction(direction)
            snake.move()
            moves += 1

            # check collision first: if the head is outside the board, it has no terrain cost
            if snake.check_collision(rocks):
                play(sfx_gameover)
                game_over = True
            else:
                head_x, head_y = snake.body[0]
                head_cost = terrain[head_y][head_x]
                time_used += head_cost

                # eat food
                if snake.body[0] == food.position:
                    play(sfx_eat)
                    score += 1
                    snake.grow = True
                    food = Food(snake.body, rocks=rocks)
                    if food.position is None:  # board is full: the snake wins
                        won = True
                        game_over = True

    # --- draw screen ---
    screen.fill(BLACK)

    # terrain (the flat map stays black, like the core game)
    if map_name != "flat":
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(board, TERRAIN_COLOR[terrain[y][x]], rect)

    # lưới nhẹ cho đẹp (cột và hàng vẽ riêng, để bàn không vuông vẫn đúng)
    for x in range(0, WIDTH + 1, CELL_SIZE):
        pygame.draw.line(board, GRID_COLOR, (x, 0), (x, ROWS * CELL_SIZE))
    for y in range(0, ROWS * CELL_SIZE + 1, CELL_SIZE):
        pygame.draw.line(board, GRID_COLOR, (0, y), (WIDTH, y))

    # explored tiles (blue) and planned path (green dots), under the snake and the apple
    if show_search:
        for (x, y) in explored:
            board.blit(explored_tile, (x * CELL_SIZE, y * CELL_SIZE))
        for (x, y) in path:
            center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
            pygame.draw.circle(board, PATH_COLOR, center, 4)

    food.draw(board)
    snake.draw(board, snake_head_img)

    # HUD: scoring and info
    hud = f"Score: {score}   Time: {time_used}   Moves: {moves}   Speed: {FPS}"
    if paused:
        hud += "  [PAUSED]"
    avg = total_explored / moves if moves else 0
    hud2 = f"AI: {algo_name}   Map: {map_name}   Explored: {len(explored)} (avg {avg:.0f})"
    hud3 = "[1]Greedy [2]BFS [3]DFS [4]Dijkstra [5]A* [M]ap"
    screen.blit(hud_font.render(hud, True, SCORE_COLOR), (10, 6))
    screen.blit(hud_font.render(hud2, True, WHITE), (10, 31))
    screen.blit(hud_font.render(hud3, True, (150, 150, 150)), (10, 56))

    if game_over:
        text = "YOU WIN! Press R to restart" if won else "GAME OVER! Press R to restart"
        msg = font.render(text, True, (255, 100, 120))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 30))

    pygame.display.flip()
    # slower on expensive terrain: a move onto mud (cost 5) takes 5 times longer than grass
    clock.tick(FPS / head_cost)
