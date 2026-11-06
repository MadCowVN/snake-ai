import heapq
from collections import deque

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right

# Every AI has the same shape:
#   ai(snake_body, apple, cols, rows, terrain=None) -> (direction, explored, path)
#   terrain:   terrain[y][x] = time cost of the tile (None = rock). None = flat board (all cost 1)
#   direction: (dx, dy), or None if there is no safe move
#   explored:  list of tiles the AI took out of its queue/stack/heap (for drawing and counting)
#   path:      list of tiles the AI plans to walk (for drawing)


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def cost_of(tile, terrain):
    return 1 if terrain is None else terrain[tile[1]][tile[0]]


def is_free(tile, walls, cols, rows, terrain=None):
    """Inside the board, not the snake's body, and not rock."""
    if not (0 <= tile[0] < cols and 0 <= tile[1] < rows) or tile in walls:
        return False
    return cost_of(tile, terrain) is not None


def build_path(came_from, head, apple):
    """Walk back from the apple to the head, then turn the list around."""
    path = []
    tile = apple
    while tile != head:
        path.append(tile)
        tile = came_from[tile]
    path.reverse()
    return path


# ---------------- Greedy (core) ----------------

def greedy(snake_body, apple, cols, rows, terrain=None):
    """Look at the (up to) 4 neighbours, drop the deadly ones, pick the one closest to the apple."""
    head = snake_body[0]
    walls = set(snake_body)
    best = None
    best_distance = None
    explored = []

    for d in DIRECTIONS:
        tile = (head[0] + d[0], head[1] + d[1])
        if not is_free(tile, walls, cols, rows, terrain):
            continue  # this move would kill the snake
        explored.append(tile)
        distance = manhattan(tile, apple)
        if best is None or distance < best_distance:
            best = d
            best_distance = distance

    path = [(head[0] + best[0], head[1] + best[1])] if best else []
    return best, explored, path


# ---------------- BFS and DFS (extra 1) ----------------

def search(snake_body, apple, cols, rows, use_stack, terrain=None):
    """BFS (queue) or DFS (stack) from the head to the apple. The body is a wall.
    Ignores the time cost of the terrain. Returns (path, explored); path is None if unreachable."""
    head = snake_body[0]
    walls = set(snake_body)
    frontier = deque([head])
    came_from = {head: None}  # tile -> the tile we came from (also works as 'visited')
    explored = []

    while frontier:
        # THE ONLY DIFFERENCE between BFS and DFS:
        # BFS takes the OLDEST tile (queue), DFS takes the NEWEST tile (stack).
        tile = frontier.pop() if use_stack else frontier.popleft()
        explored.append(tile)

        if tile == apple:
            return build_path(came_from, head, apple), explored

        for d in DIRECTIONS:
            nxt = (tile[0] + d[0], tile[1] + d[1])
            if is_free(nxt, walls, cols, rows, terrain) and nxt not in came_from:
                came_from[nxt] = tile
                frontier.append(nxt)

    return None, explored


# ---------------- Dijkstra and A* (extra 2) ----------------

def cheapest_search(snake_body, apple, cols, rows, terrain, use_heuristic):
    """Dijkstra (use_heuristic=False) or A* (use_heuristic=True): the path with the LEAST TIME.
    Returns (path, explored); path is None if unreachable."""
    head = snake_body[0]
    walls = set(snake_body)

    # A* heuristic: Manhattan distance x the cheapest terrain cost.
    # It never overestimates the time left, so A* still finds the cheapest path.
    if terrain is None:
        cheapest = 1
    else:
        cheapest = min(c for row in terrain for c in row if c is not None)

    def h(tile):
        return manhattan(tile, apple) * cheapest if use_heuristic else 0

    best_time = {head: 0}     # cheapest time found so far to reach each tile
    came_from = {head: None}
    heap = [(h(head), 0, head)]  # (priority, time so far, tile); heapq pops the smallest
    explored = []

    while heap:
        priority, time_so_far, tile = heapq.heappop(heap)
        if time_so_far > best_time[tile]:
            continue  # old entry: we already found a faster way to this tile
        explored.append(tile)

        if tile == apple:
            return build_path(came_from, head, apple), explored

        for d in DIRECTIONS:
            nxt = (tile[0] + d[0], tile[1] + d[1])
            if not is_free(nxt, walls, cols, rows, terrain):
                continue
            new_time = time_so_far + cost_of(nxt, terrain)
            if nxt not in best_time or new_time < best_time[nxt]:
                best_time[nxt] = new_time
                came_from[nxt] = tile
                # Dijkstra: priority = time so far. A*: time so far + estimated time left.
                heapq.heappush(heap, (new_time + h(nxt), new_time, nxt))

    return None, explored


# ---------------- following a path ----------------

def follow(path, explored, snake_body, apple, cols, rows, terrain):
    """Take the first step of the path. If there is no path (apple blocked by the body),
    plan B: take a safe greedy step and search again next move."""
    if not path:
        direction, _, path = greedy(snake_body, apple, cols, rows, terrain)
        return direction, explored, path
    head = snake_body[0]
    first = path[0]
    return (first[0] - head[0], first[1] - head[1]), explored, path


def bfs(snake_body, apple, cols, rows, terrain=None):
    path, explored = search(snake_body, apple, cols, rows, False, terrain)
    return follow(path, explored, snake_body, apple, cols, rows, terrain)


def dfs(snake_body, apple, cols, rows, terrain=None):
    path, explored = search(snake_body, apple, cols, rows, True, terrain)
    return follow(path, explored, snake_body, apple, cols, rows, terrain)


def dijkstra(snake_body, apple, cols, rows, terrain=None):
    path, explored = cheapest_search(snake_body, apple, cols, rows, terrain, False)
    return follow(path, explored, snake_body, apple, cols, rows, terrain)


def astar(snake_body, apple, cols, rows, terrain=None):
    path, explored = cheapest_search(snake_body, apple, cols, rows, terrain, True)
    return follow(path, explored, snake_body, apple, cols, rows, terrain)


# Name -> function, used by main.py (keys 1-5) and benchmark.py
ALGORITHMS = {
    "Greedy": greedy,
    "BFS": bfs,
    "DFS": dfs,
    "Dijkstra": dijkstra,
    "A*": astar,
}
