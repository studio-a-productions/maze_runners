import pygame
import numpy as np
import random
import math
import noise  # For Perlin noise
import pygame.gfxdraw  # For anti-aliased filled polygon drawing (used for )
from collections import deque

#import pyi_splash  # pyi_splash is used with auto-py2exe to close the splash screen (disabled for testing)


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SIDEBAR_WIDTH = int(WINDOW_WIDTH * 0.25) 
GAME_AREA_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH

ANIM_DURATION = 200  # in ms

# Maze Size Constants (all must be odd)
SMALL_MAZE_SIZE = 21  
MEDIUM_MAZE_SIZE = 41  
BOSS_MAZE_SIZE = 61 # boss maze when score is a nonzero multiple of 5

# --- COLORS ---
# Object_Colors
COLOR_WALL   = (128, 128, 128)
COLOR_BG     = (0, 0, 0)
COLOR_PLAYER = (0, 255, 0)
COLOR_TRAP   = (255, 0, 0)
COLOR_HEAL   = (0, 0, 255)
SIDEBAR_BG   = (30, 30, 30)

# PopupText_Colors
ORANGE = (255, 165, 0)          # normal trap damage
GOLD   = (255, 215, 0)          # critical damage popup
HEAL_TEXT_COLOR = (0, 0, 255)   # healing
PROJECTILE_COLOR = (255, 0, 0)  # red (same as trap)
YELLOW = (255, 255, 0)          # Divine Eyes orb
LIGHT_GRAY = (200, 200, 200)    # divine path

# --- Gameplay ---
PLAYER_START_HEALTH = 100
TRAP_DAMAGE = 20
HEAL_PROBABILITY = 0.01         # chance a free cell becomes a healing station

TRAP_PROBABILITY_NORMAL = 0.02
TRAP_PROBABILITY_MEDIUM = 0.035
TRAP_PROBABILITY_BOSS = 0.05

# only for TRAP, not for PROJECTILE
NORMAL_CRIT_CHANCE = 0.10
BOSS_CRIT_CHANCE   = 0.25
                                # units
PROJECTILE_COOLDOWN = 5000      # ms
PROJECTILE_SPEED_FACTOR = 1.5   # cells per second (cells/s)

DIVINE_EYES_SPAWN_CHANCE = 0.001
MAX_DIVINE_EYES = 2

# FOG the FROG (perlin noise)
FOG_RADIUS_CELLS = 6                # Fog radius in number of cells
FOG_NOISE_AMPLITUDE_FACTOR = 0.1    # Noise amplitude as fraction of fog radius (in world units)
FOG_NOISE_SCALE = 1.5
FOG_SPEED = 0.3                     # noise offset speed
FOG_OPACITY = 255                   # Maximum fog opacity (0-255) (counts as an RGBA value)
FOG_FADE_WIDTH = 0.5
FOG_FADE_STEPS = 3                  # Number of concentric fade steps (only works with lower fog opacity)

# Functions (helper functions)
# These functions are made to be used in the future (for modding or adding new features)

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def world_to_screen(x, y, cam_offset, zoom):
    """Convert world coordinates to screen coordinates using camera offset and zoom."""
    return int((x - cam_offset[0]) * zoom), int((y - cam_offset[1]) * zoom)

def find_path(maze, start, goal):
    """Simple BFS pathfinding from start to goal in the maze.
       Returns a list of grid positions (row, col) from start to goal."""
    queue = deque([start])
    came_from = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        r, c = current
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            neighbor = (nr, nc)
            if 0 <= nr < maze.shape[0] and 0 <= nc < maze.shape[1] and maze[nr, nc] == 0:
                if neighbor not in came_from:
                    queue.append(neighbor)
                    came_from[neighbor] = current
    if goal not in came_from:
        return []
    # Reconstruct path
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

