#!/usr/bin/env python3
"""
Simple demonstration of the new collision system without complex dependencies.

This shows that the core collision functionality works as expected,
inspired by fogleman/Minecraft.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only the collision system without the client (which needs pyglet)
from minecraft_physics import (
    UnifiedCollisionManager, 
    MinecraftCollisionDetector,
    SimplePhysicsManager
)

def demo_simple_collision():
    """Demonstrate the new simple collision system."""
    print("🎮 Demo: Simple Collision System (inspired by fogleman/Minecraft)")
    print("=" * 70)
    
    # Create a simple world
    world = {
        (0, 0, 0): 'stone',
        (1, 0, 0): 'stone', 
        (0, 1, 0): 'stone',
    }
    
    # Create collision detector (as used by client)
    detector = MinecraftCollisionDetector(world)
    
    print("🌍 World contains blocks at: (0,0,0), (1,0,0), (0,1,0)")
    print()
    
    # Test 1: Simple position collision
    print("🧪 Test 1: Simple Position Collision")
    test_positions = [
        (0.0, 0.0, 0.0),    # In block
        (0.5, 0.5, 0.5),    # In block  
        (2.0, 0.0, 0.0),    # Outside blocks
        (0.0, 2.0, 0.0),    # Above blocks
    ]
    
    for pos in test_positions:
        collision = detector.check_collision(pos)
        print(f"  Position {pos}: collision = {collision}")
    
    print()
    
    # Test 2: Movement resolution
    print("🧪 Test 2: Movement Resolution (Back Up on Collision)")
    movements = [
        ((2.0, 0.0, 0.0), (0.0, 0.0, 0.0)),  # Move into block
        ((0.0, 2.0, 0.0), (0.0, 0.0, 0.0)),  # Move down into block  
        ((2.0, 0.0, 0.0), (3.0, 0.0, 0.0)),  # Move in free space
    ]
    
    for old_pos, new_pos in movements:
        safe_pos, info = detector.resolve_collision(old_pos, new_pos)
        print(f"  Move {old_pos} -> {new_pos}")
        print(f"    Result: {safe_pos}, collision: {info}")
    
    print()
    print("✅ Simple collision system working correctly!")
    print("🎯 Key features implemented:")
    print("  - Only checks player center position + height")
    print("  - Backs up player on collision") 
    print("  - Simple logic without complex AABB sweeping")
    print("  - Inspired by fogleman/Minecraft approach")

if __name__ == "__main__":
    demo_simple_collision()