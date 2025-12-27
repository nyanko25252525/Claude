#!/usr/bin/env python3
"""
Simple NetHack-like Roguelike Game
===================================
A simple roguelike game written in Python using curses.

Controls:
- Arrow keys or WASD: Move
- i: Show inventory
- q: Quit game

Goal: Explore the dungeon, defeat enemies, and find the treasure!
"""

import curses
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional


class Tile(Enum):
    """Map tile types"""
    FLOOR = '.'
    WALL = '#'
    PLAYER = '@'
    ENEMY = 'E'
    GOBLIN = 'g'
    ORC = 'o'
    DRAGON = 'D'
    POTION = '!'
    TREASURE = '$'
    STAIRS_DOWN = '>'
    STAIRS_UP = '<'


@dataclass
class Position:
    """2D position"""
    x: int
    y: int

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False

    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


class Entity:
    """Base class for game entities"""
    def __init__(self, x: int, y: int, char: str, name: str, hp: int, attack: int, defense: int):
        self.pos = Position(x, y)
        self.char = char
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.alive = True

    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage dealt"""
        actual_damage = max(1, damage - self.defense)
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual_damage

    def heal(self, amount: int):
        """Heal the entity"""
        self.hp = min(self.max_hp, self.hp + amount)


class Player(Entity):
    """Player character"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, '@', 'Hero', hp=50, attack=10, defense=2)
        self.inventory: List[Item] = []
        self.level = 1
        self.exp = 0
        self.exp_to_next = 20

    def add_item(self, item: 'Item'):
        """Add item to inventory"""
        self.inventory.append(item)

    def gain_exp(self, amount: int) -> bool:
        """Gain experience, return True if leveled up"""
        self.exp += amount
        if self.exp >= self.exp_to_next:
            self.level_up()
            return True
        return False

    def level_up(self):
        """Level up the player"""
        self.level += 1
        self.exp = 0
        self.exp_to_next = int(self.exp_to_next * 1.5)
        self.max_hp += 10
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1


class Enemy(Entity):
    """Enemy character"""
    def __init__(self, x: int, y: int, enemy_type: str = 'goblin'):
        types = {
            'goblin': {'char': 'g', 'name': 'Goblin', 'hp': 15, 'attack': 5, 'defense': 0, 'exp': 5},
            'orc': {'char': 'o', 'name': 'Orc', 'hp': 25, 'attack': 8, 'defense': 1, 'exp': 10},
            'troll': {'char': 'T', 'name': 'Troll', 'hp': 40, 'attack': 12, 'defense': 2, 'exp': 20},
            'dragon': {'char': 'D', 'name': 'Dragon', 'hp': 80, 'attack': 20, 'defense': 5, 'exp': 50},
        }
        stats = types.get(enemy_type, types['goblin'])
        super().__init__(x, y, stats['char'], stats['name'],
                        stats['hp'], stats['attack'], stats['defense'])
        self.exp_value = stats['exp']
        self.enemy_type = enemy_type


class Item:
    """Base class for items"""
    def __init__(self, x: int, y: int, char: str, name: str, description: str):
        self.pos = Position(x, y)
        self.char = char
        self.name = name
        self.description = description

    def use(self, player: Player) -> str:
        """Use the item, return message"""
        return f"You can't use {self.name}."


class Potion(Item):
    """Healing potion"""
    def __init__(self, x: int, y: int, heal_amount: int = 20):
        super().__init__(x, y, '!', 'Health Potion', 'Restores HP')
        self.heal_amount = heal_amount

    def use(self, player: Player) -> str:
        """Use the potion"""
        old_hp = player.hp
        player.heal(self.heal_amount)
        healed = player.hp - old_hp
        return f"You drink the {self.name} and restore {healed} HP!"


