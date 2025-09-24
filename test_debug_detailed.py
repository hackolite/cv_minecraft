#!/usr/bin/env python3
"""
Detailed debug of the collision issue.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, COLLISION_EPSILON

def test_debug_detailed():
    """Debug the collision in detail."""
    print("🔍 DETAILED DEBUG: Collision Detection")
    print("=" * 60)
    
    world_blocks = {(51, 10, 10): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    print(f"Block at (51, 10, 10)")
    print(f"Player width: {PLAYER_WIDTH}")
    print(f"Player half-width: {PLAYER_WIDTH/2}")
    print(f"Collision epsilon: {COLLISION_EPSILON}")
    print()
    
    # Test positions around the expected safe position with different y coordinates
    test_positions = [
        (51.5, 10.5, 10.0),  # Original position
        (51.5, 11.1, 10.0),  # Above the block
        (51.5, 9.5, 10.0),   # Below the block
        (51.5, 10.5, 11.1),  # In front of the block
        (51.5, 10.5, 8.9),   # Behind the block
    ]
    
    for test_pos in test_positions:
        px, py, pz = test_pos
        collision = manager.check_collision(test_pos, "player1")
        
        print(f"Position ({px}, {py}, {pz}):")
        print(f"  Collision: {collision}")
        
        # Calculate player bounding box
        half_width = PLAYER_WIDTH / 2
        player_min_x = px - half_width
        player_max_x = px + half_width - COLLISION_EPSILON
        player_min_y = py
        player_max_y = py + PLAYER_WIDTH
        player_min_z = pz - half_width
        player_max_z = pz + half_width - COLLISION_EPSILON
        
        print(f"  Player bounding box: x=[{player_min_x:.4f}, {player_max_x:.4f}], y=[{player_min_y:.1f}, {player_max_y:.1f}], z=[{player_min_z:.1f}, {player_max_z:.4f}]")
        
        # Block bounding box
        block_min_x, block_max_x = 51.0, 52.0
        block_min_y, block_max_y = 10.0, 11.0
        block_min_z, block_max_z = 10.0, 11.0
        
        print(f"  Block bounding box: x=[{block_min_x:.1f}, {block_max_x:.1f}], y=[{block_min_y:.1f}, {block_max_y:.1f}], z=[{block_min_z:.1f}, {block_max_z:.1f}]")
        
        # Check overlap manually
        x_overlap = player_min_x < block_max_x and player_max_x > block_min_x
        y_overlap = player_min_y < block_max_y and player_max_y > block_min_y
        z_overlap = player_min_z < block_max_z and player_max_z > block_min_z
        
        print(f"  X overlap: {x_overlap} ({player_min_x:.4f} < {block_max_x:.1f} and {player_max_x:.4f} > {block_min_x:.1f})")
        print(f"  Y overlap: {y_overlap} ({player_min_y:.1f} < {block_max_y:.1f} and {player_max_y:.1f} > {block_min_y:.1f})")
        print(f"  Z overlap: {z_overlap} ({player_min_z:.1f} < {block_max_z:.1f} and {player_max_z:.4f} > {block_min_z:.1f})")
        print(f"  Expected collision: {x_overlap and y_overlap and z_overlap}")
        print()

if __name__ == "__main__":
    test_debug_detailed()