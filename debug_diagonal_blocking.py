#!/usr/bin/env python3
"""
Debug the specific case where diagonal movement should be fully blocked.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import MinecraftCollisionDetector, COLLISION_EPSILON

def debug_diagonal_blocking():
    """Debug why diagonal movement isn't fully blocked."""
    print("🔍 Debugging Diagonal Movement Blocking")
    print()
    
    # Simple world with one block
    world = {(10, 10, 10): "stone"}
    detector = MinecraftCollisionDetector(world)
    
    start_pos = (9.5, 10.5, 9.5)
    end_pos = (10.8, 10.5, 10.8)
    
    print(f"Testing movement from {start_pos} to {end_pos}")
    
    # Check if this is detected as diagonal
    dx = abs(end_pos[0] - start_pos[0])
    dz = abs(end_pos[2] - start_pos[2])
    is_diagonal = dx > COLLISION_EPSILON and dz > COLLISION_EPSILON
    
    print(f"Movement deltas: dx={dx:.3f}, dz={dz:.3f}")
    print(f"Is diagonal: {is_diagonal} (threshold: {COLLISION_EPSILON})")
    
    # Check ray casting
    ray_collision, hit_block = detector.ray_cast_collision(start_pos, end_pos)
    print(f"Ray casting: collision={ray_collision}, hit_block={hit_block}")
    
    if is_diagonal and ray_collision:
        print("Should trigger conservative sliding!")
    elif is_diagonal and not ray_collision:
        print("Diagonal but no ray collision - will use axis separation")
    elif not is_diagonal:
        print("Not diagonal - will use axis separation")
    
    # Test the actual resolution
    safe_pos, collision_info = detector.resolve_collision(start_pos, end_pos)
    print(f"Final result: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Calculate efficiency
    idx = end_pos[0] - start_pos[0]
    idz = end_pos[2] - start_pos[2]
    intended_distance = (idx*idx + idz*idz)**0.5
    
    dx = safe_pos[0] - start_pos[0]
    dz = safe_pos[2] - start_pos[2]
    actual_distance = (dx*dx + dz*dz)**0.5
    
    efficiency = actual_distance / intended_distance if intended_distance > 0 else 1.0
    print(f"Movement efficiency: {efficiency:.1%}")

if __name__ == "__main__":
    debug_diagonal_blocking()