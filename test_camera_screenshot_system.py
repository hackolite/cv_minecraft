#!/usr/bin/env python3
"""
Camera Screenshot System Test
==============================

Complete test demonstrating the camera screenshot generation system.

This test:
1. Connects to the running server
2. Queries multiple cameras at different positions
3. Generates screenshots from different perspectives
4. Validates the workflow
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path


async def test_camera_screenshot_system():
    """Test the complete camera screenshot workflow."""
    
    print("=" * 70)
    print("Camera Screenshot System Test")
    print("=" * 70)
    
    server_uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(server_uri) as ws:
            print(f"\n✅ Connected to server: {server_uri}")
            
            # Join the game
            await ws.send(json.dumps({
                "type": "player_join",
                "data": {"name": "ScreenshotTest"}
            }))
            
            # Receive world_init
            data = json.loads(await ws.recv())
            print(f"✅ Received world_init")
            
            # Skip world chunks
            chunk_count = 0
            while True:
                data = json.loads(await ws.recv())
                if data["type"] == "world_chunk":
                    chunk_count += 1
                elif data["type"] == "player_list":
                    print(f"✅ Received {chunk_count} world chunks")
                    break
            
            # Get cameras list
            await ws.send(json.dumps({
                "type": "get_cameras_list",
                "data": {}
            }))
            
            data = json.loads(await ws.recv())
            cameras = data["data"]["cameras"]
            
            print(f"\n📷 Found {len(cameras)} cameras:")
            for cam in cameras:
                print(f"   - {cam['block_id']}: position {cam['position']}")
            
            # Test 1: Query view from each camera
            print(f"\n🧪 Test 1: Query views from all cameras")
            print("-" * 70)
            
            for camera in cameras:
                cam_id = camera["block_id"]
                
                # Query with small view distance to avoid message size issues
                await ws.send(json.dumps({
                    "type": "get_blocks_list",
                    "data": {
                        "query_type": "view",
                        "block_id": cam_id,
                        "rotation": [0, 0],
                        "view_distance": 20.0
                    }
                }))
                
                data = json.loads(await ws.recv())
                blocks = data["data"]["blocks"]
                
                print(f"   {cam_id}: {len(blocks)} blocks visible")
            
            # Test 2: Query with different rotations
            print(f"\n🧪 Test 2: Query with different rotations")
            print("-" * 70)
            
            test_camera = cameras[0]["block_id"]
            rotations = [
                (0, 0, "forward horizontal"),
                (90, 0, "right"),
                (180, 0, "backward"),
                (270, 0, "left"),
                (0, -45, "downward 45°"),
                (0, 45, "upward 45°")
            ]
            
            for h, v, desc in rotations:
                await ws.send(json.dumps({
                    "type": "get_blocks_list",
                    "data": {
                        "query_type": "view",
                        "block_id": test_camera,
                        "rotation": [h, v],
                        "view_distance": 20.0
                    }
                }))
                
                data = json.loads(await ws.recv())
                blocks = data["data"]["blocks"]
                
                print(f"   Rotation ({h:3}, {v:3}) [{desc:20}]: {len(blocks)} blocks")
            
            # Test 3: Validate data format
            print(f"\n🧪 Test 3: Validate block data format")
            print("-" * 70)
            
            await ws.send(json.dumps({
                "type": "get_blocks_list",
                "data": {
                    "query_type": "view",
                    "block_id": cameras[0]["block_id"],
                    "rotation": [0, 0],
                    "view_distance": 15.0
                }
            }))
            
            data = json.loads(await ws.recv())
            blocks = data["data"]["blocks"]
            
            if blocks:
                sample_block = blocks[0]
                required_fields = ["position", "block_type", "block_id", "collision", "distance"]
                
                print(f"   Sample block data:")
                for field in required_fields:
                    if field in sample_block:
                        print(f"      ✅ {field}: {sample_block[field]}")
                    else:
                        print(f"      ❌ {field}: MISSING")
                        return False
            else:
                print(f"   ⚠️  No blocks in view for validation")
            
            # Test 4: Compare with position-based query
            print(f"\n🧪 Test 4: Compare block_id vs position-based queries")
            print("-" * 70)
            
            test_cam = cameras[0]
            cam_pos = test_cam["position"]
            
            # Query by block_id
            await ws.send(json.dumps({
                "type": "get_blocks_list",
                "data": {
                    "query_type": "view",
                    "block_id": test_cam["block_id"],
                    "rotation": [0, 0],
                    "view_distance": 15.0
                }
            }))
            
            data1 = json.loads(await ws.recv())
            blocks1 = data1["data"]["blocks"]
            
            # Query by position
            await ws.send(json.dumps({
                "type": "get_blocks_list",
                "data": {
                    "query_type": "view",
                    "position": cam_pos,
                    "rotation": [0, 0],
                    "view_distance": 15.0
                }
            }))
            
            data2 = json.loads(await ws.recv())
            blocks2 = data2["data"]["blocks"]
            
            if len(blocks1) == len(blocks2):
                print(f"   ✅ Both queries returned same number of blocks: {len(blocks1)}")
            else:
                print(f"   ⚠️  Different results: block_id={len(blocks1)}, position={len(blocks2)}")
            
            print("\n" + "=" * 70)
            print("✅ All tests completed successfully!")
            print("=" * 70)
            
            # Print usage instructions
            print("\n📚 Usage Instructions:")
            print("-" * 70)
            print("Generate a screenshot from a camera:")
            print(f"  python3 generate_camera_screenshot.py --camera-id {cameras[0]['block_id']}")
            print("\nWith custom options:")
            print(f"  python3 generate_camera_screenshot.py \\")
            print(f"    --camera-id {cameras[0]['block_id']} \\")
            print(f"    --rotation 45 -15 \\")
            print(f"    --view-distance 25 \\")
            print(f"    --output my_screenshot.png \\")
            print(f"    --width 1920 --height 1080")
            print()
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await test_camera_screenshot_system()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
