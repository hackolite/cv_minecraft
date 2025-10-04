#!/usr/bin/env python3
"""
Test the unified collision API to ensure all functions work properly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from minecraft_physics import (
    unified_check_collision, unified_check_player_collision,
    unified_get_player_collision_info, unified_resolve_collision,
    unified_find_ground_level, UnifiedCollisionManager,
    SimplePhysicsManager
)
from protocol import PlayerState

def test_unified_collision_api():
    """Test the unified collision API functions."""
    print("🎮 Testing Unified Collision API\n")
    
    # Create test world
    world = {
        (0, 0, 0): 'stone',
        (1, 0, 1): 'stone',
        (0, 1, 0): 'stone',
    }
    
    # Create test players
    players = [
        PlayerState("player1", (5.0, 1.0, 5.0), (0, 0), "Test1"),
        PlayerState("player2", (6.0, 1.0, 6.0), (0, 0), "Test2"),
    ]
    
    print("🧪 Testing unified_check_collision...")
    # Test block collision
    assert unified_check_collision((0.5, 0.5, 0.5), world), "Should collide with block"
    assert not unified_check_collision((0.5, 2.0, 0.5), world), "Should not collide in air"
    
    # Test with players
    assert unified_check_collision((5.1, 1.0, 5.1), world, players), "Should collide with player"
    assert not unified_check_collision((10.0, 1.0, 10.0), world, players), "Should not collide away from players"
    print("   ✅ unified_check_collision works correctly")
    
    print("\n🧪 Testing unified_check_player_collision...")
    assert unified_check_player_collision((5.1, 1.0, 5.1), players), "Should collide with player"
    assert not unified_check_player_collision((10.0, 1.0, 10.0), players), "Should not collide away from players"
    print("   ✅ unified_check_player_collision works correctly")
    
    print("\n🧪 Testing unified_get_player_collision_info...")
    collision_info = unified_get_player_collision_info((5.1, 1.0, 5.1), players)
    assert collision_info['collision'], "Should detect collision"
    print("   ✅ unified_get_player_collision_info works correctly")
    
    print("\n🧪 Testing unified_resolve_collision...")
    old_pos = (0.5, 2.0, 0.5)
    new_pos = (0.5, 0.5, 0.5)  # Trying to move into block
    safe_pos, collision_info = unified_resolve_collision(old_pos, new_pos, world)
    assert safe_pos[1] >= 1.0, "Should resolve to safe position"
    assert collision_info['y'], "Should detect Y collision"
    print("   ✅ unified_resolve_collision works correctly")
    
    print("\n🧪 Testing unified_find_ground_level...")
    ground_level = unified_find_ground_level(0.0, 0.0, world)
    assert ground_level == 2.0, f"Expected ground level 2.0, got {ground_level}"
    print("   ✅ unified_find_ground_level works correctly")
    
    print("\n🧪 Testing UnifiedCollisionManager directly...")
    manager = UnifiedCollisionManager(world)
    manager.set_other_players(players)
    
    # Test direct collision check
    assert manager.check_collision((5.1, 1.0, 5.1)), "Should collide with player"
    assert manager.check_block_collision((0.5, 0.5, 0.5)), "Should collide with block"
    assert not manager.check_collision((10.0, 1.0, 10.0)), "Should not collide in empty space"
    print("   ✅ UnifiedCollisionManager works correctly")
    
    print("\n🧪 Testing SimplePhysicsManager...")
    physics = SimplePhysicsManager(manager)
    
    # Test gravity application
    new_vy = physics.apply_gravity(0.0, 0.05, False)  # 50ms timestep, not on ground
    assert new_vy < 0, "Gravity should make velocity negative"
    
    # Test position update
    position = (10.0, 5.0, 10.0)  # In air
    velocity = (0.0, 0.0, 0.0)
    new_pos, new_vel, on_ground = physics.update_position(position, velocity, 0.05, False, False)
    assert new_pos[1] < position[1], "Should fall due to gravity"
    print("   ✅ SimplePhysicsManager works correctly")
    
    return True

if __name__ == "__main__":
    try:
        success = test_unified_collision_api()
        
        if success:
            print("\n🎉 ALL UNIFIED API TESTS PASSED!")
            print("✅ All unified collision functions working correctly")
            print("✅ UnifiedCollisionManager functioning properly")
            print("✅ SimplePhysicsManager working as expected")
            print("✅ Clean API provides all needed functionality")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)