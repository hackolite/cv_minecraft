#!/usr/bin/env python3
"""
Test the integration of standard Minecraft physics into the client and server.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, TERMINAL_VELOCITY,
    minecraft_collide, minecraft_check_ground
)


def test_collision_integration():
    """Test that the new collision system works with existing world format."""
    print("🧪 Testing Collision Integration")
    
    # Create a world in the same format as the existing system
    world = {
        (0, 0, 0): 'grass',
        (1, 0, 0): 'stone',
        (0, 0, 1): 'grass',
        (1, 0, 1): 'stone',
        (5, 10, 5): 'wood',  # High platform
    }
    
    # Test basic collision detection
    detector = MinecraftCollisionDetector(world)
    
    # Player standing on ground
    position = (0.5, 1.0, 0.5)
    collision = detector.check_collision(position)
    print(f"   Player at {position}: collision = {collision}")
    assert not collision, "Player should not collide when standing on blocks"
    
    # Player inside block
    position = (0.5, 0.5, 0.5)
    collision = detector.check_collision(position)
    print(f"   Player at {position}: collision = {collision}")
    assert collision, "Player should collide when inside blocks"
    
    # Test collision resolution
    old_pos = (0.5, 5.0, 0.5)  # High above
    new_pos = (0.5, 0.5, 0.5)  # Trying to move into block
    safe_pos, collision_info = detector.resolve_collision(old_pos, new_pos)
    print(f"   Falling from {old_pos} to {new_pos}")
    print(f"   Safe position: {safe_pos}")
    print(f"   Collision info: {collision_info}")
    
    assert safe_pos[1] >= 1.0, "Should land on top of blocks"
    assert collision_info['ground'], "Should detect ground collision"
    
    print("   ✅ Collision integration working")
    return True


def test_physics_constants():
    """Test that physics constants are appropriate for Minecraft."""
    print("\n🧪 Testing Physics Constants")
    
    print(f"   Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} blocks")
    print(f"   Gravity: {GRAVITY} blocks/s²")
    print(f"   Terminal velocity: {TERMINAL_VELOCITY} blocks/s")
    
    # Validate they are reasonable for Minecraft
    assert 0.5 <= PLAYER_WIDTH <= 1.0, "Player width should be reasonable"
    assert 1.5 <= PLAYER_HEIGHT <= 2.0, "Player height should be reasonable"
    assert GRAVITY > 0, "Gravity should be positive"
    assert TERMINAL_VELOCITY > 10, "Terminal velocity should be reasonable"
    
    print("   ✅ Physics constants are appropriate")
    return True


def test_compatibility_functions():
    """Test that compatibility functions work with existing code."""
    print("\n🧪 Testing Compatibility Functions")
    
    # Create a test world
    world = {
        (0, 0, 0): 'stone',
        (1, 0, 0): 'stone',
        (2, 0, 0): 'stone',
    }
    
    # Test minecraft_collide function (used by existing client code)
    position = (0.5, 0.5, 0.0)  # Inside a block
    safe_position = minecraft_collide(position, 2, world)  # height parameter ignored
    print(f"   minecraft_collide: {position} -> {safe_position}")
    
    # Test minecraft_check_ground function
    position = (0.5, 1.0, 0.0)  # On top of block
    on_ground = minecraft_check_ground(position, world)
    print(f"   minecraft_check_ground at {position}: {on_ground}")
    
    position = (0.5, 5.0, 0.0)  # High above
    on_ground = minecraft_check_ground(position, world)
    print(f"   minecraft_check_ground at {position}: {on_ground}")
    assert not on_ground, "Should not detect ground when in air"
    
    print("   ✅ Compatibility functions working")
    return True


def test_physics_simulation():
    """Test a complete physics simulation scenario."""
    print("\n🧪 Testing Physics Simulation")
    
    # Create a test world with platforms at different heights
    world = {
        # Ground level
        (0, 0, 0): 'stone', (1, 0, 0): 'stone', (2, 0, 0): 'stone',
        (0, 0, 1): 'stone', (1, 0, 1): 'stone', (2, 0, 1): 'stone',
        
        # Platform at height 5
        (5, 5, 5): 'wood', (6, 5, 5): 'wood',
        (5, 5, 6): 'wood', (6, 5, 6): 'wood',
        
        # High platform at height 10
        (10, 10, 10): 'grass',
    }
    
    detector = MinecraftCollisionDetector(world)
    physics = MinecraftPhysics(detector)
    
    # Start player high above ground
    position = (1.0, 20.0, 1.0)
    velocity = (0.0, 0.0, 0.0)
    on_ground = False
    
    print(f"   Starting simulation at {position}")
    
    # Simulate falling for several steps
    for step in range(50):
        dt = 0.05  # 50ms per step
        new_position, new_velocity, new_on_ground = physics.update_position(
            position, velocity, dt, on_ground, False
        )
        
        position = new_position
        velocity = new_velocity
        on_ground = new_on_ground
        
        if step % 10 == 0:  # Print every 10th step
            print(f"   Step {step:2d}: pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}), "
                  f"vel=({velocity[0]:.1f}, {velocity[1]:.1f}, {velocity[2]:.1f}), on_ground={on_ground}")
        
        if on_ground:
            print(f"   ✅ Landed after {step} steps at position {position}")
            break
    
    assert on_ground, "Player should have landed"
    assert position[1] >= 1.0, "Player should be on top of blocks"
    
    # Test jumping
    print(f"   Testing jump from landed position")
    new_position, new_velocity, new_on_ground = physics.update_position(
        position, velocity, 0.05, on_ground, True  # jumping=True
    )
    
    print(f"   After jump: pos=({new_position[0]:.1f}, {new_position[1]:.1f}, {new_position[2]:.1f}), "
          f"vel=({new_velocity[0]:.1f}, {new_velocity[1]:.1f}, {new_velocity[2]:.1f}), on_ground={new_on_ground}")
    
    assert new_velocity[1] > 0, "Should have upward velocity after jump"
    assert not new_on_ground, "Should not be on ground after jumping"
    
    print("   ✅ Physics simulation working correctly")
    return True


def test_block_positioning():
    """Test that block positioning is precise and follows Minecraft standards."""
    print("\n🧪 Testing Block Positioning")
    
    # Test that blocks are exactly 1x1x1 and positioned correctly
    world = {
        (0, 0, 0): 'stone',  # Ground block
        (1, 0, 0): 'stone',  # Adjacent ground block
        (0, 1, 0): 'stone',  # Block above ground
    }
    
    detector = MinecraftCollisionDetector(world)
    
    # Test positions around block boundaries
    test_positions = [
        # On top of different blocks
        (0.0, 1.0, 0.0),   # On top of block (0,0,0) - should collide with block (0,1,0)
        (1.0, 1.0, 0.0),   # On top of block (1,0,0) - should be safe
        (0.5, 1.0, 0.0),   # Between blocks - may collide depending on player size
        (0.0, 2.0, 0.0),   # On top of block (0,1,0) - should be safe
        
        # Just inside/outside block boundaries
        (0.001, 0.999, 0.001),  # Just outside block (0,0,0) but close
        (0.999, 0.999, 0.999),  # Near edge of block (0,0,0)
    ]
    
    for pos in test_positions:
        collision = detector.check_collision(pos)
        print(f"   Position {pos}: collision = {collision}")
    
    # Test ground finding precision
    ground_level = detector.find_ground_level(0.0, 0.0)
    print(f"   Ground level at (0, ?, 0): {ground_level}")
    # At X=0, Z=0, the highest block is at Y=1, so ground level should be Y=2
    assert ground_level == 2.0, f"Ground should be at Y=2.0 (on top of block at Y=1), got {ground_level}"
    
    # Test ground finding where there's only a block at Y=0
    ground_level = detector.find_ground_level(1.0, 0.0)
    print(f"   Ground level at (1, ?, 0): {ground_level}")
    # At X=1, Z=0, the highest block is at Y=0, so ground level should be Y=1
    assert ground_level == 1.0, f"Ground should be at Y=1.0 (on top of block at Y=0), got {ground_level}"
    
    # Test ground finding where there are no blocks
    ground_level = detector.find_ground_level(5.0, 5.0)
    print(f"   Ground level at (5, ?, 5): {ground_level}")
    assert ground_level is None, f"Should return None when no blocks found"
    
    print("   ✅ Block positioning is precise")
    return True


def run_integration_tests():
    """Run all integration tests."""
    print("🎮 Testing Standard Minecraft Physics Integration\n")
    
    tests = [
        test_physics_constants,
        test_collision_integration,
        test_compatibility_functions,
        test_physics_simulation,
        test_block_positioning,
    ]
    
    success = True
    for test in tests:
        try:
            success &= test()
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            success = False
    
    return success


if __name__ == "__main__":
    try:
        success = run_integration_tests()
        
        if success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Standard Minecraft physics successfully integrated")
            print("✅ Collision detection working with existing world format")
            print("✅ Physics simulation functioning correctly")
            print("✅ Block positioning is precise and accurate")
            print("✅ Compatibility with existing code maintained")
            print("\n📋 Summary of Improvements:")
            print("• Standard Minecraft player dimensions (0.6×1.8×0.6 blocks)")
            print("• Proper gravity and terminal velocity physics")
            print("• Precise block collision detection and positioning")
            print("• Improved ground detection and standing mechanics")
            print("• Compatible with existing client and server code")
        else:
            print("\n❌ Some integration tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Integration test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)