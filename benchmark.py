"""Compare the AIs without drawing anything, so it runs fast.

Every AI plays the same games: the same seeds give the same random generator for the apples.
Run:  python benchmark.py
"""
import glob
import os
import random

from game import Snake, Food, COLS, ROWS, flat_map, load_map, rocks_of
from ai import ALGORITHMS

MAX_MOVES = 20000               # stop a game that runs too long
STUCK_LIMIT = COLS * ROWS * 4   # stop if no apple for this many moves (walking in circles)

# Part 1: flat board, play until the snake dies
FLAT_SEEDS = range(50)
FLAT_AIS = ["Greedy", "BFS", "DFS"]

# Part 2: terrain maps, play until APPLE_GOAL apples (or the snake dies)
TERRAIN_SEEDS = range(30)
TERRAIN_AIS = ["BFS", "Dijkstra", "A*"]
APPLE_GOAL = 30


def play_game(ai, seed, terrain, max_apples=None):
    rng = random.Random(seed)
    rocks = rocks_of(terrain)
    snake = Snake()
    food = Food(snake.body, rng, rocks)
    score = moves = explored = time_used = 0
    since_apple = 0

    while moves < MAX_MOVES and since_apple < STUCK_LIMIT:
        if max_apples is not None and score >= max_apples:
            break
        direction, explored_tiles, _ = ai(snake.body, food.position, COLS, ROWS, terrain)
        explored += len(explored_tiles)
        if direction is None:   # no safe move
            break
        snake.change_direction(direction)
        snake.move()
        moves += 1
        since_apple += 1

        if snake.check_collision(rocks):
            break
        head_x, head_y = snake.body[0]
        time_used += terrain[head_y][head_x]

        if snake.body[0] == food.position:
            score += 1
            since_apple = 0
            snake.grow = True
            food = Food(snake.body, rng, rocks)
            if food.position is None:  # board full
                break

    return score, moves, explored, time_used


def run(ai_name, seeds, terrain, max_apples=None):
    """Play one game per seed and return the averages."""
    results = [play_game(ALGORITHMS[ai_name], s, terrain, max_apples) for s in seeds]
    n = len(results)
    apples = sum(r[0] for r in results)
    moves = sum(r[1] for r in results)
    explored = sum(r[2] for r in results)
    time_used = sum(r[3] for r in results)
    return {
        "apples": apples / n,
        "max_apples": max(r[0] for r in results),
        "moves": moves / n,
        "time": time_used / n,
        "time_per_apple": time_used / max(apples, 1),
        "moves_per_apple": moves / max(apples, 1),
        "explored_per_move": explored / max(moves, 1),
    }


def main():
    # ---------- Part 1: Greedy, BFS, DFS on the flat board ----------
    print(f"PART 1: flat board {COLS}x{ROWS}, {len(FLAT_SEEDS)} games per AI, play until death\n")
    print(f"{'AI':<10}{'Apples':>8}{'Max':>6}{'Moves':>9}{'Moves/apple':>13}{'Explored/move':>15}")
    for name in FLAT_AIS:
        r = run(name, FLAT_SEEDS, flat_map())
        print(f"{name:<10}{r['apples']:>8.1f}{r['max_apples']:>6}{r['moves']:>9.1f}"
              f"{r['moves_per_apple']:>13.1f}{r['explored_per_move']:>15.1f}")

    # ---------- Part 2: BFS, Dijkstra, A* on the terrain maps ----------
    here = os.path.dirname(os.path.abspath(__file__))
    maps = sorted(glob.glob(os.path.join(here, "maps", "*.txt")))
    print(f"\n\nPART 2: terrain maps, {len(TERRAIN_SEEDS)} games per AI, "
          f"stop at {APPLE_GOAL} apples (or death)\n")
    print(f"{'Map':<18}{'AI':<10}{'Apples':>8}{'Time':>9}{'Time/apple':>12}"
          f"{'Moves':>9}{'Explored/move':>15}")
    for map_path in maps:
        map_name = os.path.splitext(os.path.basename(map_path))[0]
        terrain = load_map(map_path)
        for name in TERRAIN_AIS:
            r = run(name, TERRAIN_SEEDS, terrain, APPLE_GOAL)
            print(f"{map_name:<18}{name:<10}{r['apples']:>8.1f}{r['time']:>9.1f}"
                  f"{r['time_per_apple']:>12.2f}{r['moves']:>9.1f}{r['explored_per_move']:>15.1f}")
        print()


if __name__ == "__main__":
    main()
