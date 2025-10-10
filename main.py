import asyncio
import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

# --- Window ---
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyndaquil vs Chikorita vs Totodile")

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (255, 220, 0)
GRAY = (150, 150, 150)
ORANGE = (255, 140, 0)
LEAF_GREEN = (0, 180, 0)
SKY_BLUE = (135, 206, 235)
DARK_GREEN = (20, 100, 20)
SUN_YELLOW = (255, 255, 150)
GRASS_GREEN = (60, 180, 75)
BLUE = (50, 100, 220)

TYPE_COLORS = {
    "fire": ORANGE,
    "leaf": LEAF_GREEN,
    "water": SKY_BLUE,
    "physical": GRAY,
}

# --- Fonts ---
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 64)
button_font = pygame.font.Font(None, 28)

PLAYER_KEYBINDS = [
    {"moves": [pygame.K_SPACE, pygame.K_t, pygame.K_y], "potion": pygame.K_p},
    {"moves": [pygame.K_RETURN, pygame.K_RSHIFT, pygame.K_RALT], "potion": pygame.K_RCTRL},
]

# --- Sounds ---
def load_sound(name):
    path = os.path.join(os.path.dirname(__file__), name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

fire_sound = load_sound("fire.wav")
leaf_sound = load_sound("leaf.wav")
water_sound = load_sound("water.wav")
tackle_sound = load_sound("tackle.wav")
victory_sound = load_sound("victory.wav")
potion_sound = load_sound("potion.wav")

# --- Load sprites ---
def load_sprite(path, size=(100,100)):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        # fallback colored rect
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((random.randint(50,200),random.randint(50,200),random.randint(50,200),255))
        return surf

# Pokémon data with stats, sprites, and attacks
pokemon_data = {
    "Cyndaquil": {
        "sprite": load_sprite("data/cyn.png"),
        "hp": 60,
        "max_hp": 60,
        "color": RED,
        "attacks": {
            "ember": {"name": "Ember", "type": "fire", "damage_range": (8, 18), "sound": fire_sound},
            "flamethrower": {"name": "Flamethrower", "type": "fire", "damage_range": (15, 23), "sound": fire_sound},
            "tackle": {"name": "Tackle", "type": "physical", "damage_range": (5, 12), "sound": tackle_sound}
        },
        "button_order": ["ember", "flamethrower", "tackle"]
    },
    "Chikorita": {
        "sprite": load_sprite("data/chi.png"),
        "hp": 60,
        "max_hp": 60,
        "color": GREEN,
        "attacks": {
            "razor_leaf": {"name": "Razor Leaf", "type": "leaf", "damage_range": (10, 20), "sound": leaf_sound},
            "vine_whip": {"name": "Vine Whip", "type": "leaf", "damage_range": (15, 23), "sound": leaf_sound},
            "tackle": {"name": "Tackle", "type": "physical", "damage_range": (5, 12), "sound": tackle_sound}
        },
        "button_order": ["razor_leaf", "vine_whip", "tackle"]
    },
    "Totodile": {
        "sprite": load_sprite("data/toto.png"),
        "hp": 70,
        "max_hp": 70,
        "color": BLUE,
        "attacks": {
            "water_gun": {"name": "Water Gun", "type": "water", "damage_range": (8, 18), "sound": water_sound},
            "aqua_tail": {"name": "Aqua Tail", "type": "water", "damage_range": (15, 23), "sound": water_sound},
            "tackle": {"name": "Tackle", "type": "physical", "damage_range": (5, 12), "sound": tackle_sound}
        },
        "button_order": ["water_gun", "aqua_tail", "tackle"]
    }
}

# --- Positions ---
cyndaquil_base = [200, 250]
chikorita_base = [600, 150]
totodile_base = [600, 250]

# Base positions for each pokemon (for convenience)
pokemon_positions = {
    "Cyndaquil": cyndaquil_base,
    "Chikorita": chikorita_base,
    "Totodile": totodile_base,
}

# --- Button Class for Touch Input ---
class Button:
    def __init__(self, x, y, w, h, text, color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False
    
    def draw(self, surface, font_obj=font):
        # Draw button with border
        color = tuple(min(c + 30, 255) for c in self.color) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 3)
        # Draw text centered
        text_surface = font_obj.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def update_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)

# --- Game variables ---
mode_select = True   # True when selecting mode (1P or 2P)
mode_options = ["1 Player (vs AI)", "2 Player (Local)"]
mode_selected = 0

pokemon_select = False
# Each player selects one from the three pokemon
player_choices = [0, 0]  # indices into list below
player_choice_names = list(pokemon_data.keys())
player_selecting = 0     # 0 or 1 indicating which player selecting
battle_start = False

# --- UI Buttons ---
mode_buttons = []
pokemon_selection_rects = []
battle_buttons_p1 = []
battle_buttons_p2 = []
restart_button = None

player_move_keys = [[None, None, None], [None, None, None]]

