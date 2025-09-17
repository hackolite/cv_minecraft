#!/usr/bin/env python3
"""
Debug the height calculation issue in physics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer

def debug_height_finding():
    """Debug what blocks exist at a position and what the physics system finds."""
    print("🔍 Debugging Height Finding Issue\n")
    
    # Create a server instance
    server = MinecraftServer()
    
    # Check what blocks exist at position (10, *, 10)
    print("Blocks at x=10, z=10:")
    blocks_found = []
    for y in range(0, 30):
        pos = (10, y, 10)
        if pos in server.world.world:
            block_type = server.world.world[pos]
            blocks_found.append((y, block_type))
            print(f"   Y={y}: {block_type}")
    
    if not blocks_found:
        print("   No blocks found!")
        return
    
    print(f"\nHighest block found: Y={max(blocks_found)[0]}")
    
    # Now test the physics system's height finding logic
    new_x, new_z = 10, 10
    max_y = 0
    for check_y in range(256):
        check_pos = (int(new_x), check_y, int(new_z))
        if check_pos in server.world.world:
            max_y = max(max_y, check_y)
    
    print(f"Physics system found max_y: {max_y}")
    print(f"Player would be placed at: {max_y + 1}")
    
    # Let's check a wider range to see if there are blocks higher up
    print(f"\nChecking all blocks from Y=0 to Y=30 at x=10, z=10:")
    actual_max = 0
    for y in range(0, 31):
        pos = (10, y, 10)
        if pos in server.world.world:
            actual_max = y
            print(f"   Found block at Y={y}: {server.world.world[pos]}")
    
    print(f"Actual highest block: {actual_max}")
    return True

if __name__ == "__main__":
    debug_height_finding()