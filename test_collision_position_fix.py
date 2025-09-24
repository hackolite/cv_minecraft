#!/usr/bin/env python3
"""
Test for collision position fix.
Tests the specific issue mentioned: collision position should be at block_x + 0.5, not block_x + 1.5
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH

def test_collision_position_fix():
    """Test that collision positions are correctly calculated."""
    print("🧪 TEST: Collision Position Fix")
    print("=" * 60)
    
    # Create collision manager with a test world
    world_blocks = {(51, 10, 10): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    print(f"📏 Player width: {PLAYER_WIDTH}")
    print(f"📏 Player half-width: {PLAYER_WIDTH/2}")
    print(f"🧱 Block at position: (51, 10, 10)")
    print()
    
    # Test moving right (should stop at 51 - 0.5 = 50.5)
    print("➡️  Testing movement to the right (towards block at x=51)")
    old_x = 49.0
    new_x = 52.0  # Try to move past the block
    y = 10.5
    z = 10.0
    clearance = 0.0
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    expected_x = 51.0 - PLAYER_WIDTH/2  # Should be 50.5
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Expected position: x={expected_x}")
    print(f"   ✅ PASS" if abs(safe_x - expected_x) < 0.001 else f"   ❌ FAIL")
    print()
    
    # Test moving left (should stop at 51 + 0.5 = 51.5, NOT 52.5)
    print("⬅️  Testing movement to the left (away from block at x=51)")
    old_x = 53.0
    new_x = 50.0  # Try to move past the block
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    expected_x = 51.0 + 1.0 + PLAYER_WIDTH/2  # Should be 51 + 1 + 0.5 = 52.5 (current behavior)
    correct_expected_x = 51.0 + PLAYER_WIDTH/2  # Should be 51 + 0.5 = 51.5 (desired behavior)
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Current expected position: x={expected_x}")
    print(f"   Correct expected position: x={correct_expected_x}")
    print(f"   Current behavior: {'PASS' if abs(safe_x - expected_x) < 0.001 else 'FAIL'}")
    print(f"   Desired behavior: {'PASS' if abs(safe_x - correct_expected_x) < 0.001 else 'FAIL (THIS IS THE BUG)'}")
    print()
    
    # Test same for Z axis
    print("🔄 Testing same issue for Z axis")
    print("=" * 40)
    
    # Add a block at position (10, 10, 51)
    world_blocks[(10, 10, 51)] = "stone"
    
    # Test moving forward (should stop at 51 - 0.5 = 50.5)
    print("⬆️  Testing movement forward (towards block at z=51)")
    x = 10.0
    old_z = 49.0
    new_z = 52.0
    
    safe_z = manager._snap_to_safe_z_position(x, old_z, new_z, y, "player1", clearance)
    expected_z = 51.0 - PLAYER_WIDTH/2  # Should be 50.5
    
    print(f"   Old position: z={old_z}")
    print(f"   Intended new position: z={new_z}")
    print(f"   Safe position: z={safe_z}")
    print(f"   Expected position: z={expected_z}")
    print(f"   ✅ PASS" if abs(safe_z - expected_z) < 0.001 else f"   ❌ FAIL")
    print()
    
    # Test moving backward (should stop at 51 + 0.5 = 51.5, NOT 52.5)
    print("⬇️  Testing movement backward (away from block at z=51)")
    old_z = 53.0
    new_z = 50.0
    
    safe_z = manager._snap_to_safe_z_position(x, old_z, new_z, y, "player1", clearance)
    expected_z = 51.0 + 1.0 + PLAYER_WIDTH/2  # Should be 52.5 (current behavior)
    correct_expected_z = 51.0 + PLAYER_WIDTH/2  # Should be 51.5 (desired behavior)
    
    print(f"   Old position: z={old_z}")
    print(f"   Intended new position: z={new_z}")
    print(f"   Safe position: z={safe_z}")
    print(f"   Current expected position: z={expected_z}")
    print(f"   Correct expected position: z={correct_expected_z}")
    print(f"   Current behavior: {'PASS' if abs(safe_z - expected_z) < 0.001 else 'FAIL'}")
    print(f"   Desired behavior: {'PASS' if abs(safe_z - correct_expected_z) < 0.001 else 'FAIL (THIS IS THE BUG)'}")
    print()
    
    print("🎯 SUMMARY:")
    print("The issue is in the collision resolution when moving left/backward.")
    print("Instead of stopping at block_edge + player_half_width,")
    print("the code currently stops at (block_position + 1) + player_half_width")
    print("This adds an extra 1.0 unit of distance, which is incorrect.")

if __name__ == "__main__":
    test_collision_position_fix()