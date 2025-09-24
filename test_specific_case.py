#!/usr/bin/env python3
"""
Test for the specific case mentioned in the problem statement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH

def test_specific_case():
    """Test the specific case from the problem statement."""
    print("🧪 TEST: Specific Case from Problem Statement")
    print("=" * 60)
    
    # The problem says: "Si 50 en xmin, le blocage est 50.5"
    # This suggests a block at x=50 causes blocking at 50.5
    # Then: "quand xmax a 51, je veux que l'utilisateur soit bloqué a 51,5 pas 52.5"
    # This suggests when the block extends to x=51, user should be blocked at 51.5
    
    # Let's interpret this as: block at position (50, y, z) 
    # When moving right, player stops at 50.5 ✓
    # When moving left from a block at (50, y, z), player should stop at 51.5 (not 52.5)
    
    # Test both cases: block at 50 and block at 51
    print("📋 CASE 1: Block at position (50, 10, 10)")
    print("-" * 40)
    
    world_blocks = {(50, 10, 10): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    print(f"📏 Player width: {PLAYER_WIDTH}")
    print(f"📏 Player half-width: {PLAYER_WIDTH/2}")
    print(f"🧱 Block at position: (50, 10, 10)")
    print(f"🧱 Block occupies: x=50.0 to x=51.0")
    print()
    
    # Test moving right (towards block)
    print("➡️  Testing movement to the right (towards block at x=50)")
    old_x = 48.0
    new_x = 52.0
    y = 10.5
    z = 10.0
    clearance = 0.0
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    expected_x = 50.0 - PLAYER_WIDTH/2  # Should be 49.5 (left edge of block - player half width)
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Expected position: x={expected_x}")
    print(f"   ✅ PASS" if abs(safe_x - expected_x) < 0.001 else f"   ❌ FAIL")
    print()
    
    # Test moving left (away from block)
    print("⬅️  Testing movement to the left (away from block at x=50)")
    old_x = 52.0
    new_x = 48.0
    
    safe_x = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    current_expected_x = 50.0 + 1.0 + PLAYER_WIDTH/2  # Current: 51.5 (block + 1 + half width)
    desired_expected_x = 50.0 + 1.0 + PLAYER_WIDTH/2  # Wait, this is still 51.5
    
    # Maybe the issue is that it's currently calculating as 52.5?
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Block right edge should be: {50.0 + 1.0}")
    print(f"   Player should stop at: {50.0 + 1.0 + PLAYER_WIDTH/2} (right edge + half width)")
    print()
    
    # Let me check what the current algorithm actually produces
    print("🔍 Analyzing the current algorithm:")
    print(f"   Block is at (50, 10, 10)")
    print(f"   Algorithm uses: float(block_x + 1) + player_half_width")
    print(f"   This gives: float(50 + 1) + 0.5 = 51.5")
    print(f"   Actual result: {safe_x}")
    
    if abs(safe_x - 51.5) < 0.001:
        print("   ✅ Current algorithm gives 51.5 - this seems correct!")
    else:
        print(f"   ❌ Current algorithm gives {safe_x} - something is wrong")
    
    print()
    print("📋 CASE 2: Block at position (51, 10, 10)")
    print("-" * 40)
    
    # Now test with block at (51, 10, 10) - this matches my first test
    world_blocks2 = {(51, 10, 10): "stone"}
    manager2 = UnifiedCollisionManager(world_blocks2)
    
    print(f"🧱 Block at position: (51, 10, 10)")
    print(f"🧱 Block occupies: x=51.0 to x=52.0")
    print()
    
    # Test moving left (away from block at x=51)
    print("⬅️  Testing movement to the left (away from block at x=51)")
    old_x = 53.0
    new_x = 50.0
    
    safe_x = manager2._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    
    print(f"   Old position: x={old_x}")
    print(f"   Intended new position: x={new_x}")
    print(f"   Safe position: x={safe_x}")
    print(f"   Block right edge: {51.0 + 1.0}")
    print(f"   Expected (right edge + half width): {51.0 + 1.0 + PLAYER_WIDTH/2}")
    print(f"   User wants: 51.5 instead of {safe_x}")
    
    if abs(safe_x - 52.5) < 0.001:
        print("   🐛 BUG CONFIRMED: Algorithm gives 52.5 but user wants 51.5")
    else:
        print(f"   🤔 Unexpected result: {safe_x}")
    
    # The issue seems to be that the user wants the blocking to happen at the LEFT edge of the block
    # rather than the RIGHT edge when moving left
    print()
    print("🎯 ANALYSIS:")
    print("   When moving left and hitting a block at (51, y, z):")
    print("   - Current: stops at right edge (52.0) + half_width (0.5) = 52.5")
    print("   - User wants: stop at left edge (51.0) + half_width (0.5) = 51.5")
    print("   - This suggests the collision should use the NEAR edge, not FAR edge")

if __name__ == "__main__":
    test_specific_case()