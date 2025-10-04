#!/usr/bin/env python3
"""
Camera View Query Script
========================

Query camera view data via websocket using block_id and save it to a JSON file
for client-side reconstruction.

This script:
1. Connects to the Minecraft server via websocket
2. Queries available cameras using their block_ids
3. Retrieves all blocks visible from the camera's perspective
4. Saves the view data to a JSON file for reconstruction

Usage:
    python3 camera_view_query.py [--camera-id CAMERA_ID] [--output OUTPUT_FILE]
"""

import asyncio
import websockets
import json
import argparse
from typing import Dict, Any, Optional


async def query_camera_view(
    server_uri: str = "ws://localhost:8765",
    camera_id: Optional[str] = None,
    rotation: tuple = (0, 0),
    view_distance: float = 50.0
) -> Dict[str, Any]:
    """Query camera view data from server.
    
    Args:
        server_uri: WebSocket server URI
        camera_id: Specific camera block_id to query (None = use first available)
        rotation: Camera rotation (horizontal, vertical) in degrees
        view_distance: How far the camera can see
        
    Returns:
        Dictionary containing camera info and visible blocks
    """
    print(f"🔌 Connecting to server: {server_uri}")
    
    async with websockets.connect(server_uri) as ws:
        # 1. Join the game
        await ws.send(json.dumps({
            "type": "player_join",
            "data": {"name": "CameraQueryBot"}
        }))
        
        # 2. Receive initial messages
        data = json.loads(await ws.recv())  # world_init
        print(f"📦 Received world_init: size={data.get('world_size')}, spawn={data.get('spawn_position')}")
        
        # Skip world chunks
        chunk_count = 0
        while True:
            data = json.loads(await ws.recv())
            if data["type"] == "world_chunk":
                chunk_count += 1
            elif data["type"] == "player_list":
                print(f"📦 Received {chunk_count} world chunks")
                break
        
        # 3. Get list of cameras
        await ws.send(json.dumps({
            "type": "get_cameras_list",
            "data": {}
        }))
        
        data = json.loads(await ws.recv())
        cameras = data["data"]["cameras"]
        
        print(f"\n📷 Found {len(cameras)} camera(s):")
        for cam in cameras:
            print(f"   - {cam['block_id']} at {cam['position']}")
        
        if not cameras:
            print("❌ No cameras found in the world!")
            return {"error": "No cameras available"}
        
        # 4. Select camera to query
        if camera_id:
            # Use specified camera
            selected_camera = next((c for c in cameras if c["block_id"] == camera_id), None)
            if not selected_camera:
                print(f"❌ Camera {camera_id} not found!")
                return {"error": f"Camera {camera_id} not found"}
        else:
            # Use first camera
            selected_camera = cameras[0]
        
        camera_block_id = selected_camera["block_id"]
        print(f"\n🎯 Querying view from camera: {camera_block_id}")
        print(f"   Position: {selected_camera['position']}")
        print(f"   Rotation: {rotation}")
        print(f"   View distance: {view_distance}")
        
        # 5. Query blocks from camera's perspective using block_id
        await ws.send(json.dumps({
            "type": "get_blocks_list",
            "data": {
                "query_type": "view",
                "block_id": camera_block_id,
                "rotation": list(rotation),
                "view_distance": view_distance
            }
        }))
        
        data = json.loads(await ws.recv())
        blocks = data["data"]["blocks"]
        
        print(f"✅ Retrieved {len(blocks)} blocks in camera view")
        
        # 6. Build result structure
        result = {
            "camera": {
                "block_id": camera_block_id,
                "position": selected_camera["position"],
                "rotation": list(rotation),
                "view_distance": view_distance
            },
            "blocks": blocks,
            "metadata": {
                "total_blocks": len(blocks),
                "query_timestamp": asyncio.get_event_loop().time()
            }
        }
        
        return result


def save_view_data(view_data: Dict[str, Any], output_file: str):
    """Save view data to JSON file.
    
    Args:
        view_data: Camera view data dictionary
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(view_data, f, indent=2)
    print(f"💾 View data saved to: {output_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query camera view data via websocket"
    )
    parser.add_argument(
        "--server",
        default="ws://localhost:8765",
        help="WebSocket server URI (default: ws://localhost:8765)"
    )
    parser.add_argument(
        "--camera-id",
        help="Specific camera block_id to query (default: first available)"
    )
    parser.add_argument(
        "--rotation",
        nargs=2,
        type=float,
        default=[0, 0],
        metavar=("H", "V"),
        help="Camera rotation in degrees (horizontal vertical, default: 0 0)"
    )
    parser.add_argument(
        "--view-distance",
        type=float,
        default=50.0,
        help="View distance (default: 50.0)"
    )
    parser.add_argument(
        "--output",
        default="camera_view_data.json",
        help="Output JSON file (default: camera_view_data.json)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Camera View Query Script")
    print("=" * 70)
    
    try:
        # Query camera view
        view_data = await query_camera_view(
            server_uri=args.server,
            camera_id=args.camera_id,
            rotation=tuple(args.rotation),
            view_distance=args.view_distance
        )
        
        # Check for errors
        if "error" in view_data:
            print(f"\n❌ Query failed: {view_data['error']}")
            return 1
        
        # Save to file
        save_view_data(view_data, args.output)
        
        print("\n" + "=" * 70)
        print("✅ Camera view query completed successfully!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
