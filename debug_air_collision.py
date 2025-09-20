#!/usr/bin/env python3
"""
Debug script to understand AIR block collision issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager
from protocol import BlockType

def debug_air_collision():
    """Debug AIR block collision detection step by step."""
    print("🔍 DEBUGGING AIR BLOCK COLLISION")
    print("=" * 50)
    
    # Test with single AIR block
    world = {(6, 10, 5): BlockType.AIR}
    manager = UnifiedCollisionManager(world)
    position = (6.0, 10.5, 5.0)
    
    print(f"World: {world}")
    print(f"Player position: {position}")
    print(f"Block type at (6,10,5): {world.get((6,10,5))}")
    
    # Step through the collision detection manually
    px, py, pz = position
    largeur = 1.0  # PLAYER_WIDTH
    hauteur = 1.0  # PLAYER_HEIGHT
    profondeur = 1.0  # PLAYER_WIDTH
    
    import math
    xmin = int(math.floor(px - largeur / 2))
    xmax = int(math.floor(px + largeur / 2))
    ymin = int(math.floor(py))
    ymax = int(math.floor(py + hauteur))
    zmin = int(math.floor(pz - profondeur / 2))
    zmax = int(math.floor(pz + profondeur / 2))
    
    print(f"\nVoxel bounds:")
    print(f"  X: {xmin} to {xmax}")
    print(f"  Y: {ymin} to {ymax}")
    print(f"  Z: {zmin} to {zmax}")
    
    print(f"\nChecking voxels in range:")
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            for z in range(zmin, zmax + 1):
                print(f"  Checking voxel ({x}, {y}, {z})")
                if (x, y, z) in world:
                    block_type = world[(x, y, z)]
                    print(f"    Block found: {block_type}")
                    if block_type == "air":
                        print(f"    -> AIR block, skipping collision")
                    else:
                        print(f"    -> SOLID block, would cause collision")
                else:
                    print(f"    No block at this position")
    
    # Test the actual collision detection
    collision = manager.check_block_collision(position)
    print(f"\nFinal collision result: {collision}")
    
    return collision

if __name__ == "__main__":
    collision_result = debug_air_collision()
    print(f"\nDEBUG RESULT: AIR collision = {collision_result}")
    if collision_result:
        print("❌ PROBLEM: AIR block is causing collision!")
    else:
        print("✅ CORRECT: AIR block is not causing collision")