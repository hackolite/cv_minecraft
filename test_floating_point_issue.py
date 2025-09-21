#!/usr/bin/env python3
"""
Test script to reproduce the floating-point precision issue described in the problem statement.

The issue is:
1. Arrondi flottant - floating point calculations result in positions like y=1.0000001 instead of y=1
2. Gravité appliquée en continu - gravity is always applied even when on ground
3. Pas de tolérance (epsilon) - no tolerance for tiny penetrations

This causes infinite snapping behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    UnifiedCollisionManager, TickBasedPhysicsManager,
    GRAVITY, COLLISION_EPSILON, GROUND_TOLERANCE
)

def test_floating_point_precision_issue():
    """Test the floating-point precision issue with ground detection."""
    print("🔬 Testing Floating-Point Precision Issue")
    print("=" * 60)
    
    # Setup world with a single block at y=10
    world = {
        (10, 10, 10): 'stone'
    }
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Player starting position on top of block (should be at y=11)
    position = (10.5, 11.0, 10.5)
    velocity = (0.0, 0.0, 0.0)  # Start with no velocity
    
    print(f"Initial position: {position}")
    print(f"Initial velocity: {velocity}")
    print(f"COLLISION_EPSILON: {COLLISION_EPSILON}")
    print(f"GROUND_TOLERANCE: {GROUND_TOLERANCE}")
    print(f"GRAVITY: {GRAVITY}")
    
    # Test ground detection
    ground_test = (position[0], position[1] - 0.1, position[2])
    on_ground = collision_manager.check_block_collision(ground_test)
    print(f"On ground (y-0.1): {on_ground}")
    
    # Simulate several physics ticks
    dt = 0.016  # 16ms tick (60 FPS)
    
    for tick in range(10):
        print(f"\n--- Tick {tick + 1} ---")
        print(f"Before: pos={position}, vel={velocity}")
        
        # Apply physics update 
        position, velocity, collision_info = physics_manager.update_tick(
            position, velocity, dt, jumping=False
        )
        
        print(f"After:  pos={position}, vel={velocity}")
        print(f"Collision info: {collision_info}")
        
        # Check if position has tiny floating-point errors
        y_position = position[1] 
        expected_y = 11.0
        y_diff = abs(y_position - expected_y)
        
        if y_diff > 0 and y_diff < 0.001:
            print(f"⚠️  Floating-point precision issue detected!")
            print(f"   Expected Y: {expected_y}")
            print(f"   Actual Y: {y_position}")
            print(f"   Difference: {y_diff}")
            
        # Check if we're seeing snapping behavior
        if collision_info['y'] and velocity[1] == 0.0:
            print(f"⚠️  Snapping detected: Y velocity reset to 0")
            
        # If player is stable on ground, we should not see continuous changes
        if on_ground and velocity[1] != 0.0:
            print(f"⚠️  Continuous gravity application while on ground")

def test_epsilon_tolerance():
    """Test epsilon tolerance handling."""
    print("\n🔬 Testing Epsilon Tolerance")
    print("=" * 60)
    
    # Setup world with a single block
    world = {(10, 10, 10): 'stone'}
    collision_manager = UnifiedCollisionManager(world)
    
    # Test positions very close to block surface
    test_positions = [
        (10.5, 11.0, 10.5),        # Exactly on top
        (10.5, 11.0001, 10.5),     # Tiny amount above
        (10.5, 10.9999, 10.5),     # Tiny amount below
        (10.5, 11.00001, 10.5),    # Even tinier amount above
    ]
    
    for pos in test_positions:
        collision = collision_manager.check_block_collision(pos)
        print(f"Position {pos}: collision={collision}")
        
        # Test ground detection
        ground_test = (pos[0], pos[1] - 0.1, pos[2])
        on_ground = collision_manager.check_block_collision(ground_test)
        print(f"  Ground test (y-0.1): {on_ground}")

if __name__ == "__main__":
    test_floating_point_precision_issue()
    test_epsilon_tolerance()