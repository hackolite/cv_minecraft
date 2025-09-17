#!/usr/bin/env python3
"""
Debug script to understand the collision issue with grass vs stone blocks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, BlockType
from server import MinecraftServer

def debug_collision_by_block_type():
    """Debug collision detection for different block types."""
    print("🔍 Testing Collision Detection by Block Type\n")
    
    # Create a server instance
    server = MinecraftServer()
    
    # Clear the default world to start clean
    server.world.world.clear()
    
    # Create test worlds with different block types
    test_scenarios = [
        {
            "name": "Grass Block",
            "block_type": "grass",
            "position": (10, 10, 10)
        },
        {
            "name": "Stone Block", 
            "block_type": "stone",
            "position": (20, 10, 10)
        },
        {
            "name": "Wood Block",
            "block_type": "wood", 
            "position": (30, 10, 10)
        },
        {
            "name": "Sand Block",
            "block_type": "sand",
            "position": (40, 10, 10)
        }
    ]
    
    # Create blocks
    for scenario in test_scenarios:
        server.world.world[scenario["position"]] = scenario["block_type"]
        print(f"✅ Created {scenario['name']} at {scenario['position']}")
    
    print()
    
    # Test collision detection for each block type
    for scenario in test_scenarios:
        x, y, z = scenario["position"]
        block_type = scenario["block_type"]
        
        print(f"🧪 Testing {scenario['name']} ({block_type}):")
        
        # Test player positions around the block
        test_positions = [
            (x, y + 1.1, z),    # Standing on top  
            (x, y + 0.1, z),    # Just above block
            (x, y + 0.5, z),    # Halfway into block
            (x, y - 0.1, z),    # Just below block
        ]
        
        for pos in test_positions:
            collision = server._check_ground_collision(pos)
            px, py, pz = pos
            relative_y = py - y
            print(f"   Position {pos} (y+{relative_y:.1f}): {'COLLISION' if collision else 'NO COLLISION'}")
        
        print()
    
    # Check if block type affects collision logic
    print("🔍 Block type analysis:")
    for scenario in test_scenarios:
        pos = scenario["position"]
        block_type = server.world.world.get(pos)
        print(f"   {scenario['name']}: block_type='{block_type}'")
    
    return True

if __name__ == "__main__":
    try:
        debug_collision_by_block_type()
        print("🎉 Debug completed successfully")
    except Exception as e:
        print(f"💥 Debug failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)