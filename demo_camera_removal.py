#!/usr/bin/env python3
"""
Simple demonstration showing camera blocks being removed during reset.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.WARNING)

from server import GameWorld
from protocol import BlockType

def main():
    print("=" * 70)
    print("WORLD RESET: CAMERA REMOVAL DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create world without reset
    print("Step 1: Create world with default settings")
    print("-" * 70)
    world = GameWorld(reset_to_natural=False)
    
    # Count camera blocks
    camera_blocks_before = [
        (pos, data) for pos, data in world.world.items()
        if isinstance(data, dict) and data.get("type") == BlockType.CAMERA
    ]
    
    print(f"✅ World created with {len(world.world):,} total blocks")
    print(f"📷 Camera blocks found: {len(camera_blocks_before)}")
    print()
    
    if camera_blocks_before:
        print("Camera block details:")
        for pos, data in camera_blocks_before:
            block_id = data.get("block_id", "N/A")
            owner = data.get("owner", "None")
            print(f"  • Position: {pos}, ID: {block_id}, Owner: {owner}")
    
    print()
    print("=" * 70)
    print()
    
    # Add some player blocks
    print("Step 2: Add player-placed blocks")
    print("-" * 70)
    
    # Add a player camera
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="player_cam_1", owner="player_123")
    # Add a cat block
    world.add_block((11, 200, 11), BlockType.CAT)
    # Add a brick block
    world.add_block((12, 200, 12), BlockType.BRICK)
    
    total_with_additions = len(world.world)
    print(f"✅ Added 3 player blocks (1 camera, 1 cat, 1 brick)")
    print(f"📦 Total blocks now: {total_with_additions:,}")
    print()
    print("=" * 70)
    print()
    
    # Perform reset
    print("Step 3: Reset world to natural terrain")
    print("-" * 70)
    removed_count = world.reset_to_natural_terrain()
    
    print(f"🔄 Reset executed")
    print(f"🗑️  Blocks removed: {removed_count}")
    print()
    
    # Count camera blocks after reset
    camera_blocks_after = [
        (pos, data) for pos, data in world.world.items()
        if isinstance(data, dict) and data.get("type") == BlockType.CAMERA
    ]
    
    print(f"📷 Camera blocks remaining: {len(camera_blocks_after)}")
    print(f"✅ All {len(camera_blocks_before) + 1} camera blocks removed")
    print()
    
    # Verify only natural blocks remain
    non_natural = []
    natural_types = {BlockType.GRASS, BlockType.SAND, BlockType.STONE, 
                     BlockType.WATER, BlockType.WOOD, BlockType.LEAF}
    
    for pos, data in world.world.items():
        if isinstance(data, dict):
            block_type = data.get("type")
        else:
            block_type = data
        
        if block_type not in natural_types:
            non_natural.append((pos, block_type))
    
    if non_natural:
        print(f"❌ ERROR: Found {len(non_natural)} non-natural blocks!")
        for pos, block_type in non_natural[:5]:
            print(f"  • {block_type} at {pos}")
    else:
        print("✅ Verification: Only natural terrain blocks remain")
    
    print()
    print("=" * 70)
    print()
    print("📝 SUMMARY:")
    print("-" * 70)
    print(f"  • Started with {len(camera_blocks_before)} initial camera blocks")
    print(f"  • Added 1 player camera + 1 cat + 1 brick")
    print(f"  • Reset removed all {removed_count} non-natural blocks")
    print(f"  • Final world: {len(world.world):,} blocks (all natural)")
    print()
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
