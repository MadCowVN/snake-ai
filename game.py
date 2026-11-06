import random
import pygame  # only used inside draw(); importing pygame does not open a window

# --- board setup (counted in tiles, so every tile is complete) ---
COLS, ROWS = 20, 15
CELL_SIZE = 30

# COLORS
BODY_GOLD = (255, 230, 80)
FOOD_COLOR = (255, 120, 180)  # pink pastel neon

# --- terrain ---
# character in a map file -> time cost to move onto that tile (None = rock, cannot be entered)
TERRAIN_COST = {
    '.': 1,     # grass
    ':': 2,     # sand
    '~': 5,     # mud
    '#': None,  # rock
}
START_BODY = [(5, 5), (4, 5), (3, 5)]


def flat_map():
    """A board with only grass: the same as the game without terrain."""
    return [[1] * COLS for _ in range(ROWS)]


def load_map(path):
    """Read a map file (one character per tile) into terrain[y][x] = cost."""
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    if len(lines) != ROWS or any(len(line) != COLS for line in lines):
        raise ValueError(f"{path}: a map must be {ROWS} lines of {COLS} characters")
    terrain = [[TERRAIN_COST[ch] for ch in line] for line in lines]
    for (x, y) in START_BODY:
        if terrain[y][x] is None:
            raise ValueError(f"{path}: the snake starts on rock at {(x, y)}")
    return terrain


def rocks_of(terrain):
    """All rock tiles, as a set of (x, y)."""
    return {(x, y) for y, row in enumerate(terrain) for x, cost in enumerate(row) if cost is None}


# --- class Snake & Food ---
class Snake:
    def __init__(self):
        self.body = list(START_BODY)
        self.direction = (1, 0)  # right
        self.grow = False

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if not self.grow:
            self.body.pop()
        else:
            self.grow = False

        self.body.insert(0, new_head)

    def change_direction(self, new_dir):
        opposite = (-self.direction[0], -self.direction[1])
        if new_dir != opposite:
            self.direction = new_dir

    def check_collision(self, rocks=()):
        head = self.body[0]
        # đụng tường
        if (head[0] < 0 or head[0] >= COLS or
                head[1] < 0 or head[1] >= ROWS):
            return True
        # đụng thân
        if head in self.body[1:]:
            return True
        # đụng đá
        if head in rocks:
            return True
        return False

    def draw(self, screen, snake_head_img):
        for i, (x, y) in enumerate(self.body):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if i == 0:
                # đầu rắn = ảnh pixel art, xoay theo hướng đi
                if self.direction == (1, 0):  # right
                    rotated_head = snake_head_img
                elif self.direction == (-1, 0):  # left
                    rotated_head = pygame.transform.flip(snake_head_img, True, False)
                elif self.direction == (0, -1):  # up
                    rotated_head = pygame.transform.rotate(snake_head_img, 90)
                else:  # down
                    rotated_head = pygame.transform.rotate(snake_head_img, -90)
                screen.blit(rotated_head, rect)
            else:
                # Nếu không phải đầu thì vẽ thân rắn bình thường
                pygame.draw.rect(screen, BODY_GOLD, rect, border_radius=8)


class Food:
    def __init__(self, snake_body, rng=random, rocks=()):
        # rng: pass random.Random(seed) to get the same apples every run
        self.position = self.random_position(snake_body, rng, rocks)

    def random_position(self, snake_body, rng, rocks=()):
        free = [(x, y) for x in range(COLS) for y in range(ROWS)
                if (x, y) not in snake_body and (x, y) not in rocks]
        if not free:
            return None  # the snake fills the whole board
        return rng.choice(free)

    def draw(self, screen):
        if self.position is None:
            return
        x, y = self.position
        rect = pygame.Rect(x * CELL_SIZE + 5, y * CELL_SIZE + 5, CELL_SIZE - 10, CELL_SIZE - 10)
        pygame.draw.ellipse(screen, FOOD_COLOR, rect)
