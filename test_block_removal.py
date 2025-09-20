#!/usr/bin/env python3
"""
Test to verify that block removal and AIR block handling works correctly.
This simulates the scenario where a player destroys a block and it becomes AIR.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager
from protocol import BlockType

def test_block_removal_scenario():
    """Test scenario where blocks are removed and become AIR."""
    print("🔨 TESTING BLOCK REMOVAL SCENARIO")
    print("=" * 60)
    
    # Create initial world with a single solid block to avoid confusion
    world = {
        (10, 10, 10): BlockType.STONE,
    }
    
    manager = UnifiedCollisionManager(world)
    player_position = (10.0, 10.5, 10.0)  # Inside stone block
    
    print("🏗️  Initial world state:")
    print(f"   Stone at (10,10,10): {world.get((10,10,10))}")
    
    # Test collision with original block
    collision = manager.check_block_collision(player_position)
    print(f"\n🧪 Player at (10.0, 10.5, 10.0) with stone block:")
    print(f"   Collision detected: {collision}")
    assert collision, "Should collide with stone block"
    print("   ✅ Stone block correctly blocks player")
    
    # Simulate removing the stone block (it becomes AIR)
    world[(10, 10, 10)] = BlockType.AIR
    manager.update_world(world)
    
    print(f"\n🔨 After removing stone block (becomes AIR):")
    print(f"   AIR at (10,10,10): {world.get((10,10,10))}")
    
    # Test that player can now move through the AIR block
    collision_after_removal = manager.check_block_collision(player_position)
    print(f"\n🧪 Player at same position after stone removal:")
    print(f"   Collision detected: {collision_after_removal}")
    assert not collision_after_removal, "Should NOT collide with AIR block"
    print("   ✅ AIR block correctly allows player passage")
    
    # Test with a separate world with other solid blocks to ensure they remain solid
    world_with_other_blocks = {
        (10, 10, 10): BlockType.AIR,   # Removed block
        (15, 10, 15): BlockType.WOOD,  # Separate wood block
    }
    manager2 = UnifiedCollisionManager(world_with_other_blocks)
    
    # Test that AIR block still allows passage
    collision_air = manager2.check_block_collision((10.0, 10.5, 10.0))
    print(f"\n🧪 Player in AIR block in new world:")
    print(f"   Collision detected: {collision_air}")
    assert not collision_air, "Should NOT collide with AIR block"
    print("   ✅ AIR block allows passage in new world")
    
    # Test that wood block is still solid
    collision_wood = manager2.check_block_collision((15.0, 10.5, 15.0))
    print(f"\n🧪 Player in wood block position:")
    print(f"   Collision detected: {collision_wood}")
    assert collision_wood, "Should still collide with wood block"
    print("   ✅ Wood block remains solid")
    
    return True

def test_mixed_block_types():
    """Test that different block types behave correctly in the same world."""
    print(f"\n{'🌍 MIXED BLOCK TYPES TEST' :=^60}")
    
    # Create world with mixed block types with enough spacing to avoid overlap
    world = {
        (5, 10, 5): BlockType.GRASS,
        (8, 10, 5): BlockType.AIR,      # Removed block (isolated)
        (11, 10, 5): BlockType.STONE,
        (14, 10, 5): BlockType.WATER,
        (17, 10, 5): BlockType.AIR,     # Another removed block (isolated)
        (20, 10, 5): BlockType.WOOD,
    }
    
    manager = UnifiedCollisionManager(world)
    
    test_cases = [
        # Solid blocks should cause collision
        ((5.0, 10.5, 5.0), True, "GRASS", "solid"),
        ((11.0, 10.5, 5.0), True, "STONE", "solid"),
        ((14.0, 10.5, 5.0), True, "WATER", "solid"),
        ((20.0, 10.5, 5.0), True, "WOOD", "solid"),
        # AIR blocks should NOT cause collision (isolated from other blocks)
        ((8.0, 10.5, 5.0), False, "AIR", "non-solid"),
        ((17.0, 10.5, 5.0), False, "AIR", "non-solid"),
    ]
    
    all_correct = True
    for position, expected_collision, block_name, expected_behavior in test_cases:
        actual_collision = manager.check_block_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {block_name} block ({expected_behavior}): collision = {actual_collision}")
        
        if actual_collision != expected_collision:
            all_correct = False
            print(f"      ERROR: Expected {expected_collision}, got {actual_collision}")
            
            # Debug the specific failing case
            print(f"      DEBUG: Player position {position}")
            print(f"      DEBUG: Block at that position: {world.get((int(position[0]), int(position[1]), int(position[2])))}")
            
            # Check what voxels are being tested
            px, py, pz = position
            largeur = 1.0
            hauteur = 1.0
            profondeur = 1.0
            
            import math
            xmin = int(math.floor(px - largeur / 2))
            xmax = int(math.floor(px + largeur / 2))
            ymin = int(math.floor(py))
            ymax = int(math.floor(py + hauteur))
            zmin = int(math.floor(pz - profondeur / 2))
            zmax = int(math.floor(pz + profondeur / 2))
            
            print(f"      DEBUG: Voxel bounds X:{xmin}-{xmax}, Y:{ymin}-{ymax}, Z:{zmin}-{zmax}")
            
            # Check each voxel
            for x in range(xmin, xmax + 1):
                for y in range(ymin, ymax + 1):
                    for z in range(zmin, zmax + 1):
                        if (x, y, z) in world:
                            block_type = world[(x, y, z)]
                            print(f"      DEBUG: Voxel ({x},{y},{z}): {block_type}")
    
    return all_correct

if __name__ == "__main__":
    print("🎯 Testing Block Removal and AIR Block Handling")
    print("   (Ensuring destroyed blocks become passable)")
    
    success1 = test_block_removal_scenario()
    success2 = test_mixed_block_types()
    
    overall_success = success1 and success2
    
    print(f"\n{'=' * 60}")
    print("🎯 BLOCK REMOVAL TEST CONCLUSION")
    print("=" * 60)
    
    if overall_success:
        print("🎉 SUCCESS: Block removal and AIR handling works perfectly!")
        print("✅ Destroyed blocks become AIR and allow player passage")
        print("✅ All other blocks remain solid as expected")
        print("✅ Mixed block type scenarios work correctly")
    else:
        print("❌ FAILURE: Block removal or AIR handling has issues!")
        print("🔧 Need to fix block removal behavior")
    
    sys.exit(0 if overall_success else 1)