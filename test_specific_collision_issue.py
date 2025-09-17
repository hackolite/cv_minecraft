#!/usr/bin/env python3
"""
Test the specific collision scenarios that are failing
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

def collide_current(position, height, world):
    """Current collision detection with the fix"""
    pad = 0.25
    p = list(position)
    np = normalize(position)
    collision_types = {"top": False, "bottom": False, "right": False, "left": False}
    
    for face in FACES:
        for i in xrange(3):
            if not face[i]:
                continue
            d = (p[i] - np[i]) * face[i]
            # Current FIX: Allow downward collision detection even with small d values
            if d < pad and not (face == (0, -1, 0) and i == 1):
                continue
                
            for dy in xrange(height):
                op = list(np)
                op[1] -= dy
                
                # COLLISION FIX: For downward collision, check the block the player is standing on
                if face == (0, -1, 0) and i == 1:
                    # For downward collision, we need to check the block below the player's feet
                    # Instead of adding face[i] (-1), we check the floor of the current position
                    op[1] = int(p[1]) - dy
                else:
                    op[i] += face[i]
                
                if tuple(op) not in world:
                    continue
                    
                p[i] -= (d - pad) * face[i]
                if face == (0, -1, 0):
                    collision_types["top"] = True
                if face == (0, 1, 0):
                    collision_types["bottom"] = True
                break
    
    return tuple(p), collision_types

def analyze_failing_cases():
    """Analyze the specific failing test cases"""
    print("🔍 Analyzing Failing Collision Cases\n")
    
    # Test cases from the validation test
    test_cases = [
        {
            "name": "Case 1: Player standing on platform",
            "world": {(0, 1, 0): 'GRASS'},
            "position": (0.0, 1.1, 0.0),
            "expected": "Should detect ground collision"
        },
        {
            "name": "Case 2: Player near ground block", 
            "world": {(2, 0, 0): 'STONE'},
            "position": (2.0, 0.1, 0.0),
            "expected": "Should detect ground collision"
        },
        {
            "name": "Case 3: Player on high platform (WORKING)",
            "world": {(5, 3, 5): 'WOOD'},
            "position": (5.0, 3.8, 5.0),
            "expected": "Should detect ground collision"
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 {test_case['name']}")
        print(f"   World: {test_case['world']}")
        print(f"   Position: {test_case['position']}")
        print(f"   Expected: {test_case['expected']}")
        
        pos, collisions = collide_current(test_case['position'], 2, test_case['world'])
        on_ground = collisions["top"]
        
        print(f"   Result: {test_case['position']} -> {pos}")
        print(f"   On ground: {on_ground}")
        print(f"   Status: {'✅ WORKING' if on_ground else '❌ FAILING'}")
        
        # Detailed analysis for failing cases
        if not on_ground:
            print(f"   🔍 Detailed analysis:")
            position = test_case['position']
            world = test_case['world']
            
            p = list(position)
            np = normalize(position)
            pad = 0.25
            
            print(f"      Player pos: {position}")
            print(f"      Normalized: {np}")
            print(f"      Block(s): {list(world.keys())}")
            
            # Check specifically the downward face
            face = (0, -1, 0)
            i = 1  # Y axis
            d = (p[i] - np[i]) * face[i]
            
            print(f"      Downward face check:")
            print(f"         d = ({p[i]} - {np[i]}) * {face[i]} = {d}")
            print(f"         Skip condition: d < pad = {d} < {pad} = {d < pad}")
            print(f"         Special case: face == (0, -1, 0) and i == 1 = {face == (0, -1, 0) and i == 1}")
            print(f"         Final skip: {d < pad and not (face == (0, -1, 0) and i == 1)}")
            
            if not (d < pad and not (face == (0, -1, 0) and i == 1)):
                print(f"         Would check collision...")
                for dy in xrange(2):  # height = 2
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    print(f"            dy={dy}: checking block at {tuple(op)}")
                    if tuple(op) in world:
                        print(f"            ✅ Block found at {tuple(op)}!")
                    else:
                        print(f"            ❌ No block at {tuple(op)}")
            else:
                print(f"         ❌ Skipped collision check")
        
        print()

if __name__ == "__main__":
    analyze_failing_cases()