def create_mode_buttons():
    global mode_buttons
    mode_buttons = []
    for i, option in enumerate(mode_options):
        btn = Button(WIDTH // 2 - 150, 150 + i * 70, 300, 50, option, GRAY, BLACK)
        mode_buttons.append(btn)

def create_battle_buttons():
    global battle_buttons_p1, battle_buttons_p2, player_move_keys
    # Player 1 buttons on the left
    battle_buttons_p1 = [
        Button(20, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(190, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(360, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(530, HEIGHT - 80, 120, 44, "Potion", GREEN, WHITE),
    ]
    player_move_keys[0] = [None, None, None]
    # Player 2 buttons on the right
    battle_buttons_p2 = [
        Button(WIDTH - 650, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(WIDTH - 480, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(WIDTH - 310, HEIGHT - 80, 160, 44, "Move", ORANGE, WHITE),
        Button(WIDTH - 140, HEIGHT - 80, 120, 44, "Potion", GREEN, WHITE),
    ]
    player_move_keys[1] = [None, None, None]

def create_restart_button():
    global restart_button
    restart_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Restart", RED, WHITE)


def choose_ai_pokemon(exclude_index=None):
    options = [i for i in range(len(player_choice_names)) if i != exclude_index]
    if not options:
        return 0
    return random.choice(options)


def configure_move_buttons():
    for idx in (0, 1):
        player = players[idx]
        if not player:
            continue

        buttons = battle_buttons_p1 if idx == 0 else battle_buttons_p2
        if len(buttons) < 4:
            continue

        move_order = player.get("button_order") or list(player["attacks"].keys())
        assigned_keys = []

        for btn_index in range(3):
            btn = buttons[btn_index]

            move_key = move_order[btn_index] if btn_index < len(move_order) else None
            if move_key not in player["attacks"]:
                move_key = None

            if move_key is None:
                remaining_moves = [k for k in player["attacks"] if k not in assigned_keys]
                move_key = remaining_moves[0] if remaining_moves else None

            if move_key and move_key in player["attacks"]:
                move_info = player["attacks"][move_key]
                btn.text = move_info["name"]
                btn.color = TYPE_COLORS.get(move_info["type"], ORANGE)
                btn.text_color = WHITE if sum(btn.color) < 510 else BLACK
                assigned_keys.append(move_key)
            else:
                btn.text = "Move"
                btn.color = GRAY
                btn.text_color = BLACK
                assigned_keys.append(None)

        player_move_keys[idx] = assigned_keys

        potion_button = buttons[3]
        potion_button.text = "Potion"
        potion_button.color = GREEN
        potion_button.text_color = BLACK

# Initialize buttons
create_mode_buttons()
create_battle_buttons()

# Battle variables (filled when battle starts)
players = [{}, {}]
turn = 0   # 0 for player1, 1 for player2 or AI
game_over = False
winner = None

# Animations & UI
attack_message = ""
message_timer = 0
damage_popup = None
animation_timer = 0
attacking = False
action_lockout = 0  # Timer to prevent actions during animations (in frames)

# Potion usage: 3 each
potion_counts = [3,3]

# Positions in battle for chosen pokemon
battle_positions = [[200, 250], [600, 150]]

# Particles and projectiles
particles = []
projectiles = []

# --- PARTICLES & PROJECTILES ---

def spawn_particles(p_type, target_pos):
    for _ in range(15):
        if p_type == "fire":
            color = random.choice([ORANGE, YELLOW, RED])
            radius = random.randint(3, 6)
            dx = random.uniform(-2, 2)
            dy = random.uniform(-3, -1)
        elif p_type == "leaf":
            color = LEAF_GREEN
            radius = random.randint(2, 5)
            dx = random.uniform(-2, 2)
            dy = random.uniform(-2, 0)
        elif p_type == "water":
            color = SKY_BLUE
            radius = random.randint(3, 5)
            dx = random.uniform(-2, 2)
            dy = random.uniform(-2, 0)
        else:
            color = GRAY
            radius = random.randint(2, 4)
            dx = random.uniform(-2, 2)
            dy = random.uniform(-1, 0)
        particles.append({"x": target_pos[0] + random.randint(-20, 20),
                          "y": target_pos[1] + random.randint(-10, 10),
                          "dx": dx, "dy": dy, "radius": radius, "color": color,
                          "life": random.randint(25, 45)})

def update_particles():
    for p in particles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

def draw_particles():
    for p in particles:
        pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), p["radius"])

def spawn_projectile(p_type, start_pos, target_pos, attacker_idx, attack_key):
    attacker = players[attacker_idx]
    attacker_name = attacker.get("name", "")
    start_vec = pygame.math.Vector2(start_pos[0], start_pos[1])
    target_vec = pygame.math.Vector2(target_pos[0], target_pos[1])

    if attack_key == "flamethrower":
        if attacker_name == "Cyndaquil":
            start_vec += pygame.math.Vector2(40, -30)
        direction = target_vec - start_vec
        length = direction.length()
        if length == 0:
            direction = pygame.math.Vector2(1, 0)
            length = 1
        else:
            direction = direction.normalize()
        projectiles.append({
            "type": "fire_stream",
            "start": start_vec,
            "target": target_vec,
            "direction": direction,
            "length": length,
            "progress": 0.0,
            "speed": 0.12,
            "attacker_idx": attacker_idx,
            "attack_key": attack_key,
            "noise": [random.uniform(0, math.pi * 2) for _ in range(12)],
            "linger": 0,
            "max_linger": 12,
        })
        return

    if attack_key == "vine_whip":
        if attacker_name == "Chikorita":
            sprite = attacker.get("sprite")
            if sprite:
                start_vec += pygame.math.Vector2(-sprite.get_width() * 0.08, sprite.get_height() * 0.1)
            else:
                start_vec += pygame.math.Vector2(-24, 12)

        direction = target_vec - start_vec
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        else:
            direction = direction.normalize()

        segments = 40
        growth_portion = 0.4
        base_static_idx = int(growth_portion * (segments - 1))

        core_path = []
        sweep_path = []
        for i in range(segments):
            t = i / (segments - 1)
            if t < growth_portion:
                grow = t / max(growth_portion, 0.001)
                base_offset = direction * (grow * 40) + pygame.math.Vector2(0, -30 * grow)
                core_point = start_vec + base_offset

                tip_offset = direction * (grow * 130) + pygame.math.Vector2(0, -50 * (1 - grow) + 10 * grow)
                sweep_point = start_vec + tip_offset
            else:
                sweep_t = (t - growth_portion) / max(1 - growth_portion, 0.001)
                sweep_t = min(max(sweep_t, 0.0), 1.0)
                vertical_start = target_vec.y - 140
                vertical_end = target_vec.y + 60
                y_pos = vertical_start + (vertical_end - vertical_start) * sweep_t
                sway = math.sin(sweep_t * math.pi) * 50
                sweep_point = pygame.math.Vector2(target_vec.x + sway, y_pos)
                core_point = start_vec + direction * 38 + pygame.math.Vector2(0, -28)

            core_path.append(core_point)
            sweep_path.append(sweep_point)

        for i in range(min(base_static_idx + 1, len(sweep_path))):
            sweep_path[i] = core_path[i]

        projectiles.append({
            "type": "vine_whip",
            "base_path": core_path,
            "tip_path": sweep_path,
            "progress": 0.0,
            "speed": 0.12,
            "attacker_idx": attacker_idx,
            "attack_key": attack_key,
            "impact_timer": 0,
            "base_static": base_static_idx,
        })
        return

    if attack_key == "aqua_tail":
        if attacker_name == "Totodile":
            start_vec += pygame.math.Vector2(-24, 18)
        direction = target_vec - start_vec
        length = direction.length()
        if length == 0:
            direction = pygame.math.Vector2(1, 0)
            length = 1
        else:
            direction = direction.normalize()
        axis = pygame.math.Vector2(direction.y, -direction.x)
        axis = axis.normalize() if axis.length() != 0 else pygame.math.Vector2(0, -1)
        sweep_radius = max(80, length * 0.65)
        sweep_center = start_vec + axis * sweep_radius * 0.4
        sweep_span = math.radians(150)
        sweep_dir = 1 if direction.x >= 0 else -1
        sweep_center = start_vec + axis * sweep_radius * 0.6
        sweep_dir = 1 if direction.x >= 0 else -1

        projectiles.append({
            "type": "aqua_tail",
            "start": start_vec,
            "target": target_vec,
            "center": sweep_center,
            "radius": sweep_radius,
            "progress": 0.0,
            "speed": 0.24,
            "attacker_idx": attacker_idx,
            "attack_key": attack_key,
            "phase": random.uniform(0, math.pi * 2),
            "linger": 0,
            "max_linger": 14,
            "sweep_dir": sweep_dir,
            "sweep_span": sweep_span,
            "base_direction": direction,
        })
        return

    if p_type == "fire":
        dx = (target_pos[0] - start_pos[0]) / 30
        dy = (target_pos[1] - start_pos[1]) / 30
        color = ORANGE
        projectiles.append({"x": start_pos[0], "y": start_pos[1], "dx": dx, "dy": dy,
                            "radius": 8, "color": color, "target": target_pos, "type": "fire",
                            "attacker_idx": attacker_idx, "attack_key": attack_key})
    elif p_type == "leaf":
        projectiles.append({"x": start_pos[0], "y": start_pos[1],
                            "center": target_pos, "angle": 0, "radius": 8, "color": LEAF_GREEN,
                            "distance": 0, "type": "leaf_boomerang", "start": start_pos,
                            "attacker_idx": attacker_idx, "attack_key": attack_key})
    elif p_type == "water":
        dx = (target_pos[0] - start_pos[0]) / 30
        dy = (target_pos[1] - start_pos[1]) / 30
        color = SKY_BLUE
        projectiles.append({"x": start_pos[0], "y": start_pos[1], "dx": dx, "dy": dy,
                            "radius": 8, "color": color, "target": target_pos, "type": "water",
                            "attacker_idx": attacker_idx, "attack_key": attack_key})
    elif p_type == "physical":
        # Tackle: instant hit with red circle effect
        projectiles.append({"x": target_pos[0], "y": target_pos[1],
                            "radius": 50, "color": RED, "target": target_pos, "type": "physical",
                            "attacker_idx": attacker_idx, "timer": 20, "attack_key": attack_key})

def update_projectiles():
    global game_over, winner, damage_popup
    for p in projectiles[:]:
        if p.get("attack_key") and p["attack_key"] not in players[p["attacker_idx"]]["attacks"]:
            projectiles.remove(p)
            continue
        if p["type"] == "fire":
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if abs(p["x"] - p["target"][0]) < 10 and abs(p["y"] - p["target"][1]) < 10:
                # Damage the defender (opposite of attacker)
                attacker_idx = p["attacker_idx"]
                target_index = 1 - attacker_idx
                attack_key = p.get("attack_key")
                damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[attacker_idx]["name"]
                    play_sound(victory_sound)
                spawn_particles("fire", p["target"])
                damage_popup = (f"-{damage}", p["target"][0], p["target"][1] - 50, 60)
                projectiles.remove(p)

        elif p["type"] == "fire_stream":
            p["progress"] = min(1.0, p["progress"] + p["speed"])
            if p["progress"] >= 1.0:
                if p["linger"] == 0:
                    attacker_idx = p["attacker_idx"]
                    target_index = 1 - attacker_idx
                    attack_key = p.get("attack_key")
                    damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                    players[target_index]["hp"] -= damage
                    if players[target_index]["hp"] <= 0:
                        players[target_index]["hp"] = 0
                        game_over = True
                        winner = players[attacker_idx]["name"]
                        play_sound(victory_sound)
                    spawn_particles("fire", p["target"])
                    damage_popup = (f"-{damage}", p["target"].x, p["target"].y - 50, 60)
                p["linger"] += 1
                if p["linger"] >= p["max_linger"]:
                    projectiles.remove(p)

        elif p["type"] == "vine_whip":
            total_length = len(p["tip_path"]) - 1
            p["progress"] = min(1.0, p["progress"] + p["speed"])
            if p["progress"] >= 1.0:
                if p["impact_timer"] == 0:
                    attacker_idx = p["attacker_idx"]
                    target_index = 1 - attacker_idx
                    attack_key = p.get("attack_key")
                    damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                    players[target_index]["hp"] -= damage
                    if players[target_index]["hp"] <= 0:
                        players[target_index]["hp"] = 0
                        game_over = True
                        winner = players[attacker_idx]["name"]
                        play_sound(victory_sound)
                    spawn_particles("leaf", p["tip_path"][-1])
                    damage_popup = (f"-{damage}", p["tip_path"][-1].x, p["tip_path"][-1].y - 50, 60)
                p["impact_timer"] += 1
                if p["impact_timer"] > 8:
                    projectiles.remove(p)

        elif p["type"] == "aqua_tail":
            p["progress"] = min(1.0, p["progress"] + p["speed"])
            if p["progress"] >= 1.0:
                if p["linger"] == 0:
                    attacker_idx = p["attacker_idx"]
                    target_index = 1 - attacker_idx
                    attack_key = p.get("attack_key")
                    damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                    players[target_index]["hp"] -= damage
                    if players[target_index]["hp"] <= 0:
                        players[target_index]["hp"] = 0
                        game_over = True
                        winner = players[attacker_idx]["name"]
                        play_sound(victory_sound)
                    spawn_particles("water", p["target"])
                    damage_popup = (f"-{damage}", p["target"].x, p["target"].y - 50, 60)
                p["linger"] += 1
                if p["linger"] >= p["max_linger"]:
                    projectiles.remove(p)

        elif p["type"] == "leaf_boomerang":
            p["angle"] += 0.2
            p["distance"] += 1
            x = p["center"][0] + 100 * math.cos(p["angle"]) * math.sin(p["distance"] / 30)
            y = p["center"][1] + 100 * math.sin(p["angle"]) * math.sin(p["distance"] / 30)
            p["x"] = x
            p["y"] = y
            if p["distance"] > 60:
                attacker_idx = p["attacker_idx"]
                target_index = 1 - attacker_idx
                attack_key = p.get("attack_key")
                damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[attacker_idx]["name"]
                    play_sound(victory_sound)
                spawn_particles("leaf", battle_positions[target_index])
                damage_popup = (f"-{damage}", battle_positions[target_index][0], battle_positions[target_index][1] - 50, 60)
                projectiles.remove(p)

        elif p["type"] == "water":
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if abs(p["x"] - p["target"][0]) < 10 and abs(p["y"] - p["target"][1]) < 10:
                attacker_idx = p["attacker_idx"]
                target_index = 1 - attacker_idx
                attack_key = p.get("attack_key")
                damage = random.randint(*players[attacker_idx]["attacks"][attack_key]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[attacker_idx]["name"]
                    play_sound(victory_sound)
                spawn_particles("water", p["target"])
                damage_popup = (f"-{damage}", p["target"][0], p["target"][1] - 50, 60)
                projectiles.remove(p)
        
        elif p["type"] == "physical":
            # Tackle: deal damage immediately on first frame, then show circle animation
            if "damage_dealt" not in p:
                attacker_idx = p["attacker_idx"]
                target_index = 1 - attacker_idx
                attack_key = p.get("attack_key")
                attack_data = players[attacker_idx]["attacks"].get(attack_key) if attack_key else None
                if attack_data and "damage_range" in attack_data:
                    damage = random.randint(*attack_data["damage_range"])
                else:
                    damage = 12
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[attacker_idx]["name"]
                    play_sound(victory_sound)
                damage_popup = (f"-{damage}", p["target"][0], p["target"][1] - 50, 60)
                p["damage_dealt"] = True
            
            # Count down timer and remove when done
            p["timer"] -= 1
            if p["timer"] <= 0:
                projectiles.remove(p)

def draw_projectiles():
    for p in projectiles:
        if p["type"] == "fire_stream":
            progress = p["progress"]
            start = p["start"]
            direction = p["direction"]
            length = p["length"]
            step_count = 12
            for i in range(step_count):
                t = (i / (step_count - 1)) * progress
                eased_t = t * t
                point = start + direction * (length * eased_t)
                noise_phase = p["noise"][i]
                offset = pygame.math.Vector2(direction.y, -direction.x) * math.sin(noise_phase + progress * 3) * 10 * (1 - eased_t)
                radius = int(20 * (1 - eased_t) + 4)
                color = (255, int(140 + 60 * (1 - eased_t)), 50)
                pygame.draw.circle(screen, color, (int(point.x + offset.x), int(point.y + offset.y)), radius)

        elif p["type"] == "vine_whip":
            progress = p["progress"]
            base_path = p["base_path"]
            tip_path = p["tip_path"]
            reveal = int(progress * (len(tip_path) - 1))

            for i in range(1, reveal + 1):
                base_a = base_path[min(i - 1, len(base_path) - 1)]
                base_b = base_path[min(i, len(base_path) - 1)]
                tip_a = tip_path[i - 1]
                tip_b = tip_path[i]

                width_main = int(30 * (1 - i / len(tip_path)) + 6)
                pygame.draw.line(screen, (60, 180, 80), (int(base_a.x), int(base_a.y)), (int(base_b.x), int(base_b.y)), max(5, width_main))

                sweep_width = int(26 * (1 - i / len(tip_path)) + 4)
                pygame.draw.line(screen, (40, 200, 90), (int(tip_a.x), int(tip_a.y)), (int(tip_b.x), int(tip_b.y)), max(4, sweep_width))

            if reveal >= 0:
                tip = tip_path[min(reveal, len(tip_path) - 1)]
                pygame.draw.circle(screen, (90, 210, 90), (int(tip.x), int(tip.y)), 24)

        elif p["type"] == "aqua_tail":
            progress = p["progress"]
            start = p["start"]
            center = p["center"]
            radius = p["radius"]
            sweep_dir = p["sweep_dir"]
            sweep_span = p["sweep_span"]
            angle_start = math.atan2(start.y - center.y, start.x - center.x)
            angle_offset = sweep_span * (progress ** 1.1)
            current_angle = angle_start + angle_offset * sweep_dir
            tail_tip = pygame.math.Vector2(center.x + math.cos(current_angle) * radius,
                                          center.y + math.sin(current_angle) * radius)

            trail_points = []
            trail_steps = 18
            for i in range(trail_steps + 1):
                t = i / trail_steps
                eased = (progress ** 0.8) * t
                angle = angle_start + sweep_span * (eased ** 1.1) * sweep_dir
                point = pygame.math.Vector2(center.x + math.cos(angle) * radius,
                                            center.y + math.sin(angle) * radius)
                wave = math.sin(p["phase"] + eased * 5) * (35 * (1 - eased))
                offset_dir = pygame.math.Vector2(-math.sin(angle), math.cos(angle)) * wave
                trail_points.append(point + offset_dir)

            for i in range(1, len(trail_points)):
                a = trail_points[i - 1]
                b = trail_points[i]
                width = int(36 * (1 - i / len(trail_points)) + 10)
                pygame.draw.line(screen, (150, 210, 255), (int(a.x), int(a.y)), (int(b.x), int(b.y)), max(6, width))

            pygame.draw.circle(screen, (160, 220, 255), (int(tail_tip.x), int(tail_tip.y)), 26)
            splash = max(24, int(34 * (1 - abs(math.sin(progress * math.pi)))))
            pygame.draw.circle(screen, (190, 235, 255), (int(tail_tip.x), int(tail_tip.y)), splash, 5)

        else:
            pygame.draw.circle(screen, p["color"], (int(p.get("x", p.get("start", [0, 0])[0])), int(p.get("y", p.get("start", [0, 0])[1]))), p.get("radius", 8))

# --- Background ---
def draw_background():
    screen.fill(SKY_BLUE)
    sun_pos = (700, 80)
    pygame.draw.circle(screen, SUN_YELLOW, sun_pos, 50)
    ray_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(0, 360, 20):
        length = random.randint(150, 250)
        end_x = sun_pos[0] + int(length * pygame.math.Vector2(1, 0).rotate(i).x)
        end_y = sun_pos[1] + int(length * pygame.math.Vector2(1, 0).rotate(i).y)
        pygame.draw.line(ray_surface, (255, 255, 150, 30), sun_pos, (end_x, end_y), 4)
    screen.blit(ray_surface, (0, 0))
    draw_ground_perspective()


def draw_ground_perspective():
    far_ground_left = HEIGHT // 2 + 60
    far_ground_right = HEIGHT // 2 + 20
    pygame.draw.polygon(
        screen,
        GRASS_GREEN,
        [
            (0, far_ground_left),
            (WIDTH, far_ground_right),
            (WIDTH, HEIGHT),
            (0, HEIGHT),
        ],
    )

    shadow_color = tuple(max(c - 40, 0) for c in DARK_GREEN)
    pygame.draw.polygon(
        screen,
        shadow_color,
        [
            (0, far_ground_left),
            (WIDTH // 2 + 60, far_ground_right),
            (WIDTH // 2 - 140, HEIGHT),
            (0, HEIGHT),
        ],
    )

    highlight_color = tuple(min(c + 30, 255) for c in GRASS_GREEN)
    pygame.draw.polygon(
        screen,
        highlight_color,
        [
            (WIDTH // 2 + 60, far_ground_right),
            (WIDTH, far_ground_right - 20),
            (WIDTH, HEIGHT),
            (WIDTH // 2 - 80, HEIGHT),
        ],
    )

    for idx, pad_size in ((0, (320, 120)), (1, (220, 80))):
        pos = battle_positions[idx]
        player_info = players[idx]
        sprite = player_info.get("sprite") if player_info else None
        sprite_height = sprite.get_height() if sprite else 100

        pad_width, pad_height = pad_size
        pad_rect = pygame.Rect(0, 0, pad_width, pad_height)
        pad_top = pos[1] + sprite_height // 2 - 6
        pad_rect.center = (pos[0], int(pad_top + pad_height / 2))

        base_color = tuple(max(c - 20, 0) for c in GRASS_GREEN)
        inner_color = tuple(min(c + 25, 255) for c in GRASS_GREEN)

        pygame.draw.ellipse(screen, base_color, pad_rect)
        inner_rect = pad_rect.inflate(-int(pad_width * 0.3), -int(pad_height * 0.4))
        if inner_rect.width > 0 and inner_rect.height > 0:
            pygame.draw.ellipse(screen, inner_color, inner_rect)
        rim_rect = pad_rect.inflate(-4, -4)
        pygame.draw.ellipse(screen, DARK_GREEN, rim_rect, 3)

# --- Health bar ---
def draw_health_bar(x, y, hp, max_hp, color):
    bar_width, bar_height = 200, 20
    fill = max(0, (hp / max_hp) * bar_width)
    pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height), 2)
    pygame.draw.rect(screen, color, (x, y, fill, bar_height))

# --- Draw scene ---
def draw_scene():
    draw_background()

    # Draw Pokémon sprites with bobbing effect
    for i in (0, 1):
        p = players[i]
        pos = battle_positions[i]
        y_bob = pos[1] + 5 * math.sin(pygame.time.get_ticks() / 200)
        sprite = p["sprite"]
        screen.blit(sprite, (pos[0] - sprite.get_width() // 2, y_bob - sprite.get_height() // 2))

    # Draw health bars & names
    draw_health_bar(100, 150, players[0]["hp"], players[0]["max_hp"], players[0]["color"])
    screen.blit(font.render(f"{players[0]['name']}: {players[0]['hp']} HP", True, BLACK), (100, 120))

    draw_health_bar(500, 50, players[1]["hp"], players[1]["max_hp"], players[1]["color"])
    screen.blit(font.render(f"{players[1]['name']}: {players[1]['hp']} HP", True, BLACK), (500, 20))

    draw_particles()
    draw_projectiles()

    # Draw damage popup
    if damage_popup:
        text, x, y, timer = damage_popup
        screen.blit(font.render(text, True, YELLOW), (x, y))

    # Draw attack message or turn info
    if game_over:
        screen.blit(big_font.render(f"{winner} Wins!", True, BLACK), (WIDTH // 2 - 120, HEIGHT // 2 - 50))
        if restart_button:
            restart_button.draw(screen)
    else:
        turn_name = "Player 1" if turn == 0 else ("Player 2" if mode_selected == 1 else "AI")
        screen.blit(font.render(f"{turn_name}'s turn", True, BLACK), (WIDTH // 2 - 60, HEIGHT - 110))
        if attack_message:
            screen.blit(font.render(attack_message, True, BLACK), (WIDTH // 2 - 100, HEIGHT - 90))
        
        # Draw battle action buttons for current player (only for human turns and no lockout)
        if action_lockout == 0:
            if turn == 0:  # Player 1's turn - show buttons on left
                for btn in battle_buttons_p1:
                    btn.draw(screen)
            elif turn == 1 and mode_selected == 1:  # Player 2's turn in 2P mode - show buttons on right
                for btn in battle_buttons_p2:
                    btn.draw(screen)

    # Draw potion counts on screen (above buttons)
    screen.blit(font.render(f"P1 Potions: {potion_counts[0]}", True, BLACK), (20, HEIGHT - 110))
    screen.blit(font.render(f"P2 Potions: {potion_counts[1]}", True, BLACK), (WIDTH - 190, HEIGHT - 110))

# --- Play sound safely ---
def play_sound(sound):
    if sound:
        sound.play()

# --- Attack execution ---
def perform_attack(attacker_idx, action_key):
    global attacking, attack_message, turn, animation_timer, damage_popup, game_over, winner, action_lockout
    attacker = players[attacker_idx]
    defender_idx = 1 - attacker_idx
    defender = players[defender_idx]

    if action_key == "potion":
        if potion_counts[attacker_idx] > 0 and attacker["hp"] < attacker["max_hp"]:
            potion_counts[attacker_idx] -= 1
            heal_amount = 20
            attacker["hp"] = min(attacker["hp"] + heal_amount, attacker["max_hp"])
            attack_message = f"{attacker['name']} used Potion! +20 HP"
            play_sound(potion_sound)
            damage_popup = (f"+20", battle_positions[attacker_idx][0], battle_positions[attacker_idx][1] - 50, 60)
            attacking = True
            animation_timer = 30
            action_lockout = 60  # 1 second at 60 FPS
            turn = defender_idx
        else:
            attack_message = "No potions left or HP full!"
        return

    if action_key not in attacker["attacks"]:
        attack_message = f"{attacker['name']} can't use that move!"
        return

    attack = attacker["attacks"][action_key]

    attack_message = f"{attacker['name']} used {attack['name']}!"
    play_sound(attack["sound"])

    start_pos = battle_positions[attacker_idx]
    target_pos = battle_positions[defender_idx]

    spawn_projectile(attack["type"], start_pos, target_pos, attacker_idx, action_key)

    attacking = True
    animation_timer = 30
    action_lockout = 60
    turn = defender_idx

# --- AI logic for 1P mode ---
def ai_turn():
    global turn
    attacker_idx = 1
    defender_idx = 0
    attacker = players[attacker_idx]

    # Simple AI: heal if HP < 25 and potions left, else random attack
    if potion_counts[attacker_idx] > 0 and attacker["hp"] < attacker["max_hp"] * 0.4:
        perform_attack(attacker_idx, "potion")
    else:
        move_keys = [k for k in attacker["attacks"] if k != "tackle"]
        weights = [70] * len(move_keys)
        move_keys.append("tackle")
        weights.append(30)
        choice = random.choices(move_keys, weights=weights, k=1)[0]
        perform_attack(attacker_idx, choice)

# --- Handle key events in battle ---
def handle_battle_input(event):
    global turn
    if game_over:
        if event.key == pygame.K_r:
            reset_game()
        return

    # Don't allow input during action lockout
    if action_lockout > 0:
        return

    active_player = 0 if turn == 0 else (1 if turn == 1 and mode_selected == 1 else None)

    if active_player is None:
        return

    keybinds = PLAYER_KEYBINDS[active_player]

    if event.key == keybinds["potion"]:
        perform_attack(active_player, "potion")
        return

    for idx, key in enumerate(keybinds["moves"]):
        if event.key == key:
            move_key = player_move_keys[active_player][idx]
            if move_key:
                perform_attack(active_player, move_key)
            return

# --- Reset game to mode select ---
def reset_game():
    global mode_select, pokemon_select, battle_start, player_choices, player_selecting, players, turn, game_over, winner, potion_counts, attacking, attack_message, damage_popup, projectiles, particles, restart_button, action_lockout
    mode_select = True
    pokemon_select = False
    battle_start = False
    player_choices = [0, 0]
    player_selecting = 0
    players = [{}, {}]
    turn = 0
    game_over = False
    winner = None
    potion_counts = [3, 3]
    attacking = False
    attack_message = ""
    damage_popup = None
    projectiles.clear()
    particles.clear()
    restart_button = None
    action_lockout = 0

# --- Mode select screen ---
def draw_mode_select():
    screen.fill(WHITE)
    screen.blit(big_font.render("Select Mode", True, BLACK), (WIDTH // 2 - 130, 50))
    # Draw mode buttons
    for i, btn in enumerate(mode_buttons):
        if i == mode_selected:
            btn.color = YELLOW
        else:
            btn.color = GRAY
        btn.draw(screen)
    screen.blit(font.render("Tap to select or use UP/DOWN + ENTER", True, BLACK), (WIDTH // 2 - 180, HEIGHT - 50))

# --- Pokemon select screen ---
def draw_pokemon_select():
    global pokemon_selection_rects
    screen.fill(WHITE)
    screen.blit(big_font.render(f"Player {player_selecting + 1} Select", True, BLACK), (WIDTH // 2 - 160, 50))
    spacing = 220
    start_x = WIDTH // 2 - spacing
    y = HEIGHT // 2
    pokemon_selection_rects = []
    for i, p_name in enumerate(player_choice_names):
        sprite = pokemon_data[p_name]["sprite"]
        x = start_x + i * spacing
        screen.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
        # Draw names below
        screen.blit(font.render(p_name, True, BLACK), (x - font.size(p_name)[0] // 2, y + 70))
        # Draw highlight rectangle for current selection
        if i == player_choices[player_selecting]:
            border_color = BLUE if player_selecting == 1 else RED
            pygame.draw.rect(screen, border_color, (x - 60, y - 60, 120, 120), 4)
        # Store clickable rect for each pokemon
        pokemon_selection_rects.append(pygame.Rect(x - 60, y - 60, 120, 120))
    
    # Draw confirm button
    confirm_btn = Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 50, "Confirm", GREEN, BLACK)
    confirm_btn.draw(screen)

async def main():
    global mode_select, mode_selected, animation_timer, pokemon_select, battle_start, player_choices, player_selecting, players, turn, game_over, winner, potion_counts, attacking, attack_message, damage_popup, projectiles, particles, action_lockout
    # --- Main game loop ---
    clock = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if mode_select:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        mode_selected = (mode_selected - 1) % len(mode_options)
                    elif event.key == pygame.K_DOWN:
                        mode_selected = (mode_selected + 1) % len(mode_options)
                    elif event.key == pygame.K_RETURN:
                        mode_select = False
                        pokemon_select = True
                        player_selecting = 0
                        player_choices = [0, 0]
                
                # Handle mouse/tap input for mode selection
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, btn in enumerate(mode_buttons):
                        if btn.is_clicked(mouse_pos):
                            mode_selected = i
                            mode_select = False
                            pokemon_select = True
                            player_selecting = 0
                            player_choices = [0, 0]
                            break
                            
            elif pokemon_select:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        player_choices[player_selecting] = (player_choices[player_selecting] - 1) % len(player_choice_names)
                    elif event.key == pygame.K_RIGHT:
                        player_choices[player_selecting] = (player_choices[player_selecting] + 1) % len(player_choice_names)
                    elif event.key == pygame.K_RETURN:
                        if player_selecting == 0:
                            player_selecting = 1
                            if mode_selected == 0:
                                player_choices[1] = choose_ai_pokemon(player_choices[0])
                                pokemon_select = False
                                battle_start = True
                        else:
                            pokemon_select = False
                            battle_start = True
                
                # Handle mouse/tap input for pokemon selection
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if tapped on a pokemon
                    for i, rect in enumerate(pokemon_selection_rects):
                        if rect.collidepoint(mouse_pos):
                            player_choices[player_selecting] = i
                            break
                    
                    # Check if tapped confirm button
                    confirm_btn = Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 50, "Confirm", GREEN, BLACK)
                    if confirm_btn.is_clicked(mouse_pos):
                        if player_selecting == 0:
                            player_selecting = 1
                            if mode_selected == 0:
                                player_choices[1] = choose_ai_pokemon(player_choices[0])
                                pokemon_select = False
                                battle_start = True
                        else:
                            pokemon_select = False
                            battle_start = True

            elif battle_start:
                if event.type == pygame.KEYDOWN:
                    handle_battle_input(event)
                
                # Handle mouse/tap input for battle
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game_over:
                        if restart_button and restart_button.is_clicked(mouse_pos):
                            reset_game()
                    else:
                        # Check battle action buttons (only for human players on their turn)
                        if not attacking and action_lockout == 0:
                            # Player 1 can act on turn 0
                            if turn == 0:
                                for i, btn in enumerate(battle_buttons_p1):
                                    if btn.is_clicked(mouse_pos):
                                        if i == 3:
                                            perform_attack(turn, "potion")
                                        else:
                                            move_key = player_move_keys[0][i]
                                            if move_key:
                                                perform_attack(turn, move_key)
                                        break
                            # Player 2 can act on turn 1 (if 2P mode)
                            elif turn == 1 and mode_selected == 1:
                                for i, btn in enumerate(battle_buttons_p2):
                                    if btn.is_clicked(mouse_pos):
                                        if i == 3:
                                            perform_attack(turn, "potion")
                                        else:
                                            move_key = player_move_keys[1][i]
                                            if move_key:
                                                perform_attack(turn, move_key)
                                        break

        # Update damage popup timer
        if damage_popup:
            text, x, y, timer = damage_popup
            timer -= 1
            if timer <= 0:
                damage_popup = None
            else:
                damage_popup = (text, x, y, timer)
        
        # Update action lockout timer
        if action_lockout > 0:
            action_lockout -= 1

        # Update button hover states
        if mode_select:
            for btn in mode_buttons:
                btn.update_hover(mouse_pos)
        elif battle_start:
            if not game_over:
                # Only update hover for buttons when they're visible (human player's turn and no lockout)
                if action_lockout == 0:
                    if turn == 0:  # Player 1's buttons
                        for btn in battle_buttons_p1:
                            btn.update_hover(mouse_pos)
                    elif turn == 1 and mode_selected == 1:  # Player 2's buttons in 2P mode
                        for btn in battle_buttons_p2:
                            btn.update_hover(mouse_pos)
            else:
                if restart_button:
                    restart_button.update_hover(mouse_pos)
        
        # Update particles and projectiles
        update_particles()
        update_projectiles()

        if battle_start and not game_over:
            # Setup players dict on battle start
            if not players[0]:
                p1_name = player_choice_names[player_choices[0]]
                if mode_selected == 1:
                    p2_index = player_choices[1]
                else:
                    p2_index = choose_ai_pokemon(player_choices[0])
                    player_choices[1] = p2_index
                p2_name = player_choice_names[p2_index]
                players[0] = {
                    "name": p1_name,
                    "sprite": pokemon_data[p1_name]["sprite"],
                    "hp": pokemon_data[p1_name]["hp"],
                    "max_hp": pokemon_data[p1_name]["max_hp"],
                    "color": pokemon_data[p1_name]["color"],
                    "attacks": pokemon_data[p1_name]["attacks"]
                }
                if mode_selected == 1:
                    players[1] = {
                        "name": p2_name,
                        "sprite": pokemon_data[p2_name]["sprite"],
                        "hp": pokemon_data[p2_name]["hp"],
                        "max_hp": pokemon_data[p2_name]["max_hp"],
                        "color": pokemon_data[p2_name]["color"],
                        "attacks": pokemon_data[p2_name]["attacks"]
                    }
                else:
                    # AI gets player 2 pokemon
                    players[1] = {
                        "name": p2_name,
                        "sprite": pokemon_data[p2_name]["sprite"],
                        "hp": pokemon_data[p2_name]["hp"],
                        "max_hp": pokemon_data[p2_name]["max_hp"],
                        "color": pokemon_data[p2_name]["color"],
                        "attacks": pokemon_data[p2_name]["attacks"]
                    }

                configure_move_buttons()

            # AI turn if mode 1P and turn == 1
            if mode_selected == 0 and turn == 1 and not attacking and action_lockout == 0:
                pygame.time.wait(600)
                ai_turn()
        
        # Create restart button when game is over
        if battle_start and game_over and restart_button is None:
            create_restart_button()

        # Clear screen and draw appropriate screen
        if mode_select:
            draw_mode_select()
        elif pokemon_select:
            draw_pokemon_select()
        elif battle_start:
            draw_scene()

        # Update timers
        if attacking:
            animation_timer -= 1
            if animation_timer <= 0:
                attacking = False
                attack_message = ""

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

asyncio.run(main())