def interpolate_path(path, progress, cell_size):
    """Given a list of grid cells (path) and a progress value (0-1),
       returns a world coordinate (x,y) interpolated along the path."""
    if not path:
        return None
    # Convert grid positions to world coordinates (center of cell)
    points = [(c * cell_size + cell_size/2, r * cell_size + cell_size/2) for (r, c) in path]
    total_dist = 0
    distances = []
    for i in range(len(points) - 1):
        d = math.hypot(points[i+1][0]-points[i][0], points[i+1][1]-points[i][1])
        distances.append(d)
        total_dist += d
    target = total_dist * progress
    acc = 0
    for i, d in enumerate(distances):
        if acc + d >= target:
            seg_progress = (target - acc) / d
            x = points[i][0] + (points[i+1][0]-points[i][0]) * seg_progress
            y = points[i][1] + (points[i+1][1]-points[i][1]) * seg_progress
            return (x, y)
        acc += d
    return points[-1]

# Maze + generation

def generate_maze(w, h):
    maze = np.ones((h, w), dtype=np.int8)
    start = (1, 1)
    maze[start] = 0
    stack = [start]
    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < h and 0 < nc < w and maze[nr, nc] == 1:
                neighbors.append((nr, nc))
        if neighbors:
            chosen = random.choice(neighbors)
            nr, nc = chosen
            maze[r + (nr - r)//2, c + (nc - c)//2] = 0
            maze[chosen] = 0
            stack.append(chosen)
        else:
            stack.pop()
    return maze

def add_entrance_exit(maze):
    h, w = maze.shape
    possible_cols = [col for col in range(1, w, 2)]
    top_candidates = [col for col in possible_cols if maze[1, col] == 0]
    if not top_candidates:
        top_candidates = possible_cols
    exit_col = random.choice(top_candidates)
    bottom_candidates = [col for col in possible_cols if maze[h-2, col] == 0]
    if not bottom_candidates:
        bottom_candidates = possible_cols
    entrance_col = random.choice(bottom_candidates)
    maze[0, exit_col] = 0
    maze[h-1, entrance_col] = 0
    return (h-1, entrance_col), (0, exit_col)

def generate_items(maze, entrance, exit_cell, trap_prob, heal_prob):
    traps = []
    healing_stations = []
    h, w = maze.shape
    for r in range(h):
        for c in range(w):
            if maze[r, c] == 0 and (r, c) not in (entrance, exit_cell):
                roll = random.random()
                if roll < trap_prob:
                    traps.append((r, c))
                elif roll < trap_prob + heal_prob:
                    healing_stations.append((r, c))
    return traps, healing_stations

def generate_projectile_traps(maze, proj_chance):
    proj_traps = []
    h, w = maze.shape
    for r in range(1, h-1):
        for c in range(1, w-1):
            if maze[r, c] == 1:
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and maze[nr, nc] == 0:
                        nr2, nc2 = r+2*dr, c+2*dc
                        if 0 <= nr2 < h and 0 <= nc2 < w and maze[nr2, nc2] == 0:
                            if random.random() < proj_chance:
                                proj_traps.append({
                                    "pos": (r, c),
                                    "dir": (dr, dc),
                                    "last_shot": 0,
                                    "cooldown": PROJECTILE_COOLDOWN
                                })
                            break
    return proj_traps

def get_map_settings(score):
    if score > 0 and score % 5 == 0:
        size = BOSS_MAZE_SIZE
        trap_prob = TRAP_PROBABILITY_BOSS
        crit_chance = BOSS_CRIT_CHANCE
        boss = True
    elif score < 2:
        size = SMALL_MAZE_SIZE
        trap_prob = TRAP_PROBABILITY_NORMAL
        crit_chance = NORMAL_CRIT_CHANCE
        boss = False
    else:
        size = MEDIUM_MAZE_SIZE
        trap_prob = TRAP_PROBABILITY_MEDIUM
        crit_chance = NORMAL_CRIT_CHANCE
        boss = False
    proj_chance = (0.30 if boss else min(0.02 + 0.005 * score, 0.15))
    return size, size, trap_prob, crit_chance, proj_chance, boss

def is_visible(item_pos, player_pos, maze):
    pr, pc = player_pos
    ir, ic = item_pos
    if pr == ir:
        step = 1 if ic > pc else -1
        for c in range(pc+step, ic, step):
            if maze[pr, c] == 1:
                return False
        return True
    elif pc == ic:
        step = 1 if ir > pr else -1
        for r in range(pr+step, ir, step):
            if maze[r, pc] == 1:
                return False
        return True
    else:
        return False

def draw_maze(maze, screen, cell_size, exit_cell, cam_offset, zoom):
    h, w = maze.shape
    for r in range(h):
        for c in range(w):
            world_x = c * cell_size
            world_y = r * cell_size
            rect = pygame.Rect(*world_to_screen(world_x, world_y, cam_offset, zoom),
                               math.ceil(cell_size * zoom),
                               math.ceil(cell_size * zoom))
            if maze[r, c] == 1:
                pygame.draw.rect(screen, COLOR_WALL, rect)
            if (r, c) == exit_cell:
                pygame.draw.rect(screen, (255,255,255), rect, 2)

# --- Main Game Loop ---
# finally... right?
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Maze Runners v0.0.2") # type.version.patch (type: beta 0/indev -1/release 1+)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    current_zoom = 1.0
    target_zoom = 1.0
    min_zoom = 1.0
    max_zoom = 3.0
    zoom_speed = 0.5  # change per second
    zoom_interp_rate = 5.0

    score = 0
    player_health = PLAYER_START_HEALTH

    # Debug/Cheat flags
    show_all_traps = False
    no_collision = False
    fog_on = True  # Fog is on by default (applies in boss levels)

    divine_inventory = 0
    divine_state = None  # None, "animating", or "sustain"
    divine_path = []     # List of grid positions for the computed path
    divine_anim_progress = 0.0
    divine_anim_duration = 5000  # ms for the animation

    # create maze
    maze_w, maze_h, trap_prob, crit_chance, proj_chance, boss = get_map_settings(score)
    maze = generate_maze(maze_w, maze_h)
    entrance, exit_cell = add_entrance_exit(maze)
    traps, healing_stations = generate_items(maze, entrance, exit_cell, trap_prob, HEAL_PROBABILITY)
    projectile_traps = generate_projectile_traps(maze, proj_chance)
    divine_powerups = []
    if maze_w == MEDIUM_MAZE_SIZE:
        for r in range(maze_h):
            for c in range(maze_w):
                if maze[r, c] == 0 and (r, c) not in (entrance, exit_cell):
                    if random.random() < DIVINE_EYES_SPAWN_CHANCE:
                        divine_powerups.append((r, c))
    projectiles = []

    # Calculate cell size so maze fits within game area
    cell_size = min(GAME_AREA_WIDTH / maze_w, WINDOW_HEIGHT / maze_h)

    # Player pos, and world coords
    player_grid = list(entrance)
    player_pixel = [player_grid[1] * cell_size, player_grid[0] * cell_size]

    # animation state for movement
    is_animating = False
    anim_start_time = 0
    start_pixel = player_pixel[:]
    target_grid = player_grid[:]
    target_pixel = player_pixel[:]

    last_damaged_position = None
    popups = []  # list of dicts: {text, pos, start_time, duration, color}
    #pyi_splash.close()
    running = True
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Cheat keybinds:
                if event.key == pygame.K_t:
                    show_all_traps = not show_all_traps
                    print("Toggled showAllTraps:", show_all_traps)
                elif event.key == pygame.K_n:
                    no_collision = not no_collision
                    print("Toggled noCollision:", no_collision)
                elif event.key == pygame.K_h:
                    player_health += 50
                    popups.append({"text": "+50", "pos": (player_pixel[0], player_pixel[1]),
                                    "start_time": current_time, "duration": 1000, "color": HEAL_TEXT_COLOR})
                    print("Added 50 health. New Health:", player_health)
                elif event.key == pygame.K_l:
                    # Complete level cheat: reinitialize level and clear projectiles. (against bugs that happened when using the cheat during testing -> player coords not matching rendering and particles staying)
                    score += 1
                    print("Cheat: Level complete! Score:", score)
                    maze_w, maze_h, trap_prob, crit_chance, proj_chance, boss = get_map_settings(score)
                    maze = generate_maze(maze_w, maze_h)
                    entrance, exit_cell = add_entrance_exit(maze)
                    traps, healing_stations = generate_items(maze, entrance, exit_cell, trap_prob, HEAL_PROBABILITY)
                    projectile_traps = generate_projectile_traps(maze, proj_chance)
                    divine_powerups = []
                    if maze_w == MEDIUM_MAZE_SIZE:
                        for r in range(maze_h):
                            for c in range(maze_w):
                                if maze[r, c] == 0 and (r, c) not in (entrance, exit_cell):
                                    if random.random() < DIVINE_EYES_SPAWN_CHANCE:
                                        divine_powerups.append((r, c))
                    projectiles = []
                    cell_size = min(GAME_AREA_WIDTH / maze_w, WINDOW_HEIGHT / maze_h)
                    player_grid = list(entrance)
                    player_pixel = [player_grid[1] * cell_size, player_grid[0] * cell_size]
                    last_damaged_position = None
                    divine_state = None
                elif event.key == pygame.K_e:
                    print("Cheat: End Game")
                    running = False
                elif event.key == pygame.K_f:
                    fog_on = not fog_on
                    print("Toggled Fog:", fog_on)
                elif event.key == pygame.K_o:
                    if divine_inventory < MAX_DIVINE_EYES:
                        divine_inventory += 1
                        popups.append({"text": "Divine Eyes +1", "pos": (player_pixel[0], player_pixel[1]),
                                       "start_time": current_time, "duration": 1000, "color": YELLOW})
                        print("Cheat: Spawned Divine Eyes. Inventory:", divine_inventory)
                elif event.key == pygame.K_p:
                    if divine_state is None and divine_inventory > 0:
                        path = find_path(maze, tuple(player_grid), exit_cell)
                        if path:
                            divine_inventory -= 1
                            divine_state = "animating"
                            divine_anim_progress = 0.0
                            divine_path = path
                            popups.append({"text": "Divine Eyes opened", "pos": (player_pixel[0], player_pixel[1]),
                                           "start_time": current_time, "duration": 1000, "color": YELLOW})
                            print("Activated Divine Eyes. Inventory left:", divine_inventory)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_z]:
            target_zoom = min(target_zoom + zoom_speed * dt / 1000.0, max_zoom)
        if keys[pygame.K_x]:
            target_zoom = max(target_zoom - zoom_speed * dt / 1000.0, min_zoom)
        current_zoom += (target_zoom - current_zoom) * zoom_interp_rate * (dt / 1000.0)

        if not is_animating:
            new_grid = player_grid.copy()
            if keys[pygame.K_UP]:
                new_grid[0] -= 1
            elif keys[pygame.K_DOWN]:
                new_grid[0] += 1
            elif keys[pygame.K_LEFT]:
                new_grid[1] -= 1
            elif keys[pygame.K_RIGHT]:
                new_grid[1] += 1
            if new_grid != player_grid:
                if no_collision or (0 <= new_grid[0] < maze_h and 0 <= new_grid[1] < maze_w and maze[new_grid[0], new_grid[1]] == 0):
                    is_animating = True
                    anim_start_time = current_time
                    start_pixel = player_pixel[:]
                    target_grid = new_grid
                    target_pixel = [target_grid[1]*cell_size, target_grid[0]*cell_size]
        if is_animating:
            t = (current_time - anim_start_time) / ANIM_DURATION
            if t >= 1:
                t = 1
                is_animating = False
                player_grid = target_grid[:]
            player_pixel[0] = start_pixel[0] + (target_pixel[0]-start_pixel[0])*t
            player_pixel[1] = start_pixel[1] + (target_pixel[1]-start_pixel[1])*t

        # collision checks
        if not is_animating and not no_collision:
            if tuple(player_grid) in traps:
                if last_damaged_position != tuple(player_grid):
                    if random.random() < crit_chance:
                        extra = int(0.25 * player_health)
                        damage = TRAP_DAMAGE + extra
                        popup_text = f"CRIT! -{damage}"
                        popup_color = GOLD
                    else:
                        damage = TRAP_DAMAGE
                        popup_text = f"-{damage}"
                        popup_color = ORANGE
                    player_health -= damage
                    popups.append({"text": popup_text, "pos": (player_pixel[0], player_pixel[1]),
                                   "start_time": current_time, "duration": 1000, "color": popup_color})
                    print("Trap triggered! Damage:", damage, "Health:", player_health)
                    last_damaged_position = tuple(player_grid)
            else:
                last_damaged_position = None
            if tuple(player_grid) in healing_stations:
                old_health = player_health
                player_health = int(player_health + player_health * 0.5)
                heal_amt = player_health - old_health
                popups.append({"text": f"+{heal_amt}", "pos": (player_pixel[0], player_pixel[1]),
                               "start_time": current_time, "duration": 1000, "color": HEAL_TEXT_COLOR})
                print(f"Healed from {old_health} to {player_health}")
                healing_stations.remove(tuple(player_grid))
            # -- experimental (ik it could be optimized, leave me alone mom)
            if tuple(player_grid) in divine_powerups:
                if divine_inventory < MAX_DIVINE_EYES:
                    divine_inventory += 1
                    popups.append({"text": "Divine Eyes +1", "pos": (player_pixel[0], player_pixel[1]),
                                   "start_time": current_time, "duration": 1000, "color": YELLOW})
                    print("Collected Divine Eyes. Inventory:", divine_inventory)
                divine_powerups.remove(tuple(player_grid))

        # exit check
        if not is_animating and tuple(player_grid) == exit_cell:
            score += 1
            print("Level complete! Score:", score)
            maze_w, maze_h, trap_prob, crit_chance, proj_chance, boss = get_map_settings(score)
            maze = generate_maze(maze_w, maze_h)
            entrance, exit_cell = add_entrance_exit(maze)
            traps, healing_stations = generate_items(maze, entrance, exit_cell, trap_prob, HEAL_PROBABILITY)
            projectile_traps = generate_projectile_traps(maze, proj_chance)
            divine_powerups = []
            if maze_w == MEDIUM_MAZE_SIZE:
                for r in range(maze_h):
                    for c in range(maze_w):
                        if maze[r, c] == 0 and (r, c) not in (entrance, exit_cell):
                            if random.random() < DIVINE_EYES_SPAWN_CHANCE:
                                divine_powerups.append((r, c))
                                print("devinde_powerup spawned")
            projectiles = []
            cell_size = min(GAME_AREA_WIDTH / maze_w, WINDOW_HEIGHT / maze_h)
            player_grid = list(entrance)
            player_pixel = [player_grid[1]*cell_size, player_grid[0]*cell_size]
            last_damaged_position = None
            divine_state = None

        # Divine Eyes Powerup Logic
        # If activated, animate the flying orb or "sustain" the effect
        if divine_state == "animating":
            divine_anim_progress += dt / divine_anim_duration
            if divine_anim_progress >= 1.0:
                divine_anim_progress = 1.0
                divine_state = "sustain"
            # Orb position along the precomputed path
            divine_orb_pos = interpolate_path(divine_path, divine_anim_progress, cell_size)
        elif divine_state == "sustain":
            # Continuously update the path from player's grid to exit.
            new_path = find_path(maze, tuple(player_grid), exit_cell)
            if new_path:
                divine_path = new_path
            # The sustained effect simply draws the path for now... :(
        
        # projectile trap logic
        for pt in projectile_traps:
            if current_time - pt["last_shot"] >= pt["cooldown"]:
                r, c = pt["pos"]
                center_x = c * cell_size + cell_size/2
                center_y = r * cell_size + cell_size/2
                dr, dc = pt["dir"]
                proj_start_x = center_x + dc * (cell_size/2)
                proj_start_y = center_y + dr * (cell_size/2)
                projectiles.append({"pos": [proj_start_x, proj_start_y],
                                    "dir": (dr, dc), "active": False})
                pt["last_shot"] = current_time
        for proj in projectiles[:]:
            projectile_speed = (cell_size * PROJECTILE_SPEED_FACTOR) / 1000
            proj["pos"][0] += proj["dir"][1] * projectile_speed * dt
            proj["pos"][1] += proj["dir"][0] * projectile_speed * dt
            proj_grid_x = int(proj["pos"][0] / cell_size)
            proj_grid_y = int(proj["pos"][1] / cell_size)
            if proj_grid_x < 0 or proj_grid_x >= maze_w or proj_grid_y < 0 or proj_grid_y >= maze_h:
                projectiles.remove(proj)
                continue
            if not proj["active"] and maze[proj_grid_y, proj_grid_x] == 0:
                proj["active"] = True
            if proj["active"] and maze[proj_grid_y, proj_grid_x] == 1:
                projectiles.remove(proj)
                continue
            if proj["active"]:
                proj_rect = pygame.Rect(int(proj["pos"][0] - cell_size*0.1),
                                        int(proj["pos"][1] - cell_size*0.1),
                                        math.ceil(cell_size*0.2),
                                        math.ceil(cell_size*0.2))
                player_rect = pygame.Rect(int(player_pixel[0]), int(player_pixel[1]),
                                          math.ceil(cell_size), math.ceil(cell_size))
                if player_rect.colliderect(proj_rect):
                    player_health -= TRAP_DAMAGE
                    popups.append({"text": f"-{TRAP_DAMAGE}", "pos": (player_pixel[0], player_pixel[1]),
                                   "start_time": current_time, "duration": 1000, "color": ORANGE})
                    print("Projectile hit! Damage:", TRAP_DAMAGE, "Health:", player_health)
                    projectiles.remove(proj)
                    continue

        # popup handler (definitly optimized)
        for popup in popups[:]:
            if current_time - popup["start_time"] > popup["duration"]:
                popups.remove(popup)
            else:
                popup["pos"] = (popup["pos"][0], popup["pos"][1] - 0.05 * dt)

        # Cam calculations (aka: math)
        player_center = (player_pixel[0] + cell_size/2, player_pixel[1] + cell_size/2)
        maze_pixel_width = maze_w * cell_size
        maze_pixel_height = maze_h * cell_size
        half_view_width_world = GAME_AREA_WIDTH / (2*current_zoom)
        half_view_height_world = WINDOW_HEIGHT / (2*current_zoom)
        cam_center_x = clamp(player_center[0], half_view_width_world, maze_pixel_width - half_view_width_world)
        cam_center_y = clamp(player_center[1], half_view_height_world, maze_pixel_height - half_view_height_world)
        cam_offset = (cam_center_x - half_view_width_world, cam_center_y - half_view_height_world)

        # Finally drawing stuff
        screen.fill(COLOR_BG)
        draw_maze(maze, screen, cell_size, exit_cell, cam_offset, current_zoom)
        if divine_state == "sustain":
            # Recompute path continuously. (optimized, I know)
            current_path = find_path(maze, tuple(player_grid), exit_cell)
            if current_path:
                divine_path = current_path
                points = [(c*cell_size+cell_size/2, r*cell_size+cell_size/2) for (r,c) in divine_path]
                # Draw sustained path (line and orbs)
                if len(points) >= 2:
                    screen_points = [world_to_screen(x, y, cam_offset, current_zoom) for (x,y) in points]
                    pygame.draw.lines(screen, LIGHT_GRAY, False, screen_points, max(1, int(3*current_zoom)))
                for (x,y) in points:
                    center = world_to_screen(x, y, cam_offset, current_zoom)
                    pygame.draw.circle(screen, YELLOW, center, int(cell_size*0.1*current_zoom))
        for dp in divine_powerups:  # DRAW DIVINE EYES POWERUPS
            # Convert grid position to the center of the cell
            center_world = (dp[1]*cell_size + cell_size/2, dp[0]*cell_size + cell_size/2)
            center_screen = world_to_screen(center_world[0], center_world[1], cam_offset, current_zoom)
            radius = int(cell_size*0.3*current_zoom)
            pygame.draw.circle(screen, YELLOW, center_screen, radius)
        for hs in healing_stations:
            world_x = hs[1]*cell_size
            world_y = hs[0]*cell_size
            rect = pygame.Rect(*world_to_screen(world_x, world_y, cam_offset, current_zoom),
                               math.ceil(cell_size*current_zoom),
                               math.ceil(cell_size*current_zoom))
            pygame.draw.rect(screen, COLOR_HEAL, rect)
        for trap in traps:
            if show_all_traps or is_visible(trap, tuple(player_grid), maze):
                world_x = trap[1]*cell_size
                world_y = trap[0]*cell_size
                rect = pygame.Rect(*world_to_screen(world_x, world_y, cam_offset, current_zoom),
                                   math.ceil(cell_size*current_zoom),
                                   math.ceil(cell_size*current_zoom))
                pygame.draw.rect(screen, COLOR_TRAP, rect)
        for pt in projectile_traps:
            if show_all_traps or is_visible(pt["pos"], tuple(player_grid), maze):
                r, c = pt["pos"]
                center_world_x = c*cell_size + cell_size/2
                center_world_y = r*cell_size + cell_size/2
                center_screen = world_to_screen(center_world_x, center_world_y, cam_offset, current_zoom)
                radius = int(cell_size*0.3*current_zoom)
                pygame.draw.circle(screen, COLOR_TRAP, center_screen, radius)
        for proj in projectiles:
            proj_screen = world_to_screen(proj["pos"][0], proj["pos"][1], cam_offset, current_zoom)
            radius = int(cell_size*0.1*current_zoom)
            pygame.draw.circle(screen, PROJECTILE_COLOR, proj_screen, radius)
        player_rect = pygame.Rect(*world_to_screen(player_pixel[0], player_pixel[1], cam_offset, current_zoom),
                                  math.ceil(cell_size*current_zoom),
                                  math.ceil(cell_size*current_zoom))
        pygame.draw.rect(screen, COLOR_PLAYER, player_rect)
        for popup in popups:
            popup_screen = world_to_screen(popup["pos"][0], popup["pos"][1], cam_offset, current_zoom)
            popup_surf = font.render(popup["text"], True, popup["color"])
            screen.blit(popup_surf, popup_screen)


        # I know it should be an if, else if statement (with the if divine-state == "sustain"), but this is for render layers. (solution: create a layer-render method; just some more work, yey!)
        if divine_state == "animating":
            orb_pos = interpolate_path(divine_path, divine_anim_progress, cell_size)
            if orb_pos is not None:
                orb_screen = world_to_screen(orb_pos[0]-cell_size*0.05, orb_pos[1]-cell_size*0.05, cam_offset, current_zoom)
                pygame.draw.circle(screen, YELLOW, orb_screen, int(cell_size*0.15*current_zoom))

        # FOG EFFECT DRAWING
        if boss and fog_on:
            # In boss levels, with powerup, you can see a bit more, but never enough >:)
            fog_radius_world = (FOG_RADIUS_CELLS * cell_size * (1.5 if divine_state == "sustain" else 1))
            num_points = 60
            time_offset = current_time/1000.0
            player_center_world = (player_pixel[0]+cell_size/2, player_pixel[1]+cell_size/2)
            polygon_points_world = []
            for i in range(num_points):
                angle = 2*math.pi*i/num_points
                noise_val = noise.pnoise2(math.cos(angle)*FOG_NOISE_SCALE + time_offset*FOG_SPEED,
                                           math.sin(angle)*FOG_NOISE_SCALE + time_offset*FOG_SPEED)
                noise_offset = noise_val * (FOG_NOISE_AMPLITUDE_FACTOR * fog_radius_world)
                r_val = fog_radius_world + noise_offset
                x = player_center_world[0] + r_val * math.cos(angle)
                y = player_center_world[1] + r_val * math.sin(angle)
                polygon_points_world.append((x,y))
            fog_surface = pygame.Surface((GAME_AREA_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            fog_surface.fill((0,0,0, FOG_OPACITY))
            for step in range(FOG_FADE_STEPS):
                fraction = (step+1)/FOG_FADE_STEPS
                inset = 1 - fraction * FOG_FADE_WIDTH
                clear_poly_world = []
                for (x,y) in polygon_points_world:
                    clear_poly_world.append((player_center_world[0] + (x-player_center_world[0])*inset,
                                               player_center_world[1] + (y-player_center_world[1])*inset))
                clear_poly_screen = [world_to_screen(x, y, cam_offset, current_zoom) for (x,y) in clear_poly_world]
                subtract_alpha = int((1-fraction)*FOG_OPACITY)
                temp_surface = pygame.Surface((GAME_AREA_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                temp_surface.fill((0,0,0,0))
                pygame.gfxdraw.filled_polygon(temp_surface, clear_poly_screen, (0,0,0, subtract_alpha))
                fog_surface.blit(temp_surface, (0,0), special_flags=pygame.BLEND_RGBA_SUB)
            screen.blit(fog_surface, (0,0))

        # My fav thing: SIDEBARS!!!!!
        sidebar_rect = pygame.Rect(GAME_AREA_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, SIDEBAR_BG, sidebar_rect)
        hud_texts = [
            "DEBUG INFO",
            f"Score: {score}",
            f"Health: {player_health}",
            f"Map: {maze_w}x{maze_h} {'(boss)' if boss else ''}",
            f"Zoom: {round(int(current_zoom*100)/100,1)}",
            f"Divine Eyes: {divine_inventory}/{MAX_DIVINE_EYES}",
            "",
            f"divineEyesActive: {divine_state if divine_state else 'OFF'}",
            f"showAllTraps: {'ON' if show_all_traps else 'OFF'}",
            f"noCollision: {'ON' if no_collision else 'OFF'}",
            f"maze_bossFog: {'ON' if fog_on else 'OFF'}",
            "",
            "Powerups:",
            "P: Activate Divine Eyes",
            "",
            "Zoom:",
            "Z: Zoom In",
            "X: Zoom Out",
            "",
            "Cheat Codes:",
            "T: Toggle Traps",
            "N: Toggle No Coll",
            "H: +50 Health",
            "L: Complete Level",
            "E: End Game",
            "F: Toggle Fog",
            "O: Spawn Divine Eyes",
            "",

        ]
        for i, line in enumerate(hud_texts):
            text_surf = font.render(line, True, (255,255,255))
            screen.blit(text_surf, (GAME_AREA_WIDTH+10, 10+i*20))

        pygame.display.flip()
        if player_health <= 0:
            print("Game Over! Final Score:", score)
            running = False

    pygame.quit()

if __name__ == "__main__":
    # and now finally, let's start the game!
    main()
