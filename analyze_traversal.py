#!/usr/bin/env python3
"""
Analyze the specific traversal issue in more detail to understand what's actually wrong.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def analyze_traversal_cases():
    """Analyze specific cases that are being flagged as traversal."""
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("=== ANALYZING SPECIFIC TRAVERSAL CASES ===")
    print(f"Block at: (5, 10, 5) - spans from (5,10,5) to (6,11,6)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    cases = [
        ("Case 1: -X +Z", (6.0, 10.5, 4.0), (4.0, 10.5, 6.0)),
        ("Case 2: +X -Z", (4.0, 10.5, 6.0), (6.0, 10.5, 4.0)), 
        ("Case 3: -X -Z", (6.0, 10.5, 6.0), (4.0, 10.5, 4.0)),
    ]
    
    for name, start, end in cases:
        print(f"{name}: {start} → {end}")
        
        # Check if start and end positions intersect with block
        start_collision = manager.check_block_collision(start)
        end_collision = manager.check_block_collision(end)
        
        print(f"  Start collision: {start_collision}")
        print(f"  End collision: {end_collision}")
        
        # Resolve the movement
        safe_pos, collision_info = manager.resolve_collision(start, end)
        print(f"  Safe position: {safe_pos}")
        print(f"  Collision info: {collision_info}")
        
        # Check if the player actually "went through" the block
        # A legitimate traversal would mean: 
        # 1. Start and end are on opposite sides of the block
        # 2. The straight line path goes through the block
        # 3. The final position is near the target
        
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        print(f"  Reached target: {reached_target}")
        
        if reached_target:
            # Check if this is a legitimate path that doesn't go through the block
            # For this, we need to check if there's a clear path
            print(f"  ⚠️  Need to check if this is legitimate or traversal")
            
            # Sample points along the path to see if any go through the block
            samples = 10
            path_blocked = False
            for i in range(1, samples):
                t = i / samples
                sample_x = start[0] + t * (end[0] - start[0])
                sample_y = start[1] + t * (end[1] - start[1]) 
                sample_z = start[2] + t * (end[2] - start[2])
                sample_pos = (sample_x, sample_y, sample_z)
                
                if manager.check_block_collision(sample_pos):
                    print(f"    Path blocked at sample {i}: {sample_pos}")
                    path_blocked = True
                    break
            
            if path_blocked:
                print(f"  ❌ TRUE TRAVERSAL: Path goes through block but player reached target")
            else:
                print(f"  ✅ LEGITIMATE: Path doesn't go through block")
        
        print()

def test_realistic_block_cluster():
    """Test with a more realistic scenario - a cluster of blocks."""
    print("=== TESTING WITH BLOCK CLUSTER ===")
    
    # Create a 2x2 wall of blocks
    world = {}
    for x in range(5, 7):
        for z in range(5, 7):
            world[(x, 10, z)] = 'stone'
    
    manager = UnifiedCollisionManager(world)
    
    print("Block cluster at (5,10,5), (5,10,6), (6,10,5), (6,10,6)")
    print()
    
    # Test diagonal movement that should definitely be blocked
    test_cases = [
        ("Through corner", (4.5, 10.5, 4.5), (6.5, 10.5, 6.5)),
        ("Around corner", (4.5, 10.5, 4.5), (7.5, 10.5, 4.5)), # Should be allowed
    ]
    
    for name, start, end in test_cases:
        print(f"{name}: {start} → {end}")
        safe_pos, collision_info = manager.resolve_collision(start, end)
        print(f"  Result: {safe_pos}")
        print(f"  Collision: {collision_info}")
        
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        if reached_target:
            print(f"  ✅ Movement allowed")
        else:
            print(f"  🚫 Movement blocked")
        print()

if __name__ == "__main__":
    analyze_traversal_cases()
    test_realistic_block_cluster()