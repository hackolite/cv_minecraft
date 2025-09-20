#!/usr/bin/env python3
"""
Test to verify that all generated blocks are solid for collision detection.
This test checks that all block types (grass, stone, wood, sand, water, etc.) 
behave as solid blocks for collision purposes, and that AIR blocks are NOT solid.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager
from protocol import BlockType

def test_all_block_types_are_solid():
    """Test that all block types are treated as solid for collision detection."""
    print("🧱 TESTING BLOCK SOLIDITY - All Generated Blocks")
    print("=" * 60)
    
    # Test all different block types that should be solid
    solid_block_types = [
        BlockType.GRASS,
        BlockType.STONE, 
        BlockType.WOOD,
        BlockType.SAND,
        BlockType.WATER,  # This is the critical one to test
        BlockType.LEAF,
        BlockType.BRICK
    ]
    
    test_position = (10, 10, 10)
    player_test_position = (10.0, 10.5, 10.0)  # Player inside the block
    
    all_solid = True
    
    for block_type in solid_block_types:
        print(f"\n🧪 Testing {block_type.upper()} block solidity:")
        
        # Create world with only this block type
        world = {test_position: block_type}
        manager = UnifiedCollisionManager(world)
        
        # Test if player collides with this block type
        collision_detected = manager.check_block_collision(player_test_position)
        
        if collision_detected:
            print(f"   ✅ {block_type.upper()} is SOLID - collision detected")
        else:
            print(f"   ❌ {block_type.upper()} is NOT SOLID - no collision detected")
            all_solid = False
    
    print(f"\n{'=' * 60}")
    print("📊 SOLID BLOCK TEST RESULTS")
    print("=" * 60)
    
    if all_solid:
        print("🎉 ALL SOLID BLOCK TYPES ARE PROPERLY SOLID!")
        print("✅ All generated blocks properly block player movement")
    else:
        print("❌ SOME SOLID BLOCKS ARE NOT WORKING!")
        print("❌ Players may be able to pass through certain block types")
        
    return all_solid

def test_air_blocks_are_not_solid():
    """Test that AIR blocks are NOT solid (important for removed blocks)."""
    print(f"\n{'🌬️  AIR BLOCK TEST' :=^60}")
    
    # Test with no blocks (empty space)
    world_empty = {}
    manager_empty = UnifiedCollisionManager(world_empty)
    
    player_test_position = (10.0, 10.5, 10.0)
    collision_empty = manager_empty.check_block_collision(player_test_position)
    
    print(f"   🧪 Testing empty space: collision = {collision_empty}")
    
    if not collision_empty:
        print("   ✅ Empty space is NOT solid - correct behavior")
        air_works = True
    else:
        print("   ❌ Empty space is solid - incorrect behavior")
        air_works = False
    
    # Test with AIR block explicitly (removed block)
    world_with_air = {(10, 10, 10): BlockType.AIR}
    manager_air = UnifiedCollisionManager(world_with_air)
    
    collision_air = manager_air.check_block_collision(player_test_position)
    
    print(f"   🧪 Testing AIR block: collision = {collision_air}")
    
    # CRITICAL: AIR blocks should NOT cause collision
    if not collision_air:
        print("   ✅ AIR block is NOT solid - correct behavior") 
        air_explicit_works = True
    else:
        print("   ❌ AIR block is solid - WRONG! Players should pass through AIR")
        air_explicit_works = False
    
    return air_works and air_explicit_works

def test_water_block_specifically():
    """Specifically test water block behavior since it's often treated differently."""
    print(f"\n{'🌊 WATER BLOCK SPECIFIC TEST' :=^60}")
    
    # Create a world with water blocks
    world = {
        (10, 10, 10): BlockType.WATER,
        (10, 11, 10): BlockType.WATER, 
        (10, 12, 10): BlockType.WATER,
    }
    
    manager = UnifiedCollisionManager(world)
    
    test_cases = [
        # Player positions that should collide with water
        ((10.0, 10.5, 10.0), True, "Player center in water block"),
        ((10.0, 11.5, 10.0), True, "Player in middle water block"),
        ((10.0, 12.5, 10.0), True, "Player in top water block"),
        # Player positions that should not collide
        ((10.0, 13.5, 10.0), False, "Player above water"),
        ((11.5, 10.5, 10.0), False, "Player next to water (far enough)"),
        ((10.0, 8.5, 10.0), False, "Player below water (far enough)"),
    ]
    
    water_is_solid = True
    for position, expected_collision, description in test_cases:
        actual_collision = manager.check_block_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {description}: collision = {actual_collision}")
        
        if actual_collision != expected_collision:
            water_is_solid = False
    
    return water_is_solid

if __name__ == "__main__":
    print("🎯 Vérification que tous les blocs générés sont solides")
    print("   (Verification that all generated blocks are solid)")
    
    success1 = test_all_block_types_are_solid()
    success2 = test_air_blocks_are_not_solid() 
    success3 = test_water_block_specifically()
    
    overall_success = success1 and success2 and success3
    
    print(f"\n{'=' * 60}")
    print("🎯 FINAL CONCLUSION")
    print("=" * 60)
    
    if overall_success:
        print("🎉 SUCCESS: All block solidity rules are correct!")
        print("✅ Solid blocks are solid, AIR blocks are not solid")
        print("✅ Collision detection works correctly for all block types")
    else:
        print("❌ FAILURE: Block solidity rules are incorrect!")
        print("🔧 Action needed to fix block solidity behavior")
    
    sys.exit(0 if overall_success else 1)