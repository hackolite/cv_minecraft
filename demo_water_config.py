#!/usr/bin/env python3
"""
Demonstration of the water collision configuration.

This script shows how to control water collision behavior using the
WATER_COLLISION_ENABLED configuration option in server.py.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH
from server import create_block_data
from protocol import BlockType


def demo_water_config():
    """Demonstrate water collision configuration."""
    print("\n" + "="*70)
    print("💧 WATER COLLISION CONFIGURATION DEMO")
    print("="*70 + "\n")
    
    print("This demo shows how to configure water collision behavior:")
    print("- When WATER_COLLISION_ENABLED = True:  Players walk on water")
    print("- When WATER_COLLISION_ENABLED = False: Players can swim through water")
    print()
    
    # Create a test world with water
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            # Add stone ground at y=10
            world_blocks[(x, 10, z)] = create_block_data(BlockType.STONE)
    
    print("🌍 World setup:")
    print("   Stone ground at y=10")
    print("   Water at y=15")
    print()
    
    # Test 1: Water collision ENABLED (default)
    print("="*70)
    print("📋 Configuration 1: WATER_COLLISION_ENABLED = True (DEFAULT)")
    print("="*70)
    print()
    
    server.WATER_COLLISION_ENABLED = True
    
    # Add water with current config
    for x in range(60, 70):
        for z in range(60, 70):
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128)
    
    print("🏃 Scenario: Player falls from above toward water")
    print("   Initial position: (65, 20, 65) - above water")
    print("   Trying to move to: (65, 12, 65) - through water to ground")
    
    old_pos = (65.0, 20.0, 65.0)
    new_pos = (65.0, 12.0, 65.0)
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    print(f"\n✅ Result:")
    print(f"   Player position: y={safe_pos[1]}")
    print(f"   Y collision: {collision_info['y']}")
    print()
    if safe_pos[1] > new_pos[1]:
        print("   🚶 Player BLOCKED by water at y=15")
        print("   💡 Player walks on top of water surface")
    else:
        print("   🏊 Player PASSED through water")
        print("   💡 Player can swim through water")
    print()
    
    # Test 2: Water collision DISABLED
    print("="*70)
    print("📋 Configuration 2: WATER_COLLISION_ENABLED = False")
    print("="*70)
    print()
    
    server.WATER_COLLISION_ENABLED = False
    
    # Recreate water with new config
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            world_blocks[(x, 10, z)] = create_block_data(BlockType.STONE)
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128)
    
    print("🏃 Scenario: Player falls from above toward water")
    print("   Initial position: (65, 20, 65) - above water")
    print("   Trying to move to: (65, 12, 65) - through water to ground")
    
    old_pos = (65.0, 20.0, 65.0)
    new_pos = (65.0, 12.0, 65.0)
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    print(f"\n✅ Result:")
    print(f"   Player position: y={safe_pos[1]}")
    print(f"   Y collision: {collision_info['y']}")
    print()
    if safe_pos[1] > new_pos[1]:
        print("   🚶 Player BLOCKED by stone ground at y=10")
        print("   💡 Player passed through water and stopped at stone")
    else:
        print("   🏊 Player at target position")
    print()
    
    # Reset to default
    server.WATER_COLLISION_ENABLED = True
    
    # Summary
    print("="*70)
    print("📝 SUMMARY")
    print("="*70)
    print()
    print("To configure water collision in your server:")
    print()
    print("1. Open server.py")
    print("2. Find the WATER_COLLISION_ENABLED constant (around line 45)")
    print("3. Set it to:")
    print("   - WATER_COLLISION_ENABLED = True   # Walk on water (default)")
    print("   - WATER_COLLISION_ENABLED = False  # Swim through water")
    print()
    print("This is a simple configuration - just one boolean value!")
    print()


def main():
    """Run the demonstration."""
    try:
        demo_water_config()
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
