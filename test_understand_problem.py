#!/usr/bin/env python3
"""
Test to better understand the problem statement.
Problem: "Si 50 en xmin, le blocage est 50.5 pour le bloc utilisatreur, quand xmax a 51, je veux que l'utilisateur soit bloqué a 51,5 pas 52.5"
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH

def test_understand_problem():
    """Try to understand the problem statement."""
    print("🧪 TEST: Understanding the Problem Statement")
    print("=" * 60)
    
    print("Problem statement (translated):")
    print("'If 50 in xmin, the blocking is 50.5 for the user block, when xmax has 51, I want the user to be blocked at 51.5 not 52.5'")
    print()
    
    # Interpretation 1: Different edge calculation
    print("🔍 Interpretation 1: Using left edge instead of right edge")
    print("-" * 50)
    
    # Create a block at x=50
    world_blocks = {(50, 10, 10): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    print("Block at (50, 10, 10) - occupies x=[50.0, 51.0)")
    print("xmin = 50, xmax = 51")
    print()
    
    # Test moving right (toward block)
    safe_x_right = manager._snap_to_safe_x_position(48.0, 52.0, 10.5, 10.0, "player1", 0.0)
    print(f"Moving right (48→52): stops at {safe_x_right}")
    print(f"Expected: 50.0 - 0.5 = 49.5")
    print(f"✅ PASS" if abs(safe_x_right - 49.5) < 0.001 else "❌ FAIL")
    print()
    
    # Test moving left (away from block)  
    safe_x_left = manager._snap_to_safe_x_position(52.0, 48.0, 10.5, 10.0, "player1", 0.0)
    print(f"Moving left (52→48): stops at {safe_x_left}")
    print(f"User wants: 51.5 (xmax + 0.5)")
    print(f"Current algorithm gives: {safe_x_left}")
    
    # Check if this matches the desired behavior
    if abs(safe_x_left - 51.5) < 0.001:
        print("✅ MATCHES desired behavior!")
    else:
        print("❌ Does not match desired behavior")
    
    print()
    print("🔍 Let me check the collision at 51.5...")
    collision_at_51_5 = manager.check_collision((51.5, 10.5, 10.0), "player1")
    print(f"Collision at (51.5, 10.5, 10.0): {collision_at_51_5}")
    
    if collision_at_51_5:
        print("❌ Player would collide at 51.5 - that's why algorithm rejects it")
        print("Player bounding box at x=51.5: [51.0, 52.0)")
        print("Block at (50,10,10) occupies: [50.0, 51.0)")  
        print("Wait... these don't overlap!")
        
        # Let me check what blocks are being checked
        px, py, pz = 51.5, 10.5, 10.0
        half_width = PLAYER_WIDTH / 2
        player_min_x = px - half_width
        player_max_x = px + half_width
        xmin = int(math.floor(player_min_x))
        xmax = int(math.floor(player_max_x))
        
        print(f"Player bounding box: x=[{player_min_x}, {player_max_x})")
        print(f"Blocks checked: x={xmin} to {xmax}")
        
        for x in range(xmin, xmax + 1):
            exists = (x, 10, 10) in world_blocks
            print(f"  Block ({x}, 10, 10): {'EXISTS' if exists else 'does not exist'}")
    else:
        print("✅ Player would not collide at 51.5")

if __name__ == "__main__":
    test_understand_problem()