class Treasure(Item):
    """Treasure item (win condition)"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, '$', 'Ancient Treasure', 'The legendary treasure!')

    def use(self, player: Player) -> str:
        return "You found the treasure! You win!"


class Dungeon:
    """Dungeon map generator and manager"""
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.tiles = [[Tile.WALL for _ in range(width)] for _ in range(height)]
        self.rooms: List[Tuple[int, int, int, int]] = []

    def generate(self):
        """Generate a random dungeon"""
        # Generate rooms
        num_rooms = random.randint(5, 8)
        for _ in range(num_rooms):
            self._create_room()

        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            self._create_corridor(self.rooms[i], self.rooms[i + 1])

    def _create_room(self):
        """Create a random room"""
        max_attempts = 50
        for _ in range(max_attempts):
            w = random.randint(4, 10)
            h = random.randint(4, 8)
            x = random.randint(1, self.width - w - 2)
            y = random.randint(1, self.height - h - 2)

            new_room = (x, y, w, h)

            # Check if room overlaps with existing rooms
            if not any(self._rooms_overlap(new_room, room) for room in self.rooms):
                self._carve_room(x, y, w, h)
                self.rooms.append(new_room)
                break

    def _rooms_overlap(self, room1, room2) -> bool:
        """Check if two rooms overlap"""
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2
        return not (x1 + w1 + 1 < x2 or x2 + w2 + 1 < x1 or
                   y1 + h1 + 1 < y2 or y2 + h2 + 1 < y1)

    def _carve_room(self, x: int, y: int, w: int, h: int):
        """Carve out a room"""
        for dy in range(h):
            for dx in range(w):
                self.tiles[y + dy][x + dx] = Tile.FLOOR

    def _create_corridor(self, room1, room2):
        """Create corridor between two rooms"""
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2

        center1_x = x1 + w1 // 2
        center1_y = y1 + h1 // 2
        center2_x = x2 + w2 // 2
        center2_y = y2 + h2 // 2

        # Random L-shaped corridor
        if random.random() < 0.5:
            self._carve_h_corridor(center1_x, center2_x, center1_y)
            self._carve_v_corridor(center1_y, center2_y, center2_x)
        else:
            self._carve_v_corridor(center1_y, center2_y, center1_x)
            self._carve_h_corridor(center1_x, center2_x, center2_y)

    def _carve_h_corridor(self, x1: int, x2: int, y: int):
        """Carve horizontal corridor"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = Tile.FLOOR

    def _carve_v_corridor(self, y1: int, y2: int, x: int):
        """Carve vertical corridor"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = Tile.FLOOR

    def get_random_floor_position(self) -> Optional[Position]:
        """Get a random floor position"""
        floor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == Tile.FLOOR:
                    floor_positions.append(Position(x, y))
        return random.choice(floor_positions) if floor_positions else None

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if position is walkable"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] == Tile.FLOOR


class Game:
    """Main game class"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.dungeon = Dungeon()
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self.messages: List[str] = []
        self.game_over = False
        self.won = False

        # Initialize curses settings
        curses.curs_set(0)  # Hide cursor
        self.stdscr.clear()

        # Initialize colors if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Default
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Player
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)     # Enemy
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Item
            curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Treasure

    def initialize(self):
        """Initialize the game"""
        self.add_message("Welcome to the Dungeon! Find the treasure and survive!")
        self.add_message("Use arrow keys or WASD to move. Press 'q' to quit.")

        # Generate dungeon
        self.dungeon.generate()

        # Place player
        pos = self.dungeon.get_random_floor_position()
        self.player = Player(pos.x, pos.y)

        # Spawn enemies
        self._spawn_enemies()

        # Place items
        self._spawn_items()

        # Place treasure
        pos = self.dungeon.get_random_floor_position()
        self.items.append(Treasure(pos.x, pos.y))

    def _spawn_enemies(self):
        """Spawn enemies in the dungeon"""
        num_enemies = random.randint(5, 10)
        enemy_types = ['goblin'] * 5 + ['orc'] * 3 + ['troll'] * 1 + ['dragon'] * 1

        for _ in range(num_enemies):
            pos = self.dungeon.get_random_floor_position()
            enemy_type = random.choice(enemy_types)
            self.enemies.append(Enemy(pos.x, pos.y, enemy_type))

    def _spawn_items(self):
        """Spawn items in the dungeon"""
        num_potions = random.randint(3, 6)
        for _ in range(num_potions):
            pos = self.dungeon.get_random_floor_position()
            self.items.append(Potion(pos.x, pos.y))

    def add_message(self, msg: str):
        """Add a message to the message log"""
        self.messages.append(msg)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def handle_input(self, key) -> bool:
        """Handle player input, return False to quit"""
        if key in [ord('q'), ord('Q')]:
            return False

        if self.game_over:
            return key != ord('q')

        # Movement
        dx, dy = 0, 0
        if key == curses.KEY_UP or key == ord('w') or key == ord('W'):
            dy = -1
        elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
            dy = 1
        elif key == curses.KEY_LEFT or key == ord('a') or key == ord('A'):
            dx = -1
        elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'):
            dx = 1
        elif key == ord('i') or key == ord('I'):
            self._show_inventory()
            return True

        if dx != 0 or dy != 0:
            self._move_player(dx, dy)
            self._update_enemies()

        return True

    def _move_player(self, dx: int, dy: int):
        """Move the player"""
        new_x = self.player.pos.x + dx
        new_y = self.player.pos.y + dy

        # Check for enemy collision
        enemy = self._get_entity_at(new_x, new_y, self.enemies)
        if enemy:
            self._combat(self.player, enemy)
            return

        # Check if walkable
        if self.dungeon.is_walkable(new_x, new_y):
            self.player.pos.x = new_x
            self.player.pos.y = new_y

            # Check for item pickup
            item = self._get_entity_at(new_x, new_y, self.items)
            if item:
                self._pickup_item(item)

    def _get_entity_at(self, x: int, y: int, entities: List) -> Optional:
        """Get entity at position"""
        for entity in entities:
            if entity.pos.x == x and entity.pos.y == y:
                if hasattr(entity, 'alive') and entity.alive:
                    return entity
                elif not hasattr(entity, 'alive'):
                    return entity
        return None

    def _combat(self, attacker: Entity, defender: Entity):
        """Handle combat between two entities"""
        damage = random.randint(attacker.attack // 2, attacker.attack)
        actual_damage = defender.take_damage(damage)

        self.add_message(f"{attacker.name} attacks {defender.name} for {actual_damage} damage!")

        if not defender.alive:
            self.add_message(f"{defender.name} has been defeated!")
            if isinstance(defender, Enemy) and isinstance(attacker, Player):
                leveled = attacker.gain_exp(defender.exp_value)
                if leveled:
                    self.add_message(f"Level up! You are now level {attacker.level}!")
            elif isinstance(defender, Player):
                self.game_over = True
                self.add_message("You have died! Game Over. Press 'q' to quit.")

    def _pickup_item(self, item: Item):
        """Pickup an item"""
        if isinstance(item, Treasure):
            self.won = True
            self.game_over = True
            self.add_message("YOU FOUND THE TREASURE! YOU WIN!")
        else:
            # Auto-use potions for simplicity
            if isinstance(item, Potion):
                msg = item.use(self.player)
                self.add_message(msg)
            else:
                self.player.add_item(item)
                self.add_message(f"Picked up {item.name}!")

            self.items.remove(item)

    def _update_enemies(self):
        """Update enemy AI"""
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Simple AI: move towards player if close
            dist = enemy.pos.distance_to(self.player.pos)
            if dist < 6:
                dx = 0 if enemy.pos.x == self.player.pos.x else (1 if enemy.pos.x < self.player.pos.x else -1)
                dy = 0 if enemy.pos.y == self.player.pos.y else (1 if enemy.pos.y < self.player.pos.y else -1)

                new_x = enemy.pos.x + dx
                new_y = enemy.pos.y + dy

                # Attack player if adjacent
                if new_x == self.player.pos.x and new_y == self.player.pos.y:
                    self._combat(enemy, self.player)
                # Move if walkable and no other enemy there
                elif self.dungeon.is_walkable(new_x, new_y):
                    if not self._get_entity_at(new_x, new_y, self.enemies):
                        enemy.pos.x = new_x
                        enemy.pos.y = new_y

    def _show_inventory(self):
        """Show inventory (currently just shows status)"""
        inv_items = [f"- {item.name}" for item in self.player.inventory]
        if inv_items:
            self.add_message("Inventory: " + ", ".join(inv_items))
        else:
            self.add_message("Your inventory is empty.")

    def render(self):
        """Render the game"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Calculate camera offset to center on player
        cam_x = max(0, min(self.player.pos.x - width // 2, self.dungeon.width - width))
        cam_y = max(0, min(self.player.pos.y - height // 2 + 3, self.dungeon.height - height + 6))

        # Render dungeon
        for y in range(min(height - 6, self.dungeon.height)):
            for x in range(min(width, self.dungeon.width)):
                map_x = x + cam_x
                map_y = y + cam_y

                if 0 <= map_x < self.dungeon.width and 0 <= map_y < self.dungeon.height:
                    char = self.dungeon.tiles[map_y][map_x].value

                    # Check for entities at this position
                    if self.player.pos.x == map_x and self.player.pos.y == map_y:
                        char = self.player.char
                        color = 2  # Yellow
                    else:
                        enemy = self._get_entity_at(map_x, map_y, self.enemies)
                        if enemy:
                            char = enemy.char
                            color = 3  # Red
                        else:
                            item = self._get_entity_at(map_x, map_y, self.items)
                            if item:
                                char = item.char
                                color = 4 if not isinstance(item, Treasure) else 5
                            else:
                                color = 1  # White

                    try:
                        if curses.has_colors():
                            self.stdscr.addstr(y, x, char, curses.color_pair(color))
                        else:
                            self.stdscr.addstr(y, x, char)
                    except curses.error:
                        pass

        # Render UI
        ui_y = height - 5
        try:
            # Player stats
            stats = f"HP: {self.player.hp}/{self.player.max_hp} | Lvl: {self.player.level} | Exp: {self.player.exp}/{self.player.exp_to_next} | Atk: {self.player.attack} | Def: {self.player.defense}"
            self.stdscr.addstr(ui_y, 0, "=" * min(width - 1, 80))
            self.stdscr.addstr(ui_y + 1, 0, stats[:width - 1])

            # Messages
            for i, msg in enumerate(self.messages[-3:]):
                self.stdscr.addstr(ui_y + 2 + i, 0, msg[:width - 1])
        except curses.error:
            pass

        self.stdscr.refresh()

    def run(self):
        """Main game loop"""
        self.initialize()

        while True:
            self.render()

            try:
                key = self.stdscr.getch()
            except KeyboardInterrupt:
                break

            if not self.handle_input(key):
                break


def main(stdscr):
    """Main entry point"""
    game = Game(stdscr)
    game.run()


if __name__ == '__main__':
    curses.wrapper(main)
