#!/usr/bin/env python3
"""
Test script for roguelike game components
"""

import sys
sys.path.insert(0, '/home/user/Claude')

from roguelike_game import (
    Player, Enemy, Potion, Treasure, Dungeon, Position, Tile
)


def test_player_creation():
    """Test player creation"""
    player = Player(5, 5)
    assert player.pos.x == 5
    assert player.pos.y == 5
    assert player.hp == 50
    assert player.attack == 10
    assert player.level == 1
    print("✓ Player creation test passed")


def test_enemy_creation():
    """Test enemy creation"""
    goblin = Enemy(10, 10, 'goblin')
    assert goblin.name == 'Goblin'
    assert goblin.char == 'g'
    assert goblin.hp == 15

    dragon = Enemy(15, 15, 'dragon')
    assert dragon.name == 'Dragon'
    assert dragon.hp == 80
    print("✓ Enemy creation test passed")


def test_combat():
    """Test combat system"""
    player = Player(0, 0)
    goblin = Enemy(1, 1, 'goblin')

    initial_hp = goblin.hp
    damage = player.attack
    actual_damage = goblin.take_damage(damage)

    assert goblin.hp < initial_hp
    assert actual_damage > 0
    print(f"✓ Combat test passed (dealt {actual_damage} damage)")


def test_level_up():
    """Test level up system"""
    player = Player(0, 0)
    initial_level = player.level
    initial_hp = player.max_hp

    player.gain_exp(20)

    assert player.level == initial_level + 1
    assert player.max_hp > initial_hp
    print(f"✓ Level up test passed (now level {player.level})")


def test_items():
    """Test item system"""
    player = Player(0, 0)
    player.hp = 30  # Damage player

    potion = Potion(1, 1)
    msg = potion.use(player)

    assert player.hp > 30
    assert "restore" in msg.lower()
    print(f"✓ Item test passed (HP: {player.hp})")


def test_dungeon_generation():
    """Test dungeon generation"""
    dungeon = Dungeon(80, 24)
    dungeon.generate()

    # Check that we have rooms
    assert len(dungeon.rooms) >= 5

    # Check that we have floor tiles
    floor_count = sum(
        1 for row in dungeon.tiles
        for tile in row
        if tile == Tile.FLOOR
    )
    assert floor_count > 0

    # Check that we can get random floor positions
    pos = dungeon.get_random_floor_position()
    assert pos is not None
    assert dungeon.is_walkable(pos.x, pos.y)

    print(f"✓ Dungeon generation test passed ({len(dungeon.rooms)} rooms, {floor_count} floor tiles)")


def test_position_distance():
    """Test position distance calculation"""
    pos1 = Position(0, 0)
    pos2 = Position(3, 4)

    distance = pos1.distance_to(pos2)
    assert abs(distance - 5.0) < 0.01  # 3-4-5 triangle
    print(f"✓ Position distance test passed (distance: {distance})")


def run_all_tests():
    """Run all tests"""
    print("Running Roguelike Game Tests...")
    print("=" * 50)

    try:
        test_player_creation()
        test_enemy_creation()
        test_combat()
        test_level_up()
        test_items()
        test_dungeon_generation()
        test_position_distance()

        print("=" * 50)
        print("All tests passed! ✓")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
