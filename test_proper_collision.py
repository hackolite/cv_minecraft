#!/usr/bin/env python3
"""
Proper test for collision position fix using appropriate coordinates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH

def test_proper_collision():
    """Test collision with proper coordinates to avoid Y/Z overlap."""
    print("🧪 TEST: Proper Collision Position Fix")
    print("=" * 60)
    
    # Create a block at (51, 0, 0) to avoid Y/Z overlap with player at y=2, z=0
    world_blocks = {(51, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    print(f"📏 Player width: {PLAYER_WIDTH}")
    print(f"📏 Player half-width: {PLAYER_WIDTH/2}")
    print(f"🧱 Block at position: (51, 0, 0)")
    print(f"🧱 Block occupies: x=[51.0, 52.0), y=[0.0, 1.0), z=[0.0, 1.0)")
    print()
    
    # Test coordinates: player at same Y as block to ensure collision detection works
    y = 0.5  # Player feet at y=0.5, head at y=1.5 - overlaps with block at y=[0,1)
    z = 0.5  # Player at z=[0,1) - overlaps with block's z=[0,1)
    clearance = 0.0
    
    print(f"Player Y position: {y} (feet at {y}, head at {y+1.0})")
    print(f"Player Z position: {z} (spans [{z-0.5:.1f}, {z+0.5:.1f}])")
    print(f"Block Y range: [0.0, 1.0) - Y overlap exists ✓")
    print(f"Block Z range: [0.0, 1.0) - Z overlap exists ✓")
    print()
    
    # Test moving right (towards block at x=51)
    print("➡️  Testing movement to the right (towards block at x=51)")
    old_x = 49.0
    new_x = 53.0
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    expected_x = 51.0 - PLAYER_WIDTH/2  # Should be 50.5
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Expected position: x={expected_x}")
    print(f"   ✅ PASS" if abs(safe_x - expected_x) < 0.001 else f"   ❌ FAIL")
    print()
    
    # Test moving left (away from block at x=51)
    print("⬅️  Testing movement to the left (away from block at x=51)")
    old_x = 53.0
    new_x = 49.0
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    expected_x_current = 51.0 + 1.0 + PLAYER_WIDTH/2  # Current: 52.5
    expected_x_desired = 51.0 + PLAYER_WIDTH/2  # Desired: 51.5
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Current algorithm expects: x={expected_x_current}")
    print(f"   User wants: x={expected_x_desired}")
    
    if abs(safe_x - expected_x_desired) < 0.001:
        print(f"   ✅ SUCCESS: Algorithm gives desired result!")
    else:
        print(f"   ❌ ISSUE: Algorithm gives {safe_x}, not {expected_x_desired}")
    
    # Verify no collision at the desired position
    test_pos = (expected_x_desired, y, z)
    collision = manager.check_collision(test_pos, "player1")
    print(f"   Collision check at desired position ({expected_x_desired}, {y}, {z}): {collision}")
    
    if not collision:
        print(f"   ✅ Desired position is collision-free")
    else:
        print(f"   ❌ WARNING: Desired position would cause collision")
    
    print()
    print("🎯 CONCLUSION:")
    if abs(safe_x - expected_x_desired) < 0.001 and not collision:
        print("✅ Fix is working correctly!")
    else:
        print("❌ Fix needs more work")

if __name__ == "__main__":
    test_proper_collision()