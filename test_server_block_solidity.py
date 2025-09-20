#!/usr/bin/env python3
"""
Test server-side block removal and solidity verification
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import GameWorld
from protocol import BlockType
from minecraft_physics import UnifiedCollisionManager

def test_server_block_solidity():
    """Test that server world generation creates solid blocks."""
    print("🎮 TESTING SERVER BLOCK SOLIDITY")
    print("=" * 50)
    
    # Create a game world
    world = GameWorld()
    
    # Test some generated blocks
    print("🏗️  Testing some generated blocks:")
    
    # Find some blocks in the generated world
    test_blocks = []
    count = 0
    for pos, block_type in world.world.items():
        if count < 5:  # Test first 5 blocks
            test_blocks.append((pos, block_type))
            count += 1
    
    manager = UnifiedCollisionManager(world.world)
    
    all_solid = True
    for pos, block_type in test_blocks:
        x, y, z = pos
        player_pos = (float(x) + 0.5, float(y) + 0.5, float(z) + 0.5)
        
        if block_type != BlockType.AIR:  # Only test non-AIR blocks
            collision = manager.check_block_collision(player_pos)
            status = "✅" if collision else "❌"
            print(f"   {status} {block_type.upper()} at {pos}: collision = {collision}")
            
            if not collision:
                all_solid = False
        else:
            # Test AIR blocks - they should NOT cause collision
            collision = manager.check_block_collision(player_pos)
            status = "✅" if not collision else "❌"
            print(f"   {status} AIR at {pos}: collision = {collision} (should be False)")
            
            if collision:
                all_solid = False
    
    return all_solid

def test_server_block_removal():
    """Test server block removal functionality."""
    print(f"\n{'🔨 TESTING SERVER BLOCK REMOVAL' :=^50}")
    
    world = GameWorld()
    
    # Add a test block
    test_pos = (50, 50, 50)
    world.add_block(test_pos, BlockType.WOOD)
    
    print(f"🏗️  Added wood block at {test_pos}")
    print(f"   Block type: {world.get_block(test_pos)}")
    
    # Test collision before removal
    manager = UnifiedCollisionManager(world.world)
    player_pos = (50.5, 50.5, 50.5)
    
    collision_before = manager.check_block_collision(player_pos)
    print(f"\n🧪 Before removal - collision: {collision_before}")
    assert collision_before, "Should collide with wood block"
    
    # Remove the block
    success = world.remove_block(test_pos)
    print(f"\n🔨 Block removal success: {success}")
    
    # Check what happened to the block
    remaining_block = world.get_block(test_pos)
    print(f"   Block after removal: {remaining_block}")
    
    # Update manager with new world state
    manager.update_world(world.world)
    
    # Test collision after removal
    collision_after = manager.check_block_collision(player_pos)
    print(f"\n🧪 After removal - collision: {collision_after}")
    
    # The block should be completely gone from the world, so no collision
    assert not collision_after, "Should NOT collide after block removal"
    
    print("   ✅ Block removal works correctly")
    
    return True

if __name__ == "__main__":
    print("🎯 Testing Server Block Solidity and Removal")
    
    success1 = test_server_block_solidity()
    success2 = test_server_block_removal()
    
    overall_success = success1 and success2
    
    print(f"\n{'=' * 50}")
    print("🎯 SERVER TEST CONCLUSION")
    print("=" * 50)
    
    if overall_success:
        print("🎉 SUCCESS: Server block handling works correctly!")
        print("✅ Generated blocks are solid")
        print("✅ Block removal works properly")
    else:
        print("❌ FAILURE: Server block handling has issues!")
    
    sys.exit(0 if overall_success else 1)