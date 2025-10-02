#!/usr/bin/env python3
"""
Example usage of the Minecraft Server HTTP API.

This script demonstrates how to use the API to:
1. Query camera positions
2. Get user information
3. Retrieve blocks in specific areas
4. Render views from different positions
"""

import requests
import json
import time
from typing import List, Dict, Any

API_BASE_URL = "http://localhost:8000"

class MinecraftAPIClient:
    """Client for interacting with the Minecraft Server HTTP API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
    
    def get_cameras(self) -> Dict[str, Any]:
        """Get list of all camera blocks."""
        response = requests.get(f"{self.base_url}/api/cameras")
        response.raise_for_status()
        return response.json()
    
    def get_users(self) -> Dict[str, Any]:
        """Get list of all users."""
        response = requests.get(f"{self.base_url}/api/users")
        response.raise_for_status()
        return response.json()
    
    def get_blocks(self, min_x: int = 0, min_y: int = 0, min_z: int = 0,
                   max_x: int = 128, max_y: int = 256, max_z: int = 128) -> Dict[str, Any]:
        """Get blocks in a specific area."""
        params = {
            'min_x': min_x, 'min_y': min_y, 'min_z': min_z,
            'max_x': max_x, 'max_y': max_y, 'max_z': max_z
        }
        response = requests.get(f"{self.base_url}/api/blocks", params=params)
        response.raise_for_status()
        return response.json()
    
    def render_view(self, position: List[float], rotation: List[float],
                   width: int = 640, height: int = 480,
                   fov: float = 65.0, render_distance: int = 50) -> bytes:
        """Render a view from a specific position and rotation."""
        payload = {
            'position': position,
            'rotation': rotation,
            'width': width,
            'height': height,
            'fov': fov,
            'render_distance': render_distance
        }
        response = requests.post(f"{self.base_url}/api/render", json=payload)
        response.raise_for_status()
        return response.content

def example_1_list_cameras():
    """Example 1: List all camera positions."""
    print("\n" + "="*60)
    print("Example 1: List All Cameras")
    print("="*60)
    
    client = MinecraftAPIClient()
    cameras = client.get_cameras()
    
    print(f"Found {cameras['count']} camera(s):")
    for i, camera in enumerate(cameras['cameras'], 1):
        pos = camera['position']
        print(f"  {i}. Camera at position ({pos[0]}, {pos[1]}, {pos[2]})")

def example_2_monitor_users():
    """Example 2: Monitor user positions."""
    print("\n" + "="*60)
    print("Example 2: Monitor User Positions")
    print("="*60)
    
    client = MinecraftAPIClient()
    users = client.get_users()
    
    if users['count'] == 0:
        print("No users currently connected.")
    else:
        print(f"Found {users['count']} user(s):")
        for user in users['users']:
            pos = user['position']
            rot = user['rotation']
            print(f"\n  Name: {user['name']}")
            print(f"  Position: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
            print(f"  Rotation: ({rot[0]:.1f}°, {rot[1]:.1f}°)")
            print(f"  Flying: {user['flying']}")
            print(f"  On Ground: {user['on_ground']}")

def example_3_analyze_area():
    """Example 3: Analyze blocks in an area."""
    print("\n" + "="*60)
    print("Example 3: Analyze Blocks in Spawn Area")
    print("="*60)
    
    client = MinecraftAPIClient()
    
    # Get blocks in a 20x20x20 area around spawn
    spawn_x, spawn_y, spawn_z = 64, 100, 64
    radius = 10
    
    blocks = client.get_blocks(
        min_x=spawn_x - radius,
        min_y=spawn_y - radius,
        min_z=spawn_z - radius,
        max_x=spawn_x + radius,
        max_y=spawn_y + radius,
        max_z=spawn_z + radius
    )
    
    print(f"Found {blocks['count']} blocks in area:")
    print(f"  Bounds: {blocks['bounds']}")
    
    # Count block types
    from collections import Counter
    block_types = Counter(block['block_type'] for block in blocks['blocks'])
    
    print(f"\nBlock type distribution:")
    for block_type, count in sorted(block_types.items(), key=lambda x: -x[1]):
        print(f"  {block_type:15} : {count:4} blocks")

def example_4_render_camera_views():
    """Example 4: Render views from all cameras."""
    print("\n" + "="*60)
    print("Example 4: Render Views from All Cameras")
    print("="*60)
    
    client = MinecraftAPIClient()
    
    # Get all cameras
    cameras = client.get_cameras()
    
    if cameras['count'] == 0:
        print("No cameras found.")
        return
    
    print(f"Rendering views from {cameras['count']} camera(s)...")
    
    for i, camera in enumerate(cameras['cameras'], 1):
        pos = camera['position']
        
        # Render views in 4 cardinal directions
        directions = [
            ("north", [0.0, 0.0]),
            ("east", [90.0, 0.0]),
            ("south", [180.0, 0.0]),
            ("west", [270.0, 0.0])
        ]
        
        for direction_name, rotation in directions:
            image_data = client.render_view(
                position=pos,
                rotation=rotation,
                width=640,
                height=480
            )
            
            filename = f'/tmp/camera_{i}_{direction_name}.png'
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            print(f"  ✓ Camera {i} ({direction_name}): {filename}")

def example_5_track_user_view():
    """Example 5: Track and render a user's current view."""
    print("\n" + "="*60)
    print("Example 5: Track and Render User Views")
    print("="*60)
    
    client = MinecraftAPIClient()
    users = client.get_users()
    
    if users['count'] == 0:
        print("No users currently connected.")
        return
    
    print(f"Rendering current views for {users['count']} user(s)...")
    
    for user in users['users']:
        image_data = client.render_view(
            position=user['position'],
            rotation=user['rotation'],
            width=800,
            height=600
        )
        
        filename = f"/tmp/user_{user['name']}_view.png"
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        print(f"  ✓ {user['name']}: {filename}")

def example_6_continuous_monitoring():
    """Example 6: Continuous monitoring of user positions."""
    print("\n" + "="*60)
    print("Example 6: Continuous Monitoring (5 iterations)")
    print("="*60)
    
    client = MinecraftAPIClient()
    
    for iteration in range(5):
        print(f"\n--- Iteration {iteration + 1} ---")
        
        users = client.get_users()
        print(f"Connected users: {users['count']}")
        
        for user in users['users']:
            pos = user['position']
            print(f"  {user['name']:15} at ({pos[0]:6.1f}, {pos[1]:6.1f}, {pos[2]:6.1f})")
        
        if iteration < 4:  # Don't sleep on last iteration
            time.sleep(2)

def main():
    """Run all examples."""
    print("="*60)
    print("Minecraft Server HTTP API - Example Usage")
    print("="*60)
    
    try:
        # Check if server is available
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✓ Server is available: {response.json()['name']}")
        
        # Run examples
        example_1_list_cameras()
        example_2_monitor_users()
        example_3_analyze_area()
        example_4_render_camera_views()
        example_5_track_user_view()
        example_6_continuous_monitoring()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server.")
        print("Make sure the server is running on http://localhost:8000")
        print("Start it with: python3 server.py")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
