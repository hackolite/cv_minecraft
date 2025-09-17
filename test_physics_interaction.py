#!/usr/bin/env python3
"""
Test to check if the issue is in client-server physics interaction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, BlockType
from server import MinecraftServer
import time

def test_server_client_physics_interaction():
    """Test how server physics interacts with different block types"""
    print("🔄 Testing Server-Client Physics Interaction\n")
    
    # Create server and clear world
    server = MinecraftServer()
    server.world.world.clear()
    
    # Create test scenarios
    test_blocks = [
        {"name": "Grass", "type": "grass", "pos": (10, 10, 10)},
        {"name": "Stone", "type": "stone", "pos": (20, 10, 10)},
        {"name": "Sand", "type": "sand", "pos": (30, 10, 10)},
    ]
    
    # Add blocks to world
    for block in test_blocks:
        server.world.world[block["pos"]] = block["type"]
        print(f"✅ Added {block['name']} block at {block['pos']}")
    
    print()
    
    # Test physics for each block type
    for block in test_blocks:
        x, y, z = block["pos"]
        print(f"🧪 Testing {block['name']} block:")
        
        # Create a player above the block
        player = PlayerState(
            player_id="test_player",
            position=(x, y + 5, z),  # 5 blocks above
            rotation=(0, 0),
            name=f"TestPlayer_{block['name']}"
        )
        
        # Simulate player falling
        print(f"   Initial position: {player.position}")
        
        # Simulate multiple physics ticks
        dt = 1.0 / 20  # 20 FPS
        for tick in range(100):  # 5 seconds of physics
            old_y = player.position[1]
            server._apply_physics(player, dt)
            new_y = player.position[1]
            
            # Check if player has stopped falling (landed)
            if abs(new_y - old_y) < 0.001 and player.on_ground:
                print(f"   ✅ Landed at position: {player.position} after {tick} ticks")
                print(f"   📍 Landing Y: {new_y:.3f} (block at Y: {y})")
                print(f"   🏃 On ground: {player.on_ground}")
                break
            elif tick == 99:
                print(f"   ❌ Still falling after 100 ticks: {player.position}")
                print(f"   🏃 On ground: {player.on_ground}")
        
        print()
    
    # Test collision detection directly for different scenarios
    print("🔍 Direct collision detection test:")
    for block in test_blocks:
        x, y, z = block["pos"]
        
        # Test positions around the block
        positions_to_test = [
            (x, y + 1.1, z),  # Standing on top
            (x, y + 0.9, z),  # Slightly above
            (x, y + 0.5, z),  # Inside block
            (x, y + 0.1, z),  # Just above surface
        ]
        
        print(f"   {block['name']} block collision tests:")
        for pos in positions_to_test:
            collision = server._check_ground_collision(pos)
            print(f"      Position {pos}: {'COLLISION' if collision else 'NO COLLISION'}")
        print()

if __name__ == "__main__":
    test_server_client_physics_interaction()