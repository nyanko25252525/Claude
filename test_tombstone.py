#!/usr/bin/env python3
"""
Test script for tombstone display feature
"""

import sys
sys.path.insert(0, '/home/user/Claude')

from roguelike_game import Game, Player, Enemy
import curses
import time


def test_tombstone_display(stdscr):
    """Test the tombstone display"""
    # Create a game instance
    game = Game(stdscr)
    game.initialize()

    # Simulate player death
    game.player.hp = 1
    game.kills_count = 5
    game.turn_count = 42

    # Create a goblin to kill the player
    goblin = Enemy(game.player.pos.x + 1, game.player.pos.y, 'goblin')

    # Simulate combat where player dies
    game._combat(goblin, game.player)

    # Show the game screen (should show tombstone)
    game.render()

    # Wait for a moment so we can see it
    stdscr.addstr(0, 0, "Tombstone test - the game should show RIP screen")
    stdscr.addstr(1, 0, "Press any key to exit")
    stdscr.refresh()
    stdscr.getch()


def test_game_stats():
    """Test game statistics tracking"""
    print("Testing game statistics...")

    # Test that we can create a game with statistics
    class MockStdscr:
        def clear(self): pass
        def refresh(self): pass
        def getmaxyx(self): return (24, 80)
        def addstr(self, *args): pass

    mock_screen = MockStdscr()
    game = Game(mock_screen)

    assert hasattr(game, 'death_cause'), "Game should have death_cause attribute"
    assert hasattr(game, 'kills_count'), "Game should have kills_count attribute"
    assert hasattr(game, 'turn_count'), "Game should have turn_count attribute"

    assert game.death_cause == "", "death_cause should be empty initially"
    assert game.kills_count == 0, "kills_count should be 0 initially"
    assert game.turn_count == 0, "turn_count should be 0 initially"

    print("✓ Game statistics tracking test passed")


if __name__ == '__main__':
    # Run non-curses test
    test_game_stats()

    print("\nStarting curses test for tombstone display...")
    print("This will show a sample tombstone screen.")
    print("Press any key when ready...")
    input()

    # Run curses test
    curses.wrapper(test_tombstone_display)

    print("\n✓ All tombstone tests completed!")
