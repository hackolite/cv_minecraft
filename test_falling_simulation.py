#!/usr/bin/env python3
"""
Try to reproduce the exact issue: falling through grass but not stone
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

def collide_with_debug(position, height, world, debug=False):
    """Collision detection with detailed debug output"""
    pad = 0.25
    p = list(position)
    np = normalize(position)
    collision_types = {"top": False, "bottom": False, "right": False, "left": False}
    
    if debug:
        print(f"🔍 Collision check for position {position}")
        print(f"   Normalized: {np}")
        print(f"   World blocks: {list(world.keys())}")
    
    for face in FACES:
        if debug:
            print(f"   Testing face: {face}")
            
        for i in xrange(3):
            if not face[i]:
                continue
            d = (p[i] - np[i]) * face[i]
            
            # Current FIX: Allow downward collision detection even with small d values
            if d < pad and not (face == (0, -1, 0) and i == 1):
                if debug:
                    print(f"      Axis {i}: d={d:.3f} < pad={pad}, skipping")
                continue
                
            if debug:
                print(f"      Axis {i}: d={d:.3f}, checking collision...")
                
            for dy in xrange(height):
                op = list(np)
                op[1] -= dy
                op[i] += face[i]
                
                if debug:
                    print(f"         Testing block at {tuple(op)} (dy={dy})")
                    
                if tuple(op) not in world:
                    if debug:
                        print(f"         No block at {tuple(op)}")
                    continue
                    
                if debug:
                    print(f"         ✅ COLLISION with block at {tuple(op)}")
                    
                p[i] -= (d - pad) * face[i]
                if face == (0, -1, 0):
                    collision_types["top"] = True
                    if debug:
                        print(f"         Set on_ground=True (downward collision)")
                if face == (0, 1, 0):
                    collision_types["bottom"] = True
                    if debug:
                        print(f"         Set ceiling collision (upward collision)")
                break
    
    result_pos = tuple(p)
    if debug:
        print(f"   Result: {position} -> {result_pos}")
        print(f"   Collision types: {collision_types}")
    
    return result_pos, collision_types

def simulate_falling_scenario():
    """Simulate a falling scenario that might reproduce the issue"""
    print("🎯 Simulating Falling Through Blocks Scenario\n")
    
    # Create test worlds
    grass_world = {(0, 10, 0): 'grass'}
    stone_world = {(0, 10, 0): 'stone'}
    
    # Simulate a player falling from various heights
    falling_heights = [15.0, 12.0, 11.5, 11.2, 11.0, 10.8, 10.5, 10.2, 10.0]
    
    print("🌱 GRASS WORLD - Falling simulation:")
    grass_landed = False
    for height in falling_heights:
        pos = (0.0, height, 0.0)
        new_pos, collisions = collide_with_debug(pos, 2, grass_world, debug=False)
        on_ground = collisions["top"]
        
        print(f"   Height {height:4.1f} -> {new_pos[1]:6.3f} (on_ground: {on_ground})")
        
        if on_ground and not grass_landed:
            print(f"   🎯 First landing at height {height} -> {new_pos[1]:.3f}")
            grass_landed = True
            
        # If player somehow gets below the block, that's falling through
        if new_pos[1] < 10.0:
            print(f"   ❌ FALLING THROUGH! Player at Y={new_pos[1]:.3f} below block at Y=10")
    
    print("\n🗿 STONE WORLD - Falling simulation:")
    stone_landed = False
    for height in falling_heights:
        pos = (0.0, height, 0.0)
        new_pos, collisions = collide_with_debug(pos, 2, stone_world, debug=False)
        on_ground = collisions["top"]
        
        print(f"   Height {height:4.1f} -> {new_pos[1]:6.3f} (on_ground: {on_ground})")
        
        if on_ground and not stone_landed:
            print(f"   🎯 First landing at height {height} -> {new_pos[1]:.3f}")
            stone_landed = True
            
        # If player somehow gets below the block, that's falling through
        if new_pos[1] < 10.0:
            print(f"   ❌ FALLING THROUGH! Player at Y={new_pos[1]:.3f} below block at Y=10")
    
    # Test specific problematic scenarios
    print("\n🔍 Testing specific edge cases:")
    
    edge_cases = [
        (0.0, 10.25, 0.0),  # Quarter way into block
        (0.0, 10.1, 0.0),   # Just above block surface
        (0.0, 10.01, 0.0),  # Very close to block surface
        (0.0, 9.99, 0.0),   # Just below block surface
        (0.0, 9.75, 0.0),   # Quarter way below block
    ]
    
    for test_pos in edge_cases:
        print(f"\n   Testing position {test_pos}:")
        
        grass_pos, grass_coll = collide_with_debug(test_pos, 2, grass_world, debug=True)
        print(f"   Grass result: {grass_pos} (on_ground: {grass_coll['top']})")
        
        stone_pos, stone_coll = collide_with_debug(test_pos, 2, stone_world, debug=False)
        print(f"   Stone result: {stone_pos} (on_ground: {stone_coll['top']})")
        
        if grass_pos != stone_pos or grass_coll != stone_coll:
            print(f"   ❌ DIFFERENCE FOUND!")
            print(f"      Grass: {grass_pos}, {grass_coll}")
            print(f"      Stone: {stone_pos}, {stone_coll}")
        else:
            print(f"   ✅ Same behavior for both block types")

if __name__ == "__main__":
    simulate_falling_scenario()