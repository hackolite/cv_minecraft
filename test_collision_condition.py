#!/usr/bin/env python3
"""
Test the specific collision condition to understand if it's working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def normalize(position):
    """Normalize position to block coordinates."""
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

FACES = [
    (0, 1, 0),    # Up
    (0, -1, 0),   # Down  
    (-1, 0, 0),   # Left
    (1, 0, 0),    # Right
    (0, 0, 1),    # Forward
    (0, 0, -1),   # Backward
]

try:
    xrange
except NameError:
    xrange = range

def debug_collision_condition():
    """Debug the specific collision condition that was added"""
    print("🔍 Testing Collision Condition Logic\n")
    
    # Test scenario: player standing on a block
    position = (0.0, 11.0, 0.0)  # Player position
    world = {(0, 10, 0): 'grass'}  # Block below
    pad = 0.25
    height = 2
    
    p = list(position)
    np = normalize(position)
    
    print(f"Player position: {position}")
    print(f"Normalized position: {np}")
    print(f"Block in world: {list(world.keys())[0]}")
    print(f"Padding: {pad}")
    print()
    
    for face in FACES:
        print(f"Testing face: {face}")
        
        for i in xrange(3):
            if not face[i]:
                continue
                
            d = (p[i] - np[i]) * face[i]
            print(f"  Axis {i} ({'XYZ'[i]}): d = ({p[i]} - {np[i]}) * {face[i]} = {d}")
            
            # Original condition (buggy)
            original_skip = d < pad
            print(f"  Original condition (d < pad): {original_skip}")
            
            # Fixed condition
            fixed_skip = d < pad and not (face == (0, -1, 0) and i == 1)
            print(f"  Fixed condition: {fixed_skip}")
            print(f"  Special downward case: face={face}, i={i}, is_downward_y={face == (0, -1, 0) and i == 1}")
            
            if original_skip != fixed_skip:
                print(f"  🎯 DIFFERENCE: Original would skip, fixed allows collision!")
            
            if not fixed_skip:  # Would proceed with collision check
                print(f"  ✅ Would proceed to check collision for this face/axis")
                
                for dy in xrange(height):
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    print(f"    Checking position: {tuple(op)} (dy={dy})")
                    
                    if tuple(op) in world:
                        print(f"    🎯 COLLISION FOUND at {tuple(op)}!")
                        # Would apply collision response here
                        new_pos = p[:]
                        new_pos[i] -= (d - pad) * face[i]
                        print(f"    New position after collision: {new_pos}")
                        if face == (0, -1, 0):
                            print(f"    ✅ Would set on_ground=True (downward collision)")
                        break
                    else:
                        print(f"    No block at {tuple(op)}")
            else:
                print(f"  ❌ Would skip collision check for this face/axis")
            
            print()

if __name__ == "__main__":
    debug_collision_condition()