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

# --- Fonts ---
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 64)

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
            "special": {"name":"Ember","type":"fire","damage_range":(8,18), "sound":fire_sound},
            "tackle": {"name":"Tackle","type":"physical","damage_range":(5,12), "sound":tackle_sound}
        }
    },
    "Chikorita": {
        "sprite": load_sprite("data/chi.png"),
        "hp": 60,
        "max_hp": 60,
        "color": GREEN,
        "attacks": {
            "special": {"name":"Razor Leaf","type":"leaf","damage_range":(10,20), "sound":leaf_sound},
            "tackle": {"name":"Tackle","type":"physical","damage_range":(5,12), "sound":tackle_sound}
        }
    },
    "Totodile": {
        "sprite": load_sprite("data/tot.png"),
        "hp": 70,
        "max_hp": 70,
        "color": BLUE,
        "attacks": {
            "special": {"name":"Water Gun","type":"water","damage_range":(8,18), "sound":water_sound},
            "tackle": {"name":"Tackle","type":"physical","damage_range":(5,12), "sound":tackle_sound}
        }
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

def spawn_projectile(p_type, start_pos, target_pos):
    if p_type == "fire":
        dx = (target_pos[0] - start_pos[0]) / 30
        dy = (target_pos[1] - start_pos[1]) / 30
        color = ORANGE
        projectiles.append({"x": start_pos[0], "y": start_pos[1], "dx": dx, "dy": dy,
                            "radius": 8, "color": color, "target": target_pos, "type": "fire"})
    elif p_type == "leaf":
        projectiles.append({"x": start_pos[0], "y": start_pos[1],
                            "center": target_pos, "angle": 0, "radius": 8, "color": LEAF_GREEN,
                            "distance": 0, "type": "leaf_boomerang", "start": start_pos})
    elif p_type == "water":
        dx = (target_pos[0] - start_pos[0]) / 30
        dy = (target_pos[1] - start_pos[1]) / 30
        color = SKY_BLUE
        projectiles.append({"x": start_pos[0], "y": start_pos[1], "dx": dx, "dy": dy,
                            "radius": 8, "color": color, "target": target_pos, "type": "water"})

def update_projectiles():
    global game_over, winner, damage_popup
    for p in projectiles[:]:
        if p["type"] == "fire":
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if abs(p["x"] - p["target"][0]) < 10 and abs(p["y"] - p["target"][1]) < 10:
                # Target is player 2 always for fire (player 1 attacks)
                target_index = 1 if turn == 0 else 0
                damage = random.randint(*players[turn]["attacks"]["special"]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[turn]["name"]
                    play_sound(victory_sound)
                spawn_particles("fire", p["target"])
                damage_popup = (f"-{damage}", p["target"][0], p["target"][1] - 50, 60)
                projectiles.remove(p)

        elif p["type"] == "leaf_boomerang":
            p["angle"] += 0.2
            p["distance"] += 1
            x = p["center"][0] + 100 * math.cos(p["angle"]) * math.sin(p["distance"] / 30)
            y = p["center"][1] + 100 * math.sin(p["angle"]) * math.sin(p["distance"] / 30)
            p["x"] = x
            p["y"] = y
            if p["distance"] > 60:
                target_index = 1 if turn == 0 else 0
                damage = random.randint(*players[turn]["attacks"]["special"]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[turn]["name"]
                    play_sound(victory_sound)
                spawn_particles("leaf", battle_positions[target_index])
                damage_popup = (f"-{damage}", battle_positions[target_index][0], battle_positions[target_index][1] - 50, 60)
                projectiles.remove(p)

        elif p["type"] == "water":
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if abs(p["x"] - p["target"][0]) < 10 and abs(p["y"] - p["target"][1]) < 10:
                target_index = 1 if turn == 0 else 0
                damage = random.randint(*players[turn]["attacks"]["special"]["damage_range"])
                players[target_index]["hp"] -= damage
                if players[target_index]["hp"] <= 0:
                    players[target_index]["hp"] = 0
                    game_over = True
                    winner = players[turn]["name"]
                    play_sound(victory_sound)
                spawn_particles("water", p["target"])
                damage_popup = (f"-{damage}", p["target"][0], p["target"][1] - 50, 60)
                projectiles.remove(p)

def draw_projectiles():
    for p in projectiles:
        pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), p["radius"])

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
    pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT // 2 + 50, WIDTH, HEIGHT // 2 - 50))
    for x in range(50, WIDTH, 120):
        pygame.draw.rect(screen, DARK_GREEN, (x, HEIGHT // 2 - 60, 40, 120))
        pygame.draw.polygon(screen, GREEN, [(x - 30, HEIGHT // 2 - 60), (x + 70, HEIGHT // 2 - 60), (x + 20, HEIGHT // 2 - 150)])

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
        screen.blit(font.render("Press R to restart", True, BLACK), (WIDTH // 2 - 90, HEIGHT // 2 + 10))
    else:
        turn_name = "Player 1" if turn == 0 else ("Player 2" if mode_selected == 1 else "AI")
        screen.blit(font.render(f"{turn_name}'s turn", True, BLACK), (WIDTH // 2 - 60, HEIGHT - 60))
        if attack_message:
            screen.blit(font.render(attack_message, True, BLACK), (WIDTH // 2 - 100, HEIGHT - 30))

    # Draw potion counts on screen (bottom left and right)
    screen.blit(font.render(f"Potions Left: {potion_counts[0]}", True, BLACK), (20, HEIGHT - 40))
    screen.blit(font.render(f"Potions Left: {potion_counts[1]}", True, BLACK), (WIDTH - 160, HEIGHT - 40))

# --- Play sound safely ---
def play_sound(sound):
    if sound:
        sound.play()

# --- Attack execution ---
def perform_attack(attacker_idx, attack_type):
    global attacking, attack_message, turn, animation_timer, damage_popup, game_over, winner
    attacker = players[attacker_idx]
    defender_idx = 1 - attacker_idx
    defender = players[defender_idx]

    if attack_type == "potion":
        if potion_counts[attacker_idx] > 0 and attacker["hp"] < attacker["max_hp"]:
            potion_counts[attacker_idx] -= 1
            heal_amount = 20
            attacker["hp"] = min(attacker["hp"] + heal_amount, attacker["max_hp"])
            attack_message = f"{attacker['name']} used Potion! +20 HP"
            play_sound(potion_sound)
            damage_popup = (f"+20", battle_positions[attacker_idx][0], battle_positions[attacker_idx][1] - 50, 60)
            attacking = True
            animation_timer = 30
            turn = defender_idx
        else:
            attack_message = "No potions left or HP full!"
        return

    if attack_type == "special":
        attack = attacker["attacks"]["special"]
    elif attack_type == "tackle":
        attack = attacker["attacks"]["tackle"]
    else:
        return

    attack_message = f"{attacker['name']} used {attack['name']}!"
    play_sound(attack["sound"])

    # Spawn projectile depending on attack type
    start_pos = battle_positions[attacker_idx]
    target_pos = battle_positions[defender_idx]

    spawn_projectile(attack["type"], start_pos, target_pos)

    attacking = True
    animation_timer = 30
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
        # 70% chance special, 30% tackle
        choice = random.choices(["special", "tackle"], weights=[70, 30])[0]
        perform_attack(attacker_idx, choice)

# --- Handle key events in battle ---
def handle_battle_input(event):
    global turn
    if game_over:
        if event.key == pygame.K_r:
            reset_game()
        return

    # Player 1 keys: SPACE (special), T (tackle), P (potion)
    if turn == 0:
        if event.key == pygame.K_SPACE:
            perform_attack(0, "special")
        elif event.key == pygame.K_t:
            perform_attack(0, "tackle")
        elif event.key == pygame.K_p:
            perform_attack(0, "potion")

    # Player 2 keys: (if 2P) ENTER (special), RSHIFT (tackle), RCTRL (potion)
    if turn == 1 and mode_selected == 1:
        if event.key == pygame.K_RETURN:
            perform_attack(1, "special")
        elif event.key == pygame.K_RSHIFT:
            perform_attack(1, "tackle")
        elif event.key == pygame.K_RCTRL:
            perform_attack(1, "potion")

# --- Reset game to mode select ---
def reset_game():
    global mode_select, pokemon_select, battle_start, player_choices, player_selecting, players, turn, game_over, winner, potion_counts, attacking, attack_message, damage_popup, projectiles, particles
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

# --- Mode select screen ---
def draw_mode_select():
    screen.fill(WHITE)
    screen.blit(big_font.render("Select Mode", True, BLACK), (WIDTH // 2 - 130, 50))
    for i, option in enumerate(mode_options):
        color = RED if i == mode_selected else BLACK
        screen.blit(font.render(option, True, color), (WIDTH // 2 - 100, 150 + i * 50))
    screen.blit(font.render("Use UP/DOWN + ENTER", True, BLACK), (WIDTH // 2 - 120, HEIGHT - 50))

# --- Pokemon select screen ---
def draw_pokemon_select():
    screen.fill(WHITE)
    screen.blit(big_font.render(f"Player {player_selecting + 1} Select", True, BLACK), (WIDTH // 2 - 160, 50))
    spacing = 220
    start_x = WIDTH // 2 - spacing
    y = HEIGHT // 2
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
    screen.blit(font.render("Use LEFT/RIGHT to choose, ENTER to confirm", True, BLACK), (WIDTH // 2 - 210, HEIGHT - 50))

async def main():
    global mode_select, mode_selected, animation_timer, pokemon_select, battle_start, player_choices, player_selecting, players, turn, game_over, winner, potion_counts, attacking, attack_message, damage_popup, projectiles, particles
    # --- Main game loop ---
    clock = pygame.time.Clock()

    while True:
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
            elif pokemon_select:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        player_choices[player_selecting] = (player_choices[player_selecting] - 1) % len(player_choice_names)
                    elif event.key == pygame.K_RIGHT:
                        player_choices[player_selecting] = (player_choices[player_selecting] + 1) % len(player_choice_names)
                    elif event.key == pygame.K_RETURN:
                        if player_selecting == 0:
                            player_selecting = 1
                            # If mode is 1P, skip player 2 selection and set AI Pokémon same as player 2 choice
                            if mode_selected == 0:
                                pokemon_select = False
                                battle_start = True
                            # Otherwise, let player 2 select
                        else:
                            pokemon_select = False
                            battle_start = True

            elif battle_start:
                if event.type == pygame.KEYDOWN:
                    handle_battle_input(event)

        # Update damage popup timer
        if damage_popup:
            text, x, y, timer = damage_popup
            timer -= 1
            if timer <= 0:
                damage_popup = None
            else:
                damage_popup = (text, x, y, timer)

        # Update particles and projectiles
        update_particles()
        update_projectiles()

        if battle_start and not game_over:
            # Setup players dict on battle start
            if not players[0]:
                p1_name = player_choice_names[player_choices[0]]
                p2_name = player_choice_names[player_choices[1]] if mode_selected == 1 else player_choice_names[player_choices[1]]
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

            # AI turn if mode 1P and turn == 1
            if mode_selected == 0 and turn == 1 and not attacking:
                pygame.time.wait(600)
                ai_turn()

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

