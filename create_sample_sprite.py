#!/usr/bin/env python3
"""
Create a sample sprite for Tanjiro
This creates a simple placeholder image that can be replaced with the actual sprite.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not available, trying pygame...")

import pygame


def create_sample_sprite_pygame():
    """Create a sample sprite using pygame"""
    pygame.init()

    # Create a 32x32 surface
    size = 32
    surface = pygame.Surface((size, size))

    # Fill with a color (greenish for Tanjiro's uniform)
    surface.fill((50, 100, 50))

    # Draw a simple character representation
    # Head (beige circle)
    pygame.draw.circle(surface, (230, 200, 180), (size // 2, size // 3), 8)

    # Eyes (black dots)
    pygame.draw.circle(surface, (0, 0, 0), (size // 2 - 3, size // 3), 1)
    pygame.draw.circle(surface, (0, 0, 0), (size // 2 + 3, size // 3), 1)

    # Body (dark green rectangle)
    pygame.draw.rect(surface, (30, 80, 30), (size // 2 - 6, size // 3 + 8, 12, 14))

    # Add @ symbol for roguelike feel
    font = pygame.font.Font(None, 24)
    text = font.render('@', True, (255, 255, 0))
    text_rect = text.get_rect(center=(size // 2, size - 6))
    surface.blit(text, text_rect)

    # Save the surface
    pygame.image.save(surface, '/home/user/Claude/tanjiro.png')
    print("Created sample Tanjiro sprite at /home/user/Claude/tanjiro.png")
    print("Replace this with your actual Tanjiro sprite image!")

    pygame.quit()


def create_sample_sprite_pil():
    """Create a sample sprite using PIL"""
    size = 32

    # Create image
    img = Image.new('RGB', (size, size), color=(50, 100, 50))
    draw = ImageDraw.Draw(img)

    # Draw simple character
    # Head
    draw.ellipse([size//2-8, size//3-8, size//2+8, size//3+8], fill=(230, 200, 180))

    # Eyes
    draw.ellipse([size//2-4, size//3-2, size//2-2, size//3], fill=(0, 0, 0))
    draw.ellipse([size//2+2, size//3-2, size//2+4, size//3], fill=(0, 0, 0))

    # Body
    draw.rectangle([size//2-6, size//3+8, size//2+6, size//3+22], fill=(30, 80, 30))

    # Save
    img.save('/home/user/Claude/tanjiro.png')
    print("Created sample Tanjiro sprite at /home/user/Claude/tanjiro.png")
    print("Replace this with your actual Tanjiro sprite image!")


if __name__ == '__main__':
    try:
        create_sample_sprite_pygame()
    except Exception as e:
        print(f"Error creating sprite with pygame: {e}")
        if HAS_PIL:
            try:
                create_sample_sprite_pil()
            except Exception as e2:
                print(f"Error creating sprite with PIL: {e2}")
                print("Could not create sample sprite. Please provide your own tanjiro.png")
