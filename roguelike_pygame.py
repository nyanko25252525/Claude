#!/usr/bin/env python3
"""
Graphical Roguelike Game with Pygame
=====================================
A graphical version of the NetHack-style roguelike game using Pygame.

Controls:
- Arrow keys or WASD: Move
- > key: Go down stairs
- < key: Go up stairs
- I key: Show inventory
- ESC or Q: Quit game
"""

import pygame
import sys
import os
from typing import Optional, List, Tuple
from roguelike_game import (
    Player, Enemy, Pet, Item, Potion, Treasure,
    Dungeon, Position, Tile
)


# Game constants
TILE_SIZE = 32
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)


class GraphicalGame:
    """Graphical version of the roguelike game using Pygame"""

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NetHack-style Roguelike - Tanjiro's Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Game state
        self.dungeon = Dungeon()
        self.player: Optional[Player] = None
        self.pet: Optional[Pet] = None
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self.messages: List[str] = []
        self.game_over = False
        self.won = False
        self.death_cause = ""
        self.kills_count = 0
        self.turn_count = 0

        # Multi-floor system
        self.current_floor = 1
        self.max_floors = 5
        self.stairs_down_pos: Optional[Position] = None
        self.stairs_up_pos: Optional[Position] = None

        # Camera
        self.camera_x = 0
        self.camera_y = 0

        # Load sprites
        self.load_sprites()

    def load_sprites(self):
        """Load sprite images"""
        # Try to load Tanjiro sprite
        tanjiro_paths = [
            '/home/user/Claude/tanjiro.png',
            '/home/user/Claude/tanjiro_sprite.png',
            'tanjiro.png',
            'assets/tanjiro.png'
        ]

        self.player_sprite = None
        for path in tanjiro_paths:
            if os.path.exists(path):
                try:
                    self.player_sprite = pygame.image.load(path)
                    self.player_sprite = pygame.transform.scale(
                        self.player_sprite, (TILE_SIZE, TILE_SIZE)
                    )
                    print(f"Loaded Tanjiro sprite from {path}")
                    break
                except Exception as e:
                    print(f"Failed to load {path}: {e}")

        # If no sprite found, create a placeholder
        if self.player_sprite is None:
            print("Tanjiro sprite not found, using placeholder")
            self.player_sprite = self.create_placeholder_sprite(
                YELLOW, '@'
            )

    def create_placeholder_sprite(self, color: Tuple[int, int, int], char: str) -> pygame.Surface:
        """Create a colored square with a character as placeholder"""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color)
        # Draw character
        text = self.font.render(char, True, BLACK)
        text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
        surface.blit(text, text_rect)
        return surface

    def choose_pet(self) -> str:
        """Show pet selection screen and return chosen pet type"""
        selecting = True
        selected_pet = None

        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        selected_pet = 'dog'
                        selecting = False
                    elif event.key == pygame.K_2:
                        selected_pet = 'cat'
                        selecting = False

            # Draw selection screen
            self.screen.fill(BLACK)

            title = self.font.render("Choose your companion:", True, WHITE)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(title, title_rect)

            option1 = self.font.render("1. Dog (d) - Loyal and strong (HP: 30, ATK: 8)", True, GREEN)
            option1_rect = option1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(option1, option1_rect)

            option2 = self.font.render("2. Cat (f) - Agile and quick (HP: 20, ATK: 6)", True, CYAN)
            option2_rect = option2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(option2, option2_rect)

            instruction = self.small_font.render("Press 1 or 2 to choose...", True, GRAY)
            instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            self.screen.blit(instruction, instruction_rect)

            pygame.display.flip()
            self.clock.tick(FPS)

        return selected_pet

    def initialize(self):
        """Initialize the game"""
        # Choose pet
        self.pet_type = self.choose_pet()

        self.add_message("Welcome to the Dungeon! Find the treasure!")
        self.add_message("Use arrow keys or WASD to move.")

        # Generate first floor
        self.generate_floor(self.current_floor)

    def generate_floor(self, floor_num: int):
        """Generate a new floor"""
        # Generate dungeon
        self.dungeon = Dungeon()
        self.dungeon.generate()

        # Place player
        pos = self.dungeon.get_random_floor_position()
        if self.player is None:
            self.player = Player(pos.x, pos.y)
        else:
            self.player.pos.x = pos.x
            self.player.pos.y = pos.y

        # Place or move pet near player
        if self.pet is None:
            self.pet = Pet(pos.x + 1, pos.y, self.pet_type)
        else:
            self.pet.pos.x = pos.x + 1
            self.pet.pos.y = pos.y

        # Clear entities
        self.enemies = []
        self.items = []

        # Spawn enemies
        self.spawn_enemies(floor_num)

        # Place items
        self.spawn_items()

        # Place stairs
        if floor_num < self.max_floors:
            pos = self.dungeon.get_random_floor_position()
            self.stairs_down_pos = Position(pos.x, pos.y)
        else:
            self.stairs_down_pos = None

        if floor_num > 1:
            pos = self.dungeon.get_random_floor_position()
            self.stairs_up_pos = Position(pos.x, pos.y)
        else:
            self.stairs_up_pos = None

        # Place treasure on last floor
        if floor_num == self.max_floors:
            pos = self.dungeon.get_random_floor_position()
            self.items.append(Treasure(pos.x, pos.y))

        self.add_message(f"Entered floor {floor_num}")

    def spawn_enemies(self, floor_num: int = 1):
        """Spawn enemies (logic from original game)"""
        from roguelike_game import Enemy
        import random

        base_enemies = 5 + floor_num
        num_enemies = random.randint(base_enemies, base_enemies + 3)

        if floor_num == 1:
            enemy_types = ['goblin'] * 8 + ['orc'] * 2
        elif floor_num == 2:
            enemy_types = ['goblin'] * 5 + ['orc'] * 4 + ['troll'] * 1
        elif floor_num == 3:
            enemy_types = ['goblin'] * 3 + ['orc'] * 5 + ['troll'] * 2
        elif floor_num == 4:
            enemy_types = ['orc'] * 4 + ['troll'] * 4 + ['dragon'] * 2
        else:
            enemy_types = ['orc'] * 2 + ['troll'] * 5 + ['dragon'] * 3

        for _ in range(num_enemies):
            pos = self.dungeon.get_random_floor_position()
            enemy_type = random.choice(enemy_types)
            self.enemies.append(Enemy(pos.x, pos.y, enemy_type))

    def spawn_items(self):
        """Spawn items"""
        import random
        num_potions = random.randint(3, 6)
        for _ in range(num_potions):
            pos = self.dungeon.get_random_floor_position()
            self.items.append(Potion(pos.x, pos.y))

    def add_message(self, msg: str):
        """Add a message to the log"""
        self.messages.append(msg)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def handle_input(self):
        """Handle player input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Allow quitting at any time
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    return False

                # Game over screen - any key to continue viewing, ESC/Q to quit
                if self.game_over:
                    # Already handled ESC/Q above, so just continue
                    continue

                # Movement
                dx, dy = 0, 0
                if event.key in [pygame.K_UP, pygame.K_w]:
                    dy = -1
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    dy = 1
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    dx = -1
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    dx = 1
                elif event.key == pygame.K_PERIOD and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # > key (Shift + .)
                    self.use_stairs_down()
                elif event.key == pygame.K_COMMA and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # < key (Shift + ,)
                    self.use_stairs_up()
                elif event.key == pygame.K_i:
                    self.show_inventory()

                if dx != 0 or dy != 0:
                    self.move_player(dx, dy)
                    self.update_enemies()
                    self.update_pet()
                    self.turn_count += 1

        return True

    def move_player(self, dx: int, dy: int):
        """Move the player"""
        new_x = self.player.pos.x + dx
        new_y = self.player.pos.y + dy

        # Check for enemy collision
        enemy = self.get_entity_at(new_x, new_y, self.enemies)
        if enemy:
            self.combat(self.player, enemy)
            return

        # Check if walkable
        if self.dungeon.is_walkable(new_x, new_y):
            self.player.pos.x = new_x
            self.player.pos.y = new_y

            # Check for item pickup
            item = self.get_entity_at(new_x, new_y, self.items)
            if item:
                self.pickup_item(item)

    def get_entity_at(self, x: int, y: int, entities: List):
        """Get entity at position"""
        for entity in entities:
            if entity.pos.x == x and entity.pos.y == y:
                if hasattr(entity, 'alive') and entity.alive:
                    return entity
                elif not hasattr(entity, 'alive'):
                    return entity
        return None

    def combat(self, attacker, defender):
        """Handle combat"""
        import random
        damage = random.randint(attacker.attack // 2, attacker.attack)
        actual_damage = defender.take_damage(damage)

        self.add_message(f"{attacker.name} attacks {defender.name} for {actual_damage} damage!")

        if not defender.alive:
            self.add_message(f"{defender.name} has been defeated!")
            if isinstance(defender, Enemy):
                if isinstance(attacker, Player):
                    self.kills_count += 1
                    leveled = attacker.gain_exp(defender.exp_value)
                    if leveled:
                        self.add_message(f"Level up! You are now level {attacker.level}!")
                elif isinstance(attacker, Pet):
                    self.kills_count += 1
            elif isinstance(defender, Player):
                self.game_over = True
                self.death_cause = f"a {attacker.name}"
                self.add_message("You have died! Game Over.")
            elif isinstance(defender, Pet):
                self.add_message(f"Your {defender.name} has died!")

    def pickup_item(self, item):
        """Pick up an item"""
        if isinstance(item, Treasure):
            self.won = True
            self.game_over = True
            self.add_message("YOU FOUND THE TREASURE! YOU WIN!")
        else:
            if isinstance(item, Potion):
                msg = item.use(self.player)
                self.add_message(msg)
            else:
                self.player.add_item(item)
                self.add_message(f"Picked up {item.name}!")

            self.items.remove(item)

    def update_enemies(self):
        """Update enemy AI"""
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dist = enemy.pos.distance_to(self.player.pos)
            if dist < 6:
                dx = 0 if enemy.pos.x == self.player.pos.x else (1 if enemy.pos.x < self.player.pos.x else -1)
                dy = 0 if enemy.pos.y == self.player.pos.y else (1 if enemy.pos.y < self.player.pos.y else -1)

                new_x = enemy.pos.x + dx
                new_y = enemy.pos.y + dy

                if new_x == self.player.pos.x and new_y == self.player.pos.y:
                    self.combat(enemy, self.player)
                elif self.pet and self.pet.alive and new_x == self.pet.pos.x and new_y == self.pet.pos.y:
                    self.combat(enemy, self.pet)
                elif self.dungeon.is_walkable(new_x, new_y):
                    if not self.get_entity_at(new_x, new_y, self.enemies):
                        enemy.pos.x = new_x
                        enemy.pos.y = new_y

    def update_pet(self):
        """Update pet AI - follow player and attack nearby enemies"""
        if not self.pet or not self.pet.alive:
            return

        # Check for adjacent enemies to attack
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dist = self.pet.pos.distance_to(enemy.pos)
            if dist <= 1.5:  # Adjacent
                self.combat(self.pet, enemy)
                return  # Pet attacks instead of moving

        # Check distance to player
        dist_to_player = self.pet.pos.distance_to(self.player.pos)

        # If pet is too far away (stuck or lost), teleport it near the player
        if dist_to_player > 8:
            # Find a walkable position near the player
            import random
            for _ in range(20):  # Try up to 20 times to find a spot
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                new_x = self.player.pos.x + offset_x
                new_y = self.player.pos.y + offset_y

                if (self.dungeon.is_walkable(new_x, new_y) and
                    not self.get_entity_at(new_x, new_y, self.enemies) and
                    not (new_x == self.player.pos.x and new_y == self.player.pos.y)):
                    self.pet.pos.x = new_x
                    self.pet.pos.y = new_y
                    self.add_message(f"{self.pet.name} catches up to you!")
                    return

        # Follow player if not too close
        if dist_to_player > 2:
            dx = 0 if self.pet.pos.x == self.player.pos.x else (1 if self.pet.pos.x < self.player.pos.x else -1)
            dy = 0 if self.pet.pos.y == self.player.pos.y else (1 if self.pet.pos.y < self.player.pos.y else -1)

            new_x = self.pet.pos.x + dx
            new_y = self.pet.pos.y + dy

            # Try to move towards player
            if self.dungeon.is_walkable(new_x, new_y):
                if not self.get_entity_at(new_x, new_y, self.enemies):
                    if not (new_x == self.player.pos.x and new_y == self.player.pos.y):
                        self.pet.pos.x = new_x
                        self.pet.pos.y = new_y
                        return

            # If direct path is blocked, try alternative moves
            # Try moving only in X direction
            if dx != 0:
                alt_x = self.pet.pos.x + dx
                alt_y = self.pet.pos.y
                if (self.dungeon.is_walkable(alt_x, alt_y) and
                    not self.get_entity_at(alt_x, alt_y, self.enemies) and
                    not (alt_x == self.player.pos.x and alt_y == self.player.pos.y)):
                    self.pet.pos.x = alt_x
                    return

            # Try moving only in Y direction
            if dy != 0:
                alt_x = self.pet.pos.x
                alt_y = self.pet.pos.y + dy
                if (self.dungeon.is_walkable(alt_x, alt_y) and
                    not self.get_entity_at(alt_x, alt_y, self.enemies) and
                    not (alt_x == self.player.pos.x and alt_y == self.player.pos.y)):
                    self.pet.pos.y = alt_y
                    return

    def use_stairs_down(self):
        """Use down stairs"""
        if self.stairs_down_pos and self.player.pos == self.stairs_down_pos:
            if self.current_floor < self.max_floors:
                self.current_floor += 1
                self.generate_floor(self.current_floor)
            else:
                self.add_message("There are no stairs going down.")
        else:
            self.add_message("There are no stairs here.")

    def use_stairs_up(self):
        """Use up stairs"""
        if self.stairs_up_pos and self.player.pos == self.stairs_up_pos:
            if self.current_floor > 1:
                self.current_floor -= 1
                self.generate_floor(self.current_floor)
            else:
                self.add_message("There are no stairs going up.")
        else:
            self.add_message("There are no stairs here.")

    def show_inventory(self):
        """Show inventory"""
        inv_items = [f"- {item.name}" for item in self.player.inventory]
        if inv_items:
            self.add_message("Inventory: " + ", ".join(inv_items))
        else:
            self.add_message("Your inventory is empty.")

    def update_camera(self):
        """Update camera position to follow player"""
        # Center camera on player
        tiles_width = SCREEN_WIDTH // TILE_SIZE
        tiles_height = (SCREEN_HEIGHT - 100) // TILE_SIZE  # Leave space for UI

        self.camera_x = max(0, min(
            self.player.pos.x - tiles_width // 2,
            self.dungeon.width - tiles_width
        ))
        self.camera_y = max(0, min(
            self.player.pos.y - tiles_height // 2,
            self.dungeon.height - tiles_height
        ))

    def draw_tile(self, tile: Tile, x: int, y: int):
        """Draw a dungeon tile"""
        screen_x = (x - self.camera_x) * TILE_SIZE
        screen_y = (y - self.camera_y) * TILE_SIZE

        if tile == Tile.WALL:
            pygame.draw.rect(self.screen, DARK_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        elif tile == Tile.FLOOR:
            pygame.draw.rect(self.screen, GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
            # Add grid lines
            pygame.draw.rect(self.screen, DARK_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)

    def draw_entity(self, entity, color: Tuple[int, int, int]):
        """Draw an entity as a simple shape"""
        x = (entity.pos.x - self.camera_x) * TILE_SIZE
        y = (entity.pos.y - self.camera_y) * TILE_SIZE

        # Draw as circle
        center_x = x + TILE_SIZE // 2
        center_y = y + TILE_SIZE // 2
        radius = TILE_SIZE // 3
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)

        # Draw character
        char_text = self.small_font.render(entity.char, True, WHITE)
        char_rect = char_text.get_rect(center=(center_x, center_y))
        self.screen.blit(char_text, char_rect)

    def render(self):
        """Render the game"""
        self.screen.fill(BLACK)

        # Update camera
        self.update_camera()

        # Draw dungeon
        tiles_width = SCREEN_WIDTH // TILE_SIZE + 1
        tiles_height = (SCREEN_HEIGHT - 100) // TILE_SIZE + 1

        for y in range(tiles_height):
            for x in range(tiles_width):
                map_x = x + self.camera_x
                map_y = y + self.camera_y

                if 0 <= map_x < self.dungeon.width and 0 <= map_y < self.dungeon.height:
                    self.draw_tile(self.dungeon.tiles[map_y][map_x], map_x, map_y)

        # Draw stairs
        if self.stairs_down_pos:
            x = (self.stairs_down_pos.x - self.camera_x) * TILE_SIZE
            y = (self.stairs_down_pos.y - self.camera_y) * TILE_SIZE
            pygame.draw.rect(self.screen, MAGENTA, (x, y, TILE_SIZE, TILE_SIZE))
            text = self.font.render('>', True, WHITE)
            text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
            self.screen.blit(text, text_rect)

        if self.stairs_up_pos:
            x = (self.stairs_up_pos.x - self.camera_x) * TILE_SIZE
            y = (self.stairs_up_pos.y - self.camera_y) * TILE_SIZE
            pygame.draw.rect(self.screen, MAGENTA, (x, y, TILE_SIZE, TILE_SIZE))
            text = self.font.render('<', True, WHITE)
            text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
            self.screen.blit(text, text_rect)

        # Draw items
        for item in self.items:
            if isinstance(item, Treasure):
                color = CYAN
            else:
                color = GREEN
            self.draw_entity(item, color)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.alive:
                self.draw_entity(enemy, RED)

        # Draw pet
        if self.pet and self.pet.alive:
            self.draw_entity(self.pet, BLUE)

        # Draw player (Tanjiro)
        player_x = (self.player.pos.x - self.camera_x) * TILE_SIZE
        player_y = (self.player.pos.y - self.camera_y) * TILE_SIZE
        self.screen.blit(self.player_sprite, (player_x, player_y))

        # Draw UI
        self.draw_ui()

        # Draw game over screen on top if game is over
        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_ui(self):
        """Draw user interface"""
        ui_y = SCREEN_HEIGHT - 95

        # Background for UI
        pygame.draw.rect(self.screen, BLACK, (0, ui_y, SCREEN_WIDTH, 95))
        pygame.draw.line(self.screen, WHITE, (0, ui_y), (SCREEN_WIDTH, ui_y), 2)

        # Player stats
        stats_text = f"HP: {self.player.hp}/{self.player.max_hp} | Lvl: {self.player.level} | Exp: {self.player.exp}/{self.player.exp_to_next} | Atk: {self.player.attack} | Def: {self.player.defense}"
        stats_surface = self.small_font.render(stats_text, True, WHITE)
        self.screen.blit(stats_surface, (10, ui_y + 5))

        # Pet stats
        if self.pet and self.pet.alive:
            pet_text = f"Pet ({self.pet.name}): HP {self.pet.hp}/{self.pet.max_hp} | Floor: {self.current_floor}/{self.max_floors}"
        else:
            pet_text = f"Pet: (deceased) | Floor: {self.current_floor}/{self.max_floors}"
        pet_surface = self.small_font.render(pet_text, True, BLUE if self.pet and self.pet.alive else RED)
        self.screen.blit(pet_surface, (10, ui_y + 25))

        # Messages
        for i, msg in enumerate(self.messages[-3:]):
            msg_surface = self.small_font.render(msg, True, YELLOW)
            self.screen.blit(msg_surface, (10, ui_y + 45 + i * 16))

    def draw_game_over(self):
        """Draw game over screen"""
        # Semi-transparent black overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        if self.won:
            title = "★ VICTORY! ★"
            color = YELLOW
            message = "You found the Ancient Treasure!"
            subtitle = "Congratulations, brave hero!"
        else:
            title = "GAME OVER"
            color = RED
            message = f"Killed by {self.death_cause}"
            subtitle = "Better luck next time..."

        # Draw title
        title_surface = pygame.font.Font(None, 72).render(title, True, color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(title_surface, title_rect)

        # Draw message
        msg_surface = self.font.render(message, True, WHITE)
        msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(msg_surface, msg_rect)

        # Draw subtitle
        subtitle_surface = self.small_font.render(subtitle, True, GRAY)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 35))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Draw separator
        pygame.draw.line(self.screen, GRAY,
                        (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 10),
                        (SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 - 10), 2)

        # Draw stats
        stats = [
            f"Level reached: {self.player.level}",
            f"Enemies defeated: {self.kills_count}",
            f"Turns survived: {self.turn_count}",
            f"Floor reached: {self.current_floor}/{self.max_floors}"
        ]

        for i, stat in enumerate(stats):
            stat_surface = self.font.render(stat, True, YELLOW if self.won else WHITE)
            stat_rect = stat_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 + i * 30))
            self.screen.blit(stat_surface, stat_rect)

        # Draw quit message
        quit_surface = self.font.render("Press ESC or Q to quit", True, GREEN)
        quit_rect = quit_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(quit_surface, quit_rect)

    def run(self):
        """Main game loop"""
        self.initialize()

        running = True
        while running:
            running = self.handle_input()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    """Main entry point"""
    game = GraphicalGame()
    game.run()


if __name__ == '__main__':
    main()
