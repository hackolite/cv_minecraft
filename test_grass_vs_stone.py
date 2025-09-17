#!/usr/bin/env python3
"""
Test to reproduce the specific issue: falling through grass but not stone
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simulate the client-side collision detection
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
    """Current collision detection from minecraft_client_fr.py"""
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

def test_grass_vs_stone():
    """Test collision with grass vs stone blocks specifically"""
    print("🧪 Testing Grass vs Stone Collision Detection\n")
    
    # Create test worlds
    grass_world = {
        (0, 10, 0): 'grass',  # Grass block at y=10
    }
    
    stone_world = {
        (0, 10, 0): 'stone',  # Stone block at y=10  
    }
    
    # Test player positions
    test_positions = [
        (0.0, 11.0, 0.0),    # Standing on top
        (0.0, 10.9, 0.0),    # Just above
        (0.0, 10.5, 0.0),    # Halfway through
        (0.0, 10.1, 0.0),    # Just inside
    ]
    
    height = 2  # Player height
    
    print("🌱 Testing with GRASS block:")
    for pos in test_positions:
        new_pos, collisions = collide_current(pos, height, grass_world)
        on_ground = collisions["top"]
        print(f"   Position {pos} -> {new_pos}, on_ground={on_ground}")
    
    print("\n🗿 Testing with STONE block:")
    for pos in test_positions:
        new_pos, collisions = collide_current(pos, height, stone_world)
        on_ground = collisions["top"]
        print(f"   Position {pos} -> {new_pos}, on_ground={on_ground}")
    
    print("\n🔍 Comparison:")
    print("   Looking for differences in collision behavior...")
    
    differences_found = False
    for pos in test_positions:
        grass_pos, grass_coll = collide_current(pos, height, grass_world)
        stone_pos, stone_coll = collide_current(pos, height, stone_world)
        
        if grass_pos != stone_pos or grass_coll != stone_coll:
            print(f"   ❌ DIFFERENCE at {pos}:")
            print(f"      Grass: {grass_pos}, {grass_coll}")
            print(f"      Stone: {stone_pos}, {stone_coll}")
            differences_found = True
    
    if not differences_found:
        print("   ✅ No differences found - collision works the same for both block types")
        print("   🤔 The issue might be elsewhere...")
        
        # Check the specific problem scenario
        print("\n🔍 Checking specific falling-through scenario:")
        
        # Simulate a player falling and landing on each block type
        falling_positions = [
            (0.0, 12.0, 0.0),  # High above
            (0.0, 11.5, 0.0),  # Falling
            (0.0, 11.0, 0.0),  # Should land here
            (0.0, 10.8, 0.0),  # Slightly lower
        ]
        
        print("   🌱 Grass world falling test:")
        for pos in falling_positions:
            new_pos, collisions = collide_current(pos, height, grass_world)
            print(f"      {pos} -> {new_pos} (ground: {collisions['top']})")
            
        print("   🗿 Stone world falling test:")  
        for pos in falling_positions:
            new_pos, collisions = collide_current(pos, height, stone_world)
            print(f"      {pos} -> {new_pos} (ground: {collisions['top']})")

if __name__ == "__main__":
    test_grass_vs_stone()